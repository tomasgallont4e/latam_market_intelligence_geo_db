"""Aggregate MINEDU public SNU 2025 enrollment by department and level."""
from __future__ import annotations

import csv
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('Usage: python scripts/build-peru-minedu-snu-enrollment.py <SNU-2025.csv> <output-directory>')

source, outdir = map(Path, sys.argv[1:3])
outdir.mkdir(parents=True, exist_ok=True)
departments = ['AMAZONAS','ANCASH','APURIMAC','AREQUIPA','AYACUCHO','CAJAMARCA','CALLAO','CUSCO','HUANCAVELICA','HUANUCO','ICA','JUNIN','LA LIBERTAD','LAMBAYEQUE','LIMA','LORETO','MADRE DE DIOS','MOQUEGUA','PASCO','PIURA','PUNO','SAN MARTIN','TACNA','TUMBES','UCAYALI']

def canonical(value: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFD', (value or '').strip()) if unicodedata.category(c) != 'Mn').upper()

groups = defaultdict(lambda: {'services': 0, 'men': 0, 'women': 0, 'students': 0})
source_rows = accepted_rows = 0
with source.open('r', encoding='latin1', newline='') as fh:
    for row in csv.DictReader(fh, delimiter=';'):
        source_rows += 1
        department = canonical(row.get('d_dpto'))
        level = (row.get('niv_mod') or '').strip()
        if department not in departments or level not in {'K0','M0','P0','S0','T0'}:
            continue
        accepted_rows += 1
        value = groups[(department, level)]
        value['services'] += 1
        for source_key, target in [('talum_hom','men'),('talum_muj','women'),('talum','students')]:
            try: value[target] += int((row.get(source_key) or '0').strip() or 0)
            except ValueError: pass

rows = []
department_summary = []
for department in departments:
    total = {'department': department, 'services': 0, 'students': 0, 'men': 0, 'women': 0, 'levels': {}, 'reference_year': 2025, 'source_id': 'MINEDU_SNU_ENROLLMENT_2025', 'scope': 'nonuniversity_enrollment'}
    for level in ['K0','M0','P0','S0','T0']:
        value = groups[(department, level)]
        item = {'department': department, 'level_code': level, **value, 'reference_year': 2025, 'source_id': 'MINEDU_SNU_ENROLLMENT_2025', 'scope': 'nonuniversity_enrollment'}
        rows.append(item)
        total['levels'][level] = value
        for metric in ['services','students','men','women']: total[metric] += value[metric]
    department_summary.append(total)
metadata = {'country':'PE','source':'MINEDU Número de matriculados de Educación Superior No Universitaria (SNU) 2025','source_resource_updated':'2026-07-31','reference_year':2025,'source_rows':source_rows,'accepted_rows':accepted_rows,'departments':len(department_summary),'levels':['K0','M0','P0','S0','T0'],'caveat':'Counts enrolment in non-university higher education services only. It excludes universities, programme field, modality, entrants, graduates and capacity.'}
(outdir/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf8')
(outdir/'snu_enrollment_by_department_level_2025.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf8')
(outdir/'snu_enrollment_by_department_2025.json').write_text(json.dumps(department_summary,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(metadata,ensure_ascii=False))
