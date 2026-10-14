
# Perú Day 1 — capas A, B y F (prueba)

Paquete original: `think4ever_peru_day1_FINAL.zip` (raíz del proyecto, sin cambios).
Extraído tal cual en `data/peru/think4ever_peru_day1_FINAL/`. Contiene 84 archivos.
`data/geodb-v2/` y las tablas de Colombia no se tocan.

## Qué se carga

`scripts/load-peru.js` crea 20 tablas `pe_*` y registra 20 filas `pe_*` en `meta_sources`.
La licencia del proyecto para todas ellas es «uso interno».

| Capa | Fuente | Tablas |
|---|---|---|
| A | GitHub Innovation Graph (GitHub) | pe_a_github_country_quarterly (100), pe_a_github_languages (107), pe_a_github_indicators (25) |
| B | Stack Overflow Developer Survey 2025 | pe_b_survey_indicators (1.422), pe_b_survey_distributions (315), pe_b_comparison_groups (9), pe_b_indicator_definitions (19), pe_b_reproduction_check (10) |
| F | INEI – EPEN 2025 / ENAHO 2025 / CNO 2015 | pe_f_persona_estimates (34), pe_f_persona_profiles (1.210), pe_f_persona_correspondence (13), pe_f_occupation_mapping (65), pe_f_cno_code_counts (438), pe_cno2015_ciuo08_correspondence (542), pe_f9_persona_socioeconomic_enaho (300), pe_f1_enaho_diagnostic (25), pe_f_designers_informational (10), pe_enaho_quintile_cutpoints (4), pe_decisions_log (15) |
| A+B+F | Registros de fuentes del paquete | pe_source_registry (27) |

Reglas de carga:

- Los códigos (CNO, CIUO, ISCO, ids) se guardan como texto, con sus ceros a la izquierda.
- Cada tabla tiene una clave técnica `pe_row_id`.
- `pe_source_registry` conserva la licencia original de cada fuente (`license` / `license_status`).
- Además añade `project_license = 'uso interno'`.

## Qué NO se carga

Estos archivos quedan solo en disco:

- `layerF/.../validation/internal_not_publishable/` (5 CSV);
- los scripts Python;
- los informes `.md`;
- los CSV de validación del paquete.

## Cómo ejecutarlo

    node scripts/load-peru.js --dry-run    # sin base de datos: SHA256, filas vs manifiesto, source_id
    node scripts/load-peru.js              # recrea las tablas pe_*, registra meta_sources y valida
    node scripts/load-peru.js --meta-only  # solo vuelve a registrar las 20 filas pe_* de meta_sources

El script necesita `DATABASE_URL` o `DB_*`. En esta plataforma la terminal no las recibe; solo las tiene el servicio de la app.

El script es idempotente: solo borra y recrea tablas cuyo nombre empieza por `pe_`. Al terminar compara los conteos de todas las tablas de Colombia y sus filas de `meta_sources` antes y después de la carga.

## IMPORTANTE: después de cada recarga de Colombia

La recarga de Colombia (`POST v1/load`, `scripts/load.js`, `lib/loader.js`) **no borra la base completa**. Solo vacía sus 31 tablas.

- Las tablas `pe_*` **sobreviven**.
- Pero `meta_sources` está entre esas 31 tablas. Se vacía entera y se rellena solo con Colombia, así que **las 20 filas `pe_*` se pierden**.

**Después de cada recarga de Colombia hay que correr `node scripts/load-peru.js`** (o, como mínimo, `--meta-only`).

El panel de aceptación de Colombia no revisa tablas `pe_*`, así que no avisará de que faltan esas filas.
