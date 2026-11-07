"""Layers D3 and M4 (Mexico): INEGI Censos Económicos 2024, reference year 2023 (decision D-MX-15).
D3 (IT industry census) reads SCIAN 5415 'Servicios de diseño de sistemas de cómputo y servicios relacionados'
from the national open-data table tr_ce_nac_2024.csv: economic units and people employed (H001A), by personnel stratum.
M4 (digital adoption of micro-businesses) reads the CE_TEMACE_1 tabulation, national row 'Total' activity,
stratum 0 a 10 personas. Both are labelled with period 2023 and the census universe (fixed economic units);
M1 (ENOE 2025) also counts street and home-based businesses, so M4 shares are not applied to M1.
Run after build-mexico-denue.py and build-mexico-enoe.py (it fills D3 in layer_d_mx.json and M4 in layer_m_mx.json).

Usage: python -I scripts/build-mexico-d3-m4-census.py <data/mexico/raw> [repo_dir]   (needs openpyxl)
"""
import csv, hashlib, io, json, os, re, sys, zipfile
import openpyxl

raw = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
FOLDER = os.path.join(raw, 'layers_D3_M4_inegi_censos_economicos_2024_ref2023')
CE_ZIP = os.path.join(FOLDER, 'conjunto_de_datos_ce_nac_2024_csv.zip')
TEMACE = os.path.join(FOLDER, 'CE_TEMACE_1_tema_entidad_estrato_2023.xlsx')
STRATA = {'1': '0-10', '2': '11-50', '3': '51-250', '4': '251+'}
# M4 indicators: column label in CE_TEMACE_1 (text after '>', without the unit) → key.
M4_COLUMNS = {
    'Unidades económicas que contaron con equipo de cómputo o tabletas': 'computer_or_tablet',
    'Unidades económicas que contaron con servicio de internet': 'internet',
    'Unidades económicas que utilizaron teléfono celular': 'mobile_phone',
    'Unidades económicas que sí contaron con correo electrónico': 'email',
    'Unidades económicas que contaron con redes sociales para la promoción de productos o servicios': 'social_media_promotion',
    'Unidades económicas que contaron con página de internet': 'website',
    'Unidades económicas que utilizaron algún tipo de tecnología digital': 'any_digital_technology',
    'Unidades económicas que usaron el internet para operaciones bancarias y financieras': 'internet_banking',
    'Unidades económicas que utilizaron servicios informáticos en la nube': 'cloud_services',
    'Unidades económicas que utilizaron sistemas de inteligencia artificial IA': 'artificial_intelligence',
    'Unidades económicas que sí realizaron ventas por internet': 'online_sales',
    'Unidades económicas que realizaron ventas mediante redes sociales': 'online_sales_social_media',
    'Unidades económicas que sí realizaron compras por internet': 'online_purchases',
}
# Pairs whose yes + no must equal the micro-unit total (consistency check on the tabulation).
YES_NO = {'computer_or_tablet': 'Unidades económicas que no contaron con equipo de cómputo o tabletas',
          'internet': 'Unidades económicas que no contaron con servicio de internet',
          'online_sales': 'Unidades económicas que no realizaron ventas por internet'}


