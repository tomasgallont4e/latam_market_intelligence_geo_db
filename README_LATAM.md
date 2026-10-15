# LATAM Market Intelligence — Colombia y Perú

## Uso

Ejecute `npm install` y defina las mismas variables de base de datos requeridas por Colombia. Después, ejecute `npm start` con `PORT` definido por el entorno. La vista **Mapa** incorpora un selector de país sin abandonar la página.

## Perú en el mapa

- Las capas A–R están disponibles en el selector. Una capa sin cifras publicadas se conserva como pendiente, nunca como cero.
- Los indicadores se conservan como datos nacionales cuando su fuente no aporta geografía. Las 13 personas pueden verse por departamento como **estimación modelada**, no como observación: se reparte cada total nacional publicado con pesos verificables de RUC TIC y matrícula secundaria. Las personas suprimidas por precisión permanecen sin estimación.
- **Departamentos del Perú** es una coropleta con 25 límites referenciales del IGN y cuatro indicadores con llave territorial verificable: RUC TIC activos, matrícula secundaria objetivo, servicios de secundaria y matrícula secundaria total. Sus nombres se muestran en la interfaz; no como letras de capa.
- La capa `Servicios educativos` representa 15.700 puntos de secundaria EBR. Los códigos `ubigeo` sirven para filtrar o enlazar datos, pero el paquete no incluye polígonos distritales certificados.
- Las cifras visibles mantienen periodo, estado, fuente y limitación declarada por el consolidado.

### Cartografía y uniones verificadas

- `geo_departments_ign_2025.geojson` contiene 25 polígonos WGS84 de límites departamentales referenciales del Instituto Geográfico Nacional (IGN), simplificados solo para visualización web. La fuente oficial es el conjunto público **Límites Departamentales**, escala 1:100.000.
- Los códigos departamentales IGN se unen a `fact_secondary_region_2025.json` de MINEDU; las 25 geometrías tienen datos de educación secundaria 2025.
- Los nombres departamentales IGN se unen a los agregados SUNAT de `fact_ruc_tic_district_202604.json`; las 25 geometrías tienen RUC TIC. Tres RUC cuyo departamento figura como `NO DISPONIBLE` se excluyen del mapa y del total territorial, pues no se les puede asignar ubicación.
- Para cada persona publicable, el modelo preserva su total nacional y asigna departamentos con pesos por anillo: **Core** 80% RUC TIC / 20% matrícula secundaria; **Adjacent** 60% / 40%; **Extended** 40% / 60%. Esta es una proxy de planificación territorial y no una estimación departamental de INEI.

## Datos que aún faltan en Perú

La carpeta `data/peru-map/research_layers_B_R/` conserva los contratos por capa. Antes de cargar nuevos datos, se deben mantener sus llaves geográficas, periodo, unidad, fuente, método y estado de publicación.

| Capas | Estado en el consolidado | Próxima fuente o trabajo declarado |
|---|---|---|
| C y L | Marco educativo parcial | SUNEDU y ESCALE/MINEDU; homologar programas TIC con ISCED-F, modalidad y sede. |
| D | Disponible por departamento | RUC/SUNAT, usando CIIU 6201, 6202, 6209, 6311 y 6312 con universo activo explícito. Para llegar a distrito falta cartografía distrital con UBIGEO validado. |
| E | Sin valores | CPV, RUC, SUNEDU y ESCALE, según el contrato de capa. |
| H | Sin valores | EPEN y CNO, tras resolver el mapeo y los pesos del insumo trimestral. |
| J | Sin valores | RUC y UBIGEO, para poder asociar registros empresariales a geografía válida. |
| M y N | Sin valores | ENAHO/RUC (M) y RUC (N), con el periodo y universo que define cada contrato. |
| P | Parcial documental | ESCALE, RUC, DON y LPDP; completar unidad escolar, periodo de escenario y cobertura. |
| Q | Cartografía departamental cargada | UBIGEO y CPV; falta incorporar límites distritales compatibles para cartografía de mayor detalle. |
| G | Insumo trimestral recibido, sin mapeo final | EPEN ciudades 2026 y CNO; completar diccionario y pesos antes de publicar. |
| I, K y O | Parcialmente pobladas | Completar las series/fuentes indicadas en sus contratos, conservando los valores actuales y sus limitaciones. |
| R | Control transversal pendiente | Conciliar fuentes, llaves, periodos, unidades y precisión antes de aceptar el estudio. |

## Memoria de accesos y adquisiciones

- **SUNEDU (capas C y L):** queda pendiente solicitar acceso o información pública por programa, modalidad, sede y periodo. No se debe sustituir con estimaciones. Las rutas oficiales son `https://saip.sunedu.gob.pe/` y `https://www.sunedu.gob.pe/solicitud-acceso-informacion-publica/`. La solicitud exige identificación y datos del solicitante; no se presenta sin autorización expresa del titular.
- **Fuentes ya descargadas o iniciadas:** Padrón RUC SUNAT abril 2026; EPEN 2025 por departamentos; EPEN 2026 ciudades (T1 y T2); ENAHO 2025 completa. Se conservarán como insumos pendientes de normalización, no se mezclan automáticamente con el corte base 2025.
- **RUC integrado:** el padrón SUNAT de abril de 2026 provisto por el usuario ya alimenta la capa D. Se publican únicamente agregados: 88.147 RUC activos con actividad principal CIIU rev.4 6201/6202/6209/6311/6312, distribuidos en 1.211 distritos de domicilio fiscal. No equivale a empleo o establecimientos locales.
- **ESCALE:** para conservar la comparabilidad se utilizará el corte 2025 del histórico. El padrón vigente publica archivos 2026 y necesita una decisión explícita antes de sustituir los datos escolares del mapa.
- **ESCALE — acceso técnico:** el histórico activó una verificación anti-bot al intentar recuperar el archivo. No se debe automatizar ni eludir esa comprobación; la descarga debe hacerla una persona en el sitio oficial.
- **Cartografía/UBIGEO:** se incorporaron límites departamentales IGN con llave y fuente verificadas. La capa distrital continúa pendiente hasta contar con límites oficiales compatibles por UBIGEO.

## Restricciones metodológicas

Los conteos de personas de Perú son estimaciones nacionales de ocupación, no TAM/SAM/SOM ni demanda comercial. Los valores `null` significan suprimido, no disponible o pendiente y nunca se convierten a cero. La coropleta de persona es una proxy modelada y se etiqueta como tal; no sustituye una estimación departamental observada.
