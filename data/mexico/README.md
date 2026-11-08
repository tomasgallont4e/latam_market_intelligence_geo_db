# México: datos del estudio de país

Estructura para incorporar los datos de México siguiendo la plantilla de investigación por países (capas A–R). Las tablas de salida conservan la forma de Colombia (`data/geodb-v2/csv/`, `diccionario.md`) para compararse con Colombia y Perú. La aplicación lee México desde estos archivos (D-MX-01); el cargador y el esquema de `data/geodb-v2` son solo de Colombia, y algunas columnas cambian por país (por ejemplo `median_income_mxn` en lugar de `median_income_cop`).

## Carpetas

| Carpeta | Contenido | ¿Se versiona? |
|---|---|---|
| `raw/` | Archivos oficiales descargados una sola vez, sin modificar. Ver `raw/README.md`. | No (solo su README) |
| `outputs/` | Un JSON por capa (`layer_<x>_mx.json`), producido por los scripts; cada fila lleva su clave geográfica. | Sí |
| `geodb/csv/` | Tablas con la forma de Colombia (`geo_department`, `geo_municipality`, `fact_persona_profile`, …) y `meta_sources.csv`. El contrato de cada tabla está en `geodb/diccionario.md`. | Sí |
| `validation/` | Resultados de las comprobaciones de la capa R (totales publicados, uniones de códigos, sumas). | Sí |
| `sources_register.csv` | Registro de fuentes (R2): fuente, URL, periodo, archivo, SHA-256, licencia y script de cada cifra. | Sí |
| `decisions_log.csv` | Decisiones metodológicas y desviaciones de la plantilla. | Sí |

Los scripts van en `scripts/` con el prefijo `build-mexico-<capa>` y reciben la ruta de `raw/` como argumento.

## Reglas

- Solo se versionan agregados. Ningún microdato, registro individual ni dirección de establecimiento entra al repositorio.
- Claves geográficas INEGI como texto: estado (`cve_ent`, 2 dígitos) y municipio (5 dígitos, estado + municipio), con ceros a la izquierda.
- `null` significa suprimido, no disponible o pendiente; nunca se convierte en cero.
- Las cifras nacionales no se reparten entre estados o municipios. ENOE solo se publica por estado y por ciudad ENOE (`cd_a`), nunca por municipio.
- Cada cifra de encuesta lleva su número de entrevistas y su nivel de confianza.
- Totales contra la publicación oficial: ocupados ENOE dentro de 0,5 % por trimestre; 911 dentro de 1 %; DENUE 05/2026 exacto (6.138.075 establecimientos).

## Periodos de referencia

Periodo previsto según el registro de fuentes de México (28-oct-2026) y periodo usado en los datos publicados:

| Capas | Periodo previsto | Periodo usado |
|---|---|---|
| A | GitHub Innovation Graph 2026 Q1 | 2026 Q1 frente a 2025 Q1 |
| B | Stack Overflow Developer Survey, última edición | Encuesta 2025 |
| C, K, L | Ciclo escolar 2025-2026 (respaldo conjunto: 2024-2025) | Ciclo 2024-2025, el respaldo (D-MX-11) |
| D, J, N | DENUE 05/2026 (pasan juntas a 11/2026 si se procesan después del 25-nov-2026) | DENUE 05/2026; D3 usa los Censos Económicos 2024, referencia 2023 (D-MX-15) |
| E | Población CONAPO 2025 (2024 si C usa 2024-2025) | 2024 |
| F, G, H, M | ENOE 2025, promedio de los trimestres 1 a 4 | ENOE 2025, trimestres 1 a 4; M4 usa los Censos Económicos 2024, referencia 2023 (D-MX-15) |
| I, O | 2025 (excepción: ENIF 2024); leyes vigentes en octubre de 2026 | 2025 (ENIF 2024); leyes vigentes en 2026 |
| P | Ciclo 2025-2026 + DENUE 05/2026 | Ciclo 2024-2025 + DENUE 05/2026 |
| Q | Catálogo Único, octubre de 2026 | Catálogo Único con cortes de 2025-12 a 2026-10 y Marco Geoestadístico |
