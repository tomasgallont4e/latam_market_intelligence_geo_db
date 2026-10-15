# LATAM Market Intelligence — Colombia y Perú

## Uso

Ejecute `npm install` y defina las mismas variables de base de datos requeridas por Colombia. Después, ejecute `npm start` con `PORT` definido por el entorno. La vista **Mapa** incorpora un selector de país sin abandonar la página.

## Perú en el mapa

- Las capas A–R están disponibles en el selector. Una capa sin cifras publicadas se conserva como pendiente, nunca como cero.
- Los indicadores se conservan como datos nacionales cuando su fuente no aporta geografía. El **Núcleo TIC observado (P01–P04 combinado)** y las personas P01–P04 se muestran por departamento a partir de EPEN 2025 cuando su muestra lo permite; las celdas pequeñas se suprimen. P05–P13 siguen siendo una estimación modelada con pesos de RUC TIC y matrícula secundaria.
- **Departamentos del Perú** es una coropleta con 25 límites referenciales del IGN y 24 indicadores con llave territorial verificable: actividad TIC formal, educación básica/superior, empleo, conectividad y matrícula reportada por TUNI/SUNEDU. Además, TUNI aporta dos indicadores nacionales de ingresantes 2025. Sus nombres se muestran en la interfaz; no como letras de capa.
- **Distritos del Perú** es una coropleta de detalle con 1.891 límites IGN. Para mantener la respuesta rápida, carga hasta 450 distritos del área visible y se actualiza al acercar o desplazar el mapa. La ficha incluye departamento, provincia y UBIGEO.
- La capa `Servicios educativos` representa 15.700 puntos de secundaria EBR. Los códigos `ubigeo` sirven para filtrar o enlazar datos, pero el paquete no incluye polígonos distritales certificados.
- Las cifras visibles mantienen periodo, estado, fuente y limitación declarada por el consolidado.

### Cartografía y uniones verificadas

- `geo_departments_ign_2025.geojson` contiene 25 polígonos WGS84 de límites departamentales referenciales del Instituto Geográfico Nacional (IGN), simplificados solo para visualización web. La fuente oficial es el conjunto público **Límites Departamentales**, escala 1:100.000.
- `geo_districts_ign_2025.geojson` contiene 1.891 polígonos distritales WGS84 del mismo conjunto IGN, simplificados para visualización web. Los 1.211 distritos RUC coinciden con UBIGEO; 1.847 de 1.848 hechos de secundaria coinciden con un límite distrital.
- Los códigos departamentales IGN se unen a `fact_secondary_region_2025.json` de MINEDU; las 25 geometrías tienen datos de educación secundaria 2025.
- La matrícula TUNI/SUNEDU 2025-2 se agrega desde 5.650 filas de programas/locales reportados a 25 departamentos y 146 distritos. La unión distrital usa departamento, provincia y distrito normalizados contra IGN; los 146 registros tienen un límite coincidente. Solo se publican agregados; ni nombres de estudiantes ni direcciones de locales entran al repositorio.
- Los nombres departamentales IGN se unen a los agregados SUNAT de `fact_ruc_tic_district_202604.json`; las 25 geometrías tienen RUC TIC. El desglose CIIU departamental se agrega desde los registros distritales por los dos primeros dígitos de UBIGEO. Tres RUC cuyo departamento figura como `NO DISPONIBLE` se excluyen del mapa y del total territorial, pues no se les puede asignar ubicación.
- Para cada persona publicable, el modelo preserva su total nacional y asigna departamentos o distritos con pesos por anillo: **Core** 80% RUC TIC / 20% matrícula secundaria; **Adjacent** 60% / 40%; **Extended** 40% / 60%. Esta es una proxy de planificación territorial y no una estimación territorial observada por INEI.

## Paquetes por día de la plantilla

| Día | Paquete publicado | Alcance |
|---|---|---|
| 1 | `data/peru/think4ever_peru_day1_FINAL/` | A, B y F; fuentes, controles y resultados finales. |
| 2 | `data/peru/day2_gh/` | G/H: empleo TIC por departamento e indicador de empleador; no es demanda. |
| 3 | `data/peru/day3_tuni_enrollment/` | Matrícula superior reportada por TUNI/SUNEDU, 2025-2, por departamento y distrito. |
| 3 | `data/peru/day3_tuni_ingress/` | Ingresantes reportados por TUNI/SUNEDU, 2025, con alcance nacional (sin sede ni territorio en el archivo fuente). |
| 4 | `data/peru/day4_dj_ruc/` | RUC TIC SUNAT por departamento y distrito fiscal. |
| 5 | `data/peru/day5_oq/` | Contexto ERESTEL/OSIPTEL y auditoría de llaves IGN. |

