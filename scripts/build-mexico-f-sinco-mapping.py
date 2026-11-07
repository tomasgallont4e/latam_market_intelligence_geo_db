"""Layer F (Mexico): occupation mapping SINCO 2019 -> SINCO 2011 -> CIUO-08 -> the 13 template personas.
ENOE 2025 codes occupation with SINCO 2019. INEGI publishes no SINCO 2019 -> CIUO-08 table, so the official
route is chained:
  1. SINCO 2019 <-> SINCO 2011: 'Tabla de equivalencia SINCO 2011 - 2019', annex of the SINCO 2019 manual;
  2. SINCO 2011 -> CIUO-08: 'SINCO 2011. Tablas comparativas' (INEGI, Nov 2012), sheet SINCO-CIUO.
Persona rule (Peru Day 1 FINAL f_occupation_mapping_pe.csv): a SINCO code enters a persona only when every
CIUO-08 code it links to belongs to that persona (exact_within_persona). Codes that also link outside the
persona are excluded and listed for review (excluded_ambiguous). 2019 codes without a 2011 equivalent are
listed for review, never assigned automatically. Persona definitions: data/geodb-v2/csv/fact_persona_profile.csv.

Usage: python -I scripts/build-mexico-f-sinco-mapping.py <inegi_sinco_ciuo_dir> [repo_dir]
  (needs the openpyxl and pypdf packages)
"""
import csv, hashlib, json, os, re, sys
from collections import defaultdict
import openpyxl, pypdf

src = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
XLSX = os.path.join(src, 'sinco_tablas_comparativas.xlsx')
MANUAL = os.path.join(src, 'sinco_2019_702825198411.pdf')
ANNEX_PAGES = range(357, 393)  # 'Tabla de equivalencia SINCO 2011 - 2019' in the PDF (printed pages 359-394)
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
PERSONAS_CSV = os.path.join(repo, 'data', 'geodb-v2', 'csv', 'fact_persona_profile.csv')
# Peru's persona ids, keyed by the first ISCO code of each persona (same order as the template annex 2).
PERSONA_ID = {'2511': 'P01', '2521': 'P02', '3511': 'P03', '1330': 'P04', '2163': 'P05', '2421': 'P06', '2412': 'P07',
              '2120': 'P08', '2431': 'P09', '2411': 'P10', '2141': 'P11', '1211': 'P12', '2310': 'P13'}


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


# ───────────── Personas (Colombia definitions) ─────────────
with open(PERSONAS_CSV, encoding='utf-8-sig') as f:
    personas = [{'persona': r['persona'], 'ring': r['ring'], 'isco': r['isco_codes'].split()} for r in csv.DictReader(f)]
for p in personas:
    p['persona_id'] = PERSONA_ID[p['isco'][0]]
persona_of_ciuo = {c: p['persona_id'] for p in personas for c in p['isco']}
by_id = {p['persona_id']: p for p in personas}

# ───────────── SINCO 2011 -> CIUO-08 (official comparative table) ─────────────
ws = openpyxl.load_workbook(XLSX, read_only=True, data_only=True)['SINCO-CIUO']
s11_title, s11_ciuo, ciuo_title = {}, defaultdict(list), {}
current = None
for r in ws.iter_rows(min_row=7, values_only=True):
    r = [('' if c is None else str(c).strip()) for c in r] + [''] * 8
    s, sname, c, cname = r[3], r[4], r[5], r[6]
    if re.fullmatch(r'\d{4}', s):
        current = s
        s11_title[s] = sname
    elif s:
        current = None
    if current and re.fullmatch(r'\d{4}', c):
        s11_ciuo[current].append(c)
        ciuo_title[c] = cname

