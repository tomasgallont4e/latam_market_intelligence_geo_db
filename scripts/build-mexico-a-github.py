"""Layer A (Mexico): GitHub Innovation Graph, 2026Q1 vs 2025Q1.
Runs the Peru Day 1 FINAL engine unchanged (layer_a_country.py, release 1.0.10, commit 078fb62) for MX,
re-runs it for PE as a reproduction check against Peru's published map rows, and cross-checks MX
against the Think4ever LATAM breakdown already in data/geodb-v2/csv/fact_developers_country.csv.
Writes the Peru-format files (a_github_*_mx.csv), the layer JSON, the MX rows of
fact_developers_country and the layer A rows of fact_map_indicator.

Usage: python -I scripts/build-mexico-a-github.py <innovationgraph_repo_dir> [repo_dir]
"""
import csv, hashlib, json, os, shutil, subprocess, sys, tempfile

ig = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ENGINE = os.path.join(repo, 'data', 'peru', 'think4ever_peru_day1_FINAL', 'layerA', 'think4ever_peru_day1_layerA_FINAL', 'scripts', 'layer_a_country.py')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
PE_MAP = os.path.join(repo, 'data', 'peru-map', 'fact_map_indicator.csv')
CO_DEVS = os.path.join(repo, 'data', 'geodb-v2', 'csv', 'fact_developers_country.csv')
EXPECTED_COMMIT = '078fb62ee4395d321bec9f4f06694cca68f6b6cb'  # same Innovation Graph release as Peru
SOURCE_ID = 'SRC_GH_IG'
MAP_COLUMNS = ['layer', 'metric_id', 'scope_type', 'scope_id', 'group_id', 'persona_id', 'indicator', 'category', 'value', 'unit',
               'period', 'comparison_period', 'numerator', 'denominator', 'status', 'source_id', 'method', 'limitations']


def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def run_engine(country, out_dir):
    subprocess.run([sys.executable, '-I', ENGINE, ig, out_dir, country], check=True)
    return read_csv(os.path.join(out_dir, f'layer_a_{country.lower()}_indicators.csv'))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


