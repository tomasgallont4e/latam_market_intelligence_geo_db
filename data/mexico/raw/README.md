# México: descargas originales

Todo lo que se guarde aquí, salvo este archivo, queda fuera de Git (`.gitignore`). Los archivos se dejan tal como se descargaron, con su nombre original. Registre cada descarga (URL, fecha, SHA-256) en `../sources_register.csv`.

| Subcarpeta | Fuente | Capas | Qué descargar |
|---|---|---|---|
| `github_innovationgraph/innovationgraph/` | GitHub Innovation Graph (`git clone`, en el commit `078fb62` que usó Perú, con `core.autocrlf=false`) | A | Carpeta `data/`: `developers.csv`, `organizations.csv`, `git_pushes.csv`, `languages.csv` |
| `stackoverflow_survey/so_2025/` | Stack Overflow Developer Survey 2025 (archivo del commit `c9c23dc`, objeto LFS) | B | `results.csv` y `ai.json` |
| `inegi_enoe_2025/` | INEGI ENOE, microdatos | F, G, H, M | Los cuatro trimestres de 2025 (`microdatos/`), todas las tablas, con la estructura de la base de datos y los cuestionarios (`documentacion/`) |
| `inegi_sinco_ciuo/` | INEGI SINCO 2019 y tablas comparativas SINCO 2011 – CIUO-08 | F (mapeo de ocupaciones) | Manual SINCO 2019 (anexo de equivalencia 2011-2019), fe de erratas, `sinco_tablas_comparativas.xlsx`, estructura CIUO-08 y clasificaciones de la ENOE |
| `inegi_denue_2026_05/` | INEGI DENUE 05/2026, descarga masiva | D, J, N | Los 25 archivos nacionales por sector (`denue_00_*_csv.zip`) y el diccionario de datos |
| `sep_911_2025_2026/` | SEP Formato 911 (datos.gob.mx) | C, K, L | Secundaria, media superior, superior escolarizada y no escolarizada, con sus diccionarios. Descarga manual: el sitio bloquea accesos automatizados |
| `conapo_proyecciones_municipales/` | CONAPO, proyecciones municipales 1990-2040 | E | Población a mitad de año por municipio |
| `inegi_catalogo_unico_202610/` | INEGI Catálogo Único de Claves | Q | Catálogo completo de estados, municipios y localidades, con su fecha de corte |
| `inegi_marco_geoestadistico/` | INEGI Marco Geoestadístico | Q (mapa) | Polígonos estatales y municipales |
| `contexto/` | Banxico, CONASAMI, ENDUTIH, ENIF, DOF, SAT, ATDT | I, O, P | Documentos de respaldo de las cifras y normas de contexto |