# ───────────── SINCO 2019 <-> SINCO 2011 (annex of the SINCO 2019 manual) ─────────────
LEFT = re.compile(r'^\s{0,8}(\d{4})\s+(\S.*?)(?:\s{3,}|$)')
RIGHT = re.compile(r'\s{2,}(\d{4})\s+(\S.*?)\s*$')
reader = pypdf.PdfReader(MANUAL)
s19_title, s19_to_11, unpaired_19, unpaired_11 = {}, defaultdict(set), [], []
for n in ANNEX_PAGES:
    for line in reader.pages[n - 1].extract_text(extraction_mode='layout').splitlines():
        left = LEFT.match(line)
        right = RIGHT.search(line, 35)  # the SINCO 2011 column starts right of the 2019 title
        if left and right:
            # Justified text leaves wide gaps inside titles: take everything up to the 2011 column.
            s19_title.setdefault(left.group(1), re.sub(r'\s+', ' ', line[left.end(1):right.start()]).strip())
            s19_to_11[left.group(1)].add(right.group(1))
        elif left:
            s19_title.setdefault(left.group(1), left.group(2))
            unpaired_19.append((n, left.group(1), left.group(2)))
        elif right:
            unpaired_11.append((n, right.group(1), right.group(2)))

# A 2019 code printed alone on one line is either a new group or a pair whose 2011 code sits on a wrapped line;
# the latter appears later as a lone 2011 code with the same number.
lone_11 = {c for _, c, _ in unpaired_11}
new_2019 = []
for n, code, title in unpaired_19:
    if code in s19_to_11:
        continue
    if code in lone_11:
        s19_to_11[code].add(code)
    else:
        new_2019.append({'sinco2019': code, 'title': title, 'page': n})

# ───────────── Chain and classify ─────────────
corr_rows, persona_rows = [], []
for s19 in sorted(set(s19_title) | set(s19_to_11)):
    s11s = sorted(s19_to_11.get(s19, []))
    ciuos = sorted({c for s in s11s for c in s11_ciuo.get(s, [])})
    linked = {persona_of_ciuo.get(c) for c in ciuos}
    ids = sorted(x for x in linked if x)
    if not s11s:
        status = 'new_in_2019_review'
    elif not ciuos:
        status = 'no_ciuo_link'
    elif not ids:
        status = 'outside_personas'
    elif len(linked) == 1:
        status = 'exact_within_persona'
    else:
        status = 'excluded_ambiguous'
    corr_rows.append({'sinco2019_code': s19, 'sinco2019_title': s19_title.get(s19, ''), 'sinco2011_codes': ';'.join(s11s),
                      'sinco2011_titles': ' | '.join(s11_title.get(s, '') for s in s11s), 'ciuo08_codes': ';'.join(ciuos),
                      'ciuo08_titles': ' | '.join(ciuo_title.get(c, '') for c in ciuos), 'persona_ids': ';'.join(ids), 'mapping_status': status})
    for pid in ids:
        p = by_id[pid]
        in_persona = [c for c in ciuos if persona_of_ciuo.get(c) == pid]
        outside = [c for c in ciuos if persona_of_ciuo.get(c) != pid]
        persona_rows.append({
            'persona_id': pid, 'persona': p['persona'], 'ring': p['ring'], 'sinco2019_code': s19, 'sinco2019_title': s19_title.get(s19, ''),
            'sinco2011_codes': ';'.join(s11s), 'ciuo08_codes_linked': ';'.join(ciuos), 'ciuo08_codes_in_persona': ';'.join(in_persona),
            'mapping_status': status, 'in_primary': status == 'exact_within_persona',
            'note': '' if not outside else 'Also links to CIUO ' + ', '.join(f"{c} {ciuo_title.get(c, '')}".strip() + (f' ({persona_of_ciuo[c]})' if c in persona_of_ciuo else '') for c in outside),
        })

# Reviewed overrides (data/mexico/f_mapping_overrides.csv): approved decisions only, each with its decision id.
OVERRIDES = os.path.join(repo, 'data', 'mexico', 'f_mapping_overrides.csv')
overrides = []
if os.path.exists(OVERRIDES):
    with open(OVERRIDES, encoding='utf-8') as f:
        overrides = [o for o in csv.DictReader(f) if o['status'] == 'approved']
