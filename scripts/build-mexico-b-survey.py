"""Layer B (Mexico): Stack Overflow Developer Survey 2025, Country = Mexico.
Runs the Peru Day 1 FINAL engine unchanged (layer_b_engine.py: unweighted proportions, Wilson 95% intervals,
valid_n < 30 suppressed) with MX as the focus country. Checks:
  - Mexico: every MX row must equal the Mexico comparison group already published in Peru's map rows
    (data/peru-map/fact_map_indicator.csv), which were computed from the same file;
  - global: the GLOBAL rows must equal Peru's, which Peru validated against the official ai.json
    (b_reproduction_check_pe.csv); when ai.json is given, its hash is recorded with the source.
Writes the Peru-format files (b_*_mx.csv), the layer JSON and the layer B rows of fact_map_indicator.

Usage: python -I scripts/build-mexico-b-survey.py <results.csv> [ai.json] [repo_dir]
"""
import csv, hashlib, json, os, shutil, subprocess, sys, tempfile
from collections import Counter

results = sys.argv[1]
ai_json = sys.argv[2] if len(sys.argv) > 2 and sys.argv[2].endswith('.json') else None
repo = sys.argv[3] if len(sys.argv) > 3 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ENGINE = os.path.join(repo, 'data', 'peru', 'think4ever_peru_day1_FINAL', 'layerB', 'think4ever_peru_day1_layerB_FINAL', 'scripts', 'layer_b_engine.py')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
PE_MAP = os.path.join(repo, 'data', 'peru-map', 'fact_map_indicator.csv')
EXPECTED_SHA256 = '2d1f65308877282edfb4470520eabbc08cb499118432a3dcec6a66c086aa2baa'  # results.csv used by Peru (SRC_SO_2025)
SOURCE_ID = 'SRC_SO_2025'
STATUS = 'low_confidence_self_selected_survey'
MAP_COLUMNS = ['layer', 'metric_id', 'scope_type', 'scope_id', 'group_id', 'persona_id', 'indicator', 'category', 'value', 'unit',
               'period', 'comparison_period', 'numerator', 'denominator', 'status', 'source_id', 'method', 'limitations']


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def same(a, b):
    if a in ('', None) or b in ('', None):
        return a in ('', None) and b in ('', None)
    return abs(float(a) - float(b)) <= 1e-9


errors = []
results_sha = sha256(results)
if results_sha != EXPECTED_SHA256:
    errors.append(f'results.csv sha256 {results_sha} differs from the file Peru used ({EXPECTED_SHA256})')

with tempfile.TemporaryDirectory() as tmp:
    subprocess.run([sys.executable, '-I', ENGINE, results, 'MX', tmp], check=True)
    indicators = read_csv(os.path.join(tmp, 'b_survey_indicators_mx.csv'))
    for name in ('b_survey_indicators_mx.csv', 'b_survey_distributions_mx.csv', 'b_comparison_groups_mx.csv'):
        shutil.copyfile(os.path.join(tmp, name), os.path.join(OUT, name))

# Map rows, in the same form as Peru's: one per engine row, numbered within each group.
counter = Counter()
map_rows = []
for r in indicators:
    group = (r['group_type'], r['group_code'], r['survey_segment'])
    counter[group] += 1
    map_rows.append({
        'layer': 'B', 'metric_id': f"B:{r['survey_year']}:{r['indicator_id']}:{r['group_type']}:{r['group_code']}:{r['survey_segment']}:{counter[group]}",
        'scope_type': 'country', 'scope_id': 'MX', 'group_id': r['group_code'], 'persona_id': '', 'indicator': r['item'],
        'category': r['task'], 'value': r['proportion'], 'unit': 'proportion', 'period': r['survey_year'], 'comparison_period': '',
        'numerator': r['numerator'], 'denominator': r['valid_n'], 'status': STATUS, 'source_id': r['source_id'], 'method': r['task'],
        'limitations': f"{r['group_type']}:{r['group_definition']}; suppress={r['base_flag']}; low_n={r['small_numerator_flag']}",
    })

