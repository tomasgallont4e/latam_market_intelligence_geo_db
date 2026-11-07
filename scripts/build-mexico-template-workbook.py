"""Think4Ever country-template workbook for Mexico: the counterpart of scripts/build-peru-template-workbook.mjs.
Same sheets and styling as Peru's (Summary, Indicators, Sources register, Audit), plus Decisions and Layer coverage,
which Mexico keeps in decisions_log.csv and the layer JSONs. Built only from committed outputs: nothing is typed in.
Empty indicators are listed as empty, never shown as zero. Audit runs node scripts/check-mexico.js.

Usage: python -I scripts/build-mexico-template-workbook.py [repo_dir]   (needs openpyxl; node on PATH)
Writes thinkdocuments/mexico/think4ever-mexico-country-template.xlsx
"""
import csv, json, os, re, shutil, subprocess, sys
from datetime import date
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

repo = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
MX = os.path.join(repo, 'data', 'mexico')
OUT = os.path.join(repo, 'thinkdocuments', 'mexico', 'think4ever-mexico-country-template.xlsx')
LAYER_NAMES = {'A': 'Comunidad de desarrolladores', 'B': 'Uso de IA entre desarrolladores', 'C': 'Estudiantes TIC por ciudad',
               'D': 'Empresas TIC por ciudad', 'E': 'Tipología de ciudades y población', 'F': 'Personas y empleo',
               'G': 'Personal TI en cada industria', 'H': 'Segmentos: persona × ciudad × comprador', 'I': 'Precio frente al ingreso',
               'J': 'Zonas de Ciudad de México, Estado de México, Monterrey y Guadalajara', 'K': 'Escuelas: grados objetivo',
               'L': 'Educación superior', 'M': 'Micronegocios', 'N': 'Empresas formales y tiendas', 'O': 'Contexto del país',
               'P': 'Programa de bachillerato', 'Q': 'Geografía y claves', 'R': 'Comprobaciones y fuentes'}
FONT = Font(name='Arial', size=10, color='18263D')
HEAD = dict(fill=PatternFill('solid', fgColor='173B72'), font=Font(name='Arial', size=10, bold=True, color='FFFFFF'),
            alignment=Alignment(horizontal='center', vertical='center', wrap_text=True))


