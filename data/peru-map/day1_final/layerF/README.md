# Think4ever — Perú Day 1 — Capa F (EPEN 2025 + F9 ENAHO 2025) — **FINAL** (revisión 8 — cierre FINAL, 2026-10-09)

Estado: **FINAL**, autorizado por Think4ever el 9 de octubre de 2026, 19:06 (hora de Bogotá). V1 está validado contra el informe oficial del INEI 2016‑2025 (anexo I.17) y F9 está aprobado. Limitaciones que se mantienen: V3 (diccionario anual EPEN), V4 (PDF del informe EPEN, para el hash) y V5 (F10 no disponible). V7 (aprobación final) quedó resuelta.

Población ocupacional ≠ perfil socioeconómico ≠ mercado potencial de Think4ever (no estimado en esta capa). No cargado en la plataforma. Capas A y B sin cambios. Solo agregados; microdatos INEI locales.

Documentos:
- `Peru_Day1_Auditoria_Final_Cierre.md` — **auditoría final de cierre**: matriz de hallazgos, dictamen v2 (capa F: APTO PARA FINAL; Perú Day 1: APTO PARA FINAL — C1–C3 resueltas; FINAL autorizado el 9 de octubre de 2026, 19:06, hora de Bogotá), resumen ejecutivo, pendientes y manifiesto.
- `data_dictionary.csv` (todas las columnas) y `manifest.csv` (todos los archivos con hash).
- `Peru_Day1_LayerF_EPEN2025_Auditoria_y_Resultados.md` — auditoría (A), correspondencias (B), resultados (C), metodología (D), pendientes (E).
- `Peru_Day1_LayerF_ENAHO2025_Evaluacion.md` — evaluación previa de ENAHO 2025 (superada).
- `Peru_Day1_LayerF_ENAHO2025_Auditoria_F9.md` — auditoría ENAHO 2025 y resultados F9 (fuente separada de EPEN).

Datos publicables (`data/`):
- `f_persona_correspondence_pe.csv` — tabla B (13 personas).
- `f_persona_estimates_pe.csv` — personas, anillos, combinados, informativos, sensibilidades. Valores **suprimidos vacíos** (D-PE-03). Columnas `scope_note` (persona 8: categoría amplia, incluye técnicos) y `measure` (población ocupacional; no usuarios).
- `f_persona_profiles_pe.csv` — F3–F8 (+F6 departamento). Grupos suprimidos vacíos; celdas <30 registros vacías.
- `f_occupation_mapping_pe.csv`, `f_cno_code_counts_pe.csv` — nivel código CNO; ponderado vacío si <30 registros.
- `f9_persona_socioeconomic_enaho_pe.csv` — F9 desde ENAHO 2025 (quintiles nacionales de ingreso real per cápita + ESTRSOCIAL); celdas suprimidas vacías.
- `f1_enaho_diagnostic_pe.csv` — F1 ENAHO solo diagnóstico (no reemplaza EPEN), con IC y sensibilidad de diseño. `enaho_quintile_cutpoints_pe.csv`.
- `f_designers_informational_pe.csv` — D-PE-09: grupo informativo diseñadores (CNO 2163+2166+3432) en EPEN y ENAHO por separado; fuera de personas y anillos.
- **Nunca combinar factores ENAHO (FAC500A) y EPEN (FAC300_ANUAL) ni aplicar porcentajes ENAHO a totales EPEN.**
- `cno2015_ciuo08_correspondence.csv`, `source_registry_layer_f_pe.csv`, `decisions_log_pe.csv`.

Validación (`validation/`): `audit_layer_f_checks_pe.csv` (60/60 PASS), `epen_variance_sensitivity_pe.csv`, `f_employed_totals_check_pe.csv` (EPEN 24/24 PASS vs INEI), `enaho_sumaria_checks_pe.csv` (ENAHO 7/7 PASS), `enaho_vs_inei_official_validation_pe.csv` (anexo oficial INEI: 21 cifras reproducidas), `f_run_meta_pe.json`, `SHA256SUMS.txt`.
`validation/internal_not_publishable/` — tablas completas con valores suprimidos, solo para auditoría y reproducción. **No publicar.**
Las diferencias entre agregados publicados que reproducen valores suprimidos no son fiables y no deben publicarse.

Reproducir (requiere archivos INEI originales):
Requisitos: Python 3.13 (pandas 3.0.5, numpy 2.5.3, openpyxl 3.1.5, pdfplumber 0.11.10), pdftotext 24.02; ejecutar con `python3 -I`. Tiempo total ≈ 95 s.

```
python3 -I scripts/parse_cno2015_annex.py Clasificador_Nacional_de_Ocupaciones_2015.pdf work/
python3 -I scripts/layer_f_epen_peru.py "EPEN 2025 BD_Publicacion Dpto.csv" work/cno2015_ciuo08_correspondence.csv work/out
python3 -I scripts/enaho_sumaria_quintiles_pe.py Sumaria-2025.csv deflactores_base2025_new.dta despacial_ldnew.dta work/enaho
python3 -I scripts/layer_f_enaho_f9_pe.py Enaho01a-2025-500.csv work/enaho/hh_quintiles_LOCAL_ONLY.pkl <entrega>/validation/internal_not_publishable/f_persona_estimates_internal_pe.csv ENAHO-TABLA-CNO-2015.csv work/enaho
python3 -I scripts/build_layer_f_deliverables_pe.py work/out <entrega>/data work/enaho
python3 -I scripts/validate_enaho_vs_inei_official_pe.py <anexo_dir> work/enaho/hh_quintiles_LOCAL_ONLY.pkl Sumaria-2025.csv work/enaho/enaho_vs_inei_official_validation_pe.csv   # run before the build
```