# Check 1 and 2: MX and GLOBAL rows against Peru's published rows for the same groups.
peru = [r for r in read_csv(PE_MAP) if r['layer'] == 'B']
def keyed(rows, group_code, segment='all_respondents'):
    out = {}
    for r in rows:
        parts = r['metric_id'].split(':')
        if parts[4] == group_code and parts[5] == segment:
            out[(parts[2], r['indicator'])] = r
    return out
comparisons = {}
for code in ('MX', 'GLOBAL'):
    ours, theirs = keyed(map_rows, code), keyed(peru, code)
    diff = [k for k in theirs if k not in ours or not all(same(ours[k][c], theirs[k][c]) for c in ('value', 'numerator', 'denominator'))]
    comparisons[code] = {'rows_published_by_peru': len(theirs), 'rows_reproduced': len(ours), 'differences': [list(k) for k in diff]}
    if not theirs or diff or len(ours) != len(theirs):
        errors.append(f'{code} rows differ from Peru\'s published comparison group: {diff[:5]}')

official = None
if ai_json:
    with open(ai_json, encoding='utf-8') as f:
        official = {'file': os.path.basename(ai_json), 'sha256': sha256(ai_json)}
if errors:
    sys.exit('Layer B checks failed:\n' + '\n'.join(errors))

map_path = os.path.join(CSV_DIR, 'fact_map_indicator.csv')
existing = [r for r in read_csv(map_path) if r['layer'] != 'B'] if os.path.exists(map_path) else []
with open(map_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=MAP_COLUMNS, lineterminator='\n')
    w.writeheader()
    w.writerows(sorted(existing + map_rows, key=lambda r: r['layer']))

mx = {r['indicator_id']: r for r in indicators if r['group_code'] == 'MX' and r['survey_segment'] == 'all_respondents' and r['indicator_id'] in ('B1', 'B2', 'B3')}
n = next((r for r in indicators if r['group_code'] == 'MX' and r['survey_segment'] == 'all_respondents' and r['indicator_id'] == 'B5'), None)
respondents = int(float(n['numerator'])) if n and n['numerator'] else None
layer = {
    'country': 'MX', 'layer': 'B', 'source_id': SOURCE_ID, 'survey': 'Stack Overflow Developer Survey', 'survey_year': 2025,
    'source': {'repository': 'https://github.com/StackExchange/Survey', 'commit': 'c9c23dc6f385d5be1a3011c238deb6c23b617e93',
               'path': 'packages/archive/2025/results.csv', 'sha256': results_sha, 'official_aggregate': official},
    'engine': {'script': 'data/peru/think4ever_peru_day1_FINAL/layerB/think4ever_peru_day1_layerB_FINAL/scripts/layer_b_engine.py', 'sha256': sha256(ENGINE)},
    'headline': {k: {'item': r['item'], 'proportion': float(r['proportion']) if r['proportion'] else None,
                     'numerator': r['numerator'], 'valid_n': r['valid_n'], 'ci_95': [r['ci_low'], r['ci_high']]} for k, r in mx.items()},
    'B5_respondents': respondents,
    'B5_confidence': None if respondents is None else ('low (below 300)' if respondents < 300 else 'medium or higher'),
    'checks': {'reproduces_peru_published_groups': comparisons},
    'notes': {'edition': '2025 edition, the same file as Colombia\'s template example and Peru\'s published package, so the three countries compare on one survey.'},
    'limitations': 'Self-selected online survey: unweighted, not representative of all developers in Mexico. Cells with fewer than 30 valid answers are suppressed (empty), never zero.',
}
with open(os.path.join(OUT, 'layer_b_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'rows': len(map_rows), 'respondents': respondents, 'confidence': layer['B5_confidence'],
                  'B1_B2_B3': {k: v['proportion'] for k, v in layer['headline'].items()}, 'checks': {k: (v['rows_reproduced'], len(v['differences'])) for k, v in comparisons.items()}}, ensure_ascii=False))
