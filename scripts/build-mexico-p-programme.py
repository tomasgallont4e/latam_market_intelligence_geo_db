"""Layer P (Mexico): the high-school programme sized with official numbers, plus N4 (businesses per school).
Built from layer K (SEP 911 2024-2025: schools by CCT, median size, reach with a cap of 100), layer N (DENUE 05/2026
private businesses, N1) and layer I (2025 average FIX). The 10% conversion is an ASSUMPTION, never a measured rate.
P4 (donations) and P5 (minors' data) quote the supplied law texts; the build stops if the quoted phrase is missing.
Run after build-mexico-denue.py, build-mexico-k-schools.py and build-mexico-i-price.py (it adds N4 to layer_n_mx.json).

Usage: python -I scripts/build-mexico-p-programme.py <data/mexico/raw> [repo_dir]   (needs pypdf, cryptography)
"""
import csv, json, os, re, sys
from collections import Counter
import pypdf

raw = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
CONVERSION = 0.10  # template assumption
TEAM_PLAN_USD = 250
LISR = os.path.join(raw, 'layers_O_P_leyes_camara_diputados', 'LISR_ultima_reforma_DOF_2024-04-01.pdf')
LFPDPPP = os.path.join(raw, 'layers_O_P_leyes_camara_diputados', 'LFPDPPP_ultima_reforma_DOF_2025-11-14.pdf')
MAP_COLUMNS = ['layer', 'metric_id', 'scope_type', 'scope_id', 'group_id', 'persona_id', 'indicator', 'category', 'value', 'unit',
               'period', 'comparison_period', 'numerator', 'denominator', 'status', 'source_id', 'method', 'limitations']


def load(name):
    with open(os.path.join(OUT, name), encoding='utf-8') as f:
        return json.load(f)


def pdf_text(path):
    return re.sub(r'\s+', ' ', ' '.join((p.extract_text() or '') for p in pypdf.PdfReader(path).pages))


k, n, i = load('layer_k_mx.json')['indicators'], load('layer_n_mx.json'), load('layer_i_mx.json')['indicators']
schools, median, reach = k['K1_schools_cct'], k['K5_median_students_per_school'], k['K6_reach_cap100']
businesses, fix = n['indicators']['N1_businesses'], i['I1_fix_2025_average']

lisr, lfp = pdf_text(LISR), pdf_text(LFPDPPP)
evidence = {
    'P4': (lisr, r'Art[ií]culo 27\. Las deducciones autorizadas.{0,400}donativos no onerosos ni remunerativos'),
    'P4_cap': (lisr, r'donatarias autorizadas distintas, exceda del 7% citado'),
    'P5_consent': (lfp, r'Art[ií]culo 7\. Todo tratamiento de datos personales estar[aá] sujeto al consentimiento'),
}
missing = [key for key, (txt, rx) in evidence.items() if not re.search(rx, txt, re.I)]
minors_article = bool(re.search(r'menores de edad|niñas, niños|ni[ñn]as y ni[ñn]os', lfp, re.I))
if missing:
    sys.exit(f'Layer P evidence not found: {missing}')

# N4: businesses per school, national and by state (businesses = N1 private universe; schools = K1 CCT).
with open(os.path.join(CSV_DIR, 'fact_companies_municipality.csv'), encoding='utf-8') as f:
    biz_state = Counter()
    for r in csv.DictReader(f):
        biz_state[r['department_code']] += int(r['businesses'])
with open(os.path.join(CSV_DIR, 'fact_schools_municipality.csv'), encoding='utf-8') as f:
    sch_state = Counter()
    for r in csv.DictReader(f):
        sch_state[r['department_code']] += int(r['schools'])
