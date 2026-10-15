# Think4Ever Perú — Market Research & Analytics

**Corte:** 15 de octubre de 2026. Este informe acompaña el mapa y el workbook
de Perú. Conserva la estructura de capas A–R usada para Colombia, pero no
convierte un vacío de fuente en una estimación o un cero.

## Resumen ejecutivo

Perú cuenta con resultados nacionales de actividad de desarrolladores, uso de
tecnología y empleo, y con capas territoriales por departamento o distrito
cuando la fuente publica una llave geográfica. El mapa muestra 25 departamentos
para indicadores administrativos y hasta 1.891 distritos IGN para indicadores
con UBIGEO compatible. La cobertura y los periodos no son uniformes entre
fuentes; cada ficha mantiene el año y la limitación correspondiente.

## Dónde se forman y emplean las personas

### Educación superior — C y L

SUNEDU/TUNI aporta matrícula reportada 2025-2 por programa y local, y egresados
2024 por programa y local. Ambos se agregan a 25 departamentos y a los distritos
que encuentran una llave IGN. Los ingresantes TUNI 2025 se conservan como un
indicador nacional porque su exportación pública no contiene localización.

MINEDU aporta oferta y matrícula superior no universitaria 2025 por departamento.
La oferta universitaria vigente se conserva aparte de la matrícula para evitar
doble conteo. No hay una fuente nacional homogénea publicada para modalidad ni
capacidad/vacantes por sede; por eso esos indicadores continúan no disponibles.

### Personas y empleo — F, G y H

EPEN 2025 y la correspondencia CNO 2015–CIUO-08 producen observaciones
departamentales para el núcleo TIC y P01–P04 cuando la muestra permite su
publicación. Las demás personas quedan identificadas como estimaciones modeladas,
nunca como observaciones. ENAHO 2025 aporta empleo, tamaño reportado del
establecimiento, registro SUNAT declarado y conectividad por departamento de
residencia. Esto describe personas ocupadas, no empresas ni demanda comercial.

## Empresas y territorio

### Empresas TIC y zonas — D y J

El padrón RUC SUNAT de abril de 2026 se agrega por CIIU 6201, 6202, 6209, 6311 y
6312. Se publican RUC activos TIC por departamento y distrito fiscal. La capa no
debe interpretarse como empleo, ventas, establecimientos con atención al público
ni empresas renovadas en el año.

### Empresas formales y micronegocios — M y N

El padrón reducido de locales SUNAT agrega 775.150 registros con UBIGEO válido,
en 25 departamentos y 1.891 distritos. Es una evidencia territorial de locales
registrados, no de empresas únicas, actividad económica, forma legal ni tamaño.
ENAHO permite indicadores de empleo por tamaño reportado, pero no el universo
legal de micronegocios. Por ello N1–N4 y la medición empresarial de M permanecen
pendientes de un directorio con tamaño y actividad.

## Escuelas y programa — K y P

Los servicios educativos secundarios se muestran como 15.700 puntos y los
agregados departamentales mantienen matrícula y servicios. Los escenarios de
patrocinio no se presentan como cifras comerciales: todavía falta evidencia del
programa, conversión aprobada y regla fiscal aplicable.

## Contexto, datos y controles — O, Q y R

La capa O conserva contexto digital ERESTEL/OSIPTEL. Q usa límites y llaves IGN;
la auditoría técnica verifica que los indicadores territoriales publicados cubran
los 25 departamentos. R no representa una aprobación de negocio: sólo prueba
cobertura de llaves, periodos y metadatos técnicos. La conciliación de conceptos
incompatibles requiere una matriz aprobada por negocio.

## Estado de entrega

| Entregable de plantilla | Estado |
|---|---|
| Workbook Indicators y Sources register | Publicado en `thinkdocuments/think4ever-peru-country-template.xlsx` |
| JSON agregados y scripts reproducibles | Publicados en `data/peru/`, `data/peru-map/` y `scripts/` |
| Auditoría técnica | 19 checks aprobados; pendientes explícitos en `peru_template_audit_2026-10-14.json` |
| Mapa interactivo | Departamentos, distritos, puntos escolares y métricas nacionales |
| Deck de país | Pendiente de construir con la plantilla visual y los resultados publicados |

## Límites que siguen abiertos

1. Modalidad y capacidad de educación superior comparables a nivel nacional.
2. Universo legal de micronegocios, tamaño empresarial y comercios 4711.
3. Evidencia del programa escolar y patrocinios.
4. Conciliación de negocio entre universos, periodos y definiciones de fuentes.

