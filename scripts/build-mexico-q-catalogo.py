"""Layer Q (Mexico): states and municipalities from INEGI Catálogo Único de Claves (AGEEML).
Reads the delivered nested zips directly; writes Colombia-shaped geo tables and the layer JSON.
Raw files stay local; outputs are code lists and one point per municipality.

Usage: python -I scripts/build-mexico-q-catalogo.py <raw_dir> [repo_dir]
  raw_dir holds catun_entidad.zip, catun_municipio.zip and min_con_acento.zip
"""
import csv, hashlib, io, json, os, sys, zipfile

raw = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
csv_out = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
layer_out = os.path.join(repo, 'data', 'mexico', 'outputs')
SOURCES = {'entidad': 'catun_entidad.zip', 'municipio': 'catun_municipio.zip', 'localidad': 'min_con_acento.zip'}
# CDMX alcaldías carry CVE_CAB '----' (no cabecera); locality 0001 is the alcaldía's main locality.
NO_CABECERA_LOCALITY = '0001'
MX_BBOX = (14.0, 33.0, -119.0, -86.0)


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def read_utf8_member(path):
    """The UTF-8 CSV inside an AGEEML zip (INEGI ships the same table as csv/txt/xlsx/dbf, latin-1 and UTF-8)."""
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.lower().endswith('.csv') and '_utf' in n.lower())
        info = z.getinfo(member)
        rows = list(csv.DictReader(io.TextIOWrapper(z.open(member), encoding='utf-8-sig', newline='')))
    return member, '%04d-%02d-%02d' % info.date_time[:3], rows


src, data = {}, {}
for key, name in SOURCES.items():
    path = os.path.join(raw, name)
    member, cut_off, rows = read_utf8_member(path)
    src[key] = {'zip': name, 'zip_sha256': sha256(path), 'member': member, 'file_date': cut_off, 'rows': len(rows)}
    data[key] = rows
states, munis, locs = data['entidad'], data['municipio'], data['localidad']
loc_by_code = {r['CVEGEO']: r for r in locs}

errors = []
if len(states) != 32 or len({r['CVE_ENT'] for r in states}) != 32:
    errors.append('expected 32 unique states')
state_codes = {r['CVE_ENT'] for r in states}

dept_rows = [{'department_code': r['CVE_ENT'], 'name': r['NOM_ENT']} for r in sorted(states, key=lambda r: r['CVE_ENT'])]
muni_rows, point_rules = [], {'cabecera': 0, 'cdmx_locality_0001': 0}
for r in sorted(munis, key=lambda r: r['CVEGEO']):
    code = r['CVEGEO']
    if code != r['CVE_ENT'] + r['CVE_MUN'] or len(code) != 5 or r['CVE_ENT'] not in state_codes:
        errors.append(f'bad municipality code {code}')
    rule = 'cabecera' if r['CVE_CAB'].isdigit() else 'cdmx_locality_0001'
    loc = loc_by_code.get(code + (r['CVE_CAB'] if rule == 'cabecera' else NO_CABECERA_LOCALITY))
    if rule == 'cdmx_locality_0001' and r['CVE_ENT'] != '09':
        errors.append(f'{code} has no cabecera outside Ciudad de México')
    lat = lon = None
    if loc:
        lat, lon = float(loc['LAT_DECIMAL']), float(loc['LON_DECIMAL'])
        if not (MX_BBOX[0] < lat < MX_BBOX[1] and MX_BBOX[2] < lon < MX_BBOX[3]):
            errors.append(f'{code} point outside Mexico: {lat}, {lon}')
        point_rules[rule] += 1
    else:
        errors.append(f'{code} reference locality not found')
    muni_rows.append({
        'municipality_code': code, 'department_code': r['CVE_ENT'], 'name': r['NOM_MUN'],
        'lat': f'{lat:.8f}' if lat is not None else '', 'lon': f'{lon:.8f}' if lon is not None else '',
        'wkt': f'POINT({lon:.6f} {lat:.6f})' if lat is not None else '',
    })
if len({r['municipality_code'] for r in muni_rows}) != len(muni_rows):
    errors.append('duplicate municipality codes')
if errors:
    sys.exit('Layer Q checks failed:\n' + '\n'.join(errors[:50]))

os.makedirs(csv_out, exist_ok=True)
os.makedirs(layer_out, exist_ok=True)
for table, rows in (('geo_department', dept_rows), ('geo_municipality', muni_rows)):
    with open(os.path.join(csv_out, table + '.csv'), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)

no_census_population = [{'municipality_code': r['CVEGEO'], 'name': r['NOM_MUN']} for r in munis if not r['POB_TOTAL'].isdigit()]
layer = {
    'country': 'MX', 'layer': 'Q', 'source_id': 'INEGI_CATALOGO_UNICO',
    'sources': src,
    'counts': {'states': len(dept_rows), 'municipalities': len(muni_rows), 'localities': len(locs),
               'municipalities_per_state': {d['department_code']: sum(1 for m in muni_rows if m['department_code'] == d['department_code']) for d in dept_rows}},
    'point_method': {
        'rule': 'Municipal point = coordinates of the cabecera locality (CVE_CAB). Ciudad de México alcaldías have no cabecera code (----): their locality 0001 is used.',
        'counts': point_rules,
    },
    'municipalities_without_2020_population': no_census_population,
    'limitations': 'Codes and points only; no boundaries. Catálogo population columns are Censo 2020 and are not used (layer E uses CONAPO). Municipalities created after 2020 have no census population.',
}
with open(os.path.join(layer_out, 'layer_q_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
print(json.dumps({'states': len(dept_rows), 'municipalities': len(muni_rows), 'point_rules': point_rules,
                  'no_2020_population': len(no_census_population)}, ensure_ascii=False))
