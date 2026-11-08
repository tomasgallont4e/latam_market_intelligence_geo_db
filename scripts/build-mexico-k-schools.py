"""Layer K (Mexico): schools with the target grades, SEP Formato 911, cycle 2024-2025.
Target grades: 3º de secundaria + 1º to 3º de media superior (template annex 1; grades 4-5 of four-year technical
programmes are left out). School = CCT work-centre code (decision D-MX-12): secundaria clave_cct; media superior
escuela[:10] (escuela = CCT + shift digit). Campuses (media superior plantel) are reported as an extra count.
Rural = locality classed 'R' (AMBITO) in the INEGI Catálogo Único. Writes fact_schools_municipality and layer_k_mx.json.

Usage: python -I scripts/build-mexico-k-schools.py <sep_911_dir> [repo_dir]
"""
import csv, glob, hashlib, json, os, statistics, sys
from collections import Counter, defaultdict

src = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
LOCALITIES = glob.glob(os.path.join(repo, 'data', 'mexico', 'raw', 'inegi_catalogo_unico_202610', 'localidad', '*.csv'))[0]
BASIC = os.path.join(src, 'educacion_basica_2024_2025.csv')
UPPER = os.path.join(src, 'educacion_media_superior_2024_2025.csv')
# SEP, Principales cifras del Sistema Educativo Nacional 2024-2025 (enrolment, all grades).
PUBLISHED = {'secundaria': 6293530, 'media_superior': 5492491}
TOLERANCE = 0.01
SIZE_BANDS = [(49, '1-49'), (99, '50-99'), (199, '100-199'), (499, '200-499'), (10 ** 9, '500+')]


def n(v):
    return int(float(v)) if v not in ('', None) else 0


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def pct(a, b):
    return round(100 * a / b, 1) if b else None


with open(os.path.join(CSV_DIR, 'geo_municipality.csv'), encoding='utf-8') as f:
    munis = {r['municipality_code']: r['department_code'] for r in csv.DictReader(f)}
with open(LOCALITIES, encoding='utf-8-sig', newline='') as f:
    ambito = {r['CVEGEO']: r['AMBITO'] for r in csv.DictReader(f)}

# One record per CCT with its target-grade students.
schools = {}  # cct -> dict
errors, unjoined_munis, unknown_locality = [], Counter(), 0
totals = Counter()


def add(cct, level, ent, mun, loc, public, grades, women, campus):
    global unknown_locality
    ent, mun, loc = ent.zfill(2), mun.zfill(3), loc.zfill(4)
    code = ent + mun
    if code not in munis:
        unjoined_munis[code] += sum(grades.values())
    rural = ambito.get(code + loc)
    if rural is None:
        unknown_locality += sum(grades.values())
    s = schools.setdefault(cct, {'level': level, 'municipality_code': code, 'department_code': ent, 'public': public,
                                 'rural': rural == 'R', 'grades': Counter(), 'women': 0, 'campuses': set()})
    s['grades'].update(grades)
    s['women'] += women
    s['campuses'].add(campus)


