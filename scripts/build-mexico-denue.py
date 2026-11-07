"""Layers D, J and N (Mexico): INEGI DENUE 05/2026, all sector files read directly from the delivered zips.
Writes fact_companies_municipality (Colombia-shaped counterpart of fact_companies_chamber), the J zones
(geo_zone, fact_companies_zone) and the layer JSONs. Only counts leave the raw folder: names, addresses,
phones and e-mails are never written.

Universes (decisions_log.csv D-MX-03, D-MX-04, D-MX-05, D-MX-06):
  establishments       every DENUE row, as published (must equal the bulletin total exactly)
  businesses (N1)      private businesses: excludes associations (SCIAN 813), cooperatives (legal name)
                       and public-sector establishments (SCIAN 93 and classes named 'sector público'),
                       the closest universe to Colombia's RUES private merchant register
  shops_4711 (N3)      SCIAN 461110 abarrotes, ultramarinos y misceláneas (template shop code)
  it_companies_active  SCIAN 2018 541510 + 518210 + 519290 (template ISIC 6201/6202/6209, 6311, 6312)
  J zones              Ciudad de México: its 16 alcaldías. Monterrey: the 16 municipalities of the
                       Zona Metropolitana de Monterrey (Metrópolis de México 2020, cuadro A.19.1.01).
                       Zone counts use the private-business universe, like Colombia's register.

Usage: python -I scripts/build-mexico-denue.py <raw_dir> [repo_dir]
"""
import csv, glob, hashlib, io, json, os, re, sys, zipfile
from collections import Counter, defaultdict

raw = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
LAYER_DIR = os.path.join(repo, 'data', 'mexico', 'outputs')
PUBLISHED_TOTAL = 6138075  # DENUE 05/2026 bulletin
IT_CODES = {'541510': 'it_541510', '518210': 'it_518210', '519290': 'it_519290'}
SHOP_CODE = '461110'
COOP = re.compile(r'COOPERATIVA|\bS\.?\s*C\.?\s*(DE\s*P\.?\s*)?(DE\s*R\.?\s*L|L)\b\.?', re.I)
SIZE_BANDS = ['0 a 5 personas', '6 a 10 personas', '11 a 30 personas', '31 a 50 personas',
              '51 a 100 personas', '101 a 250 personas', '251 y más personas']
COLUMNS = ['establishments', 'businesses', 'shops_4711', 'it_companies_active', 'it_541510', 'it_518210', 'it_519290']

# Layer J. Zone cities: prefix → (zone type, member municipalities).
MTY_METRO = ['19006', '19009', '19010', '19012', '19018', '19019', '19021', '19025', '19026', '19031',
             '19039', '19041', '19045', '19046', '19048', '19049']
ZONE_CITIES = {'CMX': ('alcaldia', None), 'MTY': ('municipio_metropolitano', MTY_METRO)}  # None = every municipality of state 09
# Size by people employed, INEGI strata: micro 0-10, medium and large 51+ (Colombia uses assets).
MICRO_BANDS = {'0 a 5 personas', '6 a 10 personas'}
MEDIUM_LARGE_BANDS = {'51 a 100 personas', '101 a 250 personas', '251 y más personas'}
# Template annex 3 (Colombian CIIU Rev. 4 A.C.) mapped to SCIAN 2018, private classes only.
J_GROUPS = {
    'design': {'541410', '541420', '541430', '541490'},                       # 7410
    'accounting_audit': {'541211', '541219'},                                  # 6920
    'management_consulting': {'541610'},                                       # 7020
    'research_market_studies': {'541711', '541721', '541910'},                 # 7210, 7220, 7320
    'higher_education_training': {'611211', '611311',                          # 8541-8544 tertiary
                                  '611411', '611421', '611431', '611511', '611631',  # 8551 non-formal training
                                  '611691', '611698'},                         # 8559 other education
    'private_schools': {'611111', '611121', '611131', '611141', '611151', '611161', '611171'},  # 8511-8523
}
ZONE_COLUMNS = ['companies_total', 'micro', 'medium_large', 'software_it', 'design', 'accounting_audit',
                'management_consulting', 'research_market_studies', 'higher_education_training', 'shops_4711', 'private_schools']


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def excluded_as(r):
    """Reason a row is outside the private-business universe (N1), or None."""
    code, activity = r['codigo_act'], r['nombre_act']
    if code.startswith('93') or 'sector público' in activity:
        return 'public_sector'
    if code.startswith('813'):
        return 'association'
    if COOP.search(r['raz_social'] or ''):
        return 'cooperative'
    return None