per_school = round(businesses / schools, 1)
n['indicators']['N4_businesses_per_school'] = per_school
n['indicators']['N4_businesses_per_school_by_state'] = {s: round(biz_state[s] / sch_state[s], 1) for s in sorted(sch_state) if sch_state[s]}
n['notes']['N4_businesses_per_school'] = 'N1 private businesses (DENUE 05/2026) ÷ K1 schools by CCT (SEP 911 2024-2025); added by build-mexico-p-programme.py.'
with open(os.path.join(OUT, 'layer_n_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(n, f, ensure_ascii=False, indent=2)
    f.write('\n')

paid = round(reach * CONVERSION)
plans_usd = schools * TEAM_PLAN_USD
facts = [
    ('P1_schools', 'Escuelas con alumnos en los grados objetivo (CCT)', schools, 'escuelas', 'SEP_911_2024_2025', 'verified', 'Capa K1 (D-MX-12).'),
    ('P1_median_students_per_school', 'Mediana de alumnos en grados objetivo por escuela', median, 'alumnos', 'SEP_911_2024_2025', 'verified', 'Capa K5.'),
    ('P1_students_reached_cap100', 'Alumnos alcanzables con un tope de 100 por escuela', reach, 'alumnos', 'SEP_911_2024_2025', 'verified', 'Capa K6.'),
    ('P1_paid_users_at_10pct', 'Usuarios de pago con la conversión supuesta', paid, 'usuarios', 'SEP_911_2024_2025', 'assumption',
     'La conversión del 10 % es un supuesto de la plantilla, no una tasa medida.'),
    ('P2_sponsored_team_plans_usd', 'Planes de equipo patrocinados al año (escuelas × USD 250)', plans_usd, 'USD', 'SEP_911_2024_2025', 'scenario',
     'USD 250 por escuela es un escenario de precio no aprobado.'),
    ('P2_sponsored_team_plans_mxn', 'Planes de equipo patrocinados al año, en pesos', round(plans_usd * fix), 'MXN', 'BANXICO_FIX_2025', 'scenario',
     f"Al tipo de cambio FIX promedio de 2025, {fix:.2f} MXN por USD.".replace('.', ',', 1)),
    ('P3_businesses_per_school', 'Negocios privados formales por escuela', per_school, 'negocios por escuela', 'INEGI_DENUE_202605', 'verified',
     'N1 (DENUE 05/2026, universo privado) ÷ K1 (911 2024-2025); periodos distintos, como indica la plantilla.'),
    ('P4_donation_incentive', 'Incentivo fiscal a donativos para educación', 7, 'porcentaje de la utilidad fiscal (tope)', 'LISR_DOF_20240401', 'to_confirm_with_legal',
     'Ley del ISR art. 27 fr. I: los donativos a donatarias autorizadas son deducibles, con tope del 7 % de la utilidad fiscal del ejercicio anterior. Confirmar el artículo y el tope con el área legal.'),
    ('P5_minors_data', 'Reglas para datos de menores', '', '', 'LFPDPPP_DOF_20251114', 'verified',
     'LFPDPPP art. 7: todo tratamiento requiere consentimiento (expreso o tácito); excepciones en el art. 9. '
     + ('La ley menciona a los menores de forma expresa.' if minors_article else 'La ley no tiene un artículo específico sobre menores; su consentimiento sigue las reglas generales (confirmar con el área legal).')),
]
rows = [{'layer': 'P', 'metric_id': m, 'scope_type': 'country', 'scope_id': 'MX', 'group_id': '', 'persona_id': '', 'indicator': ind, 'category': '',
         'value': val, 'unit': unit, 'period': '2024-2025 / 2026', 'comparison_period': '', 'numerator': '', 'denominator': '', 'status': st,
         'source_id': sid, 'method': '', 'limitations': note} for m, ind, val, unit, sid, st, note in facts]
map_path = os.path.join(CSV_DIR, 'fact_map_indicator.csv')
with open(map_path, encoding='utf-8') as f:
    existing = [r for r in csv.DictReader(f) if r['layer'] != 'P']
with open(map_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=MAP_COLUMNS, lineterminator='\n')
    w.writeheader()
    w.writerows(sorted(existing + rows, key=lambda r: r['layer']))
layer = {'country': 'MX', 'layer': 'P', 'inputs': {'K1': schools, 'K5_median': median, 'K6_reach': reach, 'N1': businesses, 'fix_2025': fix},
         'facts': [{x: r[x] for x in ('metric_id', 'indicator', 'value', 'unit', 'status', 'source_id', 'limitations')} for r in rows],
         'notes': {'conversion': 'The 10% conversion is stated as an assumption on every slide, never as a measured rate.'}}
with open(os.path.join(OUT, 'layer_p_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'P1': [schools, median, reach, paid], 'P2_usd': plans_usd, 'P2_mxn': round(plans_usd * fix), 'P3_N4': per_school,
                  'minors_article_found': minors_article}, ensure_ascii=False))