for o in overrides:
    code, pid = o['sinco2019_code'], o['persona_id']
    hit = [r for r in persona_rows if r['sinco2019_code'] == code and r['persona_id'] == pid]
    if o['action'] == 'include':
        if hit:
            hit[0].update(in_primary=True, mapping_status='included_by_review', note=(hit[0]['note'] + ' ' if hit[0]['note'] else '') + f"Included by {o['decision_id']}.")
        else:
            corr = next(r for r in corr_rows if r['sinco2019_code'] == code)
            persona_rows.append({'persona_id': pid, 'persona': by_id[pid]['persona'], 'ring': by_id[pid]['ring'], 'sinco2019_code': code,
                                 'sinco2019_title': corr['sinco2019_title'], 'sinco2011_codes': corr['sinco2011_codes'],
                                 'ciuo08_codes_linked': corr['ciuo08_codes'], 'ciuo08_codes_in_persona': '', 'mapping_status': 'included_by_review',
                                 'in_primary': True, 'note': f"New in SINCO 2019, no SINCO 2011 equivalent. Included by {o['decision_id']}."})
    elif o['action'] == 'exclude' and hit:
        hit[0].update(in_primary=False, mapping_status='excluded_by_review', note=(hit[0]['note'] + ' ' if hit[0]['note'] else '') + f"Excluded by {o['decision_id']}.")

# Codes left out by the strict rule, and new 2019 groups, go to a review list with a suggested action.
SUGGEST = {  # sinco2019_code: (persona_id, suggested action, reason)
    '2321': ('P13', 'include', 'Title is university and higher-education teachers; the extra link (CIUO 2320 vocational teachers) is minor. Without it P13 has no code.'),
    '1329': ('P04', 'include', 'New 2019 group "Otros directores y gerentes en informática, telecomunicaciones": same scope as CIUO 1330.'),
    '1319': ('P12', 'include', 'New 2019 group "Otros directores y gerentes de área en producción": CIUO 1321-1324 production managers.'),
    '1711': ('P12', 'include', 'Sales and marketing area heads: mostly CIUO 1221-1222; the retail-manager link (1420) is secondary.'),
    '2111': ('P06', 'include', 'HR administrators and professionals: links to 2421-2422 (persona) and 2423-2424 (HR). Without it P06 rests on 2113 hotel and tourism professionals only.'),
    '2713': ('P13', 'exclude', 'Commercial training instructors: links to IT trainers (2356) and teachers n.e.c. (2359); the title is not IT.'),
    '1524': ('P12', 'exclude', 'Legal-services area heads: links to judges (2612).'),
    '1224': ('P12', 'exclude', 'Judges and legal-services directors: links to judges (2612).'),
    '2611': ('P08', 'exclude', 'Physics, astronomy and mathematics technicians: links mostly outside the persona (3111, 4312).'),
    '2131': ('P08', 'exclude', 'Anthropologists, archaeologists and historians: links to 2633 philosophers and historians.'),
    '2132': ('P08', 'exclude', 'Sociology researchers: links to 2164 urban planners.'),
    '2262': ('P11', 'exclude', 'Topography, hydrology and geology engineers: links mostly to geologists (2114) and surveyors (2165).'),
    '1422': ('P12', 'exclude', 'Museum and cinema managers: links to 1431 recreation and culture managers.'),
    '1423': ('P12', 'exclude', 'Funeral-services managers: links to 1439 services managers n.e.c.'),
}
decided = {(o['sinco2019_code'], o['persona_id']): o['decision_id'] for o in overrides}
review = []
for r in persona_rows:
    if r['mapping_status'] in ('excluded_ambiguous', 'excluded_by_review', 'included_by_review'):
        s = SUGGEST.get(r['sinco2019_code'], (r['persona_id'], 'review', ''))
        review.append({'sinco2019_code': r['sinco2019_code'], 'sinco2019_title': r['sinco2019_title'], 'persona_id': r['persona_id'],
                       'persona': r['persona'], 'ciuo08_codes_linked': r['ciuo08_codes_linked'], 'strict_rule': 'excluded_ambiguous' if r['mapping_status'] != 'included_by_review' or r['ciuo08_codes_linked'] else 'new_in_2019',
                       'suggested_action': s[1], 'reason': s[2] or r['note'], 'decision_id': decided.get((r['sinco2019_code'], r['persona_id']), ''),
                       'current': 'included' if r['in_primary'] else 'excluded'})