with open(BASIC, encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        if r['nivel'] != 'Secundaria':
            continue
        totals['secundaria_all_grades'] += n(r['insc_t'])
        totals['secundaria_by_subnivel|' + r['subnivel']] += n(r['insc_03'])
        if n(r['insc_03']) > 0:
            add(r['clave_cct'], 'secundaria', r['entidad'], r['municipio'], r['localidad'], r['control'].startswith('P') and 'blico' in r['control'],
                {'sec3': n(r['insc_03'])}, n(r['muj_03']), r['clave_cct'])
with open(UPPER, encoding='utf-8-sig', newline='') as f:
    for r in csv.DictReader(f):
        totals['media_superior_all_grades'] += n(r['alumnos'])
        g = {'ms1': n(r['alumnos_01']), 'ms2': n(r['alumnos_02']), 'ms3': n(r['alumnos_03'])}
        totals['media_superior_by_subnivel|' + r['subnivel']] += sum(g.values())
        if sum(g.values()) > 0:
            add(r['escuela'][:10], 'media_superior', r['entidad'], r['cv_mun'], r['cv_loc'], 'blico' in r['control'], g,
                n(r['mujeres_01']) + n(r['mujeres_02']) + n(r['mujeres_03']), r['plantel'])

checks = {}
for key, published in PUBLISHED.items():
    got = totals[f'{key}_all_grades']
    checks[key] = {'file_total': got, 'published': published, 'difference_pct': round(100 * (got - published) / published, 3),
                   'within_1pct': abs(got - published) <= TOLERANCE * published}
    if not checks[key]['within_1pct']:
        errors.append(f'{key}: file {got:,} vs published {published:,}')
if unjoined_munis:
    errors.append(f'municipality codes not in the catalogue: {dict(unjoined_munis.most_common(10))}')
if errors:
    sys.exit('Layer K checks failed:\n' + '\n'.join(errors))

for s in schools.values():
    s['target'] = sum(s['grades'].values())
by_muni = defaultdict(list)
for s in schools.values():
    by_muni[s['municipality_code']].append(s)
rows = []
for code in sorted(by_muni):
    ss = by_muni[code]
    rows.append({
        'municipality_code': code, 'department_code': munis[code],
        'students_target': sum(s['target'] for s in ss),
        'students_sec3': sum(s['grades']['sec3'] for s in ss),
        'students_ms1': sum(s['grades']['ms1'] for s in ss), 'students_ms2': sum(s['grades']['ms2'] for s in ss),
        'students_ms3': sum(s['grades']['ms3'] for s in ss),
        'students_public': sum(s['target'] for s in ss if s['public']),
        'students_rural': sum(s['target'] for s in ss if s['rural']),
        'schools': len(ss), 'schools_public': sum(1 for s in ss if s['public']),
        'reach_cap100': sum(min(s['target'], 100) for s in ss),
    })
with open(os.path.join(CSV_DIR, 'fact_schools_municipality.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(rows)

all_s = list(schools.values())
target = sum(s['target'] for s in all_s)
sizes = Counter(next(label for limit, label in SIZE_BANDS if s['target'] <= limit) for s in all_s)
by_state = defaultdict(lambda: Counter())
for s in all_s:
    by_state[s['department_code']]['students'] += s['target']
    by_state[s['department_code']]['schools'] += 1
technical = sum(v for k, v in totals.items() if k.startswith('media_superior_by_subnivel|') and ('Tecnol' in k or 'cnico' in k))
layer = {
    'country': 'MX', 'layer': 'K', 'source_id': 'SEP_911_2024_2025', 'period': 'school cycle 2024-2025',
    'sources': [{'file': os.path.basename(p), 'sha256': sha256(p)} for p in (BASIC, UPPER)],
    'target_grades': '3º de secundaria + 1º, 2º and 3º de media superior',
    'indicators': {
        'K1_schools_cct': len(all_s),
        'K1_by_level': dict(Counter(s['level'] for s in all_s)),
        'K1_campuses': len({c for s in all_s if s['level'] == 'secundaria' for c in s['campuses']}) + len({c for s in all_s if s['level'] == 'media_superior' for c in s['campuses']}),
        'K2_students_by_grade': {'sec3': sum(s['grades']['sec3'] for s in all_s), 'ms1': sum(s['grades']['ms1'] for s in all_s),
                                 'ms2': sum(s['grades']['ms2'] for s in all_s), 'ms3': sum(s['grades']['ms3'] for s in all_s)},
        'K2_students_target': target,
        'K3_public_schools': sum(1 for s in all_s if s['public']), 'K3_public_students_pct': pct(sum(s['target'] for s in all_s if s['public']), target),
        'K4_women_pct': pct(sum(s['women'] for s in all_s), target),
        'K4_rural_pct': pct(sum(s['target'] for s in all_s if s['rural']), target),
        'K4_technical_track_students': technical,
        'K4_technical_track_note': 'Media superior grades 1-3 in Bachillerato Tecnológico, Profesional Técnico Bachiller and Profesional Técnico (incl. CONALEP).',
        'K4_under_18_pct': None,
        'K5_schools_by_size': {label: sizes[label] for _, label in SIZE_BANDS},
        'K5_median_students_per_school': statistics.median(s['target'] for s in all_s),
        'K6_reach_cap100': sum(min(s['target'], 100) for s in all_s),
        'K6_reach_cap100_media_superior_only': sum(min(s['target'], 100) for s in all_s if s['level'] == 'media_superior'),
        'K7_by_state': {k: dict(v) for k, v in sorted(by_state.items())},
        'K7_top_municipalities': sorted(({'municipality_code': r['municipality_code'], 'students': r['students_target'], 'schools': r['schools']} for r in rows),
                                        key=lambda x: -x['students'])[:10],
    },
    'checks': {'enrolment_vs_principales_cifras': checks,
               'students_with_locality_not_in_catalogue': unknown_locality,
               'subnivel_target_students': {k.split('|', 1)[1] + (' (secundaria 3º)' if k.startswith('secundaria') else ' (media superior 1-3)'): v
                                            for k, v in totals.items() if '|' in k}},
    'notes': {'K4_under_18_pct': 'Not available: the 911 school files give enrolment by grade and sex, not by age.',
              'K6': 'Sum over CCT of min(target-grade students, 100); the second figure starts at the first grade of media superior.',
              'school_unit': 'School = CCT code (D-MX-12). A site offering secundaria and media superior has two CCTs; campuses (planteles) are given in K1_campuses.',
              'rural': 'Locality AMBITO = R in the INEGI Catálogo Único (2026-10); students whose locality is not found are counted as not rural.'},
}
with open(os.path.join(OUT, 'layer_k_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
ind = layer['indicators']
print(json.dumps({'checks': {k: v['difference_pct'] for k, v in checks.items()}, 'K1': ind['K1_schools_cct'], 'campuses': ind['K1_campuses'],
                  'K2': ind['K2_students_target'], 'public_pct': ind['K3_public_students_pct'], 'women_pct': ind['K4_women_pct'],
                  'rural_pct': ind['K4_rural_pct'], 'K5_median': ind['K5_median_students_per_school'], 'K6': ind['K6_reach_cap100'],
                  'municipalities': len(rows), 'locality_not_found_students': unknown_locality}, ensure_ascii=False))
