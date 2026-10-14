"""Peru Day 1 - documentary closure DRAFT -> FINAL (authorised by Think4ever 2026-10-09 19:06 America/Bogota).
Copies the approved DRAFT integral package to a FINAL folder, renames the layer folders and applies ONLY explicit
status/documentation edits. Results, tables, personas, rings, suppression rules and decisions are not touched
(the only data file that changes is decisions_log_pe.csv, which gains the closure record; regenerated separately).
Every edit must match exactly once, otherwise the script stops.

Usage: python3 -I close_peru_day1_final.py <draft_integral_dir> <final_integral_dir> <master_scripts_dir>
"""
import sys, os, shutil

SRC, DST, MASTER = sys.argv[1:4]
AUTH = "9 de octubre de 2026, 19:06 (hora de Bogotá)"
shutil.rmtree(DST, ignore_errors=True)
shutil.copytree(SRC, DST)
for L in "ABF":
    os.rename(os.path.join(DST, f"layer{L}", f"think4ever_peru_day1_layer{L}_DRAFT"), os.path.join(DST, f"layer{L}", f"think4ever_peru_day1_layer{L}_FINAL"))
for f in ("SHA256SUMS.txt", "manifest_peru_day1.csv"):           # regenerated at the end
    os.remove(os.path.join(DST, f))
for L in "ABF":
    os.remove(os.path.join(DST, f"layer{L}", f"think4ever_peru_day1_layer{L}_FINAL", "validation", "SHA256SUMS.txt"))
A, B, F = (f"layer{L}/think4ever_peru_day1_layer{L}_FINAL" for L in "ABF")

def edit(rel, pairs, base=DST):
    p = os.path.join(base, rel); s = open(p, encoding="utf-8").read()
    for old, new in pairs:
        n = s.count(old)
        if n != 1:
            raise SystemExit(f"EDIT FAILED ({n} matches) in {rel}: {old[:80]!r}")
        s = s.replace(old, new)
    open(p, "w", encoding="utf-8").write(s)

# ---------------- integral README (rewritten)
open(os.path.join(DST, "README.md"), "w", encoding="utf-8").write(f"""# Think4ever — Perú Day 1 — Paquete integral **FINAL**

**Estado:** **FINAL**. Think4ever autorizó el cierre el {AUTH}, con el dictamen "APTO PARA FINAL" de la auditoría final v2.
**Alcance de la aprobación:** cierre documental y metodológico de Perú Day 1 (capas A, B y F). **No** aprueba estimaciones de mercado potencial ni recomendaciones comerciales.
No está cargado en la plataforma Think4ever. No se modificaron otros países, personas, anillos ni la plataforma.
**Versión anterior:** `think4ever_peru_day1_DRAFT.zip` (histórica). Los resultados son idénticos byte a byte; los cambios están detallados en `Peru_Day1_Informe_Cierre_FINAL.md`.

| Carpeta o archivo | Contenido |
|---|---|
| `Peru_Day1_Informe_Cierre_FINAL.md` | Informe de cierre: archivos incluidos, controles, limitaciones que se mantienen y estado de cada capa |
| `Peru_Day1_Resumen_Ejecutivo.md` | Resultados y límites de A, B y F, sin estimaciones de mercado potencial |
| `Peru_Day1_Auditoria_Final_Cierre.md` | Auditoría final v2: controles, matriz de hallazgos y recomendación (más la sección 6, sobre el cierre FINAL) |
| `layerA/think4ever_peru_day1_layerA_FINAL/` | Capa A: GitHub Innovation Graph (2026T1 frente a 2025T1) |
| `layerB/think4ever_peru_day1_layerB_FINAL/` | Capa B: Stack Overflow Developer Survey 2025 (Perú, n = 64) |
| `layerF/think4ever_peru_day1_layerF_FINAL/` | Capa F: EPEN 2025 (13 personas y anillos) + F9 con ENAHO 2025 (fuente separada) |
| `audit/` | Scripts y resultados de auditoría, control DRAFT → FINAL y clasificación de las referencias a DRAFT que quedan |
| `manifest_peru_day1.csv` | Todos los archivos, con capa, rol, tamaño y SHA‑256 |
| `SHA256SUMS.txt` | Verificación: `sha256sum -c think4ever_peru_day1_FINAL/SHA256SUMS.txt`, desde la carpeta que contiene `think4ever_peru_day1_FINAL/` |

**Reglas de uso:**
- Las capas miden cosas distintas en periodos distintos: **no se suman, no se multiplican y no se combinan**.
- Ninguna cifra es TAM, SAM, SOM ni número de clientes de Think4ever.
- Cada capa tiene su propio README con fuentes, metodología, limitaciones y cómo reproducir.
- El paquete no contiene microdatos ni archivos fuente oficiales.

**Limitaciones que se mantienen** (detalle en el informe de cierre):
- F10 (trabajo desde casa) no está disponible.
- A4 y A5 son provisionales (D‑03 y D‑04).
- Documentos de EPEN 2025 pendientes de archivo (V3: diccionario anual; V4: PDF del informe anual).
- Verificaciones opcionales que no se hicieron: comparación con la web de Innovation Graph, `latam-country-breakdown-2026Q1.csv` y valores anteriores de Think4ever para la capa B.
""")

