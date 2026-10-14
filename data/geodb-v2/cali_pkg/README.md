# Cali: paquete exclusivo para añadir a Think4Ever

Solo incluye Cali. Municipio`76001`, zonas`CAL-01`a`CAL-22`. No contiene registros deBogotá niMedellín y no debe reemplazar sus tablas completas.

## Contenido

-22comunas con geometrías oficiales.
-13personas del dominio **Cali–Yumbo**, GEIH2025, con perfiles y segmentos laborales.
-22filas de contexto local con población proyectada2021, ASISCali.
-22comunas empresariales2025,94.415registros en total, con tamaño por ingresos. ActividadCIIUporcomuna no disponible.
-CSVUTF-8sinBOM,SQLiteindependiente, metadatos y validación.

`fact_persona_metro`usa las cuatro columnas de contenido del esquema existente. Los perfiles metropolitanos no reemplazan perfiles nacionales. `fact_zone_context`conserva campos no disponibles como vacíos/NULL, incluidos ocupados y las13personas por comuna. Población2021no se transforma en2025.

Los polígonos se vinculan por`zone_id`; perfiles y totalesGEIHpor`municipality_code`. Cali–Yumbo incluyeYumbo: el código76001ancla el dominio y no implica conteo exclusivo deCali. Las cifrasGEIHno se distribuyen entre las22comunas.

## Importar sin reemplazar Medellín

1. Importar/actualizar las22zonas por`zone_id`. Si ya están cargadas, no duplicarlas.
2. Añadir/actualizar hechos locales y empresas por`zone_id`; filtrar este lote a`CAL-%`.
3. Añadir/actualizar las13personas por`(persona,municipality_code)`; todos los registros de este lote son76001.
4. Registrar perfiles por`(persona,municipality_code,survey_year)`y resumen por`(municipality_code,survey_year)`.
5. Cargar`meta_sources.csv`mediante fusión por`table_name`:los textos indican que estos metadatos pertenecen al loteCali y se deben conservar también las fuentes deMedellín/Bogotá. No reemplazar su procedencia con una descripción exclusiva deCali.
6. El cargador debe tener registradas las nuevas tablas y columnas. La entrega anterior falló aceptación; este paquete separa los datos deCali, pero no corrige por sí mismo un cargador que omita esas tablas.

No usarTRUNCATE, borrado global o reemplazo completo de tablas nacionales para importar este lote. No sumar`CAL-00`:el grupoOtros no permite atribución municipal confirmada y se excluye del paquete.

## Controles de aceptación del lote

| Tabla / control | Esperado |
|---|---:|
|`geo_zone`CAL |22|
|ContextosCALunidos a`geo_zone` |22|
|EmpresasCAL |22filas,94.415registros|
|`fact_persona_metro`76001 |13|
|PerfilesGEIH76001unidos a`geo_municipality` |13|
|ResumenGEIH76001 |1|
|Conteos de personas disponibles por comuna |0|

Las verificaciones del lote no sustituyen la aceptación completa de la aplicación. Mantener las pruebas existentes deBogotá yMedellín.

## Fuentes y años

-GEIH2025:DANE, https://microdatos.dane.gov.co/index.php/catalog/853/get-microdata. Resultados reutilizados del procesamiento de12meses, no nueva descarga.
-Población2021:ASISCali,Tabla2,páginaPDF28, fuenteDANE/Planeación: https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/VS/ED/PSP/asis-cali-distrito-2021.pdf. Filas suman2.174.660; el documento muestra subtotalurbano2.217.961. No se forzó conciliación.
-Empresas2025:CámaraComercioCali: https://www.ccc.org.co/informacion-y-estudios-economicos/tableros-economicos/.
-Cartografía2026:IDESC/PlaneaciónCali, https://mg-idesc.cali.gov.co/geonetwork/srv/api/records/f33097b6-33db-4bc8-8674-f9848b763fc0. CC BY-SA4.0, atribución y cambios en`meta_geo_zone.csv`. No se levantan restricciones del cargador automáticamente.

No se armonizaron límites2021con cartografía2026. Los puntoslat/lonson interiores para etiquetas. `geometry`se entrega comoWKT; convertir en destino si la columna esPostGIS.

LaSQLitees una base independiente del loteCali, no una copia completa deproducción. No se cargó la aplicación en esta ejecución.