def file_sha(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def share(a, b):
    return round(100 * a / b, 1) if b else None


# ───────────── D3: SCIAN 5415, national rows (no state, no municipality) ─────────────
with zipfile.ZipFile(CE_ZIP) as z, z.open('conjunto_de_datos/tr_ce_nac_2024.csv') as f:
    reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
    it = {r['ID_ESTRATO'].strip(): (int(r['UE']), int(r['H001A'])) for r in reader
          if r['CODIGO'].strip() == '5415' and not r['E03'].strip() and not r['E04'].strip()}
if '' not in it or set(it) - {''} != set(STRATA):
    sys.exit(f'D3: expected the SCIAN 5415 national total and strata 1-4, found {sorted(it)}')
units, people = it['']
if sum(it[s][0] for s in STRATA) != units or sum(it[s][1] for s in STRATA) != people:
    sys.exit('D3: the strata of SCIAN 5415 do not add up to the total')
d3 = {
    'units': units, 'people_employed': people,
    'by_stratum': {STRATA[s]: {'units': it[s][0], 'people_employed': it[s][1], 'share_units_pct': share(it[s][0], units)} for s in STRATA},
    'pct_micro_units': share(it['1'][0], units), 'period': '2023', 'universe': 'fixed economic units (census)',
    'classification': 'SCIAN 2018 5415 (= class 541510)',
}

# ───────────── M4: micro units (0 a 10 personas), national total activity ─────────────
ws = openpyxl.load_workbook(TEMACE, read_only=True, data_only=True).worksheets[0]
ws.reset_dimensions()
rows = [r for r in ws.iter_rows(values_only=True) if r and any(c is not None for c in r)]
hi = next(i for i, r in enumerate(rows) if r[0] == 'Entidad federativa')
labels = [re.sub(r'\s+', ' ', re.sub(r'\s*\((Número|Millones de pesos)\)\s*$', '', str(c).split('>')[-1])).strip() if c else '' for c in rows[hi]]
micro = [r for r in rows[hi + 1:] if str(r[0]).startswith('00 ') and r[1] == 'Total' and re.match(r'01\)\s+0 a\s+10 personas', str(r[2]))]
if len(micro) != 1:
    sys.exit(f'M4: expected one national micro-unit row, found {len(micro)}')
row = dict(zip(labels, micro[0]))
total = int(row['Total de unidades económicas'])
missing = [lab for lab in list(M4_COLUMNS) + list(YES_NO.values()) if lab not in row]
if missing:
    sys.exit(f'M4: columns not found: {missing}')
counts = {key: int(row[lab]) for lab, key in M4_COLUMNS.items()}
for key, no_label in YES_NO.items():
    if counts[key] + int(row[no_label]) != total:
        sys.exit(f'M4: {key} yes + no != {total}')
m4 = {
    'micro_units_total': total,
    'indicators': {key: {'units': v, 'pct': share(v, total)} for key, v in counts.items()},
    'period': '2023', 'universe': 'fixed economic units with 0 to 10 people (census)',
}

# ───────────── Write into the layer JSONs ─────────────
source = {'source_id': 'INEGI_CE_2024', 'edition': 'Censos Económicos 2024 (reference year 2023), open data 2025-09-25 and tabulation CE_TEMACE_1',
          'sha256': {'conjunto_de_datos_ce_nac_2024_csv.zip': file_sha(CE_ZIP), os.path.basename(TEMACE): file_sha(TEMACE)}}
with open(os.path.join(OUT, 'layer_d_mx.json'), encoding='utf-8') as f:
    layer_d = json.load(f)
dlnk = layer_d['indicators'].get('D1_by_code', {}).get('541510')
layer_d['indicators']['D3_industry_census'] = {**d3, **source}
layer_d['notes']['D3_industry_census'] = (
    'Censos Económicos 2024, reference year 2023 (D-MX-15: period exception, like Colombia\'s Fedesoft own census). '
    f'Counts economic units with fixed premises; DENUE 05/2026 class 541510 has {dlnk:,} establishments (directory, 2026), '
    'so the two are not added or compared as growth.')
with open(os.path.join(OUT, 'layer_m_mx.json'), encoding='utf-8') as f:
    layer_m = json.load(f)
layer_m['M4_digital'] = {**m4, **source}
layer_m['notes']['M4_digital'] = (
    'Censos Económicos 2024, reference year 2023 (D-MX-15). Universe: fixed economic units with 0-10 people (5.2 million); '
    'M1 (ENOE 2025, 15.8 million) also counts street and home-based businesses, so these shares are not applied to M1.')
for name, doc in (('layer_d_mx.json', layer_d), ('layer_m_mx.json', layer_m)):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write('\n')
print(json.dumps({'D3': {'units': units, 'people': people, 'pct_micro': d3['pct_micro_units']},
                  'M4_total': total, 'M4_pct': {k: v['pct'] for k, v in m4['indicators'].items()}}, ensure_ascii=False))
