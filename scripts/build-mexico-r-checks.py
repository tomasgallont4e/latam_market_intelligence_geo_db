"""Layer R (Mexico): checks and provenance summary.
R1 collects every published-total check already computed by the layer builds (tolerances from the template:
employed 0.5%, others 1%, DENUE exact). R2 checks that every source in the register has a URL, period, file,
hash or package hash, licence and script, and lists what is still to confirm. Writes data/mexico/validation/r_checks_mx.json.
Run after all layer builds; `node scripts/check-mexico.js` covers the table-level checks.

Usage: python -I scripts/build-mexico-r-checks.py [repo_dir]
"""
import csv, json, os, sys

repo = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
VALID = os.path.join(repo, 'data', 'mexico', 'validation')
load = lambda name: json.load(open(os.path.join(OUT, name), encoding='utf-8'))

f, m, k, l, n = (load(x) for x in ('layer_f_mx.json', 'layer_m_mx.json', 'layer_k_mx.json', 'layer_l_mx.json', 'layer_n_mx.json'))
r1 = []
for q, c in f['checks']['employed_vs_bulletins'].items():
    r1.append({'check': f'Employed (F), ENOE 2025 {q}', 'processed': c['employed'], 'published': round(c['published_millions'] * 1e6),
               'difference_pct': c['difference_pct'], 'tolerance': '0.5% (bulletin rounded to 0.1 million)', 'ok': c['within_tolerance']})
for q, c in m['check_position_totals_vs_bulletins'].items():
    for key, x in c.items():
        r1.append({'check': f"{key.replace('_vs_bulletin', '').replace('_', '-')} (M base), ENOE 2025 {q}", 'processed': x['microdata'],
                   'published': x['published'], 'difference_pct': x['difference_pct'], 'tolerance': '1%', 'ok': x['within_1pct']})
for key, x in k['checks']['enrolment_vs_principales_cifras'].items():
    r1.append({'check': f'Enrolment {key} (K), 911 2024-2025', 'processed': x['file_total'], 'published': x['published'],
               'difference_pct': x['difference_pct'], 'tolerance': '1%', 'ok': x['within_1pct']})
x = l['check_total_vs_principales_cifras']
r1.append({'check': 'Higher education (L), 911 2024-2025', 'processed': x['file_total'], 'published': x['published'],
           'difference_pct': x['difference_pct'], 'tolerance': '1%', 'ok': abs(x['difference_pct']) <= 1})
x = n['checks']
r1.append({'check': 'Businesses (N), DENUE 05/2026', 'processed': n['indicators']['establishments_total'], 'published': x['published_total'],
           'difference_pct': 0.0 if x['establishments_equal_published_total'] else None, 'tolerance': 'exact', 'ok': x['establishments_equal_published_total']})

with open(os.path.join(repo, 'data', 'mexico', 'sources_register.csv'), encoding='utf-8') as fh:
    register = list(csv.DictReader(fh))
required = ('url', 'reference_period', 'file_name', 'license', 'script')
r2 = [{'source_id': s['source_id'], 'missing': [c for c in required if not s[c].strip()],
       'to_confirm': [c for c in ('dataset_version', 'license', 'url', 'status') if 'to confirm' in s[c].lower() or s[c] == 'to_confirm'],
       'hash_recorded': bool(s['sha256'].strip()) or 'sha256' in s['access_method']} for s in register]
summary = {
    'country': 'MX', 'layer': 'R',
    'R1_published_totals': {'checks': r1, 'passed': sum(1 for c in r1 if c['ok']), 'total': len(r1)},
    'R2_sources_register': {'sources': len(r2), 'complete': sum(1 for s in r2 if not s['missing'] and s['hash_recorded']),
                            'incomplete': [s for s in r2 if s['missing'] or not s['hash_recorded']],
                            'to_confirm': [s for s in r2 if s['to_confirm']]},
    'table_checks': 'node scripts/check-mexico.js (joins, parts add up, published totals, empty-not-zero rules).',
}
os.makedirs(VALID, exist_ok=True)
with open(os.path.join(VALID, 'r_checks_mx.json'), 'w', encoding='utf-8') as fh:
    json.dump(summary, fh, ensure_ascii=False, indent=2)
    fh.write('\n')
print(json.dumps({'R1': f"{summary['R1_published_totals']['passed']}/{summary['R1_published_totals']['total']}",
                  'R2_complete': f"{summary['R2_sources_register']['complete']}/{len(r2)}",
                  'incomplete': [s['source_id'] for s in summary['R2_sources_register']['incomplete']],
                  'to_confirm': [(s['source_id'], s['to_confirm']) for s in summary['R2_sources_register']['to_confirm']]}, ensure_ascii=False))
if summary['R1_published_totals']['passed'] != len(r1):
    sys.exit('R1: some published-total checks fail')
