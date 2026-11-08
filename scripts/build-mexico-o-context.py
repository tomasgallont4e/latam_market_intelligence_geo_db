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
    ('O1_min_wage_daily', 'Salario mínimo 2025, zona general', 278.80, 'MXN al día', '2025', 'CONASAMI_DOF_20241219',
     r'Salario M[ií]nimo General \(ZSMG\) el salario m[ií]nimo ser[aá] de 278\.80 pesos diarios', 'verified', 'Zona Libre de la Frontera Norte: 419,88 pesos al día.'),
    ('O1_min_wage_daily_northern_border', 'Salario mínimo 2025, zona libre de la frontera norte', 419.88, 'MXN al día', '2025', 'CONASAMI_DOF_20241219',
     r'ser[aá]n de 419\.88 pesos diarios', 'verified', ''),
    ('O1_min_wage_monthly', 'Salario mínimo 2025, zona general, mensual', round(278.80 * 30.4, 2), 'MXN al mes', '2025', 'CONASAMI_DOF_20241219',
     None, 'derived', 'Diario × 30,4 días (D-MX-13).'),
    ('O1_developer_median_income', 'Ingreso laboral mensual mediano de los desarrolladores (persona P01)', dev_income, 'MXN al mes', '2025', 'INEGI_ENOE_2025',
     None, 'derived', 'Mediana ponderada de ingocup de la ENOE 2025 entre los desarrolladores que reportan ingreso (fact_persona_profile).'),
    ('O1_gdp_per_capita', 'PIB per cápita (FMI, WEO)', round(gdp_pc['MEX'], 1), 'USD', '2025', 'IMF_WEO_DATAMAPPER', None, 'verified',
     f"FMI, World Economic Outlook, indicador NGDPDPC de DataMapper (USD corrientes), consultado el 2026-11-07. En el mismo archivo: "
     f"Colombia {format(round(gdp_pc['COL']), ',').replace(',', '.')}, Perú {format(round(gdp_pc['PER']), ',').replace(',', '.')}."),
    ('O2_financial_product', 'Población con al menos un producto financiero formal', 76.5, 'porcentaje', '2024', 'INEGI_ENIF_2024',
     r'pas[oó] de 68\.4 a 76\.5 por ciento', 'verified', 'ENIF 2024 (no hay edición 2025). Cuenta o tarjeta de ahorro, crédito, seguro o cuenta de ahorro para el retiro. El comunicado habla de personas de 15 a 70 años; las notas de sus gráficas dicen 18 a 70.'),
    ('O2_formal_credit', 'Población con al menos un crédito formal', 37.3, 'porcentaje', '2024', 'INEGI_ENIF_2024',
     r'37\.3 % de la poblaci[oó]n dispon[ií]a de al menos uno', 'verified', ''),
    ('O2_insurance', 'Población con seguro', 22.9, 'porcentaje', '2024', 'INEGI_ENIF_2024', r'22\.9 % de la poblaci[oó]n contaba con un seguro', 'verified', ''),
    ('O2_spei_operations', 'Pagos inmediatos SPEI entre terceros', round(spei_ops), 'operaciones', '2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Suma de los 365 valores diarios de la serie CF891 de Banxico. SPEI opera 24/7; DiMo (pagos a un número celular) no está en los archivos entregados.'),
    ('O2_spei_amount', 'Monto SPEI entre terceros', round(spei_amount / 1e12, 2), 'billones de MXN', '2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Suma de los 365 valores diarios de la serie CF890 de Banxico (pesos).'),
    ('O2_codi_operations', 'Operaciones de pago CoDi', round(codi_ops), 'operaciones', '2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Suma diaria de operaciones CoDi enviadas (serie CF884); CoDi opera sobre SPEI.'),
    ('O2_codi_paying_accounts', 'Cuentas CoDi que han hecho al menos un pago', round(codi_paid_accounts), 'cuentas', 'cierre de 2025', 'BANXICO_SPEI_CODI_2025', None, 'verified',
     'Conteo acumulado al 31-12-2025 (serie CF882).'),
    ('O3_vat_rate', 'Tasa de IVA, incluidos los servicios digitales del extranjero', 16, 'porcentaje', 'vigente en 2026', 'LIVA_DOF_20211112',
     r'la tasa del 16%', 'verified', 'Ley del IVA art. 1; el capítulo III BIS (arts. 18-B y siguientes, adicionado en el DOF del 09-12-2019) grava los servicios digitales de residentes en el extranjero sin establecimiento en México.'),
    ('O3_digital_services_chapter', 'IVA de servicios digitales del extranjero (Ley del IVA, capítulo III BIS)', '', '', 'vigente en 2026', 'LIVA_DOF_20211112',
     r'CAP[IÍ]TULO III BIS De la prestaci[oó]n de servicios digitales por residentes en el extranjero', 'verified', 'Los proveedores extranjeros se inscriben ante el SAT (según el registro de fuentes).'),
    ('O4_data_protection_authority', 'Protección de datos: ley y autoridad', '', '', 'vigente en 2026', 'LFPDPPP_DOF_20251114',
     r'Secretar[ií]a: Secretar[ií]a Anticorrupci[oó]n y Buen Gobierno', 'verified',
     'Ley Federal de Protección de Datos Personales en Posesión de los Particulares (2025; última reforma DOF 14-11-2025). Autoridad: Secretaría Anticorrupción y Buen Gobierno, que absorbió al INAI.'),
    ('O4_consent', 'Protección de datos: consentimiento', '', '', 'vigente en 2026', 'LFPDPPP_DOF_20251114',
     r'Art[ií]culo 7\. Todo tratamiento de datos personales estar[aá] sujeto al consentimiento', 'verified',
     'Art. 7: todo tratamiento requiere el consentimiento del titular, expreso o tácito; excepciones en el art. 9. La ley no tiene un artículo específico sobre menores (P5).'),
    ('O5_ai_policy', 'Política nacional de IA', '', '', '2026', 'ATDT_PLAN_IA_2026',
     r'Plan Nacional de Inteligencia Artificial establece una ruta de acci[oó]n p[uú]blica', 'verified',
     'Plan Nacional de Inteligencia Artificial (ATDT, 2026): un plan de política pública, no una ley; cita los Principios de Chapultepec (29-01-2026) como el primer marco ético oficial. El documento no da un monto de financiamiento.'),
    ('O6_internet_users_pct', 'Personas de 6 años o más que usaron internet', 86.1, 'porcentaje', '2025', 'INEGI_ENDUTIH_2025',
     r'En 2025, 86\.1 % de la poblaci[oó]n mexicana us[oó] internet', 'verified', ''),
    ('O6_internet_users_millions', 'Personas de 6 años o más que usaron internet', 104.9, 'millones de personas', '2025', 'INEGI_ENDUTIH_2025',
     r'104\.9 millones de personas de 6 a[ñn]os y m[aá]s', 'verified', ''),
    ('O6_households_internet_pct', 'Hogares con internet', 78.3, 'porcentaje', '2025', 'INEGI_ENDUTIH_2025', r'78\.3 % de los hogares ten[ií]a internet', 'verified', ''),
    ('O6_computer_use_pct', 'Personas de 6 años o más que usaron computadora', 38.1, 'porcentaje', '2025', 'INEGI_ENDUTIH_2025', r'38\.1 %, computadora', 'verified', ''),
    ('O6_fixed_download_speed', 'Velocidad mediana de descarga, internet fijo (Ookla)', 90.59, 'Mbps', 'cierre de 2025', 'DATAREPORTAL_DIGITAL_2026_MX',
     r'Median fixed internet download speed: 90\.59 Mbps', 'verified', 'DataReportal Digital 2026 México, con datos de Ookla.'),
    ('O6_mobile_download_speed', 'Velocidad mediana de descarga, internet móvil (Ookla)', 45.21, 'Mbps', 'cierre de 2025', 'DATAREPORTAL_DIGITAL_2026_MX',
     r'Median mobile internet download speed via cellular data networks \* : 45\.21 Mbps', 'verified', 'DataReportal Digital 2026 México, con datos de Ookla.'),
    ('O6_internet_users_datareportal', 'Usuarios de internet (DataReportal)', 110, 'millones de personas', 'octubre de 2025', 'DATAREPORTAL_DIGITAL_2026_MX',
     r'110 million internet users in Mexico in October 2025', 'verified', 'Estimación de Kepios; la cifra oficial es la ENDUTIH 2025 (86,1 % de las personas de 6 años o más, 104,9 millones).'),
    ('O6_desktop_share', 'Participación de computadoras de escritorio en el tráfico web (StatCounter)', platform.get('Desktop'), 'porcentaje', '2025', 'STATCOUNTER_2025', None, 'verified',
     f"StatCounter, año 2025: móvil {str(platform.get('Mobile')).replace('.', ',')} %, tableta {str(platform.get('Tablet')).replace('.', ',')} %."),
    ('O7_pestel', 'Resumen PESTEL', '', '', '', 'O1-O6', None, 'pending', 'Una línea por factor, redactada en el deck a partir de O1-O6.'),
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
