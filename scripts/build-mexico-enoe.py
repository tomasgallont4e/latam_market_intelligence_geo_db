"""Layers F, G, H and M (Mexico): INEGI ENOE 2025 microdata, quarters 1-4, read directly from the delivered zips.
Annual figures = sum of the quarterly expansion factor (fac_tri) over the four quarters / 4; interviews = records
over the four quarters (ENOE is a rotating panel, so one person can appear in several quarters).
Universe (ENOE codebook): r_def = 00, c_res 1 or 3, age 15 to 98, employed (clase2 = 1).
Occupations: SINCO 2019 (COE1 p3) mapped to the 13 personas by data/mexico/outputs/f_occupation_mapping_mx.csv
(scripts/build-mexico-f-sinco-mapping.py; decisions D-MX-07 to D-MX-09).
Writes the Colombia-shaped tables fact_persona_profile, fact_persona_department, fact_persona_metro,
fact_persona_segment, fact_ict_by_sector, fact_micro_department and fact_micro_national, and the layer JSONs.

Usage: python -I scripts/build-mexico-enoe.py <enoe_microdatos_dir> [repo_dir]
"""
import csv, hashlib, io, json, os, sys, unicodedata, zipfile
from collections import Counter, defaultdict

micro = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
MAPPING = os.path.join(OUT, 'f_occupation_mapping_mx.csv')
PERSONAS_CSV = os.path.join(repo, 'data', 'geodb-v2', 'csv', 'fact_persona_profile.csv')
QUARTERS = (1, 2, 3, 4)
# Published employed totals, ENOE quarterly bulletins 265/25, 433/25, 636/25 and 97/26 (millions, one decimal).
PUBLISHED_EMPLOYED_M = {1: 59.0, 2: 59.4, 3: 59.5, 4: 59.8}
TOLERANCE = 0.005  # template: employed within 0.5%
# Employers and own-account workers (all sizes), same bulletins, table "Población ocupada por posición en la ocupación"
# (p. 6, 2025 column). No micro-business total is published, so layer M is checked through these (tolerance 1%).
PUBLISHED_POSITION = {1: {'employers': 3043023, 'own_account': 13023470}, 2: {'employers': 3541449, 'own_account': 12860970},
                      3: {'employers': 3675572, 'own_account': 12950556}, 4: {'employers': 3572775, 'own_account': 12980516}}
M_TOLERANCE = 0.01
KEY = ('cd_a', 'ent', 'con', 'v_sel', 'n_hog', 'h_mud', 'n_ren')
RENAMES = {'cve_ent': 'ent', 'cve_mun': 'mun', 'cve_loc': 'loc', 'cve_ageb': 'ageb'}  # renamed by INEGI from Q3 2025
PERSONA_ID = {'2511': 'P01', '2521': 'P02', '3511': 'P03', '1330': 'P04', '2163': 'P05', '2421': 'P06', '2412': 'P07',
              '2120': 'P08', '2431': 'P09', '2411': 'P10', '2141': 'P11', '1211': 'P12', '2310': 'P13'}