for n in new_2019:
    s = SUGGEST.get(n['sinco2019'])
    if s and not any(x['sinco2019_code'] == n['sinco2019'] for x in review):
        review.append({'sinco2019_code': n['sinco2019'], 'sinco2019_title': s19_title.get(n['sinco2019'], n['title']), 'persona_id': s[0],
                       'persona': by_id[s[0]]['persona'], 'ciuo08_codes_linked': '', 'strict_rule': 'new_in_2019', 'suggested_action': s[1],
                       'reason': s[2], 'decision_id': decided.get((n['sinco2019'], s[0]), ''), 'current': 'excluded'})

summary = []
for p in personas:
    pid = p['persona_id']
    rows = [r for r in persona_rows if r['persona_id'] == pid]
    primary = [r['sinco2019_code'] for r in rows if r['in_primary']]
    reached = {c for r in rows if r['in_primary'] for c in r['ciuo08_codes_in_persona'].split(';') if c}
    summary.append({'persona_id': pid, 'persona': p['persona'], 'ring': p['ring'], 'isco08_template_codes': ';'.join(p['isco']),
                    'sinco2019_codes_primary': ';'.join(primary),
                    'sinco2019_codes_excluded': ';'.join(r['sinco2019_code'] for r in rows if not r['in_primary']),
                    'isco08_codes_reached': ';'.join(sorted(reached)),
                    'isco08_codes_not_reached': ';'.join(c for c in p['isco'] if c not in reached),
                    'review_status': 'pending_approval'})

os.makedirs(OUT, exist_ok=True)
def write(name, rows):
    with open(os.path.join(OUT, name), 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
write('f_sinco2019_ciuo08_correspondence_mx.csv', corr_rows)
write('f_occupation_mapping_mx.csv', sorted(persona_rows, key=lambda r: (r['persona_id'], r['sinco2019_code'])))
write('f_persona_correspondence_mx.csv', summary)
write('f_mapping_review_mx.csv', sorted(review, key=lambda r: (r['suggested_action'], r['persona_id'], r['sinco2019_code'])))

counts = defaultdict(int)
for r in corr_rows:
    counts[r['mapping_status']] += 1
meta = {
    'country': 'MX', 'layer': 'F', 'purpose': 'Occupation mapping for ENOE 2025 (SINCO 2019) to the 13 template personas (CIUO-08). Pending approval.',
    'sources': {'sinco2011_ciuo08': {'file': os.path.basename(XLSX), 'sheet': 'SINCO-CIUO', 'sha256': sha256(XLSX), 'pairs': sum(len(v) for v in s11_ciuo.values())},
                'sinco2019_2011': {'file': os.path.basename(MANUAL), 'pdf_pages': f'{ANNEX_PAGES.start}-{ANNEX_PAGES.stop - 1}', 'sha256': sha256(MANUAL),
                                   'paired_2019_codes': len(s19_to_11)}},
    'rule': 'exact_within_persona: every linked CIUO-08 code belongs to the persona (Peru Day 1 FINAL rule); excluded_ambiguous otherwise.',
    'counts_by_status': dict(counts),
    'overrides_applied': overrides,
    'review_pending': sum(1 for r in review if not r['decision_id']),
    'new_2019_groups_without_2011_equivalent': new_2019,
    'persona_summary': summary,
}
with open(os.path.join(OUT, 'f_sinco_mapping_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(meta, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'sinco2019_codes': len(corr_rows), 'by_status': dict(counts), 'new_2019': [x['sinco2019'] for x in new_2019]}, ensure_ascii=False))
for s in summary:
    print(s['persona_id'], s['persona'][:38].ljust(38), 'primary:', s['sinco2019_codes_primary'] or '-', '| excluded:', s['sinco2019_codes_excluded'] or '-', '| not reached:', s['isco08_codes_not_reached'] or '-')
