"""Layers C and L (Mexico): higher education, SEP Formato 911 cycle 2024-2025 (school-level files, D-MX-11).
Writes fact_higher_ed_municipality (students by municipality where the school is; on campus = escolarizada,
since distance programmes are registered at the school's seat) and layer_c_mx.json / layer_l_mx.json.
The 911 files have no field of study. C1 and L3 (ICT students) and students_ict_field come from the ANUIES yearbook
2024-2025, the programme-level view of the same 911 data (decision D-MX-14): the build stops unless its total and
on-campus figures equal the 911 files. ICT = broad field 'Tecnologías de la Información y la Comunicación'
(the ISCED-F 06 equivalent); systems/computing programmes classified in other fields are reported apart.

Usage: python -I scripts/build-mexico-cl-higher-ed.py <sep_911_dir> [repo_dir]   (needs openpyxl for the ANUIES file)
"""
import csv, glob, hashlib, json, os, re, sys, unicodedata
from collections import Counter, defaultdict
import openpyxl

src = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
ESC = os.path.join(src, 'educacion_superior_escolarizada_2024_2025.csv')
NOESC = os.path.join(src, 'educacion_superior_no_escolarizada_2024_2025.csv')
UPPER = os.path.join(src, 'educacion_media_superior_2024_2025.csv')
PUBLISHED_SUPERIOR = 5519791  # SEP Principales cifras 2024-2025 (normal 127,938 + licenciatura 4,913,471 + posgrado 478,382)
ANUIES = glob.glob(os.path.join(repo, 'data', 'mexico', 'raw', 'layers_C_L_anuies_anuario_2024_2025', '*.xlsx'))
ANUIES = ANUIES[0] if ANUIES else None
# ANUIES gives names, not codes: short state names and one municipality renamed in the catalogue.
STATE_ALIASES = {'VERACRUZ': 'VERACRUZ DE IGNACIO DE LA LLAVE', 'MICHOACAN': 'MICHOACAN DE OCAMPO', 'COAHUILA': 'COAHUILA DE ZARAGOZA'}
MUNI_ALIASES = {('20', 'MIAHUATLAN DE PORFIRIO DIAZ'): '20059',  # catalogue: Heroica Ciudad de Miahuatlán de Porfirio Díaz
                ('20', 'SAN PEDRO MIXTEPEC'): '20318'}  # two Oaxaca municipalities share this name; the 911 files place the students in 20318
SYSTEMS = re.compile(r'SISTEMAS COMPUTACIONALES|INFORMATICA|COMPUTACION|SOFTWARE|SISTEMAS DE INFORMACION')