CORE = ('P01', 'P02', 'P03', 'P04')
# ENOE cities (cd_a) anchored to their main municipality, as Colombia anchors metro areas to the capital.
# The expected catalogue name is checked, so a wrong code stops the build.
CITIES = {
    '01': ('Ciudad de México', '09015', 'Cuauhtémoc'), '02': ('Guadalajara', '14039', 'Guadalajara'), '03': ('Monterrey', '19039', 'Monterrey'),
    '04': ('Puebla', '21114', 'Puebla'), '05': ('León', '11020', 'León'), '06': ('Torreón', '05035', 'Torreón'),
    '07': ('San Luis Potosí', '24028', 'San Luis Potosí'), '08': ('Mérida', '31050', 'Mérida'), '09': ('Chihuahua', '08019', 'Chihuahua'),
    '10': ('Tampico', '28038', 'Tampico'), '12': ('Veracruz', '30193', 'Veracruz'), '13': ('Acapulco', '12001', 'Acapulco de Juárez'),
    '14': ('Aguascalientes', '01001', 'Aguascalientes'), '15': ('Morelia', '16053', 'Morelia'), '16': ('Toluca', '15106', 'Toluca'),
    '17': ('Saltillo', '05030', 'Saltillo'), '18': ('Villahermosa', '27004', 'Centro'), '19': ('Tuxtla Gutiérrez', '07101', 'Tuxtla Gutiérrez'),
    '20': ('Ciudad Juárez', '08037', 'Juárez'), '21': ('Tijuana', '02004', 'Tijuana'), '24': ('Culiacán', '25006', 'Culiacán'),
    '25': ('Hermosillo', '26030', 'Hermosillo'), '26': ('Durango', '10005', 'Durango'), '27': ('Tepic', '18017', 'Tepic'),
    '28': ('Campeche', '04002', 'Campeche'), '29': ('Cuernavaca', '17007', 'Cuernavaca'), '30': ('Coatzacoalcos', '30039', 'Coatzacoalcos'),
    '31': ('Oaxaca', '20067', 'Oaxaca de Juárez'), '32': ('Zacatecas', '32056', 'Zacatecas'), '33': ('Colima', '06002', 'Colima'),
    '36': ('Querétaro', '22014', 'Querétaro'), '39': ('Tlaxcala', '29033', 'Tlaxcala'), '40': ('La Paz', '03003', 'La Paz'),
    '41': ('Cancún', '23005', 'Benito Juárez'), '42': ('Ciudad del Carmen', '04003', 'Carmen'), '43': ('Pachuca', '13048', 'Pachuca de Soto'),
    '44': ('Mexicali', '02002', 'Mexicali'), '46': ('Reynosa', '28032', 'Reynosa'), '52': ('Tapachula', '07089', 'Tapachula'),
}
REST = 'Rest of the country'
# Sector codes (the SDEM 'scian' numbering) assigned from the activity code COE1 p4a, one variable for every sector as
# Colombia uses one ISIC variable (D-MX-17); the tech sector is SCIAN 51 (p4a 51xx). INEGI's derived 'scian' is only compared.
SECTORS = {'1': 'Agriculture', '2': 'Mining', '3': 'Utilities', '4': 'Construction', '5': 'Manufacturing', '6': 'Wholesale commerce',
           '7': 'Retail commerce', '8': 'Transport', '9': 'Information (SCIAN 51)', '10': 'Finance and insurance', '11': 'Real estate',
           '12': 'Professional and scientific services', '13': 'Corporate management', '14': 'Administrative services', '15': 'Education',
           '16': 'Health', '17': 'Arts and recreation', '18': 'Food and lodging', '19': 'Other services',
           '20': 'Public administration and defence', '21': 'Not specified'}
TECH_LABEL = 'Information (tech sector: SCIAN 51)'
P4A_SECTOR = {'11': '1', '21': '2', '22': '3', '23': '4', '31': '5', '32': '5', '33': '5', '43': '6', '46': '7', '48': '8', '49': '8',
              '51': '9', '52': '10', '53': '11', '54': '12', '55': '13', '56': '14', '61': '15', '62': '16', '71': '17', '72': '18',
              '81': '19', '93': '20'}  # 2-digit SCIAN sector of p4a → sector code; anything else is '21' (not specified)
SIZE_BANDS = {'01': 'alone', '02': '2-10', '03': '2-10', '04': '11-50', '05': '11-50', '06': '11-50', '07': '11-50',
              '08': '51-250', '09': '51-250', '10': '251+', '11': '251+'}  # ENOE p3q bands; template uses 201+, ENOE splits at 250


