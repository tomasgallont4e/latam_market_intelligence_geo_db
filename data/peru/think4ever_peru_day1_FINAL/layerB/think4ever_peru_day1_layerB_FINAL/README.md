# Think4ever · Perú Day 1 · Capa B: adopción de IA entre desarrolladores · **FINAL**

**Paquete:** `think4ever_peru_day1_layerB_FINAL` · **Preparado:** 9 de octubre de 2026 (condición C2 de la auditoría de cierre) · **País:** Perú (`PE`).
**Estado:** **FINAL**, autorizado por Think4ever el 9 de octubre de 2026, 19:06 (hora de Bogotá). No está cargado en la plataforma Think4ever. Versión anterior: `think4ever_peru_day1_layerB_DRAFT`, con datos idénticos.

> **Las cifras se tomaron tal cual de las salidas existentes del motor (8 de octubre de 2026), reproducidas byte a byte.** Únicos ajustes:
> 1. La columna `vs_latam_ex_pe` se renombró a **`vs_regional_ex_focus`** (convención de Argentina), con los valores sin cambios.
> 2. Los booleanos se pasaron a minúsculas.
> 3. Se agregaron `b_indicator_definitions_pe.csv` y el contraste **`b_reproduction_check_pe.csv`**.

## 1. Qué mide esta capa (y qué no)
- **Mide** las respuestas de los encuestados de la **Stack Overflow Developer Survey 2025** que declararon `Country = "Peru"`: uso de IA, uso diario, agentes, herramientas, actitudes y compras.
- **No mide** la población de desarrolladores de Perú. La muestra es **autoseleccionada, no ponderada y pequeña**.
- **Prohibido:** multiplicar estos porcentajes por las poblaciones de la capa F o por las cuentas de la capa A.
- No son clientes potenciales ni mercado de Think4ever.

## 2. Fuente
- `results.csv`: 49.191 filas; el total publicado es de 49.019. SHA‑256 `2d1f6530…`, igual que en Argentina y Chile. Licencia ODbL/DbCL.
- Agregado oficial `ai.json`, del mismo commit del archivo, `c9c23dc`.
- Detalle en `data/source_registry_layer_b_pe.csv`.

## 3. Metodología (el mismo motor de Argentina y Chile: `layer_b_engine.py`)
- **Indicadores** (`b_indicator_definitions_pe.csv`):
  - B1–B5 de la plantilla y BX1–BX12 suplementarios. Las definiciones son las de Argentina; solo se adaptó el texto de B5 a "Peru".
  - Cada pregunta usa su propio denominador (`valid_n`).
- **Grupos comparados:**
  - Perú (todos los encuestados y profesionales);
  - LATAM sin Perú (18 países, 1.965 encuestados);
  - Global (49.191);
  - BR, MX, AR, CO y CL como referencia.
- **Intervalos:** Wilson al 95 %.
- **Etiquetas** `higher/lower/no_clear_difference_exploratory`: se basan en si los intervalos no se solapan, **no son pruebas estadísticas**.
- **Marcas de base (D‑PE‑02):**
  - `ok` si n ≥ 50;
  - `indicative` si n está entre 30 y 49;
  - `suppressed` si n < 30, y en ese caso el numerador, la proporción y el intervalo quedan **vacíos**.

## 4. Resultados de Perú (encuestados 2025)

| Indicador | Perú | LATAM sin Perú | Global | Base |
|---|---|---|---|---|
| B5 Encuestados | **64** (46 profesionales) | 1.965 | 49.191 | **Confianza BAJA (< 300)** |
| B1 Usa herramientas de IA | **88,1 %** (52/59) | 85,8 % | 78,5 % | ok |
| B2 Usa IA a diario | **62,7 %** (37/59) | 54,5 % | 47,1 % | ok; mayor que global (exploratorio) |
| B3 Usa agentes de IA | **43,9 %** (25/57) | 36,3 % | 30,9 % | ok; mayor que global (exploratorio) |
| B4 Editores | VS Code 80,0 % (36/45) · IntelliJ 37,8 % · Cursor 22,2 % | | | **indicativo** (n = 45) |
| B4 Modelos de IA | GPT 75,8 % (25/33) · DeepSeek R 42,4 % · Gemini Flash 39,4 % · Claude Sonnet 36,4 % | | | **indicativo** (n = 33) |
| B4c Agentes externos | **suprimido** | | | n = 22 |

En el segmento de profesionales (42 a 43 respuestas por pregunta) todo es **indicativo**. De las 316 filas de Perú, 64 son `ok`, 164 `indicative`, 86 `suppressed` y 2 `not_applicable`.

## 5. Validaciones (`data/b_reproduction_check_pe.csv`, `validation/b_validation_checks_pe.csv`)

| Control | Resultado |
|---|---|
| **Contraste con el agregado oficial de Stack Overflow** (`ai.json`) | B1 global 78,496 % frente a 78,483 % oficial · B2 47,103 % frente a 47,086 % · B3 30,938 % frente a 30,931 %. **MATCH** (diferencia ≤ 0,02 pp; el CSV público tiene más filas que el total publicado) |
| Cruce con el paquete FINAL de Argentina (mismo archivo y mismo motor) | GLOBAL, BR, MX, CO, CL y AR: 158 de 158 filas idénticas por grupo |
| Valores anteriores de Think4ever para Perú | **No disponibles**: nunca se entregaron |
| Re‑ejecución del motor | 3 de 3 archivos idénticos byte a byte |
| Valores del paquete frente a la salida existente | Idénticos; solo cambia el nombre de una columna |
| Regla de marcas y supresión | Cumplida; las celdas suprimidas no tienen valor |

## 6. Limitaciones
1. **La muestra es autoseleccionada y pequeña** (64 encuestados). Los porcentajes describen a esos encuestados, no a los desarrolladores de Perú.
2. **Confianza BAJA:** los intervalos de B1–B3 tienen una amplitud de unos ±12 pp. Ninguna diferencia frente a LATAM sin Perú es distinguible.
3. **Las comparaciones son exploratorias, no pruebas estadísticas.**
4. **El periodo es 2025.** No coincide con el de la capa A (2026T1) ni con el de la capa F (promedio 2025, a partir de encuestas de hogares).
5. **No se combina** con las capas A ni F.

## 7. Archivos

| Ruta | Contenido |
|---|---|
| `data/b_survey_indicators_pe.csv` | 1.422 filas de indicadores (Perú, LATAM sin Perú, Global y países de referencia), con IC de Wilson, marcas y etiquetas exploratorias |
| `data/b_survey_distributions_pe.csv` | 315 filas con las distribuciones completas de respuestas |
| `data/b_comparison_groups_pe.csv` | Grupos y número de encuestados |
| `data/b_indicator_definitions_pe.csv` | Pregunta, numerador y denominador de B1–B5 y BX1–BX12 |
| `data/b_reproduction_check_pe.csv` | Contraste con `ai.json` y cruce con el paquete de Argentina |
| `data/source_registry_layer_b_pe.csv` | Fuentes, hashes y solicitudes |
| `data_dictionary.csv`, `manifest.csv`, `validation/` | Diccionario, inventario, controles y hashes |
| `scripts/` | `layer_b_engine.py` (cálculo), `build_layer_ab_packages_pe.py` y `finalize_ab_packages_pe.py` |

## 8. Reproducir
```
python3 -I scripts/layer_b_engine.py results.csv PE <out_dir>     # results.csv sha256 2d1f6530...
python3 -I scripts/build_layer_ab_packages_pe.py <work_a> <out_dir> <ig_repo> results.csv ai.json <AR_FINAL> <CL_FINAL> <root>
```
