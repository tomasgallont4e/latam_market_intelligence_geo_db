# Perú — estado de ejecución de la plantilla (2026-10-14)

Este registro separa lo reproducido de lo pendiente; un valor no disponible no
se sustituye por cero ni por una distribución sintética.

| Día | Capas | Estado verificable | Publicado en este repositorio |
|---|---|---|---|
| 1 | A, B, F | Completo: GitHub Innovation Graph, Stack Overflow 2025, EPEN/ENAHO 2025 y CNO 2015 | `data/peru/think4ever_peru_day1_FINAL/` |
| 2 | F, G, H, I | F completo. G/H reproducidos desde EPEN anual 2025 por departamento; I conserva solo escenarios sin precio aprobado | `data/peru/day2_gh/` y `data/peru-map/fact_persona_department_epen2025.json` |
| 3 | K, L, C | K tiene padrones/MINEDU procesados y mapa de servicios; se publicó oferta superior no universitaria y el inventario SUNEDU de universidades licenciadas. C/L aún requieren programa, sede, modalidad y periodo | `data/peru/day3_higher_education_offer/`, `data/peru/day3_sunedu/`, `data/peru-map/fact_secondary_*` |
| 4 | M, N, J, D, E | D tiene agregado RUC TIC por distrito. M tiene empleo ENAHO por tamaño reportado y registro SUNAT declarado; N/J/E no tienen aún un insumo publicable con las definiciones completas de la plantilla | `data/peru-map/fact_ruc_tic_district_202604.json`, `data/peru/day4_m_enaho/`, `data/peru/day4_n_padron_local/` |
| 5 | O, P, Q, R | O contiene contexto ERESTEL. Q tiene geometrías IGN. R tiene conciliación técnica de cobertura geográfica de las capas mapeadas; P y la conciliación de negocio requieren evidencia/aprobación | `data/peru/day5_oq/`, `data/peru-map/fact_digital_context_erestel_2025.json`, `geo_*ign_2025.geojson` |

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
   aprobada por negocio para R. No se infieren de geografía o encuestas. La
   conciliación técnica actualmente publicada solo prueba cobertura de llaves,
   no equivalencia de conceptos entre fuentes.