with open(os.path.join(CSV_DIR, 'geo_municipality.csv'), encoding='utf-8') as f:
    geo_munis = {r['municipality_code']: r for r in csv.DictReader(f)}
munis = {code: r['department_code'] for code, r in geo_munis.items()}
zone_of = {}  # municipality_code → (prefix, zone type)
for prefix, (zone_type, members) in ZONE_CITIES.items():
    for code in members or [m for m, d in munis.items() if d == '09']:
        if code not in munis:
            sys.exit(f'Layer J: zone municipality {code} not in catalogue')
        zone_of[code] = (prefix, zone_type)
by_zone_muni = defaultdict(Counter)
code_to_group = {code: group for group, codes in J_GROUPS.items() for code in codes}

by_muni = defaultdict(Counter)
national = Counter()
size = Counter()
it_size = Counter()
exclusions = Counter()
excluded_classes = defaultdict(Counter)
legal_name = Counter()
unit_type = Counter()
ids, duplicates, sources, errors = set(), [], [], []

files = sorted(glob.glob(os.path.join(raw, 'denue_00_*_csv.zip')))
if len(files) != 25:
    errors.append(f'expected 25 sector zips, found {len(files)}')
for path in files:
    with zipfile.ZipFile(path) as z:
        member = next(n for n in z.namelist() if n.startswith('conjunto_de_datos/') and n.endswith('.csv'))
        rows = 0
        with z.open(member) as f:
            for r in csv.DictReader(io.TextIOWrapper(f, encoding='latin-1', newline='')):
                rows += 1
                if r['id'] in ids:
                    duplicates.append({'id': r['id'], 'clee': r['clee'], 'file': os.path.basename(path), 'codigo_act': r['codigo_act'],
                                       'municipality_code': r['cve_ent'] + r['cve_mun']})
                ids.add(r['id'])
                code = r['cve_ent'] + r['cve_mun']
                if code not in munis:
                    errors.append(f'{os.path.basename(path)} id {r["id"]}: municipality {code} not in catalogue')
                    continue
                c = by_muni[code]
                c['establishments'] += 1
                reason = excluded_as(r)
                if reason:
                    exclusions[reason] += 1
                    excluded_classes[reason][r['codigo_act'] + ' ' + r['nombre_act']] += 1
                else:
                    c['businesses'] += 1
                    if code in zone_of:
                        z = by_zone_muni[code]
                        z['companies_total'] += 1
                        z['micro'] += r['per_ocu'] in MICRO_BANDS
                        z['medium_large'] += r['per_ocu'] in MEDIUM_LARGE_BANDS
                        z['software_it'] += r['codigo_act'] in IT_CODES
                        z['shops_4711'] += r['codigo_act'] == SHOP_CODE
                        group = code_to_group.get(r['codigo_act'])
                        if group:
                            z[group] += 1
                if r['codigo_act'] == SHOP_CODE:
                    c['shops_4711'] += 1
                if r['codigo_act'] in IT_CODES:
                    c['it_companies_active'] += 1
                    c[IT_CODES[r['codigo_act']]] += 1
                    it_size[r['per_ocu']] += 1
                size[r['per_ocu']] += 1
                legal_name['with_legal_name' if r['raz_social'].strip() else 'without_legal_name'] += 1
                unit_type[r['tipoUniEco']] += 1
        sources.append({'zip': os.path.basename(path), 'sha256': sha256(path), 'member': member, 'rows': rows})

for c in by_muni.values():
    national.update(c)
if national['establishments'] != PUBLISHED_TOTAL:
    errors.append(f'establishments {national["establishments"]} != published {PUBLISHED_TOTAL}')
if set(size) - set(SIZE_BANDS):
    errors.append(f'unexpected size bands {set(size) - set(SIZE_BANDS)}')
if national['businesses'] + sum(exclusions.values()) != national['establishments']:
    errors.append('businesses + exclusions != establishments')
for code, z in by_zone_muni.items():
    # Zones are municipalities, so each zone must equal its municipality's private-business count.
    if z['companies_total'] != by_muni[code]['businesses']:
        errors.append(f'zone {code}: companies_total {z["companies_total"]} != businesses {by_muni[code]["businesses"]}')
    if z['shops_4711'] > by_muni[code]['shops_4711'] or z['software_it'] > by_muni[code]['it_companies_active']:
        errors.append(f'zone {code}: shops or IT above the municipal total')