def key(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', str(s or '')) if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).upper().strip()
TOLERANCE = 0.01
# Student, new-entrant and women columns per level and modality.
LEVELS = {
    'esc': {'tecnico_superior': ('alumnos_tec_esc', 'ni_tec_total_esc', 'tec_muj_esc'),
            'licenciatura': ('alumnos_lic_esc', 'ni_lic_total_esc', 'lic_muj_esc'),
            'normal': ('alumnos_lic_esc_normal', 'ni_normal_total_esc', 'normal_muj_esc'),
            'posgrado': ('alum_pos_esc', 'ni_pos_totales_esc', 'pos_mujeres_esc')},
    'no_esc': {'tecnico_superior': ('total_alumnos_tec_no_esc', 'ni_tec_total_no_esc', 'tec_muj_no_esc'),
               'licenciatura': ('alumnos_lic_no_esc', 'ni_lic_total_no_esc', 'lic_muj_no_esc'),
               'posgrado': ('alum_pos_no_esc', 'ni_pos_totales_no_esc', 'pos_mujeres_no_esc')},
}


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


def norm(s):
    return re.sub(r'\s+', ' ', s.upper().replace('Ó', 'O').replace('É', 'E').replace('Á', 'A').replace('Í', 'I').replace('Ú', 'U')).strip()


with open(os.path.join(CSV_DIR, 'geo_municipality.csv'), encoding='utf-8') as f:
    munis = {r['municipality_code']: r['department_code'] for r in csv.DictReader(f)}

records = []  # one per school and modality with students
errors = []
for path, mode in ((ESC, 'esc'), (NOESC, 'no_esc')):
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        missing = [c for spec in LEVELS[mode].values() for c in spec if c not in reader.fieldnames]
        if missing:
            sys.exit(f'{os.path.basename(path)}: missing columns {missing}')
        for r in reader:
            code = r['cve_entidad'].zfill(2) + r['cve_municipio'].zfill(3)
            for level, (col, ni, women) in LEVELS[mode].items():
                if n(r[col]) == 0 and n(r[ni]) == 0:
                    continue
                if code not in munis:
                    errors.append(f'{r["escuela"]}: municipality {code} not in catalogue')
                records.append({'mode': mode, 'level': level, 'code': code, 'institution': r['institucion'], 'name': r['nombre_institucion'],
                                'school': r['escuela'], 'public': 'blico' in r['control'], 'subcontrol': r['c_subcontrol'],
                                'students': n(r[col]), 'new': n(r[ni]), 'women': n(r[women])})
total = sum(x['students'] for x in records)
diff = 100 * (total - PUBLISHED_SUPERIOR) / PUBLISHED_SUPERIOR
if abs(diff) > 100 * TOLERANCE:
    errors.append(f'higher education {total:,} vs published {PUBLISHED_SUPERIOR:,} ({diff:.2f}%)')
if errors:
    sys.exit('Layers C/L checks failed:\n' + '\n'.join(errors[:30]))

by_muni = defaultdict(lambda: Counter())
for x in records:
    by_muni[x['code']]['total'] += x['students']
    if x['mode'] == 'esc':
        by_muni[x['code']]['on_campus'] += x['students']
# ───────────── ANUIES programme-level file: ICT field (C1, L3, students_ict_field) ─────────────
ict = None
if ANUIES:
    with open(os.path.join(CSV_DIR, 'geo_department.csv'), encoding='utf-8') as f:
        state_code = {key(r['name']): r['department_code'] for r in csv.DictReader(f)}
    with open(os.path.join(CSV_DIR, 'geo_municipality.csv'), encoding='utf-8') as f:
        muni_code, ambiguous = {}, set()
        for r in csv.DictReader(f):
            k = (r['department_code'], key(r['name']))
            if k in muni_code:
                ambiguous.add(k)
            muni_code[k] = r['municipality_code']
    ws = openpyxl.load_workbook(ANUIES, read_only=True, data_only=True).worksheets[0]
    ws.reset_dimensions()
    it = ws.iter_rows(values_only=True)
    col = {str(h).strip(): i for i, h in enumerate(next(it))}
    programmes = []
    for r in it:
        if not r or not r[col['ENTIDAD']]:
            continue
        st = state_code.get(STATE_ALIASES.get(key(r[col['ENTIDAD']]), key(r[col['ENTIDAD']])))
        mk = (st, key(r[col['MUNICIPIO']]))
        code = MUNI_ALIASES.get(mk) or muni_code.get(mk)
        if mk in ambiguous and mk not in MUNI_ALIASES and n(r[col['Matrícula Total']]):
            errors.append(f'ANUIES municipality name is shared by two catalogue codes, add an alias: {mk}')
            continue
        if code is None:
            errors.append(f'ANUIES municipality not in catalogue: {r[col["ENTIDAD"]]} / {r[col["MUNICIPIO"]]}')
            continue
        programmes.append({'code': code, 'field': key(r[col['CAMPO AMPLIO']]), 'detail': str(r[col['CAMPO DETALLADO']] or ''),
                           'programme': key(r[col['PROGRAMA (CARRERA)']]), 'level': r[col['NIVEL']], 'mode': r[col['MODALIDAD']],
                           'public': key(r[col['SOSTENIMIENTO']]) == 'PUBLICO', 'subsystem': key(r[col['SUBSISTEMA']]), 'students': n(r[col['Matrícula Total']]),
                           'women': n(r[col['Matrícula Mujeres']]), 'new': n(r[col['Nuevo Ingreso Total']]), 'graduates': n(r[col['Egresados Total']])})
    a_total = sum(p['students'] for p in programmes)
    a_campus = sum(p['students'] for p in programmes if p['mode'] == 'ESCOLARIZADA')
    if a_total != total:
        errors.append(f'ANUIES total {a_total:,} differs from the 911 files {total:,}')
    if a_campus != sum(v['on_campus'] for v in by_muni.values()):
        errors.append(f'ANUIES on-campus total {a_campus:,} differs from the 911 escolarizada files')
    if errors:
        sys.exit('ANUIES checks failed:\n' + '\n'.join(errors[:30]))
    ict_rows = [p for p in programmes if p['field'].startswith('TECNOLOGIAS DE LA INFORMACION')]
    systems_outside = [p for p in programmes if not p['field'].startswith('TECNOLOGIAS DE LA INFORMACION') and SYSTEMS.search(p['programme'])]
    ict_by_muni = Counter()
    for p in ict_rows:
        if p['students']:  # programmes listed with zero enrolment do not place students anywhere
            ict_by_muni[p['code']] += p['students']
    muni_totals = Counter()
    for p in programmes:
        if p['students']:
            muni_totals[p['code']] += p['students']
    moved = {c: (muni_totals.get(c, 0), by_muni[c]['total'] if c in by_muni else 0) for c in set(muni_totals) | set(by_muni)
             if muni_totals.get(c, 0) != (by_muni[c]['total'] if c in by_muni else 0)}
    if moved:
        sys.exit(f'ANUIES and 911 municipal totals differ (ANUIES, 911): {dict(list(moved.items())[:10])}')
    unplaced = [c for c in ict_by_muni if c not in by_muni]
    if unplaced:
        sys.exit(f'ICT students in municipalities without 911 higher-education records: {unplaced}')
    ict_total = sum(p['students'] for p in ict_rows)
    ict_campus = Counter()
    for p in ict_rows:
        if p['mode'] == 'ESCOLARIZADA':
            ict_campus[p['code']] += p['students']
    field_totals = Counter()
    for p in programmes:
        field_totals[p['field']] += p['students']
    ict = {
        'C1_ict_students': ict_total,
        'C1_ict_students_on_campus': sum(ict_campus.values()),
        'C1_ict_by_detailed_field': dict(Counter({d: sum(p['students'] for p in ict_rows if p['detail'] == d) for d in {p['detail'] for p in ict_rows}}).most_common()),
        'C1_ict_by_level': dict(Counter({lv: sum(p['students'] for p in ict_rows if p['level'] == lv) for lv in {p['level'] for p in ict_rows}}).most_common()),
        'C1_ict_public_pct': pct(sum(p['students'] for p in ict_rows if p['public']), ict_total),
        'C1_ict_women_pct': pct(sum(p['women'] for p in ict_rows), ict_total),
        'C1_ict_distance_pct': pct(sum(p['students'] for p in ict_rows if p['mode'] != 'ESCOLARIZADA'), ict_total),
        'C1_systems_programmes_outside_ict_field': sum(p['students'] for p in systems_outside),
        'C2_ict_on_campus_top_municipalities': [{'municipality_code': c, 'students': v, 'share_pct': pct(v, sum(ict_campus.values()))}
                                                for c, v in ict_campus.most_common(10)],
        'L3_ict_share_pct': pct(ict_total, total),
        'L3_by_broad_field': {f: {'students': v, 'pct': pct(v, total)} for f, v in field_totals.most_common()},
        'L4_ict_first_year_entrants': sum(p['new'] for p in ict_rows),
        'ict_graduates': sum(p['graduates'] for p in ict_rows),
        # TecNM from the ANUIES subsystem: federal and decentralised units of the Tecnológico Nacional de México.
        'L5_tecnm_students': sum(p['students'] for p in programmes if 'TECNOLOGICO NACIONAL DE MEXICO' in p['subsystem']),
        'L5_tecnm_by_unit': {u: sum(p['students'] for p in programmes if p['subsystem'] == u) for u in sorted({p['subsystem'] for p in programmes if 'TECNOLOGICO NACIONAL DE MEXICO' in p['subsystem']})},
    }

rows = [{'municipality_code': c, 'department_code': munis[c], 'students_total': v['total'], 'students_on_campus': v['on_campus'],
         'students_ict_field': ict_by_muni.get(c, 0) if ict else ''}
        for c, v in sorted(by_muni.items()) if v['total'] > 0]
with open(os.path.join(CSV_DIR, 'fact_higher_ed_municipality.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(rows)

on_campus = sum(r['students_on_campus'] for r in rows)
ranked = sorted(rows, key=lambda r: -r['students_on_campus'])
def cities_to(share):
    acc = 0
    for i, r in enumerate(ranked, 1):
        acc += r['students_on_campus']
        if acc >= share * on_campus:
            return i
# L5: capacitación para el trabajo (SEP 911, cycle 2024-2025, by state). The states must add up to the file's TOTAL row.
capacitacion = None
CAP = glob.glob(os.path.join(repo, 'data', 'mexico', 'raw', 'layer_L5_sep_capacitacion_para_el_trabajo_2024_2025', '*.xlsx'))
if CAP:
    with open(os.path.join(CSV_DIR, 'geo_department.csv'), encoding='utf-8') as f:
        cap_states = {key(r['name']): r['department_code'] for r in csv.DictReader(f)}
    sheet = openpyxl.load_workbook(CAP[0], read_only=True, data_only=True).worksheets[0]
    sheet.reset_dimensions()
    cap_rows = [r for r in sheet.iter_rows(values_only=True) if r and r[0]]
    hdr = next(i for i, r in enumerate(cap_rows) if str(r[0]).strip() == 'Entidad')
    ci = {str(h).strip(): i for i, h in enumerate(cap_rows[hdr])}
    by_state, total_row = {}, None
    for r in cap_rows[hdr + 1:]:
        name = key(r[0])
        if name == 'TOTAL':
            total_row = r
            continue
        code = cap_states.get(STATE_ALIASES.get(name, name))
        if code is None:
            sys.exit(f'Capacitación para el trabajo: state not matched: {r[0]}')
        by_state[code] = {'students': n(r[ci['Alumnos']]), 'schools': n(r[ci['Escuelas']]), 'women': n(r[ci['Alumnos Mujeres']])}
    cap_total = {k: sum(v[k] for v in by_state.values()) for k in ('students', 'schools', 'women')}
    if len(by_state) != 32 or total_row is None or cap_total['students'] != n(total_row[ci['Alumnos']]) or cap_total['schools'] != n(total_row[ci['Escuelas']]):
        sys.exit('Capacitación para el trabajo: states do not add up to the TOTAL row')
    capacitacion = {'students': cap_total['students'], 'schools': cap_total['schools'], 'women_pct': pct(cap_total['women'], cap_total['students']),
                    'by_state': {c: v['students'] for c, v in sorted(by_state.items())}, 'file': os.path.basename(CAP[0]), 'sha256': sha256(CAP[0])}

undergrad = [x for x in records if x['level'] in ('tecnico_superior', 'licenciatura', 'normal')]
first_year = sum(x['new'] for x in undergrad)
with open(UPPER, encoding='utf-8-sig', newline='') as f:
    upper = list(csv.DictReader(f))
ms3 = sum(n(r['alumnos_03']) for r in upper)
conalep = [r for r in upper if 'CONALEP' in norm(r['nom_escuela']) or 'EDUCACION PROFESIONAL TECNICA' in norm(r['nom_escuela'])]
tecnm = [x for x in records if x['public'] and norm(x['name']).startswith('INSTITUTO TECNOLOGICO')]
level_totals = Counter()
for x in records:
    level_totals[x['level']] += x['students']
institutions = {x['institution'] for x in records if x['students'] > 0}

common = {'country': 'MX', 'source_id': 'SEP_911_2024_2025', 'period': 'school cycle 2024-2025 (start of cycle)',
          'sources': [{'file': os.path.basename(p), 'sha256': sha256(p)} for p in (ESC, NOESC) + ((ANUIES,) if ict else ())],
          'check_total_vs_principales_cifras': {'file_total': total, 'published': PUBLISHED_SUPERIOR, 'difference_pct': round(diff, 3)}}
layer_c = {**common, 'layer': 'C', 'indicators': {
    'C1_ict_students': ict['C1_ict_students'] if ict else None,
    **({k: v for k, v in ict.items() if k.startswith(('C1_', 'C2_'))} if ict else {}),
    'C2_on_campus_students': on_campus,
    'C2_top_municipalities': [{'municipality_code': r['municipality_code'], 'students_on_campus': r['students_on_campus'],
                               'share_pct': pct(r['students_on_campus'], on_campus)} for r in ranked[:10]],
    'C3_municipalities_to_reach': {'50pct': cities_to(0.5), '75pct': cities_to(0.75), '90pct': cities_to(0.9)},
    'C4_level_pct': {k: pct(v, total) for k, v in level_totals.items()},
    'C4_public_pct': pct(sum(x['students'] for x in records if x['public']), total),
    'C4_distance_pct': pct(sum(x['students'] for x in records if x['mode'] == 'no_esc'), total),
    'C4_women_pct': pct(sum(x['women'] for x in records), total)},
    'notes': {'C1_ict_students': ('ANUIES yearbook 2024-2025 (programme-level 911 data; totals equal SEP exactly; D-MX-14): broad field "Tecnologías de la Información y la Comunicación", '
                                  'the ISCED-F 06 equivalent, all levels and modalities. Systems/computing programmes classified in other broad fields are reported apart '
                                  '(C1_systems_programmes_outside_ict_field), as Colombia shows systems and ICT field separately.')
                                 if ict else 'Not available: no programme-level file supplied.',
              'C2': 'On campus = escolarizada; distance programmes are registered at the school seat, so cities use on-campus figures only (template rule).'}}
layer_l = {**common, 'layer': 'L', 'indicators': {
    'L1_students': total, 'L1_institutions': len(institutions), 'L1_schools': len({x['school'] for x in records if x['students'] > 0}),
    'L2_by_level': dict(level_totals),
    'L2_by_subcontrol': dict(Counter({k: sum(x['students'] for x in records if x['subcontrol'] == k) for k in {x['subcontrol'] for x in records}})),
    'L2_by_modality': {'escolarizada': sum(x['students'] for x in records if x['mode'] == 'esc'), 'no_escolarizada': sum(x['students'] for x in records if x['mode'] == 'no_esc')},
    'L3_ict_share': ict['L3_ict_share_pct'] if ict else None,
    **({k: v for k, v in ict.items() if k.startswith(('L3_by', 'L4_ict', 'ict_', 'L5_tecnm'))} if ict else {}),
    'L4_first_year_entrants': first_year,
    'L4_by_level': {k: sum(x['new'] for x in undergrad if x['level'] == k) for k in ('tecnico_superior', 'licenciatura', 'normal')},
    **({} if ict else {'L5_tecnm_approx_students': sum(x['students'] for x in tecnm)}),
    'L5_conalep_approx_students': sum(n(r['alumnos']) for r in conalep), 'L5_conalep_approx_schools': len(conalep),
    'L5_capacitacion_para_el_trabajo': capacitacion,
    'L6_on_campus_top_municipalities': layer_c['indicators']['C2_top_municipalities'],
    'L6_largest_institutions_on_campus': [{'institution': k, 'students': v} for k, v in Counter(
        {name: sum(x['students'] for x in records if x['name'] == name and x['mode'] == 'esc') for name in {x['name'] for x in records}}).most_common(10)],
    'L7_media_superior_grade3': ms3, 'L7_first_year_entrants': first_year},
    'notes': {'L3_ict_share': 'Percent of all higher-education students in the ICT broad field (ANUIES programme-level file, D-MX-14).' if ict else 'Not available without a programme-level file.',
              'L4': 'New entrants (ni_) in técnico superior, licenciatura and normal, both modalities; posgrado excluded.',
              'L5': ('TecNM = the ANUIES subsystems "Unidades federales" and "Unidades descentralizadas del Tecnológico Nacional de México" (exact). ' if ict else 'Approximation: TecNM = public institutions named "Instituto Tecnológico…". ') + 'CONALEP = media superior schools named CONALEP or Educación Profesional Técnica. The 911 files carry no TecNM or CONALEP flag. Capacitación para el trabajo comes from its own 911 form (SEP, cycle 2024-2025, by state); it is outside higher education and is not added to L1.',
              'L7': '3º of media superior vs first-year entrants of the same cycle.'}}
for name, doc in (('layer_c_mx.json', layer_c), ('layer_l_mx.json', layer_l)):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write('\n')
print(json.dumps({'total': total, 'diff_pct': round(diff, 3), 'on_campus': on_campus, 'municipalities': len(rows), 'C3': layer_c['indicators']['C3_municipalities_to_reach'],
                  'public_pct': layer_c['indicators']['C4_public_pct'], 'women_pct': layer_c['indicators']['C4_women_pct'], 'institutions': len(institutions),
                  'L4': first_year, 'L5_tecnm': layer_l['indicators'].get('L5_tecnm_students', layer_l['indicators'].get('L5_tecnm_approx_students')), 'L5_conalep': layer_l['indicators']['L5_conalep_approx_students'],
                  'L7': [ms3, first_year]}, ensure_ascii=False))