def norm(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower().strip()


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def rows(z, member):
    with z.open(member) as f:
        reader = csv.reader(io.TextIOWrapper(f, encoding='latin-1', newline=''))
        header = [RENAMES.get(h.strip(), h.strip()) for h in next(reader)]
        for values in reader:
            yield dict(zip(header, (v.strip() for v in values)))


SIZE_LIMITS = [(1, '01'), (5, '02'), (10, '03'), (15, '04'), (20, '05'), (30, '06'), (50, '07'), (100, '08'), (250, '09'), (500, '10')]


def workplace_size(r, size_var):
    """ENOE workplace-size band code (01-11) for everyone employed.
    Employees answer P3Q/P3L directly. Employers and own-account workers answer P3D (has workers or helpers?)
    and P3G1_2..P3G4_2 (how many, by type), the inputs INEGI uses for its own size classification (ambito2)."""
    band = r.get(size_var, '')
    if band.isdigit() and band != '99':
        return band.zfill(2)
    if r.get('p3d') == '2':
        return '01'
    if r.get('p3d') == '1':
        counts = [r.get(f'p3g{i}_2', '') for i in range(1, 5)]
        if any(c in ('999',) for c in counts):
            return ''
        n = 1 + sum(int(c) for c in counts if c.isdigit())
        return next((code for limit, code in SIZE_LIMITS if n <= limit), '11')
    return ''


def wmedian(pairs):
    pairs = sorted(p for p in pairs if p[0] is not None)
    total = sum(w for _, w in pairs)
    if not total:
        return None
    acc = 0.0
    for v, w in pairs:
        acc += w
        if acc >= total / 2:
            return v
    return pairs[-1][0]


def pct(num, den):
    return round(100 * num / den, 1) if den else None


# ───────────── Inputs: personas, mapping, geography ─────────────
with open(PERSONAS_CSV, encoding='utf-8-sig') as f:
    personas = [{'persona': r['persona'], 'ring': r['ring'], 'isco_codes': r['isco_codes']} for r in csv.DictReader(f)]
for p in personas:
    p['persona_id'] = PERSONA_ID[p['isco_codes'].split()[0]]
name_of = {p['persona_id']: p['persona'] for p in personas}
with open(MAPPING, encoding='utf-8') as f:
    persona_of_sinco = {}
    for r in csv.DictReader(f):
        if r['in_primary'] == 'True':
            if r['sinco2019_code'] in persona_of_sinco:
                sys.exit(f"SINCO {r['sinco2019_code']} assigned to two personas: no double counting allowed")
            persona_of_sinco[r['sinco2019_code']] = r['persona_id']
with open(os.path.join(CSV_DIR, 'geo_municipality.csv'), encoding='utf-8') as f:
    muni_name = {r['municipality_code']: r['name'] for r in csv.DictReader(f)}
with open(os.path.join(CSV_DIR, 'geo_department.csv'), encoding='utf-8') as f:
    state_name = {r['department_code']: r['name'] for r in csv.DictReader(f)}
errors = [f'city {cd}: {code} is {muni_name.get(code)!r}, expected {expected!r}' for cd, (_, code, expected) in CITIES.items()
          if norm(muni_name.get(code, '')) != norm(expected)]
if errors:
    sys.exit('City anchors do not match the catalogue:\n' + '\n'.join(errors))

# ───────────── Read the four quarters ─────────────
recs = []  # one tuple per employed person-quarter
checks, sources = {}, []
sector_agreement = Counter()  # weight where the p4a sector equals / differs from INEGI's derived scian
for q in QUARTERS:
    path = os.path.join(micro, f'enoe_2025_trim{q}_csv.zip')
    sources.append({'zip': os.path.basename(path), 'sha256': sha256(path)})
    with zipfile.ZipFile(path) as z:
        names = {n.upper(): n for n in z.namelist()}
        # Workplace size: P3Q in the extended questionnaire (Q1), P3L in the basic one (Q2-Q4), same codes.
        size_var = 'p3q' if q == 1 else 'p3l'
        coe1 = {tuple(r[k] for k in KEY): (r['p3'], workplace_size(r, size_var), r['p4a'], r['p4e'], r['p4f'], r['p4g'])
                for r in rows(z, names[f'ENOE_COE1T{q}25.CSV'])}
        employed, missing = 0.0, 0
        position = Counter()
        for r in rows(z, names[f'ENOE_SDEMT{q}25.CSV']):
            if r['r_def'] not in ('0', '00') or r['c_res'] not in ('1', '3') or not r['eda'].isdigit() or not 15 <= int(r['eda']) <= 98:
                continue
            if r['clase2'] != '1':
                continue
            w = float(r['fac_tri'])
            employed += w
            position[r['pos_ocu']] += w
            occ = coe1.get(tuple(r[k] for k in KEY))
            if occ is None:
                missing += 1
                occ = ('',) * 6
            p3, p3q, p4a, p4e, p4f, p4g = occ
            p3 = p3.zfill(4) if p3.isdigit() else p3
            tech = p4a.startswith('51')  # SCIAN hogares: IT services sit inside 5411 with all professional services
            sector = P4A_SECTOR.get(p4a[:2], '21')
            sector_agreement['same' if sector == r['scian'] else 'different'] += w
            recs.append((q, w, persona_of_sinco.get(p3), p3, r['ent'].zfill(2), r['cd_a'].zfill(2), r['pos_ocu'], r['tue3'], p3q,
                         sector, tech, r['sex'], int(r['eda']), r['cs_p13_1'].zfill(2) if r['cs_p13_1'] else '',
                         float(r['ingocup']) if r['ingocup'] not in ('', '0') else None, r['est'][:1], r['ur'], r['tue_ppal'], p4e, p4f, p4g,
                         p4a == '5411'))
    published = PUBLISHED_EMPLOYED_M[q] * 1e6
    checks[f'Q{q}'] = {'employed': round(employed), 'published_millions': PUBLISHED_EMPLOYED_M[q],
                       'difference_pct': round(100 * (employed - published) / published, 3),
                       'within_tolerance': abs(employed - published) <= max(TOLERANCE * published, 0.05e6),
                       'records_without_occupation_record': missing}
    for key, code in (('employers', '2'), ('own_account', '3')):
        pub = PUBLISHED_POSITION[q][key]
        checks[f'Q{q}'][f'{key}_vs_bulletin'] = {'microdata': round(position[code]), 'published': pub,
                                                  'difference_pct': round(100 * (position[code] - pub) / pub, 3),
                                                  'within_1pct': abs(position[code] - pub) <= M_TOLERANCE * pub}
        if not checks[f'Q{q}'][f'{key}_vs_bulletin']['within_1pct']:
            sys.exit(f'Q{q} {key} {position[code]:,.0f} differs from the published {pub:,} by more than 1%')
    if not checks[f'Q{q}']['within_tolerance']:
        sys.exit(f'Q{q} employed {employed:,.0f} differs from the published {published:,.0f} by more than 0.5%')
Q, W, PID, P3, ENT, CDA, POS, TUE3, P3Q, SCIAN, TECH, SEX, EDA, EDU, INC, STRAT, UR, TUEP, P4E, P4F, P4G, PROF5411 = range(22)
annual = lambda rs: sum(r[W] for r in rs) / len(QUARTERS)


def share(rs, test, valid=lambda r: True):
    base = [r for r in rs if valid(r)]
    return pct(sum(r[W] for r in base if test(r)), sum(r[W] for r in base))


def confidence(n, high=1000, medium=300):
    return 'high' if n >= high else 'medium' if n >= medium else 'low'


# ───────────── F: personas ─────────────
by_persona = defaultdict(list)
for r in recs:
    if r[PID]:
        by_persona[r[PID]].append(r)
known_pos = lambda r: r[POS] in ('1', '2', '3', '4')
known_size = lambda r: r[P3Q] in SIZE_BANDS
known_sector = lambda r: r[SCIAN] not in ('', '21')
known_edu = lambda r: r[EDU] not in ('', '99')
profile = []
for p in personas:
    rs = by_persona[p['persona_id']]
    profile.append({
        'persona': p['persona'], 'ring': p['ring'], 'isco_codes': p['isco_codes'], 'employed': round(annual(rs)), 'interviews': len(rs),
        'pct_private_employee': share(rs, lambda r: r[POS] == '1' and r[TUE3] != '1', known_pos),
        'pct_government_employee': share(rs, lambda r: r[POS] == '1' and r[TUE3] == '1', known_pos),
        'pct_self_employed_or_employer': share(rs, lambda r: r[POS] in ('2', '3'), known_pos),
        'pct_firm_251_plus': share(rs, lambda r: SIZE_BANDS[r[P3Q]] == '251+', known_size),
        'pct_works_alone': share(rs, lambda r: r[P3Q] == '01', known_size),
        'pct_outside_tech_sector': share(rs, lambda r: not r[TECH], known_sector),
        'pct_women': share(rs, lambda r: r[SEX] == '2'),
        'pct_university': share(rs, lambda r: r[EDU] in ('07', '08', '09'), known_edu),
        'median_age': wmedian([(r[EDA], r[W]) for r in rs]),
        'median_income_mxn': wmedian([(r[INC], r[W]) for r in rs if r[INC]]),
        'pct_stratum_3_4': share(rs, lambda r: r[STRAT] in ('3', '4'), lambda r: r[STRAT] in ('1', '2', '3', '4')),
        'pct_works_from_home': None,
    })

department, metro, segment = [], [], []
for p in personas:
    rs = by_persona[p['persona_id']]
    for ent in sorted({r[ENT] for r in rs}):
        cell = [r for r in rs if r[ENT] == ent]
        department.append({'persona': p['persona'], 'department_code': ent, 'department': state_name.get(ent, ''), 'employed': round(annual(cell)), 'interviews': len(cell)})
    city_of = lambda r: CITIES[r[CDA]][0] if r[CDA] in CITIES else REST
    for city in sorted({city_of(r) for r in rs}, key=lambda c: (c == REST, c)):
        cell = [r for r in rs if city_of(r) == city]
        code = next((c for _, (n, c, _) in CITIES.items() if n == city), '')
        metro.append({'persona': p['persona'], 'municipality_code': code, 'metro_area': city, 'employed': round(annual(cell)), 'interviews': len(cell)})

    def buyer(r):
        if r[POS] in ('2', '3'):
            return 'Self-employed or employer'
        if r[POS] == '1' and r[TUE3] == '1':
            return 'Government employee'
        if r[POS] == '1' and r[P3Q] in SIZE_BANDS:
            band = SIZE_BANDS[r[P3Q]]
            return {'251+': 'Employee, firm 251+', '51-250': 'Employee, firm 11-250', '11-50': 'Employee, firm 11-250'}.get(band, 'Employee, firm up to 10')
        return 'Other or unknown'
    cells = defaultdict(list)
    for r in rs:
        cells[(city_of(r), buyer(r))].append(r)
    for (city, btype), cell in sorted(cells.items(), key=lambda kv: (kv[0][0] == REST, kv[0])):
        code = next((c for _, (n, c, _) in CITIES.items() if n == city), '')
        segment.append({'persona': p['persona'], 'municipality_code': code, 'city': city, 'buyer_type': btype,
                        'employed': round(annual(cell)), 'interviews': len(cell)})

# ───────────── G: IT staff (4 core personas) in every industry ─────────────
core = [r for r in recs if r[PID] in CORE]
sector_of = lambda r: TECH_LABEL if r[TECH] else SECTORS.get(r[SCIAN], 'Not specified')
core_total = annual(core)
by_sector = defaultdict(list)
for r in core:
    by_sector[sector_of(r)].append(r)
ict_by_sector = sorted(({'sector': s, 'employed': round(annual(rs)), 'share_pct': pct(annual(rs), core_total)} for s, rs in by_sector.items()),
                       key=lambda x: -x['employed'])
outside = [r for r in core if not r[TECH] and known_sector(r)]
gov = [r for r in core if r[POS] == '1' and r[TUE3] == '1']
layer_g = {
    'sector_variable': {'source': 'COE1 p4a, 2-digit SCIAN sector (D-MX-17)',
                        'pct_employed_same_as_inegi_derived_scian': round(100 * sector_agreement['same'] / sum(sector_agreement.values()), 2)},
    'G1_it_staff_total': round(core_total), 'G1_outside_tech_pct': share(core, lambda r: not r[TECH], known_sector),
    'G1_outside_tech_pct_sensitivity_incl_5411': share(core, lambda r: not (r[TECH] or r[PROF5411]), known_sector),
    'G1_core_in_5411_professional_services_pct': share(core, lambda r: r[PROF5411], known_sector),
    'G1_check_equals_sum_of_core_personas': round(core_total) == sum(x['employed'] for x in profile if PERSONA_ID[x['isco_codes'].split()[0]] in CORE)
                                            or abs(core_total - sum(annual(by_persona[c]) for c in CORE)) < 1,
    'G2_outside_tech_by_size': {b: round(annual([r for r in outside if r[P3Q] in SIZE_BANDS and SIZE_BANDS[r[P3Q]] == b])) for b in ('alone', '2-10', '11-50', '51-250', '251+')},
    'G2_outside_tech_size_unknown': round(annual([r for r in outside if r[P3Q] not in SIZE_BANDS])),
    'G3_government_it_staff': round(annual(gov)),
    'G3_government_by_sector': {s: round(annual([r for r in gov if sector_of(r) == s])) for s in sorted({sector_of(r) for r in gov})},
    'G4_public_share_by_persona': {name_of[pid]: {'government_employee_pct': share(rs, lambda r: r[POS] == '1' and r[TUE3] == '1', known_pos),
                                                  'public_administration_sector_pct': share(rs, lambda r: r[SCIAN] == '20', known_sector)}
                                   for pid, rs in sorted(by_persona.items())},
}

# ───────────── M: micro-businesses (own-account workers and employers in units of up to 10 people) ─────────────
micro_rs = [r for r in recs if r[POS] in ('2', '3') and r[P3Q] in ('01', '02', '03')]
micro_total = annual(micro_rs)
micro_dept = [{'department_code': e, 'department': state_name.get(e, ''), 'micro_businesses': round(annual([r for r in micro_rs if r[ENT] == e]))}
              for e in sorted({r[ENT] for r in micro_rs})]
dims = {
    'total': lambda r: 'micro_businesses',
    'activity': lambda r: SECTORS.get(r[SCIAN], 'Not specified'),
    'position': lambda r: 'Own-account worker' if r[POS] == '3' else 'Employer',
    'owner_sex': lambda r: 'Women' if r[SEX] == '2' else 'Men',
    'owner_age': lambda r: '15-29' if r[EDA] < 30 else '30-44' if r[EDA] < 45 else '45-59' if r[EDA] < 60 else '60+',
    'informal_sector': lambda r: 'Informal sector' if r[TUEP] == '1' else 'Outside the informal sector' if r[TUEP] == '2' else 'Not specified',
    'accounts': lambda r: {'1': 'Accountant', '2': 'Personal notebook', '3': 'No records', '4': 'Other'}.get(r[P4G], 'Not asked or not specified'),
    'premises': lambda r: {'1': 'Establishment and office', '2': 'Office only', '3': 'Premises only', '4': 'No premises'}.get(r[P4E], 'Not asked or not specified'),
    'site_without_premises': lambda r: ({'01': 'Field', '02': 'Street, door to door', '03': 'Improvised stall', '04': 'Non-motor vehicle', '05': 'Motor vehicle',
                                         '06': 'Own home', '07': 'Own home', '08': "Client's or employer's premises", '09': 'Semi-fixed stall', '10': 'Fixed stall',
                                         '11': 'Other place'}.get(r[P4F], 'Not specified') if r[P4E] == '4' else None),
    'zone': lambda r: 'Urban' if r[UR] == '1' else 'Rural' if r[UR] == '2' else 'Not specified',
}
micro_national = []
for dim, fn in dims.items():
    groups = defaultdict(list)
    for r in micro_rs:
        k = fn(r)
        if k is not None:
            groups[k].append(r)
    base = sum(annual(v) for v in groups.values())
    for k, v in sorted(groups.items(), key=lambda kv: -annual(kv[1])):
        micro_national.append({'dimension': dim, 'category': k, 'micro_businesses': round(annual(v)), 'pct': pct(annual(v), base)})

# ───────────── Write ─────────────
def write(name, rows_, folder=CSV_DIR):
    with open(os.path.join(folder, name), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows_[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows_)
write('fact_persona_profile.csv', profile)
write('fact_persona_department.csv', department)
write('fact_persona_metro.csv', metro)
write('fact_persona_segment.csv', segment)
write('fact_ict_by_sector.csv', ict_by_sector)
write('fact_micro_department.csv', micro_dept)
write('fact_micro_national.csv', micro_national)

# Parts add up: every persona's departments, cities and segments sum to its total (rounding only).
add_up = {}
for p in profile:
    for name, rows_ in (('department', department), ('metro', metro), ('segment', segment)):
        s = sum(x['employed'] for x in rows_ if x['persona'] == p['persona'])
        add_up[f"{p['persona']}|{name}"] = abs(s - p['employed']) <= len([x for x in rows_ if x['persona'] == p['persona']])
common = {'country': 'MX', 'source_id': 'INEGI_ENOE_2025', 'period': '2025 (Q1-Q4 average)', 'sources': sources,
          'universe': 'r_def = 00, c_res 1 or 3, age 15-98, employed (clase2 = 1); annual = sum of fac_tri over 4 quarters / 4'}
layer_f = {**common, 'layer': 'F',
           'checks': {'employed_vs_bulletins': checks, 'parts_add_up': all(add_up.values()), 'no_double_counting': True},
           'unassigned_blank_occupation_employed': round(annual([r for r in recs if not r[P3]])),
           'personas': [{**p, 'confidence': confidence(p['interviews'])} for p in profile],
           'rings': {ring: round(sum(p['employed'] for p in profile if p['ring'] == ring)) for ring in ('core', 'adjacent', 'extended')},
           'F10_context_home_based_without_premises_pct': {name_of[pid]: share(rs, lambda r: r[P4F] in ('06', '07'), lambda r: r[P4E] == '4')
                                                           for pid, rs in sorted(by_persona.items())},
           'notes': {
               'workplace_size_variable': 'P3Q in the extended questionnaire (Q1) and P3L in the basic questionnaire (Q2-Q4): same question and codes.',
               'pct_firm_251_plus': 'ENOE p3q bands split at 250 people (101-250 / 251-500), so the template band 201+ becomes 251+. Size counts people at the workplace, not the whole firm.',
               'pct_works_from_home': 'Not available: ENOE asks where the work is done (p4f) only for businesses without premises (p4e = 4), not for employees. The home-based share among those businesses is given as context.',
               'pct_stratum_3_4': 'ENOE socioeconomic stratum (first digit of est: 1 low, 2 lower-middle, 3 upper-middle, 4 high), share in strata 3-4.',
               'pct_outside_tech_sector': 'Tech sector = SCIAN 51 (p4a 51xx). ENOE codes activity with SCIAN hogares, where IT services (SCIAN 5415, ISIC 62) sit inside 5411 together with legal, accounting, architecture and consulting services, so they cannot be separated: outside-tech shares are overstated against ISIC section J (Colombia). layer_g_mx.json gives a sensitivity that also counts 5411 as tech.',
               'workplace_size_independents': 'Employers and own-account workers: 1 + workers reported in P3G1_2..P3G4_2 when P3D = 1, alone when P3D = 2 (the inputs of INEGI ambito2).',
               'median_income_mxn': 'Weighted median monthly labour income (ingocup) among those who report a positive income.',
               'interviews': 'Records over the four quarters; ENOE is a rotating panel, so a person can be counted in up to four quarters.',
               'denominators': 'Each share uses only valid answers for its variable (not specified excluded).'},
           'limitations': 'Survey estimates with sampling error; cells with few interviews (see interviews and confidence) are indicative only.'}
layer_h = {**common, 'layer': 'H', 'buyer_types': sorted({x['buyer_type'] for x in segment}),
           'cities': {cd: {'name': n, 'anchor_municipality': c} for cd, (n, c, _) in CITIES.items()},
           'cells': len(segment), 'confidence_rule': 'high >= 1,000 interviews, medium 100-999, low < 100 (template H2)',
           'cells_by_confidence': dict(Counter(confidence(x['interviews'], 1000, 100) for x in segment)),
           'notes': {'firm_size_bands': 'Employee bands use ENOE p3q: up to 10, 11-250, 251+ (Colombia: up to 10, 11-200, 201+).',
                     'method': 'Direct cross-tabulation; cells of each persona add to the persona total.'}}
layer_m = {**common, 'layer': 'M', 'M1_micro_businesses': round(micro_total),
           'definition': 'Own-account workers and employers (pos_ocu 2-3) whose workplace has up to 10 people (p3q 01-03), the template fallback; ENAMIN was discontinued after 2012.',
           'M1_by_position': {'own_account': round(annual([r for r in micro_rs if r[POS] == '3'])), 'employers': round(annual([r for r in micro_rs if r[POS] == '2']))},
           'check_position_totals_vs_bulletins': {q: {k: v for k, v in c.items() if k.endswith('_vs_bulletin')} for q, c in checks.items()},
           'check_note': 'No micro-business total is published. All-size employers and own-account workers in the microdata are checked against the quarterly bulletins (within 1%); M1 is the subset in units of up to 10 people.',
           'M4_digital': None, 'M6_median_monthly_owner_income_mxn': wmedian([(r[INC], r[W]) for r in micro_rs if r[INC]]),
           'notes': {'M4_digital': 'Filled by build-mexico-d3-m4-census.py (Censos Económicos 2024, reference year 2023; D-MX-15).',
                     'M6': 'Not sales: ENOE has no business sales question; this is the owner\'s labour income, labelled as such.',
                     'size_limit': 'Up to 10 people: ENOE p3q bands give 1, 2-5, 6-10, so the template limit of 9 cannot be applied.'}}
for name, doc in (('layer_f_mx.json', layer_f), ('layer_g_mx.json', {**common, 'layer': 'G', **layer_g}), ('layer_h_mx.json', layer_h), ('layer_m_mx.json', layer_m)):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write('\n')
print(json.dumps({'employed_checks': {k: v['difference_pct'] for k, v in checks.items()}, 'parts_add_up': all(add_up.values()),
                  'rings': layer_f['rings'], 'G1': layer_g['G1_it_staff_total'], 'G1_outside_tech_pct': layer_g['G1_outside_tech_pct'],
                  'M1': layer_m['M1_micro_businesses']}, ensure_ascii=False))
for p in profile:
    print(p['persona'][:40].ljust(40), str(p['employed']).rjust(9), str(p['interviews']).rjust(6), confidence(p['interviews']).ljust(6),
          'inc', p['median_income_mxn'], 'women', p['pct_women'], 'univ', p['pct_university'])
