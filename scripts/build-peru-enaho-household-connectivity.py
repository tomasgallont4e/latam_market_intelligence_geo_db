"""Aggregate ENAHO 2025 module 01 household connectivity by department.

The source CSV is a microdata extract and is deliberately not stored in git.
Only department-level weighted estimates and unweighted sample counts are emitted.
"""
from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('Usage: python scripts/build-peru-enaho-household-connectivity.py <Enaho01-2025-100.csv> <output-directory>')

source = Path(sys.argv[1])
outdir = Path(sys.argv[2])
outdir.mkdir(parents=True, exist_ok=True)

def number(value: str) -> float:
    try:
        return float((value or '').strip().replace(',', '.'))
    except ValueError:
        return 0.0

totals = defaultdict(lambda: {
    'sample_households': 0,
    'sample_internet_households': 0,
    'sample_fixed_internet_households': 0,
    'sample_mobile_postpaid_households': 0,
    'sample_mobile_prepaid_households': 0,
    'weighted_households': 0.0,
    'weighted_internet_households': 0.0,
    'weighted_fixed_internet_households': 0.0,
    'weighted_mobile_postpaid_households': 0.0,
    'weighted_mobile_prepaid_households': 0.0,
})
source_rows = accepted_rows = 0
with source.open('r', encoding='latin1', newline='') as fh:
    for row in csv.DictReader(fh, delimiter=';'):
        source_rows += 1
        ubigeo = (row.get('UBIGEO') or '').strip()
        weight = number(row.get('FACTOR07') or '')
        if len(ubigeo) != 6 or not ubigeo.isdigit() or weight <= 0:
            continue
        accepted_rows += 1
        values = totals[ubigeo[:2]]
        values['sample_households'] += 1
        values['weighted_households'] += weight
        tests = [
            ('P1144', 'sample_internet_households', 'weighted_internet_households', '1'),
            ('P1144B1', 'sample_fixed_internet_households', 'weighted_fixed_internet_households', '1'),
            ('P1144B2', 'sample_mobile_postpaid_households', 'weighted_mobile_postpaid_households', '2'),
            ('P1144B3', 'sample_mobile_prepaid_households', 'weighted_mobile_prepaid_households', '3'),
        ]
        for field, sample_key, weighted_key, yes in tests:
            if (row.get(field) or '').strip() == yes:
                values[sample_key] += 1
                values[weighted_key] += weight

rows = []
for department_code, values in sorted(totals.items()):
    households = values['weighted_households']
    rows.append({
        'department_code': department_code,
        **{key: (round(value, 2) if key.startswith('weighted_') else value) for key, value in values.items()},
        'internet_household_rate': round(values['weighted_internet_households'] / households, 6) if households else None,
        'fixed_internet_household_rate': round(values['weighted_fixed_internet_households'] / households, 6) if households else None,
    })

metadata = {
    'country': 'PE',
    'source': 'INEI ENAHO 2025, módulo 01: Condiciones de la vivienda y del hogar',
    'reference_year': 2025,
    'unit': 'households',
    'method': 'Annual expansion factor FACTOR07; geographic aggregation by first two digits of UBIGEO.',
    'variables': {
        'P1144': 'Household has fixed or mobile internet connection',
        'P1144B1': 'Household fixed connection',
        'P1144B2': 'Household mobile post-paid/controlled connection',
        'P1144B3': 'Household mobile prepaid connection',
    },
    'caveat': 'Survey estimates, not administrative counts. Connection modes can overlap; do not add mode totals.',
    'source_rows': source_rows,
    'accepted_rows': accepted_rows,
    'departments': len(rows),
}
(outdir / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf8')
(outdir / 'household_connectivity_by_department_2025.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(metadata, ensure_ascii=False))
