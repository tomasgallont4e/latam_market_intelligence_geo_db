"""Layer I (Mexico): plan prices against income, 2025 (to match ENOE 2025 incomes).
I1: USD 25 and USD 250 plans in MXN at the 2025 average FIX rate (Banxico, 'Determinación' column; non-business
days marked N/E are skipped). I2: individual plan as % of each persona's median monthly labour income (layer F).
I3: plan as % of the monthly minimum wage (CONASAMI, DOF 19-12-2024: MXN 278.80 a day, 419.88 in the northern
border zone; monthly = daily × 30.4, decision D-MX-13) and of the developers' median income (P01, ENOE 2025).
Writes layer_i_mx.json and the layer I rows of fact_map_indicator.

Usage: python -I scripts/build-mexico-i-price.py <fix.xls> [repo_dir]   (needs xlrd)
"""
import csv, hashlib, json, os, statistics, sys
from datetime import datetime
import xlrd

src = sys.argv[1]
repo = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
CSV_DIR = os.path.join(repo, 'data', 'mexico', 'geodb', 'csv')
OUT = os.path.join(repo, 'data', 'mexico', 'outputs')
PLANS_USD = {'individual': 25, 'team': 250}
MIN_WAGE_DAILY = {'general': 278.80, 'northern_border': 419.88}  # CONASAMI resolution, DOF 19-12-2024
DAYS_PER_MONTH = 30.4
MAP_COLUMNS = ['layer', 'metric_id', 'scope_type', 'scope_id', 'group_id', 'persona_id', 'indicator', 'category', 'value', 'unit',
               'period', 'comparison_period', 'numerator', 'denominator', 'status', 'source_id', 'method', 'limitations']

with open(src, 'rb') as f:
    sha = hashlib.sha256(f.read()).hexdigest()
sheet = xlrd.open_workbook(src).sheet_by_index(0)
header_row = next(i for i in range(sheet.nrows) if str(sheet.cell_value(i, 0)).strip() == 'Fecha')
col = next(j for j in range(sheet.ncols) if str(sheet.cell_value(header_row, j)).startswith('Determinaci'))
fix = []
for i in range(header_row + 1, sheet.nrows):
    date, value = str(sheet.cell_value(i, 0)).strip(), sheet.cell_value(i, col)
    if date and isinstance(value, float):
        fix.append((datetime.strptime(date, '%d/%m/%Y'), value))
if not fix or {d.year for d, _ in fix} != {2025}:
    sys.exit('FIX file does not hold 2025 daily data')
fix_avg = statistics.mean(v for _, v in fix)
fix_dec = statistics.mean(v for d, v in fix if d.month == 12)

plans_mxn = {k: round(usd * fix_avg, 2) for k, usd in PLANS_USD.items()}
min_wage_monthly = {k: round(v * DAYS_PER_MONTH, 2) for k, v in MIN_WAGE_DAILY.items()}
with open(os.path.join(CSV_DIR, 'fact_persona_profile.csv'), encoding='utf-8') as f:
    personas = list(csv.DictReader(f))
dev = next(p for p in personas if p['persona'] == 'Software developers and analysts')
pct = lambda a, b: round(100 * a / b, 2)
i2 = [{'persona': p['persona'], 'median_income_mxn': float(p['median_income_mxn']),
       'individual_plan_pct_of_income': pct(plans_mxn['individual'], float(p['median_income_mxn']))} for p in personas if p['median_income_mxn']]
i3 = {
    'individual_plan_pct_of_min_wage_general': pct(plans_mxn['individual'], min_wage_monthly['general']),
    'individual_plan_pct_of_min_wage_northern_border': pct(plans_mxn['individual'], min_wage_monthly['northern_border']),
    'individual_plan_pct_of_developer_median_income': pct(plans_mxn['individual'], float(dev['median_income_mxn'])),
}

