# Perú — estado de ejecución de la plantilla (2026-10-14)

Este registro separa lo reproducido de lo pendiente; un valor no disponible no
se sustituye por cero ni por una distribución sintética.

| Día | Capas | Estado verificable | Publicado en este repositorio |
|---|---|---|---|
| 1 | A, B, F | Completo: GitHub Innovation Graph, Stack Overflow 2025, EPEN/ENAHO 2025 y CNO 2015 | `data/peru/think4ever_peru_day1_FINAL/` |
| 2 | F, G, H, I | F completo. G/H reproducidos desde EPEN anual 2025 por departamento; I conserva solo escenarios sin precio aprobado | `data/peru/day2_gh/` y `data/peru-map/fact_persona_department_epen2025.json` |
| 3 | K, L, C | K tiene padrones/MINEDU procesados y mapa de servicios. C/L requieren programa, sede, modalidad y periodo de SUNEDU | `data/peru-map/fact_secondary_*`, `geo_secondary_services_2025.geojson` |
| 4 | M, N, J, D, E | D tiene agregado RUC TIC por distrito. M/N/J/E no tienen aún un insumo publicable con las definiciones de la plantilla | `data/peru-map/fact_ruc_tic_district_202604.json` |
| 5 | O, P, Q, R | O contiene contexto ERESTEL. Q tiene geometrías IGN y llaves UBIGEO ya verificadas. P/R necesitan evidencia de programa y conciliaciones finales | `data/peru-map/fact_digital_context_erestel_2025.json`, `geo_*ign_2025.geojson` |

## Día 2: alcance exacto

La EPEN 2025 anual disponible está ponderada a nivel de departamento, no de
ciudad. Por ello, G/H se publican con `geographic_level=department_proxy`.
El selector del mapa ofrece **Núcleo TIC observado (P01–P04 combinado)**: tiene
estimaciones publicables en 16 departamentos. P01–P04 se conservan además de
forma individual, pero se suprimen cuando hay menos de 30 registros muestrales.
No se convierten a estimaciones distritales.

El campo `buyer_proxy` en H procede de las variables EPEN C310/C311 y describe
la posición/sector del empleador. No mide compradores ni demanda comercial.

## Insumos necesarios para cerrar los pendientes

1. SUNEDU: matrícula por programa, sede, modalidad y periodo; el acceso se
   solicita en https://saip.sunedu.gob.pe/ cuando el titular autorice la
   solicitud.
2. Definición y fuente oficial de micronegocio, empresa formal, zona comercial
   y tipología de ciudad para M/N/J/E. El padrón RUC por sí solo no contiene
   empleo, ventas, tamaño o universo de micronegocios.
3. Evidencia del programa/patrocinios para P y una matriz de conciliación
   aprobada por negocio para R. No se infieren de geografía o encuestas.
