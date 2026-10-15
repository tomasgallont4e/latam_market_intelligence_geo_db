# Consolidado de datos de Perú para el mapa Think4ever

## Qué contiene y cómo se muestra

Este paquete integra la entrega autorizada Perú Day1 FINAL (capas A, B y F) con los contratos y datos B–R ya procesados en el paquete de investigación. Es una entrega de datos para montar en el artefacto; no modifica el código de la aplicación ni certifica una carga en producción.

Las métricas A, B y F tienen ámbito nacional. El mapa debe mostrarlas como indicadores o paneles de Perú. La encuesta Stack Overflow conserva su carácter autoseleccionado y baja confianza. La capa F incluye 13 filas de persona y conserva supresiones y precisión; varias personas no tienen estimación publicable. Ningún valor nacional se distribuye entre departamentos, ciudades, provincias o distritos.

La geografía disponible para detalle consiste en puntos de servicios escolares de secundaria EBR y códigos/nombres de distrito de reporte del Censo Educativo. El GeoJSON de escuelas es un overlay de puntos. No se incluyen polígonos distritales; para coropletas hace falta enlazar una cartografía cuyo código coincida con `ubigeo`. El distrito de reporte educativo no se declara límite político certificado.

## Archivos principales

- `map_catalog.json`: catálogo A–R, alcance, conteos y reglas de visualización.
- `map_payload.json`: rutas relativas de carga para los datos incluidos.
- `mapAdapterPeru.mjs`: funciones sencillas para consultar métricas nacionales, personas y puntos escolares sin inventar valores locales.
- `fact_map_indicator.csv`: hechos A–R en formato común, con unidad, periodo, geografía/ámbito, fuente, método y estado.
- `fact_persona_estimates_epen2025.json`: 13 personas, anillos y totales autorizados, con valores suprimidos como null.
- `fact_persona_profiles_2025.json`: perfiles EPEN y contexto socioeconómico ENAHO 2025; revisar fuente, estado y supresión.
- `fact_ruc_tic_district_202604.json`: agregado de RUC SUNAT abril de 2026 para CIIU 6201, 6202, 6209, 6311 y 6312, por UBIGEO fiscal. No contiene RUC individuales ni permite inferir empleo local.
- `geo_units.json`: país y distritos educativos con código/nombre, sin polígonos distritales.
- `geo_secondary_services_2025.geojson`: 15700 servicios secundarios como puntos y sus cifras por grado/sexo.
- `research_layers_B_R/`: contratos originales C–R y K procesada; pendiente no equivale a cero.
- `day1_final/`: datos CSV de las capas A, B y F, diccionarios, fuentes y evidencia FINAL publicada. Se omiten microdatos y directorio interno no publicable.
- `peru_educacion_contexto_2025.sqlite`: base educativa existente con consultas por distrito y nivel.

## Montaje recomendado

1. Registrar `PE` como ámbito nacional para los hechos A, B y F. Mantener `period`, `source_id`, `status` y `unit` en cada consulta.
2. Filtrar F por P01–P13. Si `publication_status=suppressed_unreliable`, mostrar “suprimido por precisión”; no mostrar cero. Los anillos/ALL13 son agregados solapados o definidos por método: no sumar persona por persona encima de ellos.
3. Mostrar ERESTEL por su dominio publicado; los ámbitos nacional, Lima/Callao, resto urbano y rural son separados, no partes sumables sin comprobación.
4. Cargar escuelas como capa de puntos. Una selección de distrito puede filtrar las escuelas por `properties.ubigeo`; no usar ese conteo de servicios como conteo de colegios únicos.
5. Mantener K (matrícula escolar) y F (personas trabajadoras) como temas diferentes. No inferir personas objetivo entre estudiantes ni perfiles de ocupación por distrito.
6. Las capas C–R conservan indicadores pendientes donde faltan fuentes o definiciones. No construir ceros de relleno.

## Formato común de `fact_map_indicator.csv`

`layer, metric_id, scope_type, scope_id, group_id, persona_id, indicator, category, value, unit, period, comparison_period, numerator, denominator, status, source_id, method, limitations`.

Para país se usa `scope_type=country`, `scope_id=PE`. Las comparaciones globales/regionales de B usan `scope_type=comparison` y `scope_id` vacío. Los hechos K por código geográfico pertenecen a su nivel original y se mantienen en las tablas fuente. `value` vacío es nulo semántico, no 0.

## Límites de esta entrega

- Día1 FINAL declara 82/82 comprobaciones A/B/F y autoriza cierre documental/metodológico. No autoriza TAM/SAM/SOM ni recomendaciones comerciales.
- A4 y A5 siguen provisionales. La reconciliación opcional con el desglose anterior de Think4ever no se hizo.
- Layer F usa EPEN2025 y ENAHO2025 complementaria. F10 (trabajo desde casa) sigue no disponible; el diccionario anual EPEN pendiente de archivo en el cierre Day1. Los conteos/estimaciones respetan supresiones del paquete fuente.
- Las cifras de personas son totales nacionales, no distribución espacial. No son clientes de Think4ever ni demanda comercial.
- 2084 servicios escolares carecen de CODINST. Por ello, número nacional de instituciones y tope100 por institución permanecen parciales; véase K.
- La cartografía distrital no está incluida. No se modificó ni publicó la aplicación.
- La licencia de insumos INEI/microdatos se debe validar antes de republicar fuera de los agregados permitidos por la autorización interna. Este consolidado no incluye microdatos.

## Memoria de accesos pendientes

- Para completar las capas C y L se requiere información de SUNEDU a nivel de programa, modalidad, sede y periodo. La fuente se debe solicitar mediante `https://saip.sunedu.gob.pe/` o `https://www.sunedu.gob.pe/solicitud-acceso-informacion-publica/`. No se ha presentado la solicitud porque requiere datos e identificación del solicitante.
- Se iniciaron descargas públicas de RUC abril 2026, EPEN 2025, EPEN 2026 T1/T2 y ENAHO 2025. Son insumos para normalizar y validar; no cambian automáticamente los indicadores con corte 2025.
- El padrón RUC abril 2026 entregado por el usuario fue procesado: 88.147 RUC activos bajo el filtro CIIU rev.4 definido, en 1.211 distritos con coincidencias. Hash del ZIP original: `E631FE9E6169712C0C1AC7981D007CAB35A2AFFFC2012629469BAAD154698150`.
- La cartografía oficial compatible para la capa Q todavía no está cargada. No se deben construir coropletas ni asignar cifras nacionales a distritos hasta verificar la versión del límite y la llave UBIGEO.

## Integridad y fuentes

El informe de cierre y manifiesto del Day1 FINAL están en `day1_final/`. SHA256 del archivo anidado suministrado: `8c02d84d3c984fba833642862e31b2e68b70938ff28ec26bd04e4e4d77278519`. La entrega original pasó `SHA256SUMS.txt`. Los resúmenes de origen, hashes y controles A/B/F están en `day1_final/layerA`, `layerB`, `layerF` y el informe de cierre.