if errors:
    sys.exit('Layers D/J/N checks failed:\n' + '\n'.join(errors[:50]))

# Every municipality gets a row: DENUE enumerates establishments, so a municipality with no record
# of a class has an observed count of 0 (not a missing value).
rows = [{'municipality_code': m, 'department_code': d, **{k: by_muni[m][k] for k in COLUMNS}} for m, d in sorted(munis.items())]
with open(os.path.join(CSV_DIR, 'fact_companies_municipality.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['municipality_code', 'department_code'] + COLUMNS, lineterminator='\n')
    w.writeheader()
    w.writerows(rows)

by_state = defaultdict(Counter)
for r in rows:
    by_state[r['department_code']].update({k: r[k] for k in COLUMNS})


def share(part, whole):
    return round(100 * part / whole, 1) if whole else None


def top(key, n=10):
    total = national[key]
    best = sorted(rows, key=lambda r: -r[key])[:n]
    return [{'municipality_code': r['municipality_code'], key: r[key], 'share_pct': share(r[key], total)} for r in best]


common = {
    'country': 'MX', 'source_id': 'INEGI_DENUE_202605', 'period': '2026-05',
    'edition': 'DENUE 05/2026 (metadata: Modified 2026-05-20)', 'classification': 'SCIAN 2018 (6 digits)',
    'sources': sources,
}
duplicate_note = ('One record (id 9701347, same clee, SCIAN 722511, municipality 20342) is repeated in sector files 72_1 and 72_2. '
                  'It is kept so the file total equals the published 6,138,075.') if duplicates else None
layer_d = {
    **common, 'layer': 'D',
    'indicators': {
        'D1_it_companies': national['it_companies_active'],
        'D1_by_code': {code: national[col] for code, col in IT_CODES.items()},
        'D1_software_only': None,
        'D2_top_municipalities': top('it_companies_active'),
        'D2_by_state': {s: by_state[s]['it_companies_active'] for s in sorted(by_state)},
        'D3_industry_census': None,
        'it_by_size_band': {b: it_size[b] for b in SIZE_BANDS},
    },
    'notes': {
        'D1_software_only': 'Not available: SCIAN 2018 541510 covers software development, IT consulting and other IT services together (ISIC 6201, 6202, 6209).',
        'D3_industry_census': 'Filled by build-mexico-d3-m4-census.py (Censos Económicos 2024, reference year 2023; D-MX-15).',
    },
    'limitations': 'DENUE counts establishments with a physical location, not firms or registrations: home-based and freelance IT work is largely absent, and a firm with several branches counts once per branch. Not comparable in level with registry counts such as Colombia RUES.',
}
layer_n = {
    **common, 'layer': 'N',
    'indicators': {
        'establishments_total': national['establishments'],
        'N1_businesses': national['businesses'],
        'N1_exclusions': dict(exclusions),
        'N1_excluded_classes': {reason: dict(c.most_common()) for reason, c in sorted(excluded_classes.items())},
        'N2_with_legal_name': legal_name['with_legal_name'],
        'N2_without_legal_name': legal_name['without_legal_name'],
        'N3_shops': national['shops_4711'],
        'N4_by_state': {s: {'businesses': by_state[s]['businesses'], 'shops_4711': by_state[s]['shops_4711'],
                            'share_of_businesses_pct': share(by_state[s]['businesses'], national['businesses'])} for s in sorted(by_state)},
        'N4_businesses_per_school': None,
        'size_bands_all_establishments': {b: size[b] for b in SIZE_BANDS},
        'unit_type': dict(unit_type),
    },
    'checks': {'establishments_equal_published_total': national['establishments'] == PUBLISHED_TOTAL, 'published_total': PUBLISHED_TOTAL,
               'duplicate_records': duplicates, 'duplicate_note': duplicate_note},
    'notes': {
        'N1_businesses': 'Private-business universe, closest to Colombia RUES (private merchants): excludes SCIAN 813 associations, cooperatives identified by legal name (COOPERATIVA, S.C. de R.L., S.C.L.) and public-sector establishments (SCIAN 93 and the classes whose name says \'sector público\').',
        'N2': 'Establishments with and without a razón social recorded; a proxy for legal entities vs natural persons, counted by establishment, not by firm.',
        'N4_businesses_per_school': 'Pending layer K (schools, cycle 2025-2026).',
    },
    'limitations': 'DENUE includes informal fixed and semi-fixed premises and has no renewal flag, so "active in the year" cannot be applied as in Colombia. Counts are establishments, not firms.',
}
# ───────────── Layer J: zones of Ciudad de México and Monterrey ─────────────
csv.field_size_limit(1 << 30)
with open(os.path.join(CSV_DIR, 'geo_municipality_shape.csv'), encoding='utf-8') as f:
    shapes = {r['municipality_code']: r['geojson'] for r in csv.DictReader(f)}
zone_rows, geo_zone_rows = [], []
for code in sorted(zone_of, key=lambda c: (zone_of[c][0], c)):
    prefix, zone_type = zone_of[code]
    g = geo_munis[code]
    zone_id = f'{prefix}-{code[2:]}'
    geo_zone_rows.append({'zone_id': zone_id, 'municipality_code': code, 'zone_type': zone_type, 'zone_code': code[2:],
                          'name': g['name'], 'lat': g['lat'], 'lon': g['lon'], 'geojson': shapes[code], 'wkt': g['wkt']})
    zone_rows.append({'zone_id': zone_id, 'zone_name': g['name'], **{k: by_zone_muni[code][k] for k in ZONE_COLUMNS}})
with open(os.path.join(CSV_DIR, 'geo_zone.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(geo_zone_rows[0]), lineterminator='\n')
    w.writeheader()
    w.writerows(geo_zone_rows)
with open(os.path.join(CSV_DIR, 'fact_companies_zone.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=['zone_id', 'zone_name'] + ZONE_COLUMNS, lineterminator='\n')
    w.writeheader()
    w.writerows(zone_rows)

cities = {}
for prefix in ZONE_CITIES:
    zr = [r for r in zone_rows if r['zone_id'].startswith(prefix + '-')]
    total = {k: sum(r[k] for r in zr) for k in ZONE_COLUMNS}
    cities[prefix] = {
        'zones': len(zr), 'totals': total,
        # Share of the city total held by each zone, per indicator (J1 medium/large, J2 IT, J3 groups, J4 shops).
        'zone_shares_pct': {r['zone_id']: {k: share(r[k], total[k]) for k in ZONE_COLUMNS} for r in zr},
        'zones_add_up': all(sum(r[k] for r in zr) == total[k] for k in ZONE_COLUMNS),
    }
layer_j = {
    **common, 'layer': 'J',
    'cities': {
        'CMX': {'name': 'Ciudad de México', 'zone_type': 'alcaldía (16)', **cities['CMX']},
        'MTY': {'name': 'Zona Metropolitana de Monterrey', 'zone_type': 'municipio (16)',
                'definition_source': 'SEDATU, CONAPO and INEGI, Metrópolis de México 2020, cuadros A.19.1.01 and B.19.1.01', **cities['MTY']},
    },
    'definitions': {
        'universe': 'Private businesses (N1 universe): excludes associations, cooperatives and the public sector.',
        'micro': 'DENUE size bands 0-5 and 6-10 people employed.',
        'medium_large': 'DENUE size bands 51-100, 101-250 and 251+ people employed (INEGI medium and large). Colombia measures size by assets, so shares are comparable only in direction.',
        'scian_groups': {**{k: sorted(v) for k, v in J_GROUPS.items()}, 'software_it': sorted(IT_CODES), 'shops_4711': [SHOP_CODE]},
    },
    'limitations': 'Zones are whole municipalities or alcaldías (Monterrey has no official internal division comparable to Colombian comunas). Counts are establishments, not firms.',
}
for name, doc in (('layer_d_mx.json', layer_d), ('layer_j_mx.json', layer_j), ('layer_n_mx.json', layer_n)):
    with open(os.path.join(LAYER_DIR, name), 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write('\n')
print(json.dumps({'establishments': national['establishments'], 'businesses': national['businesses'], 'exclusions': dict(exclusions),
                  'shops_4711': national['shops_4711'], 'it_companies_active': national['it_companies_active'],
                  'municipalities': len(rows), 'with_it': sum(1 for r in rows if r['it_companies_active']),
                  'duplicates': len(duplicates), 'zones': {p: c['zones'] for p, c in cities.items()},
                  'zone_totals': {p: c['totals']['companies_total'] for p, c in cities.items()}}, ensure_ascii=False))