# ---------------- executive summary
edit("Peru_Day1_Resumen_Ejecutivo.md", [
    ("Estado: **DRAFT** (apto para FINAL según la auditoría v2; falta la autorización).",
     f"Estado: **FINAL**. Think4ever autorizó el cierre el {AUTH}. Es un cierre documental y metodológico; no aprueba estimaciones de mercado potencial ni recomendaciones comerciales."),
    ("dentro de `think4ever_peru_day1_DRAFT.zip`", "dentro de `think4ever_peru_day1_FINAL.zip`")])

# ---------------- final audit (root and layer F copy)
CLOSE_SEC = f"""

## 6. Cierre FINAL ({AUTH})

- **Autorización:** Think4ever aceptó el dictamen de esta auditoría (v2) y autorizó el cierre de Perú Day 1 y de sus capas A, B y F como **FINAL**.
- **Alcance:** es un cierre documental y metodológico. **No aprueba** estimaciones de mercado potencial ni recomendaciones comerciales.
- **Qué se cambió:** solo estados y documentación. El detalle está en `Peru_Day1_Informe_Cierre_FINAL.md` y en `audit/draft_to_final_change_control_pe.csv`.
- **Qué no se cambió:** resultados, indicadores, personas, anillos, reglas de supresión ni decisiones metodológicas.
- **Contexto histórico:** las secciones 1 a 5 se escribieron cuando los paquetes estaban en DRAFT. Sus menciones a DRAFT describen esa etapa.
- **Limitaciones:** las de la sección 4 se mantienen sin cambios.
"""
for rel in ("Peru_Day1_Auditoria_Final_Cierre.md", f"{F}/Peru_Day1_Auditoria_Final_Cierre.md"):
    edit(rel, [("**Estado de todos los paquetes: DRAFT** (no se cambió a FINAL).",
                f"**Estado: FINAL**: autorizado por Think4ever el {AUTH} (sección 6). Este informe se emitió cuando los paquetes estaban en DRAFT."),
               ("- **Contenido:** `think4ever_peru_day1_DRAFT.zip` con",
                "- **Contenido:** `think4ever_peru_day1_FINAL.zip` (antes `think4ever_peru_day1_DRAFT.zip`) con")])
    p = os.path.join(DST, rel); open(p, "a", encoding="utf-8").write(CLOSE_SEC)

# ---------------- layer READMEs
for L, pkg, cond in (("A", A, "C1"), ("B", B, "C2")):
    title = {"A": "Capa A: desarrolladores en GitHub", "B": "Capa B: adopción de IA entre desarrolladores"}[L]
    edit(f"{pkg}/README.md", [
        (f"# Think4ever · Perú Day 1 · {title} · **DRAFT**", f"# Think4ever · Perú Day 1 · {title} · **FINAL**"),
        (f"**Paquete:** `think4ever_peru_day1_layer{L}_DRAFT`", f"**Paquete:** `think4ever_peru_day1_layer{L}_FINAL`"),
        ("**Estado:** DRAFT; no está cargado en la plataforma Think4ever.",
         f"**Estado:** **FINAL**, autorizado por Think4ever el {AUTH}. No está cargado en la plataforma Think4ever. Versión anterior: `think4ever_peru_day1_layer{L}_DRAFT`, con datos idénticos.")])
edit(f"{F}/README.md", [
    ("— **DRAFT** (revisión 7 — cierre conjunto, 2026-10-09)", "— **FINAL** (revisión 8 — cierre FINAL, 2026-10-09)"),
    ("Estado: DRAFT hasta la validación final. V1 validado contra el informe oficial INEI 2016-2025 (anexo I.17) y F9 aprobado. Pendientes: V3 (diccionario anual EPEN), V4 (PDF informe EPEN para hash), V5 (F10, información oficial), V7 (aprobación final).",
     f"Estado: **FINAL**, autorizado por Think4ever el {AUTH}. V1 está validado contra el informe oficial del INEI 2016‑2025 (anexo I.17) y F9 está aprobado. Limitaciones que se mantienen: V3 (diccionario anual EPEN), V4 (PDF del informe EPEN, para el hash) y V5 (F10 no disponible). V7 (aprobación final) quedó resuelta.")])
