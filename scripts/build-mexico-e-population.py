"""Layer E (Mexico): population and city typology.
Population: CONAPO, Reconstrucción y proyecciones de la población de los municipios de México 1990-2040 (release 2024),
mid-year population 2024 (men + women), to match the 2024-2025 school cycle (decision D-MX-11).
E1 = municipal share of IT establishments (layer D, DENUE 05/2026) ÷ municipal share of on-campus higher-education
students (layer C, 911 2024-2025); E2 = on-campus students per 100,000 inhabitants. Municipalities with fewer than
3,000 on-campus students are left out of both ratios (template rule).
Writes fact_population_municipality and layer_e_mx.json.

Usage: python -I scripts/build-mexico-e-population.py <conapo_00_Republica_mexicana.zip> [repo_dir]   (needs openpyxl)
"""
import csv, hashlib, io, json, os, sys, zipfile
from collections import Counter
import openpyxl

src = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
MEMBER = '00_Republica_mexicana/2_Gran_Gedad_00_RM.xlsx'
YEAR = 2024
MIN_STUDENTS = 3000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read(table):
    with open(os.path.join(CSV_DIR, f'{table}.csv'), encoding='utf-8') as f:
        return list(csv.DictReader(f))


munis = {r['municipality_code']: r for r in read('geo_municipality')}
with zipfile.ZipFile(src) as z:
    raw = z.read(MEMBER)
ws = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True).worksheets[0]
ws.reset_dimensions()  # the sheet declares a 1x1 size; read every row
rows = ws.iter_rows(values_only=True)
header = next(rows)
idx = {h: i for i, h in enumerate(header)}
population, names = Counter(), {}
for r in rows:
    if r[idx['AÑO']] != YEAR:
        continue
    code = str(r[idx['CLAVE']]).zfill(5)
    population[code] += int(r[idx['POB_TOTAL']])
    names[code] = r[idx['NOM_MUN']]
errors = [f'CONAPO municipality {c} ({names[c]}) not in the catalogue' for c in population if c not in munis]
if errors:
    sys.exit('Layer E checks failed:\n' + '\n'.join(errors))
not_in_conapo = [{'municipality_code': c, 'name': munis[c]['name']} for c in sorted(munis) if c not in population]

out_rows = [{'municipality_code': c, 'department_code': munis[c]['department_code'], 'year': YEAR, 'population': population[c]} for c in sorted(population)]
with open(os.path.join(CSV_DIR, 'fact_population_municipality.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(out_rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(out_rows)

# City typology (E1, E2) on municipalities with at least 3,000 on-campus students.
students = {r['municipality_code']: int(r['students_on_campus']) for r in read('fact_higher_ed_municipality')}
it = {r['municipality_code']: int(r['it_companies_active']) for r in read('fact_companies_municipality')}
students_total, it_total = sum(students.values()), sum(it.values())
typology = []
for code, s in students.items():
    if s < MIN_STUDENTS:
        continue
    pop = population.get(code)
    typology.append({
        'municipality_code': code, 'name': munis[code]['name'], 'students_on_campus': s, 'it_establishments': it.get(code, 0),
        'E1_it_share_over_student_share': round((it.get(code, 0) / it_total) / (s / students_total), 2),
        'population_2024': pop,
        'E2_students_per_100k': round(100000 * s / pop, 1) if pop else None,
    })
typology.sort(key=lambda r: -r['E1_it_share_over_student_share'])
layer = {
    'country': 'MX', 'layer': 'E', 'source_id': 'CONAPO_PROY_MUN_2024',
    'source': {'file': os.path.basename(src), 'member': MEMBER, 'member_sha256': sha256(raw), 'variable': 'POB_TOTAL (men + women), mid-year', 'year': YEAR},
    'indicators': {
        'population_2024_national': sum(population.values()),
        'municipalities_with_population': len(population),
        'municipalities_not_in_conapo': not_in_conapo,
        'municipalities_in_typology': len(typology),
        'E1_highest': typology[:10], 'E1_lowest': typology[-10:],
        'E2_highest': sorted((r for r in typology if r['E2_students_per_100k'] is not None), key=lambda r: -r['E2_students_per_100k'])[:10],
        'typology': typology,
    },
    'notes': {
        'E1': 'Share of national IT establishments (DENUE 05/2026: SCIAN 541510, 518210, 519290) divided by share of national on-campus higher-education students (911 2024-2025). Above 1: the municipality hosts more IT establishments than its share of students ("employs more than it trains").',
        'E2': 'On-campus higher-education students per 100,000 inhabitants (CONAPO 2024).',
        'threshold': 'Municipalities with fewer than 3,000 on-campus students are excluded from E1 and E2 (template rule).',
        'periods': 'Population 2024 matches the 2024-2025 school cycle (D-MX-11); DENUE is 05/2026, the only edition used for D, J and N.',
        'missing': 'Municipalities created after CONAPO\'s 2024 release have no projection and are left without population (never zero).',
    },
}
with open(os.path.join(OUT, 'layer_e_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'population_2024': sum(population.values()), 'municipalities': len(population), 'not_in_conapo': not_in_conapo,
                  'typology': len(typology), 'E1_top3': [(r['name'], r['E1_it_share_over_student_share']) for r in typology[:3]],
                  'E1_bottom3': [(r['name'], r['E1_it_share_over_student_share']) for r in typology[-3:]]}, ensure_ascii=False))
