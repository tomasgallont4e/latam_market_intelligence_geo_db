"""Layer O (Mexico): country context, 2025 figures (ENIF 2024 the one exception) and laws in force in 2026.
Each fact carries the phrase it relies on; the build stops if that phrase is not found in its source document,
so every published figure is traceable to the supplied PDFs. Facts with no supplied source are kept empty and
marked not_checked (never filled from memory). Layout follows Peru's layer O rows (O1-O7) in fact_map_indicator.
Non-PDF sources are read from the supplied files: IMF DataMapper JSON (GDP per capita), Banxico daily series
(SPEI, CoDi), the DataReportal Digital 2026 Mexico page (quoted like the PDFs) and StatCounter's yearly CSV.

Usage: python -I scripts/build-mexico-o-context.py <data/mexico/raw> [repo_dir]   (needs pypdf, cryptography, openpyxl)
"""
import csv, glob, hashlib, html, json, os, re, sys
import openpyxl, pypdf

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

def file_sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


# O1: IMF World Economic Outlook via DataMapper (indicator NGDPDPC, current USD).
imf_path = glob.glob(os.path.join(raw, 'layer_O1_imf_weo_gdp_per_capita', '*.json'))[0]
imf = json.load(open(imf_path, encoding='utf-8'))['values']['NGDPDPC']
hashes['IMF_WEO_DATAMAPPER'] = file_sha(imf_path)
gdp_pc = {iso: imf[iso]['2025'] for iso in ('MEX', 'COL', 'PER')}


# O2: Banxico daily series for 2025, summed over the year (flows) or taken on 31-12-2025 (cumulative counts).
def banxico(code, label_start, how):
    path = glob.glob(os.path.join(raw, 'layer_O2_banxico_spei_codi_2025', f'{code}_*.xlsx'))[0]
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True).worksheets[0]
    ws.reset_dimensions()
    rows = [list(r) for r in ws.iter_rows(values_only=True) if r and any(c is not None for c in r)]
    date = re.compile(r'\d\d/\d\d/\d{4}')
    hi = next(i for i, r in enumerate(rows) if sum(1 for c in r if c and date.fullmatch(str(c).strip())) > 5)
    cols = [j for j, c in enumerate(rows[hi]) if c and date.fullmatch(str(c).strip())]
    if len(cols) != 365 or str(rows[hi][cols[0]]).strip() != '01/01/2025' or str(rows[hi][cols[-1]]).strip() != '31/12/2025':
        sys.exit(f'{code}: expected the 365 days of 2025')
    clean = lambda c: re.sub(r'^[\s\u2002\u2003●⚬]+', '', str(c))
    row = next(r for r in rows[hi + 1:] if any(c and clean(c).startswith(label_start) for c in r))
    vals = [float(row[j]) for j in cols if j < len(row) and row[j] not in (None, '', 'N/E')]
    hashes.setdefault('BANXICO_SPEI_CODI_2025', {})[code] = file_sha(path)
    return sum(vals) if how == 'sum' else vals[-1]


spei_ops = banxico('CF891', 'Total de número de operaciones', 'sum')
spei_amount = banxico('CF890', 'Total de monto operado', 'sum')
codi_ops = banxico('CF884', 'Total de operaciones enviadas', 'sum')
codi_paid_accounts = banxico('CF882', 'Cuentas que han realizado al menos un pago', 'last')

# O6: DataReportal Digital 2026 Mexico page (quoted like the PDFs) and StatCounter platform shares for 2025.
dr_path = glob.glob(os.path.join(raw, 'layer_O6_datareportal_digital_2026_mexico', '*.html'))[0]
hashes['DATAREPORTAL_DIGITAL_2026_MX'] = file_sha(dr_path)
page = open(dr_path, encoding='utf-8', errors='replace').read()
text['DATAREPORTAL_DIGITAL_2026_MX'] = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', page)).replace('\xa0', ' '))
sc_path = glob.glob(os.path.join(raw, 'layer_O6_statcounter_2025', '*.csv'))[0]
hashes['STATCOUNTER_2025'] = file_sha(sc_path)
with open(sc_path, encoding='utf-8-sig') as f:
    platform = {r[0]: float(r[1]) for r in csv.reader(f) if len(r) == 2 and r[1].replace('.', '', 1).isdigit()}
