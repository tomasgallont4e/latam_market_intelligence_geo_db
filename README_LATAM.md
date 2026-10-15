# LATAM Market Intelligence — Colombia y Perú

## Uso

Ejecute `npm install` y defina las mismas variables de base de datos requeridas por Colombia. Después, ejecute `npm start` con `PORT` definido por el entorno. La vista **Mapa** incorpora un selector de país sin abandonar la página.

## Perú en el mapa

- Las capas A–R están disponibles en el selector. Una capa sin cifras publicadas se conserva como pendiente, nunca como cero.
- Los indicadores y las 13 personas se presentan como datos nacionales. No se interpolan ni se asignan a departamentos, provincias ni distritos.
- La capa `Servicios educativos` representa 15.700 puntos de secundaria EBR. Los códigos `ubigeo` sirven para filtrar o enlazar datos, pero el paquete no incluye polígonos distritales certificados.
- Las cifras visibles mantienen periodo, estado, fuente y limitación declarada por el consolidado.

## Datos que aún faltan en Perú

La carpeta `data/peru-map/research_layers_B_R/` conserva los contratos por capa. Antes de cargar nuevos datos, se deben mantener sus llaves geográficas, periodo, unidad, fuente, método y estado de publicación.

| Capas | Estado en el consolidado | Próxima fuente o trabajo declarado |
|---|---|---|
| C y L | Marco educativo parcial | SUNEDU y ESCALE/MINEDU; homologar programas TIC con ISCED-F, modalidad y sede. |
| D | Sin valores | RUC/SUNAT, usando CIIU 6201, 6202, 6209, 6311 y 6312 con universo activo explícito. |
| E | Sin valores | CPV, RUC, SUNEDU y ESCALE, según el contrato de capa. |
| H | Sin valores | EPEN y CNO, tras resolver el mapeo y los pesos del insumo trimestral. |
| J | Sin valores | RUC y UBIGEO, para poder asociar registros empresariales a geografía válida. |
| M y N | Sin valores | ENAHO/RUC (M) y RUC (N), con el periodo y universo que define cada contrato. |
| P | Parcial documental | ESCALE, RUC, DON y LPDP; completar unidad escolar, periodo de escenario y cobertura. |
| Q | Diseño sin carga | UBIGEO y CPV; cargar la cartografía/estadística con llaves compatibles. |
| G | Insumo trimestral recibido, sin mapeo final | EPEN ciudades 2026 y CNO; completar diccionario y pesos antes de publicar. |
| I, K y O | Parcialmente pobladas | Completar las series/fuentes indicadas en sus contratos, conservando los valores actuales y sus limitaciones. |
| R | Control transversal pendiente | Conciliar fuentes, llaves, periodos, unidades y precisión antes de aceptar el estudio. |

## Memoria de accesos y adquisiciones

- **SUNEDU (capas C y L):** queda pendiente solicitar acceso o información pública por programa, modalidad, sede y periodo. No se debe sustituir con estimaciones. Las rutas oficiales son `https://saip.sunedu.gob.pe/` y `https://www.sunedu.gob.pe/solicitud-acceso-informacion-publica/`. La solicitud exige identificación y datos del solicitante; no se presenta sin autorización expresa del titular.
- **Fuentes ya descargadas o iniciadas:** Padrón RUC SUNAT abril 2026; EPEN 2025 por departamentos; EPEN 2026 ciudades (T1 y T2); ENAHO 2025 completa. Se conservarán como insumos pendientes de normalización, no se mezclan automáticamente con el corte base 2025.
- **RUC integrado:** el padrón SUNAT de abril de 2026 provisto por el usuario ya alimenta la capa D. Se publican únicamente agregados: 88.147 RUC activos con actividad principal CIIU rev.4 6201/6202/6209/6311/6312, distribuidos en 1.211 distritos de domicilio fiscal. No equivale a empleo o establecimientos locales.
- **ESCALE:** para conservar la comparabilidad se utilizará el corte 2025 del histórico. El padrón vigente publica archivos 2026 y necesita una decisión explícita antes de sustituir los datos escolares del mapa.
- **ESCALE — acceso técnico:** el histórico activó una verificación anti-bot al intentar recuperar el archivo. No se debe automatizar ni eludir esa comprobación; la descarga debe hacerla una persona en el sitio oficial.
- **Cartografía/UBIGEO:** no incorporar polígonos sin versión, licencia y llave de unión verificadas. La capa Q permanece pendiente hasta contar con la cartografía oficial compatible.

## Restricciones metodológicas

Los conteos de personas de Perú son estimaciones nacionales de ocupación, no TAM/SAM/SOM ni demanda comercial. Los valores `null` significan suprimido, no disponible o pendiente. No deben convertirse a cero ni utilizarse para colorear geografía subnacional.
