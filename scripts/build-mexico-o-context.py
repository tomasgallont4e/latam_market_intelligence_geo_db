"""Layer O (Mexico): country context, 2025 figures (ENIF 2024 the one exception) and laws in force in 2026.
Each fact carries the phrase it relies on; the build stops if that phrase is not found in its source document,
so every published figure is traceable to the supplied PDFs. Facts with no supplied source are kept empty and
marked not_checked (never filled from memory). Layout follows Peru's layer O rows (O1-O7) in fact_map_indicator.

Usage: python -I scripts/build-mexico-o-context.py <data/mexico/raw> [repo_dir]   (needs pypdf, cryptography)
"""
import csv, hashlib, json, os, re, sys
import pypdf

raw = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
DOCS = {
    'CONASAMI_DOF_20241219': 'layers_I_O_dof_salarios_minimos_2025/CONASAMI_191224.pdf',
    'INEGI_ENIF_2024': 'layer_O_context/inegi_enif_2024/ENIF2024_CP.pdf',
    'LIVA_DOF_20211112': 'layers_O_P_leyes_camara_diputados/LIVA_ultima_reforma_DOF_2021-11-12.pdf',
    'LFPDPPP_DOF_20251114': 'layers_O_P_leyes_camara_diputados/LFPDPPP_ultima_reforma_DOF_2025-11-14.pdf',
    'ATDT_PLAN_IA_2026': 'layer_O_atdt_plan_nacional_ia_2026/Plan-Nacional-de-IA.pdf',
    'INEGI_ENDUTIH_2025': 'layer_O_context/inegi_endutih_2025/ENDUTIH_25.pdf',
}
MAP_COLUMNS = ['layer', 'metric_id', 'scope_type', 'scope_id', 'group_id', 'persona_id', 'indicator', 'category', 'value', 'unit',
               'period', 'comparison_period', 'numerator', 'denominator', 'status', 'source_id', 'method', 'limitations']

text, hashes = {}, {}
for sid, rel in DOCS.items():
    path = os.path.join(raw, rel)
    with open(path, 'rb') as f:
        hashes[sid] = hashlib.sha256(f.read()).hexdigest()
    text[sid] = re.sub(r'\s+', ' ', ' '.join((p.extract_text() or '') for p in pypdf.PdfReader(path).pages))

with open(os.path.join(CSV_DIR, 'fact_persona_profile.csv'), encoding='utf-8') as f:
    dev_income = next(float(r['median_income_mxn']) for r in csv.DictReader(f) if r['persona'] == 'Software developers and analysts')