commit = subprocess.run(['git', '-C', ig, 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
errors = []
if commit != EXPECTED_COMMIT:
    errors.append(f'Innovation Graph checkout is {commit}, expected {EXPECTED_COMMIT} (Peru release)')

with tempfile.TemporaryDirectory() as tmp:
    mx_dir, pe_dir = os.path.join(tmp, 'mx'), os.path.join(tmp, 'pe')
    mx = run_engine('MX', mx_dir)
    pe = run_engine('PE', pe_dir)
    languages = read_csv(os.path.join(mx_dir, 'layer_a_mx_languages.csv'))
    quarterly = read_csv(os.path.join(mx_dir, 'layer_a_mx_quarterly.csv'))
    with open(os.path.join(mx_dir, 'layer_a_mx_meta.json'), encoding='utf-8') as f:
        meta = json.load(f)
    with open(os.path.join(mx_dir, 'layer_a_source_hashes.json'), encoding='utf-8') as f:
        source_hashes = json.load(f)
    for name in ('indicators', 'languages', 'quarterly'):
        target = {'indicators': 'a_github_indicators_mx.csv', 'languages': 'a_github_languages_mx.csv', 'quarterly': 'a_github_country_quarterly_mx.csv'}[name]
        shutil.copyfile(os.path.join(mx_dir, f'layer_a_mx_{name}.csv'), os.path.join(OUT, target))

# Reproduction: the engine must give Peru's published values exactly.
published_pe = {r['metric_id']: r for r in read_csv(PE_MAP) if r['layer'] == 'A' and r['scope_id'] == 'PE'}
reproduction = []
for r in pe:
    p = published_pe.get(r['indicator_id'])
    same = bool(p) and abs(float(p['value']) - float(r['value'])) <= 1e-9 * max(1.0, abs(float(r['value'])))
    reproduction.append({'indicator_id': r['indicator_id'], 'published': p['value'] if p else None, 'reproduced': r['value'], 'ok': same})
if not all(x['ok'] for x in reproduction):
    errors.append('Peru reproduction failed: ' + ', '.join(x['indicator_id'] for x in reproduction if not x['ok']))

# Cross-check with the Think4ever LATAM breakdown already loaded for Colombia (fact_developers_country).
by_id = {r['indicator_id']: float(r['value']) for r in mx}
co_row = next(r for r in read_csv(CO_DEVS) if r['iso2'] == 'MX')
benchmark = [
    ('developers', float(co_row['developers']), by_id['A1_developer_accounts'], 0),
    ('developers_yoy_pct', float(co_row['developers_yoy_pct']), round(100 * by_id['A1_developer_accounts_yoy'], 1), 0.05),
    ('organizations', float(co_row['organizations']), by_id['A2_organizations'], 0),
    ('organizations_yoy_pct', float(co_row['organizations_yoy_pct']), round(100 * by_id['A2_organizations_yoy'], 1), 0.05),
    ('pushes_per_dev', float(co_row['pushes_per_dev']), round(by_id['A3_pushes_per_developer_account'], 2), 0.005),
    ('enterprise_lang_share_pct', float(co_row['enterprise_lang_share_pct']), round(100 * by_id['A5_enterprise_share_earlier_method'], 2), 0.005),
]
benchmark = [{'field': f, 'fact_developers_country': b, 'engine': e, 'ok': abs(b - e) <= tol + 1e-9} for f, b, e, tol in benchmark]
if errors:
    sys.exit('Layer A checks failed:\n' + '\n'.join(errors))

# fact_developers_country: the Colombia table's MX row, verified above against the engine.
with open(os.path.join(CSV_DIR, 'fact_developers_country.csv'), 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=list(co_row), lineterminator='\n')
    w.writeheader()
    w.writerow(co_row)

benchmark_note = ('Matches the Think4ever LATAM breakdown (data/geodb-v2/csv/fact_developers_country.csv, MX row).'
                  if all(b['ok'] for b in benchmark) else 'Differs from the Think4ever LATAM breakdown; see layer_a_mx.json benchmark.')
map_rows = [{
    'layer': 'A', 'metric_id': r['indicator_id'], 'scope_type': 'country', 'scope_id': 'MX', 'group_id': '', 'persona_id': '',
    'indicator': r['indicator_name'], 'category': '', 'value': r['value'], 'unit': r['unit'], 'period': r['period_label'],
    'comparison_period': r['comparison_period_label'], 'numerator': r['numerator'], 'denominator': r['denominator'],
    'status': f"{r['canonical_status']};{r['validation_status']}", 'source_id': SOURCE_ID, 'method': r['method'], 'limitations': benchmark_note,
} for r in mx]

map_path = os.path.join(CSV_DIR, 'fact_map_indicator.csv')
existing = [r for r in read_csv(map_path) if r['layer'] != 'A'] if os.path.exists(map_path) else []
with open(map_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=MAP_COLUMNS, lineterminator='\n')
    w.writeheader()
    w.writerows(sorted(map_rows + existing, key=lambda r: r['layer']))

top_now = [l for l in languages if l['period_label'] == '2026Q1'][:10]
layer = {
    'country': 'MX', 'layer': 'A', 'source_id': SOURCE_ID, 'period': '2026Q1', 'comparison_period': '2025Q1',
    'source': {'repository': 'https://github.com/github/innovationgraph', 'commit': commit, 'release': '1.0.10', 'file_sha256': source_hashes},
    'engine': {'script': 'data/peru/think4ever_peru_day1_FINAL/layerA/think4ever_peru_day1_layerA_FINAL/scripts/layer_a_country.py', 'sha256': sha256(ENGINE)},
    'indicators': {r['indicator_id']: float(r['value']) for r in mx},
    'top_languages_2026Q1': [{'rank': int(l['rank_in_period']), 'language': l['language'], 'pushers': int(l['num_pushers'])} for l in top_now],
    'engine_meta': meta,
    'checks': {'peru_reproduction': {'rows': len(reproduction), 'all_equal': True},
               'benchmark_fact_developers_country': benchmark},
    'notes': {
        'period': 'Q1 2026 vs Q1 2025, the same quarters and Innovation Graph release as Colombia and Peru. Q2 2026 was published upstream on 2026-10-27 and is not used, to keep the three countries comparable.',
        'A4_A5': 'Fastest-growing threshold and enterprise basket inherit the Chile/Peru precedents, still pending methodological validation (decisions D-03, D-04 of the Day 1 packages).',
    },
    'limitations': 'Developer accounts are located by the most frequent daily IP and include inactive accounts; organisations are GitHub workspaces, not legal companies.',
}
with open(os.path.join(OUT, 'layer_a_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'commit': commit[:7], 'indicators': len(mx), 'peru_reproduced': len(reproduction),
                  'benchmark_ok': [b['field'] for b in benchmark if b['ok']], 'benchmark_diff': [b for b in benchmark if not b['ok']],
                  'A1': by_id['A1_developer_accounts'], 'A3': by_id['A3_git_pushes'], 'top5': [l['language'] for l in top_now[:5]]}, ensure_ascii=False))
