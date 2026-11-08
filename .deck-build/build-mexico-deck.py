"""Mexico country deck: the counterpart of .deck-build/build-peru-deck.mjs (same 1280×720 layout, colours and
slide pattern), built with python-pptx because @oai/artifact-tool is not installed. Figures come from the Mexico
report (thinkdocuments/mexico/Mexico_market_research_report_2026-11-07.md), which cites the layer outputs.

Usage: python -I .deck-build/build-mexico-deck.py   (needs python-pptx)
"""
import os
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.util import Emu, Pt

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'thinkdocuments', 'mexico', 'deck-output', 'Think4Ever_Mexico_market_research_2026-11-07.pptx')
NAVY, INK, MUTED, ORANGE = RGBColor(0x17, 0x3B, 0x72), RGBColor(0x18, 0x26, 0x3D), RGBColor(0x50, 0x65, 0x7F), RGBColor(0xF5, 0x82, 0x20)
WHITE, PALE = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xDC, 0xE7, 0xF4)
px = lambda v: Emu(int(v * 9525))  # Peru's deck is laid out in pixels at 96 dpi

deck = Presentation()
deck.slide_width, deck.slide_height = px(1280), px(720)
blank = deck.slide_layouts[6]


def box(slide, text, left, top, width, height, size=22, color=INK, bold=False):
    tf = slide.shapes.add_textbox(px(left), px(top), px(width), px(height)).text_frame
    tf.word_wrap = True
    for i, line in enumerate(text.split('\n')):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        r = p.add_run()
        r.text = line
        r.font.name, r.font.size, r.font.color.rgb, r.font.bold = 'Arial', Pt(size * 0.75), color, bold
    return tf


def fill(slide, color):
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = color


def page(title, kicker, body, foot='Fuentes y periodos en el workbook de México'):
    s = deck.slides.add_slide(blank)
    fill(s, WHITE)
    box(s, kicker, 72, 50, 600, 24, 14, ORANGE, True)
    box(s, title, 72, 88, 1080, 58, 34, NAVY, True)
    line = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, px(72), px(158), px(1136), px(2))
    line.fill.solid()
    line.fill.fore_color.rgb = NAVY
    line.line.fill.background()
    box(s, body, 72, 205, 1100, 420, 21, INK)
    box(s, foot, 72, 660, 1040, 20, 12, MUTED)
    return s


cover = deck.slides.add_slide(blank)
fill(cover, NAVY)
box(cover, 'think4ever', 72, 70, 300, 44, 30, WHITE, True)
box(cover, 'México\nMarket Research & Analytics', 72, 182, 760, 140, 46, WHITE, True)
box(cover, 'Corte de datos: 7 de noviembre de 2026', 76, 360, 620, 30, 20, PALE)
box(cover, 'Indicadores publicados, fuentes y límites de cobertura', 76, 404, 760, 28, 18, PALE)

page('México: cobertura de datos', 'RESUMEN',
     'Las 18 capas A–R tienen datos: 32 estados, 2.478 municipios y zonas de cuatro ciudades, más los indicadores nacionales.\n\n'
     'Periodo base 2025 (ciclo escolar 2024-2025; DENUE 05/2026). Excepciones declaradas: ENIF 2024 y Censos Económicos 2024 (referencia 2023).\n\n'
     '16 de 16 totales publicados conciliados, 31 de 31 fuentes completas y 76 de 76 comprobaciones técnicas.')
page('Desarrolladores y uso de IA', 'CAPAS A Y B',
     'GitHub: 2.865.151 cuentas de desarrolladores en el primer trimestre de 2026 (+35,1 % interanual) y 92.440 organizaciones (+17,1 %).\n\n'
     'Stack Overflow 2025: el 82,1 % de los 268 encuestados de México que respondieron sobre IA (de 286) usa estas herramientas; el 47,0 % las usa a diario.')
page('Educación superior y talento', 'CAPAS C Y L',
     '5.519.791 estudiantes de educación superior (SEP 911 2024-2025, igual a la cifra publicada).\n\n'
     '330.358 en el campo TIC (6,0 %): 245.244 presenciales, 82.345 de primer ingreso y 48.678 egresados (ANUIES).\n\n'
     'TecNM: 573.976 estudiantes. Capacitación para el trabajo: 2.153.875 alumnos en 4.146 escuelas.')
page('Personas y empleo', 'CAPAS F, G Y H',
     'Núcleo TIC (P01–P04): 617.393 ocupados (ENOE 2025). Desarrolladores de software: 369.645, ingreso mediano de 19.350 pesos al mes.\n\n'
     'El 92,2 % del personal TI trabaja fuera del sector tecnológico (60,6 % si se cuentan los servicios profesionales).\n\n'
     'Ocupados dentro del 0,1 % de cada boletín trimestral. Las 2.402 celdas de la capa H son indicativas.')
page('Empresas y territorio', 'CAPAS D, E, J, M Y N',
     'DENUE 05/2026: 5.798.408 negocios privados y 3.305 establecimientos de servicios TI. Censos 2023: 2.820 unidades de SCIAN 5415, 62,5 % micro.\n\n'
     'Zonas (empresas privadas): Ciudad de México 445.397 · Estado de México 563.301 · Monterrey 182.122 · Guadalajara 218.513.\n\n'
     '15.752.397 micronegocios de hasta 10 personas (ENOE). Unidades fijas en 2023: 23,6 % con internet, 4,4 % con venta en línea.')
page('Escuelas, programa y precio', 'CAPAS K, P E I',
     '58.471 escuelas y 7.331.571 alumnos en los grados objetivo; mediana de 35 por escuela; alcance con tope de 100: 2.742.061.\n\n'
     'Conversión del 10 % (supuesto): 274.206 usuarios pagados. USD 250 por escuela: USD 14.617.750.\n\n'
     'Plan individual: 479,99 pesos al mes = 2,48 % del ingreso de un desarrollador y 5,66 % del salario mínimo mensual.')
page('Contexto, auditoría y límites', 'CAPAS O, Q Y R',
     'PIB per cápita USD 13.759 (Colombia 8.617, Perú 9.938). SPEI: 7.006 millones de transferencias en 2025. Internet: 86,1 % de las personas de 6 años o más.\n\n'
     'Pendientes: edad de los alumnos (K4), trabajo desde casa (F10), software separado del resto de servicios TI, DiMo y licencias por confirmar.',
     'Ver detalle reproducible en el workbook, scripts y datos del repositorio')

os.makedirs(os.path.dirname(OUT), exist_ok=True)
deck.save(OUT)
print(os.path.relpath(OUT, ROOT), len(deck.slides), 'slides')