edit(f"{F}/Peru_Day1_LayerF_ENAHO2025_Auditoria_F9.md", [
    ("La capa F sigue en **DRAFT** hasta la aprobación final. No está cargado en la plataforma.",
     f"**Capa F: FINAL** (autorizada el {AUTH}). No está cargada en la plataforma."),
    ("La capa F sigue en DRAFT hasta la aprobación final de Think4ever.",
     f"En ese momento la capa F seguía en DRAFT. Think4ever autorizó su cierre como FINAL el {AUTH}.")])
edit(f"{F}/Peru_Day1_LayerF_EPEN2025_Auditoria_y_Resultados.md", [
    ("Estado: **DRAFT hasta la aprobación final**. No está cargado en la plataforma.",
     f"Estado: **FINAL** (autorizado el {AUTH}). No está cargado en la plataforma."),
    ("| V7 | Revisión final del paquete y cambio de DRAFT a FINAL | Pendiente | Decisión de Think4ever (V1 y V6 ya resueltos) |",
     f"| V7 | Revisión final del paquete y cambio de DRAFT a FINAL | **Resuelto**: FINAL autorizado el {AUTH} | — |")])

# ---------------- scripts (package copies and master copies): FINAL folder names, neutral docstrings, closure record
def script_edits(base, rel_ab, rel_f, rel_audit):
    for rel in rel_ab:
        edit(rel, [('PA, PB = os.path.join(OUT, "think4ever_peru_day1_layerA_DRAFT"), os.path.join(OUT, "think4ever_peru_day1_layerB_DRAFT")',
                    'PA, PB = os.path.join(OUT, "think4ever_peru_day1_layerA_FINAL"), os.path.join(OUT, "think4ever_peru_day1_layerB_FINAL")')], base)
    for rel in [r for r in rel_ab if r.endswith("build_layer_ab_packages_pe.py")]:
        edit(rel, [("(Stack Overflow) DRAFT packages from the EXISTING outputs.", "(Stack Overflow) packages from the EXISTING outputs.")], base)
    for rel in [r for r in rel_ab if r.endswith("finalize_ab_packages_pe.py")]:
        edit(rel, [("finalize Layer A and B DRAFT packages:", "finalize Layer A and B packages:")], base)
    for rel in rel_f:
        edit(rel, [('''    ("D-03/D-04", "2026-10-09", "A4 threshold and A5 definition", "kept provisional (Layer A unchanged)", ""),''',
                    '''    ("CLOSE-PE-D1", "2026-10-09", "Peru Day 1 (Layers A, B and F) declared FINAL", "AUTHORISED by Think4ever 2026-10-09 19:06 (America/Bogota)",
     "Documentary and methodological closure; not an approval of potential-market estimates or commercial recommendations. Results unchanged"),
    ("D-03/D-04", "2026-10-09", "A4 threshold and A5 definition", "kept provisional (Layer A unchanged)", ""),''')], base)
    for rel in rel_audit:
        s = open(os.path.join(base, rel)).read()
        s = s.replace("closure audit of the Layer F DRAFT package", "closure audit of the Layer F package").replace(
            "closure audit of Layer A and Layer B DRAFT packages", "closure audit of Layer A and Layer B packages")
        open(os.path.join(base, rel), "w").write(s)
script_edits(DST, [f"{A}/scripts/build_layer_ab_packages_pe.py", f"{A}/scripts/finalize_ab_packages_pe.py",
                   f"{B}/scripts/build_layer_ab_packages_pe.py", f"{B}/scripts/finalize_ab_packages_pe.py"],
             [f"{F}/scripts/build_layer_f_deliverables_pe.py"],
             [f"{F}/scripts/audit_closure_layer_f_pe.py", "audit/audit_closure_layer_f_pe.py", "audit/audit_closure_ab_pe.py"])
script_edits(MASTER, ["build_layer_ab_packages_pe.py", "finalize_ab_packages_pe.py"], ["build_layer_f_deliverables_pe.py"],
             ["audit_closure_layer_f_pe.py", "audit_closure_ab_pe.py"])
print("FINAL tree prepared:", DST)