# (metric_id, indicator, value, unit, period, source_id, evidence regex or None, status, note)
FACTS = [
    ('O1_min_wage_daily', 'Minimum wage 2025, general zone', 278.80, 'MXN per day', '2025', 'CONASAMI_DOF_20241219',
     r'Salario M[ií]nimo General \(ZSMG\) el salario m[ií]nimo ser[aá] de 278\.80 pesos diarios', 'verified', 'Zona Libre de la Frontera Norte: MXN 419.88 a day.'),
    ('O1_min_wage_daily_northern_border', 'Minimum wage 2025, northern border zone', 419.88, 'MXN per day', '2025', 'CONASAMI_DOF_20241219',
     r'ser[aá]n de 419\.88 pesos diarios', 'verified', ''),
    ('O1_min_wage_monthly', 'Minimum wage 2025, general zone, monthly', round(278.80 * 30.4, 2), 'MXN per month', '2025', 'CONASAMI_DOF_20241219',
     None, 'derived', 'Daily × 30.4 days (D-MX-13).'),
    ('O1_developer_median_income', 'Developer median monthly labour income (persona P01)', dev_income, 'MXN per month', '2025', 'INEGI_ENOE_2025',
     None, 'derived', 'Weighted median of ENOE 2025 ingocup among developers reporting income (fact_persona_profile).'),
    ('O1_gdp_per_capita', 'GDP per capita (IMF WEO)', '', 'USD', '2025', 'IMF_WEO', None, 'not_checked', 'International source not supplied; left empty, never zero.'),
    ('O2_financial_product', 'Population with at least one formal financial product', 76.5, 'percent', '2024', 'INEGI_ENIF_2024',
     r'pas[oó] de 68\.4 a 76\.5 por ciento', 'verified', 'ENIF 2024 (no 2025 edition). Account or savings card, credit, insurance or retirement account. The release text refers to people aged 15-70; its chart notes say 18-70.'),
    ('O2_formal_credit', 'Population with at least one formal credit', 37.3, 'percent', '2024', 'INEGI_ENIF_2024',
     r'37\.3 % de la poblaci[oó]n dispon[ií]a de al menos uno', 'verified', ''),
    ('O2_insurance', 'Population with insurance', 22.9, 'percent', '2024', 'INEGI_ENIF_2024', r'22\.9 % de la poblaci[oó]n contaba con un seguro', 'verified', ''),
    ('O2_instant_payments', 'Instant payments (SPEI, CoDi, DiMo)', '', '', '2025', 'BANXICO_SPEI', None, 'not_checked',
     'SPEI (since 2004) with CoDi and DiMo on top, per the source register; Banxico statistics not supplied.'),
    ('O3_vat_rate', 'VAT rate (IVA), including digital services from abroad', 16, 'percent', 'in force 2026', 'LIVA_DOF_20211112',
     r'la tasa del 16%', 'verified', 'Ley del IVA art. 1; chapter III BIS (arts. 18-B onwards, added DOF 09-12-2019) taxes digital services provided by residents abroad without establishment in Mexico.'),
    ('O3_digital_services_chapter', 'VAT on digital services from abroad (Ley del IVA, chapter III BIS)', '', '', 'in force 2026', 'LIVA_DOF_20211112',
     r'CAP[IÍ]TULO III BIS De la prestaci[oó]n de servicios digitales por residentes en el extranjero', 'verified', 'Foreign providers register with SAT (per the source register).'),
    ('O4_data_protection_authority', 'Data protection: law and authority', '', '', 'in force 2026', 'LFPDPPP_DOF_20251114',
     r'Secretar[ií]a: Secretar[ií]a Anticorrupci[oó]n y Buen Gobierno', 'verified',
     'Ley Federal de Protección de Datos Personales en Posesión de los Particulares (2025; last reform DOF 14-11-2025). Authority: Secretaría Anticorrupción y Buen Gobierno, which absorbed INAI.'),
    ('O4_consent', 'Data protection: consent', '', '', 'in force 2026', 'LFPDPPP_DOF_20251114',
     r'Art[ií]culo 7\. Todo tratamiento de datos personales estar[aá] sujeto al consentimiento', 'verified',
     'Art. 7: every processing requires the data subject\'s consent, express or tacit; exceptions in art. 9. The law text has no article specific to minors (P5).'),
    ('O5_ai_policy', 'National AI policy', '', '', '2026', 'ATDT_PLAN_IA_2026',
     r'Plan Nacional de Inteligencia Artificial establece una ruta de acci[oó]n p[uú]blica', 'verified',
     'Plan Nacional de Inteligencia Artificial (ATDT, 2026): a public-policy plan, not a law; it cites the Principios de Chapultepec (29-01-2026) as the first official ethical framework. The document gives no funding amount.'),
    ('O6_internet_users_pct', 'People aged 6+ who used the internet', 86.1, 'percent', '2025', 'INEGI_ENDUTIH_2025',
     r'En 2025, 86\.1 % de la poblaci[oó]n mexicana us[oó] internet', 'verified', ''),
    ('O6_internet_users_millions', 'People aged 6+ who used the internet', 104.9, 'million people', '2025', 'INEGI_ENDUTIH_2025',
     r'104\.9 millones de personas de 6 a[ñn]os y m[aá]s', 'verified', ''),
    ('O6_households_internet_pct', 'Households with internet', 78.3, 'percent', '2025', 'INEGI_ENDUTIH_2025', r'78\.3 % de los hogares ten[ií]a internet', 'verified', ''),
    ('O6_computer_use_pct', 'People aged 6+ who used a computer', 38.1, 'percent', '2025', 'INEGI_ENDUTIH_2025', r'38\.1 %, computadora', 'verified', ''),
    ('O6_broadband_speed', 'Fixed broadband speed / desktop share of traffic', '', '', '2025', 'DATAREPORTAL_STATCOUNTER', None, 'not_checked',
     'International sources not supplied; left empty.'),
    ('O7_pestel', 'PESTEL summary', '', '', '', 'O1-O6', None, 'pending', 'One line per factor, written in the deck from O1-O6.'),
]
errors = [f'{m}: evidence not found in {sid}' for m, _, _, _, _, sid, rx, _, _ in FACTS if rx and not re.search(rx, text[sid], re.I)]
if errors:
    sys.exit('Layer O evidence check failed:\n' + '\n'.join(errors))

rows = [{'layer': 'O', 'metric_id': m, 'scope_type': 'country', 'scope_id': 'MX', 'group_id': '', 'persona_id': '', 'indicator': ind, 'category': '',
         'value': val, 'unit': unit, 'period': per, 'comparison_period': '', 'numerator': '', 'denominator': '', 'status': st, 'source_id': sid,
         'method': 'quoted from the source document' if rx else ('derived' if st == 'derived' else ''), 'limitations': note}
        for m, ind, val, unit, per, sid, rx, st, note in FACTS]
map_path = os.path.join(CSV_DIR, 'fact_map_indicator.csv')
with open(map_path, encoding='utf-8') as f:
    existing = [r for r in csv.DictReader(f) if r['layer'] != 'O']
with open(map_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=MAP_COLUMNS, lineterminator='\n')
    w.writeheader()
    w.writerows(sorted(existing + rows, key=lambda r: r['layer']))
layer = {'country': 'MX', 'layer': 'O', 'sources': {sid: {'file': DOCS[sid], 'sha256': hashes[sid]} for sid in DOCS},
         'facts': [{k: v for k, v in r.items() if k in ('metric_id', 'indicator', 'value', 'unit', 'period', 'status', 'source_id', 'limitations')} for r in rows],
         'evidence_rule': 'Every verified fact was matched against its quoted phrase in the source PDF at build time.'}
with open(os.path.join(OUT, 'layer_o_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'rows': len(rows), 'by_status': {s: sum(1 for r in rows if r['status'] == s) for s in {r['status'] for r in rows}}}))