`scripts/audit-peru-template.js` verifica la presencia de los paquetes y deja el resultado en `thinkdocuments/peru_template_audit_2026-10-14.json`.

## Datos que aún faltan en Perú

La carpeta `data/peru-map/research_layers_B_R/` conserva los contratos por capa. Antes de cargar nuevos datos, se deben mantener sus llaves geográficas, periodo, unidad, fuente, método y estado de publicación.

| Capas | Estado en el consolidado | Próxima fuente o trabajo declarado |
|---|---|---|
| C y L | Marco educativo parcial | TUNI/SUNEDU aporta matrícula reportada 2025-2 por programa/local e ingresantes nacionales 2025; faltan modalidad, capacidad, egresados y homologación ISCED-F. |
| D | Disponible por departamento | RUC/SUNAT, usando CIIU 6201, 6202, 6209, 6311 y 6312 con universo activo explícito. Para llegar a distrito falta cartografía distrital con UBIGEO validado. |
| E | Sin valores | CPV, RUC, SUNEDU y ESCALE, según el contrato de capa. |
| H | Parcial departamental | EPEN 2025 y CNO: empleador como proxy; falta el cruce de ciudad/cliente de la plantilla. |
| J | Disponible por distrito fiscal | RUC y UBIGEO; faltan zona comercial y tamaño empresarial. |
| M y N | Sin valores | ENAHO/RUC (M) y RUC (N), con el periodo y universo que define cada contrato. |
| P | Parcial documental | ESCALE, RUC, DON y LPDP; completar unidad escolar, periodo de escenario y cobertura. |
| Q | Cartografía departamental y distrital cargada | UBIGEO y CPV; validar futuras actualizaciones contra los límites IGN ya incorporados. |
| G | Parcial departamental | EPEN 2025 y CNO; completar ciudades 2026 si se requiere el dominio exacto de la plantilla. |
| I, K y O | Parcialmente pobladas | Completar las series/fuentes indicadas en sus contratos, conservando los valores actuales y sus limitaciones. |
| R | Control transversal pendiente | Conciliar fuentes, llaves, periodos, unidades y precisión antes de aceptar el estudio. |

## Memoria de accesos y adquisiciones

- **SUNEDU (capas C y L):** TUNI publica matrícula por periodo/programa/local e ingresantes por programa; la primera se agrega territorialmente y los segundos se muestran solo a nivel nacional porque el archivo no trae sede ni territorio. Aún quedan pendiente modalidad, capacidad y egresados; no se sustituyen con estimaciones. Las rutas oficiales son `https://www.tuni.pe/comunidad/estudiantes`, `https://saip.sunedu.gob.pe/` y `https://www.sunedu.gob.pe/solicitud-acceso-informacion-publica/`. La solicitud exige identificación y datos del solicitante; no se presenta sin autorización expresa del titular.
- **Fuentes ya descargadas o iniciadas:** Padrón RUC SUNAT abril 2026; EPEN 2025 por departamentos; EPEN 2026 ciudades (T1 y T2); ENAHO 2025 completa. Se conservarán como insumos pendientes de normalización, no se mezclan automáticamente con el corte base 2025.
- **RUC integrado:** el padrón SUNAT de abril de 2026 provisto por el usuario ya alimenta la capa D. Se publican únicamente agregados: 88.147 RUC activos con actividad principal CIIU rev.4 6201/6202/6209/6311/6312, distribuidos en 1.211 distritos de domicilio fiscal. No equivale a empleo o establecimientos locales.
- **ESCALE:** para conservar la comparabilidad se utilizará el corte 2025 del histórico. El padrón vigente publica archivos 2026 y necesita una decisión explícita antes de sustituir los datos escolares del mapa.
- **ESCALE — acceso técnico:** el histórico activó una verificación anti-bot al intentar recuperar el archivo. No se debe automatizar ni eludir esa comprobación; la descarga debe hacerla una persona en el sitio oficial.
- **Cartografía/UBIGEO:** se incorporaron límites departamentales y distritales IGN con llave UBIGEO. La visualización distrital se consulta por área visible para conservar un tiempo de carga razonable.

## Restricciones metodológicas

Los conteos de personas de Perú son estimaciones nacionales de ocupación, no TAM/SAM/SOM ni demanda comercial. Los valores `null` significan suprimido, no disponible o pendiente y nunca se convierten a cero. La coropleta de persona es una proxy modelada y se etiqueta como tal; no sustituye una estimación departamental observada.