source_rate = 'BANXICO_FIX_2025'
rows = [
    {'metric_id': 'I1_fix_2025_average', 'indicator': 'Tipo de cambio FIX, promedio 2025', 'value': round(fix_avg, 4), 'unit': 'MXN por USD',
     'numerator': '', 'denominator': '', 'source_id': source_rate, 'method': f'mean of {len(fix)} daily FIX determinations, 2025'},
    {'metric_id': 'I1_fix_2025_december_average', 'indicator': 'Tipo de cambio FIX, promedio de diciembre de 2025', 'value': round(fix_dec, 4), 'unit': 'MXN por USD',
     'numerator': '', 'denominator': '', 'source_id': source_rate, 'method': 'mean of daily FIX determinations, December 2025'},
    {'metric_id': 'I1_plan_individual_mxn', 'indicator': 'Plan individual (USD 25) en pesos', 'value': plans_mxn['individual'], 'unit': 'MXN al mes',
     'numerator': PLANS_USD['individual'], 'denominator': '', 'source_id': source_rate, 'method': 'USD 25 × 2025 average FIX'},
    {'metric_id': 'I1_plan_team_mxn', 'indicator': 'Plan de equipo (USD 250) en pesos', 'value': plans_mxn['team'], 'unit': 'MXN',
     'numerator': PLANS_USD['team'], 'denominator': '', 'source_id': source_rate, 'method': 'USD 250 × 2025 average FIX'},
    {'metric_id': 'I3_min_wage_monthly_general', 'indicator': 'Salario mínimo mensual 2025 (zona general)', 'value': min_wage_monthly['general'], 'unit': 'MXN al mes',
     'numerator': MIN_WAGE_DAILY['general'], 'denominator': '', 'source_id': 'CONASAMI_DOF_20241219', 'method': 'daily × 30.4 (D-MX-13)'},
    {'metric_id': 'I3_plan_pct_min_wage_general', 'indicator': 'Plan individual como % del salario mínimo mensual', 'value': i3['individual_plan_pct_of_min_wage_general'],
     'unit': 'porcentaje', 'numerator': plans_mxn['individual'], 'denominator': min_wage_monthly['general'], 'source_id': 'CONASAMI_DOF_20241219', 'method': 'I1 ÷ monthly minimum wage'},
    {'metric_id': 'I3_plan_pct_developer_income', 'indicator': 'Plan individual como % del ingreso mensual mediano de los desarrolladores', 'value': i3['individual_plan_pct_of_developer_median_income'],
     'unit': 'porcentaje', 'numerator': plans_mxn['individual'], 'denominator': float(dev['median_income_mxn']), 'source_id': 'INEGI_ENOE_2025', 'method': 'I1 ÷ persona P01 median income (ENOE 2025)'},
] + [{'metric_id': f'I2_plan_pct_income_{k:02d}', 'indicator': f"Plan individual como % del ingreso mediano: {x['persona']}", 'value': x['individual_plan_pct_of_income'],
      'unit': 'porcentaje', 'numerator': plans_mxn['individual'], 'denominator': x['median_income_mxn'], 'source_id': 'INEGI_ENOE_2025', 'method': 'I1 ÷ F8 median monthly labour income'}
     for k, x in enumerate(i2, 1)]
map_rows = [{'layer': 'I', 'scope_type': 'country', 'scope_id': 'MX', 'group_id': '', 'persona_id': '', 'category': '', 'period': '2025',
             'comparison_period': '', 'status': 'verified', 'limitations': 'El precio es un escenario no aprobado (USD 25 / USD 250), mostrado con su tipo de cambio y fecha; no es una recomendación.', **r}
            for r in rows]
map_path = os.path.join(CSV_DIR, 'fact_map_indicator.csv')
with open(map_path, encoding='utf-8') as f:
    existing = [r for r in csv.DictReader(f) if r['layer'] != 'I']
with open(map_path, 'w', encoding='utf-8', newline='') as f:
    w = csv.DictWriter(f, fieldnames=MAP_COLUMNS, lineterminator='\n')
    w.writeheader()
    w.writerows(sorted(existing + map_rows, key=lambda r: r['layer']))

layer = {
    'country': 'MX', 'layer': 'I', 'period': '2025',
    'sources': {'fix': {'file': os.path.basename(src), 'sha256': sha, 'days': len(fix), 'column': 'Determinación'},
                'minimum_wage': 'CONASAMI resolution, DOF 19-12-2024: MXN 278.80 a day (general zone), 419.88 (Zona Libre de la Frontera Norte), from 1 January 2025'},
    'indicators': {'I1_fix_2025_average': round(fix_avg, 4), 'I1_fix_2025_december_average': round(fix_dec, 4), 'I1_plans_mxn': plans_mxn,
                   'I2_by_persona': i2, 'I3': i3, 'min_wage_monthly_mxn': min_wage_monthly},
    'notes': {'rate': 'State the rate and its period on every slide: 2025 average FIX.',
              'monthly_min_wage': 'Daily minimum wage × 30.4 days (D-MX-13).',
              'I2': 'Median monthly labour income from ENOE 2025 (fact_persona_profile.median_income_mxn), the official alternative to job boards.'},
}
with open(os.path.join(OUT, 'layer_i_mx.json'), 'w', encoding='utf-8') as f:
    json.dump(layer, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'fix_avg': round(fix_avg, 4), 'fix_dec': round(fix_dec, 4), 'days': len(fix), 'plans': plans_mxn, 'I3': i3,
                  'I2_range': [min(x['individual_plan_pct_of_income'] for x in i2), max(x['individual_plan_pct_of_income'] for x in i2)]}, ensure_ascii=False))
