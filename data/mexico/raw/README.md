# México: descargas originales

Todo lo que se guarde aquí, salvo este archivo, queda fuera de Git (`.gitignore`). Los archivos se dejan tal como se descargaron, con su nombre original. Registre cada descarga (URL, fecha, SHA-256) en `../sources_register.csv`.

| Subcarpeta | Fuente | Capas | Qué descargar |
|---|---|---|---|
| `github_innovationgraph/innovationgraph/` | GitHub Innovation Graph (`git clone`, en el commit `078fb62` que usó Perú, con `core.autocrlf=false`) | A | Carpeta `data/`: `developers.csv`, `organizations.csv`, `git_pushes.csv`, `languages.csv` |
| `stackoverflow_survey/so_2025/` | Stack Overflow Developer Survey 2025 (archivo del commit `c9c23dc`, objeto LFS) | B | `results.csv` y `ai.json` |
| `inegi_enoe_2025/` | INEGI ENOE, microdatos | F, G, H, M | Los cuatro trimestres de 2025 (`microdatos/`), todas las tablas, con la estructura de la base de datos y los cuestionarios (`documentacion/`) |
| `inegi_sinco_ciuo/` | INEGI SINCO 2019 y tablas comparativas SINCO 2011 – CIUO-08 | F (mapeo de ocupaciones) | Manual SINCO 2019 (anexo de equivalencia 2011-2019), fe de erratas, `sinco_tablas_comparativas.xlsx`, estructura CIUO-08 y clasificaciones de la ENOE |
| `inegi_denue_2026_05/` | INEGI DENUE 05/2026, descarga masiva | D, J, N | Los 25 archivos nacionales por sector (`denue_00_*_csv.zip`) y el diccionario de datos |
| `layers_C_K_L_sep_formato911_2024_2025/` | SEP Formato 911, ciclo 2024-2025 (datos.gob.mx) | C, K, L | Básica, media superior, superior escolarizada y no escolarizada (CSV por escuela). Descarga manual: el sitio bloquea accesos automatizados |
| `layer_E_conapo_proyecciones_municipios_1990_2040/` | CONAPO, proyecciones municipales 1990-2040 (2024) | E | `00_Republica_mexicana.zip` (población a mitad de año por municipio), metodología y resultados |
| `inegi_catalogo_unico_202610/` | INEGI Catálogo Único de Claves | Q | Catálogo completo de estados, municipios y localidades, con su fecha de corte |
| `inegi_marco_geoestadistico/` | INEGI Marco Geoestadístico | Q (mapa) | Polígonos estatales y municipales |
| `layer_I_banxico_fix_2025/`, `layers_I_O_dof_salarios_minimos_2025/`, `layer_O_context/`, `layer_O_atdt_plan_nacional_ia_2026/`, `layers_O_P_leyes_camara_diputados/`, `layer_M_notes/` | Banxico FIX 2025, CONASAMI (DOF 19-12-2024), ENDUTIH 2025, ENIF 2024, Plan Nacional de IA, LFPDPPP, LIVA, LISR, nota ENAMIN | I, O, P, M | Documentos de respaldo de las cifras y normas de contexto |
| `layer_L5_sep_capacitacion_para_el_trabajo_2024_2025/` | SEP, capacitación para el trabajo 2024-2025 por estado | L (L5) | Consulta del Sistema Educativo Nacional (xlsx) |
| `layer_O1_imf_weo_gdp_per_capita/`, `layer_O2_banxico_spei_codi_2025/`, `layer_O6_datareportal_digital_2026_mexico/`, `layer_O6_statcounter_2025/` | FMI WEO (DataMapper NGDPDPC), Banxico SIE (SPEI y CoDi, CF881-CF891), DataReportal Digital 2026 Mexico, StatCounter 2025 | O (O1, O2, O6) | JSON de la API, series diarias 2025 (xlsx), página guardada (html) y CSV anual |
| `layers_D3_M4_inegi_censos_economicos_2024_ref2023/` | INEGI Censos Económicos 2024 (año de referencia 2023) | D (D3), M (M4) | Datos abiertos nacionales (`conjunto_de_datos_ce_nac_2024_csv.zip`) y tabulado CE_TEMACE_1 por estrato |
| `layer_R_checks/` | Boletines ENOE 2025, boletín DENUE 05/2026, SEP Principales Cifras 2024-2025 | R | Totales publicados para las comprobaciones |
| `sedatu_metropolis_2020/` | SEDATU, CONAPO e INEGI, Metrópolis de México 2020, parte 17 | J | Cuadros A.19.1.01 y B.19.1.01 de la Zona Metropolitana de Monterrey (descargado de gob.mx) |