def read_csv(path):
    with open(path, encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(v):
    """Numbers stay numbers in Excel; empty stays empty (never zero)."""
    if v in (None, ''):
        return None
    try:
        f = float(v)
        return int(f) if f.is_integer() and not re.search(r'[.eE]', str(v)) else f
    except (TypeError, ValueError):
        return v


def empty_keys(obj, prefix='', depth=0):
    """Keys whose value is null in a layer JSON (pending or not available), two levels deep; notes and metadata skipped."""
    found = []
    for k, v in obj.items():
        if k in ('notes', 'sources', 'limitations', 'checks', 'definitions'):
            continue
        if v is None:
            found.append(prefix + k)
        elif isinstance(v, dict) and depth < 2:
            found += empty_keys(v, '' if k == 'indicators' else prefix + k + '.', depth + 1)
    return found


def write(ws, rows, start=1):
    for i, row in enumerate(rows, start):
        for j, v in enumerate(row, 1):
            ws.cell(i, j, v).font = FONT


def header(ws, row, ncols):
    for j in range(1, ncols + 1):
        c = ws.cell(row, j)
        c.fill, c.font, c.alignment = HEAD['fill'], HEAD['font'], HEAD['alignment']


def widths(ws, maxw=60):
    for col in ws.columns:
        w = max((len(str(c.value)) for c in col if c.value is not None), default=8)
        ws.column_dimensions[get_column_letter(col[0].column)].width = min(max(w + 2, 8), maxw)


indicators = read_csv(os.path.join(MX, 'geodb', 'csv', 'fact_map_indicator.csv'))
register = read_csv(os.path.join(MX, 'sources_register.csv'))
decisions = read_csv(os.path.join(MX, 'decisions_log.csv'))
r = json.load(open(os.path.join(MX, 'validation', 'r_checks_mx.json'), encoding='utf-8'))

node = shutil.which('node')
if not node:
    sys.exit('node not found on PATH: needed for the Audit sheet (scripts/check-mexico.js)')
run = subprocess.run([node, os.path.join(repo, 'scripts', 'check-mexico.js')], capture_output=True, text=True, encoding='utf-8')
checks = [(m.group(1), m.group(2)) for m in re.finditer(r'^(ok|FAIL)\s+(.*)$', run.stdout, re.M)]
passed = sum(1 for s, _ in checks if s == 'ok')
failed = len(checks) - passed

wb = Workbook()
summary = wb.active
summary.title = 'Summary'
ind = wb.create_sheet('Indicators')
src = wb.create_sheet('Sources register')
cov = wb.create_sheet('Layer coverage')
dec = wb.create_sheet('Decisions')
aud = wb.create_sheet('Audit')

# ── Summary (same layout as Peru's) ──
summary['A2'] = 'Think4Ever México · registro de investigación'
summary.merge_cells('A2:G2')
header(summary, 2, 7)
summary['A2'].font = Font(name='Arial', size=14, bold=True, color='FFFFFF')
r1 = r['R1_published_totals']['checks']
write(summary, [['País', 'México'], ['Corte del workbook', date.today().isoformat()],
                ['Indicadores nacionales publicados', sum(1 for x in indicators if x['value'] != '')],
                ['Capas definidas', 'A–R'], ['Checks aprobados', passed], ['Checks fallidos', failed],
                ['Totales publicados conciliados (R1)', f"{sum(1 for c in r1 if c['ok'])}/{len(r1)}"],
                ['Fuentes completas en el registro (R2)', f"{r['R2_sources_register']['complete']}/{r['R2_sources_register']['sources']}"]], start=4)
summary_rows = [
    ['Estado de cobertura', 'Detalle'],
    ['Mapas territoriales', '32 estados y 2.478 municipios (INEGI); zonas de Ciudad de México, Estado de México, Monterrey y Guadalajara (capa J). '
                            'Las personas de la ENOE se publican solo por estado.'],
    ['Periodo base', '2025 (ENOE, Banxico, CONASAMI, ENDUTIH); ciclo escolar 2024-2025 (SEP 911, ANUIES); DENUE 05/2026. '
                     'Excepciones registradas: ENIF 2024 y Censos Económicos 2024 con año de referencia 2023 (D3, M4; D-MX-15).'],
    ['Pendientes no sustituidos', 'Edad < 18 de alumnos (K4: el 911 no trae edad), trabajo desde casa (F10: la ENOE no lo pregunta a asalariados), DiMo (no está en los archivos de Banxico) y los indicadores vacíos de la hoja Layer coverage.'],
    ['Uso', 'Los datos nacionales no se distribuyen artificialmente a territorios. Un valor vacío es suprimido o no disponible, nunca cero. '
            'Consulte Indicators, Sources register, Decisions y Audit.'],
]
write(summary, summary_rows, start=13)
summary.merge_cells('B13:G13')
header(summary, 13, 7)
for i in range(14, 13 + len(summary_rows)):
    summary.merge_cells(f'B{i}:G{i}')
    summary[f'B{i}'].alignment = Alignment(wrap_text=True, vertical='top')
    summary.row_dimensions[i].height = 42
summary.column_dimensions['A'].width = 38
for col in 'BCDEFG':
    summary.column_dimensions[col].width = 18

# ── Indicators: every national row of fact_map_indicator (layers A, B, I, O, P), Peru's columns ──
cols = ['layer', 'metric_id', 'indicator', 'value', 'unit', 'period', 'status', 'source_id', 'limitations']
write(ind, [['Layer', 'Metric ID', 'Indicator', 'Value', 'Unit', 'Period', 'Status', 'Source ID', 'Limitations']]
      + [[num(x[c]) if c == 'value' else x[c] for c in cols] for x in indicators])
header(ind, 1, len(cols))
for row in ind.iter_rows(min_row=2, min_col=4, max_col=4):
    for c in row:
        if isinstance(c.value, float):
            c.number_format = '#,##0.0###'
        elif isinstance(c.value, int):
            c.number_format = '#,##0'

# ── Sources register: the full register ──
rcols = list(register[0])
write(src, [rcols] + [[x[c] for c in rcols] for x in register])
header(src, 1, len(rcols))

# ── Layer coverage: one row per layer, with its output and the indicators left empty ──
crow = [['Layer', 'Nombre', 'Salida', 'Indicadores vacíos (null: pendiente o no disponible)', 'Filas en Indicators']]
for layer, name in LAYER_NAMES.items():
    path = os.path.join(MX, 'outputs', f'layer_{layer.lower()}_mx.json')
    if layer == 'R':
        path = os.path.join(MX, 'validation', 'r_checks_mx.json')
    doc = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else None
    gaps = empty_keys(doc) if doc else ['(sin salida)']
    crow.append([layer, name, os.path.relpath(path, repo).replace('\\', '/') if doc else '', ', '.join(gaps) or '—',
                 sum(1 for x in indicators if x['layer'] == layer) or None])
write(cov, crow)
header(cov, 1, 5)

# ── Decisions ──
dcols = list(decisions[0])
write(dec, [dcols] + [[x[c] for c in dcols] for x in decisions])
header(dec, 1, len(dcols))

# ── Audit: table checks, published totals (R1) and sources to confirm (R2) ──
arows = [['Check', 'Result'], ['Passed checks', passed], ['Failed checks', failed]]
arows += [[name, 'ok' if s == 'ok' else 'FAIL'] for s, name in checks]
arows += [['', ''], ['Published total (R1)', 'Processed / published / difference % / ok']]
arows += [[c['check'], f"{c['processed']:,} / {c['published']:,} / {c['difference_pct']} / {'ok' if c['ok'] else 'FAIL'}"] for c in r1]
arows += [['', ''], ['Source to confirm (R2)', 'Fields']]
arows += [[s['source_id'], ', '.join(s['to_confirm'])] for s in r['R2_sources_register']['to_confirm']]
write(aud, arows)
header(aud, 1, 2)
for i, row in enumerate(arows, 1):
    if row[0] in ('Published total (R1)', 'Source to confirm (R2)'):
        header(aud, i, 2)

for ws in (ind, src, cov, dec, aud):
    widths(ws)
    ws.freeze_panes = 'A2'
for ws in (summary, ind, src, cov, dec, aud):
    ws.sheet_view.showGridLines = False
for ws, col in ((ind, 'I'), (src, get_column_letter(len(rcols))), (cov, 'D'), (dec, 'E')):
    ws.column_dimensions[col].width = 80
    for c in ws[col][1:]:
        c.alignment = Alignment(wrap_text=True, vertical='top')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
wb.save(OUT)
print(json.dumps({'file': os.path.relpath(OUT, repo), 'indicators': len(indicators), 'sources': len(register), 'decisions': len(decisions),
                  'checks': f'{passed}/{len(checks)}', 'R1': summary['B10'].value, 'R2': summary['B11'].value}, ensure_ascii=False))