DOCS.update({'IMF_WEO_DATAMAPPER': os.path.relpath(imf_path, raw), 'BANXICO_SPEI_CODI_2025': 'layer_O2_banxico_spei_codi_2025/ (one xlsx per series)',
             'DATAREPORTAL_DIGITAL_2026_MX': os.path.relpath(dr_path, raw),
             'STATCOUNTER_2025': os.path.relpath(sc_path, raw)})

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
    ('O1_gdp_per_capita', 'GDP per capita (IMF WEO)', round(gdp_pc['MEX'], 1), 'USD', '2025', 'IMF_WEO_DATAMAPPER', None, 'verified',
     f"IMF World Economic Outlook, DataMapper indicator NGDPDPC (current USD), as served on 2026-11-07. Same file: Colombia {gdp_pc['COL']:,.0f}, Peru {gdp_pc['PER']:,.0f}."),
    ('O2_financial_product', 'Population with at least one formal financial product', 76.5, 'percent', '2024', 'INEGI_ENIF_2024',
     r'pas[oó] de 68\.4 a 76\.5 por ciento', 'verified', 'ENIF 2024 (no 2025 edition). Account or savings card, credit, insurance or retirement account. The release text refers to people aged 15-70; its chart notes say 18-70.'),
    ('O2_formal_credit', 'Population with at least one formal credit', 37.3, 'percent', '2024', 'INEGI_ENIF_2024',
     r'37\.3 % de la poblaci[oó]n dispon[ií]a de al menos uno', 'verified', ''),
    ('O2_insurance', 'Population with insurance', 22.9, 'percent', '2024', 'INEGI_ENIF_2024', r'22\.9 % de la poblaci[oó]n contaba con un seguro', 'verified', ''),
    ('O2_spei_operations', 'SPEI instant payments, third party to third party', round(spei_ops), 'operations', '2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Sum of the 365 daily values of Banxico series CF891. SPEI runs 24/7; DiMo (payments to a mobile number) is not in the supplied files.'),
    ('O2_spei_amount', 'SPEI amount, third party to third party', round(spei_amount / 1e12, 2), 'MXN trillion', '2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Sum of the 365 daily values of Banxico series CF890 (pesos).'),
    ('O2_codi_operations', 'CoDi payment operations', round(codi_ops), 'operations', '2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Sum of daily CoDi operations sent (series CF884); CoDi runs on top of SPEI.'),
    ('O2_codi_paying_accounts', 'CoDi accounts that have made at least one payment', round(codi_paid_accounts), 'accounts', 'end of 2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Cumulative count on 31-12-2025 (series CF882).'),
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
    ('O6_fixed_download_speed', 'Median fixed internet download speed (Ookla)', 90.59, 'Mbps', 'end of 2025', 'DATAREPORTAL_DIGITAL_2026_MX',
     r'Median fixed internet download speed: 90\.59 Mbps', 'verified', 'DataReportal Digital 2026 Mexico, citing Ookla.'),
    ('O6_mobile_download_speed', 'Median mobile internet download speed (Ookla)', 45.21, 'Mbps', 'end of 2025', 'DATAREPORTAL_DIGITAL_2026_MX',
     r'Median mobile internet download speed via cellular data networks \* : 45\.21 Mbps', 'verified', 'DataReportal Digital 2026 Mexico, citing Ookla.'),
    ('O6_internet_users_datareportal', 'Internet users (DataReportal)', 110, 'million people', 'October 2025', 'DATAREPORTAL_DIGITAL_2026_MX',
     r'110 million internet users in Mexico in October 2025', 'verified', 'Kepios estimate; the official figure is ENDUTIH 2025 (86.1% of people aged 6+, 104.9 million).'),
    ('O6_desktop_share', 'Desktop share of web traffic (StatCounter)', platform.get('Desktop'), 'percent', '2025', 'STATCOUNTER_2025', None, 'verified',
     f"StatCounter yearly 2025: mobile {platform.get('Mobile')}%, tablet {platform.get('Tablet')}%."),
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
         'evidence_rule': 'Every quoted fact was matched against its phrase in the source PDF or page at build time; data-file facts (IMF, Banxico, StatCounter) are read from the supplied files.'}
with open(os.path.join(OUT, 'layer_o_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'rows': len(rows), 'by_status': {s: sum(1 for r in rows if r['status'] == s) for s in {r['status'] for r in rows}}}))
