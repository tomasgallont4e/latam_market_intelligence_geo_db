"""Aggregate public SUNEDU programme offer by department.

The downloaded source has programme/local rows and no enrolment; raw rows stay
outside the repository while this builder publishes only regional aggregates.
"""
from __future__ import annotations

import csv
import json
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

if len(sys.argv) != 3:
    raise SystemExit('Usage: python scripts/build-peru-sunedu-programs.py <Programas de Universidades.csv> <output-directory>')

source, outdir = map(Path, sys.argv[1:3])
outdir.mkdir(parents=True, exist_ok=True)
departments = ['AMAZONAS','ANCASH','APURIMAC','AREQUIPA','AYACUCHO','CAJAMARCA','CALLAO','CUSCO','HUANCAVELICA','HUANUCO','ICA','JUNIN','LA LIBERTAD','LAMBAYEQUE','LIMA','LORETO','MADRE DE DIOS','MOQUEGUA','PASCO','PIURA','PUNO','SAN MARTIN','TACNA','TUMBES','UCAYALI']
aliases = {'ÁNCASH':'ANCASH','APURÍMAC':'APURIMAC','HUÁNUCO':'HUANUCO','JUNÍN':'JUNIN','SAN MARTÍN':'SAN MARTIN'}

def canonical(value: str) -> str:
    value = ''.join(char for char in unicodedata.normalize('NFD', (value or '').strip()) if unicodedata.category(char) != 'Mn').upper()
    return aliases.get(value, value)

data = {department: {'department': department, 'university_programme_rows': 0, 'ict_programme_rows': 0, 'universities': set(), 'locales': set(), 'ict_universities': set(), 'ict_locales': set(), 'programme_names': set(), 'ict_programme_names': set()} for department in departments}
source_rows = 0
accepted_rows = 0
cutoffs = set()
with source.open('r', encoding='latin1', newline='') as fh:
    for row in csv.DictReader(fh, delimiter='|'):
        source_rows += 1
        department = canonical(row.get('DEPARTAMENTO_LOCAL'))
        if department not in data:
            continue
        accepted_rows += 1
        item = data[department]
        programme = (row.get('DENOMINACION_PROGRAMA') or '').strip()
        university = (row.get('NOMBRE') or '').strip()
        local = (row.get('CODIGO_LOCAL') or '').strip()
        item['university_programme_rows'] += 1
        item['universities'].add(university)
        item['locales'].add(local)
        item['programme_names'].add((university, local, programme, (row.get('NIVEL_ACADEMICO') or '').strip()))
        if canonical(row.get('NOMBRE_CLASE_PROGRAMA_N2')) == 'INFORMATICA':
            item['ict_programme_rows'] += 1
            item['ict_universities'].add(university)
            item['ict_locales'].add(local)
            item['ict_programme_names'].add((university, local, programme, (row.get('NIVEL_ACADEMICO') or '').strip()))
        cutoffs.add((row.get('FECHA_CORTE') or '').strip())

rows = []
for department in departments:
    item = data[department]
    rows.append({
        'department': department,
        'university_programme_rows': item['university_programme_rows'],
        'unique_university_programmes': len(item['programme_names']),
        'universities_with_programmes': len(item['universities']),
        'locales_with_programmes': len(item['locales']),
        'ict_programme_rows': item['ict_programme_rows'],
        'unique_ict_programmes': len(item['ict_programme_names']),
        'universities_with_ict_programmes': len(item['ict_universities']),
        'locales_with_ict_programmes': len(item['ict_locales']),
        'reference_cutoff': sorted(cutoffs),
        'source_id': 'SUNEDU_PROGRAMAS_ACADEMICOS',
        'scope': 'current_programme_offer_not_enrollment',
        'ict_definition': 'NOMBRE_CLASE_PROGRAMA_N2 = INFORMÁTICA',
        'caveat': 'Counts offer rows/programmes by local, not students, entrants, graduates, capacity, demand, teaching modality or programme quality.'
    })
metadata = {
    'country': 'PE', 'source': 'SUNEDU Programas Académicos, Plataforma Nacional de Datos Abiertos',
    'source_resource_updated': '2026-10-13', 'reference_cutoff': sorted(cutoffs),
    'source_rows': source_rows, 'accepted_rows': accepted_rows, 'departments': len(rows),
    'ict_definition': 'NOMBRE_CLASE_PROGRAMA_N2 = INFORMÁTICA',
    'caveat': 'Public programme offer by local. It does not include enrolment, entrants, graduates, capacity, demand or modality.'
}
(outdir / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding='utf8')
(outdir / 'university_programmes_by_department_20240828.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf8')
print(json.dumps(metadata, ensure_ascii=False))
