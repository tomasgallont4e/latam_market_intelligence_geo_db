# Perú Day 1: informe de cierre FINAL

**Think4ever · Market Research & Analytics · LATAM** · 9 de octubre de 2026
**Estado:** **FINAL**. Think4ever lo autorizó el 9 de octubre de 2026 a las 19:06, hora de Bogotá.

**Alcance de la autorización:** es un cierre documental y metodológico de Perú Day 1. **No aprueba** estimaciones de mercado potencial ni recomendaciones comerciales, porque todavía no se han investigado. Ninguna cifra del paquete es TAM, SAM, SOM ni número de clientes de Think4ever.

**Qué no se tocó:**
- No se amplió la investigación ni se recalculó ningún indicador.
- No se modificaron Argentina, Chile, otros países ni la plataforma Think4ever.

## 1. Estado definitivo de cada capa

| Capa | Estado | Auditoría FINAL | Resultados |
|---|---|---|---|
| A. GitHub Innovation Graph (2026T1 frente a 2025T1) | **FINAL** | 10/10 PASS; validaciones internas: 13 PASS y 1 no verificable (opcional) | Idénticos byte a byte al DRAFT. A4 y A5 siguen **provisionales** |
| B. Stack Overflow Developer Survey 2025 | **FINAL** | 12/12 PASS; validaciones internas: 12/12 PASS | Idénticos byte a byte al DRAFT |
| F. EPEN 2025 (13 personas y anillos) y F9 con ENAHO 2025 | **FINAL** | 60/60 PASS | Idénticos byte a byte al DRAFT. El registro de decisiones solo suma la fila `CLOSE-PE-D1` |
| **Perú Day 1 completo** | **FINAL** | 82/82 PASS (22 de A/B y 60 de F) | Sin cambios en resultados, indicadores, personas, anillos, reglas de supresión ni decisiones validadas |

## 2. Archivos incluidos

`think4ever_peru_day1_FINAL.zip` contiene 84 archivos en la carpeta `think4ever_peru_day1_FINAL/`. Cada archivo, con su capa, rol, tamaño y SHA‑256, está en `manifest_peru_day1.csv`.

| Ubicación | Archivos | Contenido |
|---|---|---|
| Raíz | 6 | `README.md`; este informe; `Peru_Day1_Resumen_Ejecutivo.md`; `Peru_Day1_Auditoria_Final_Cierre.md` (v2 con la sección 6 de cierre); `manifest_peru_day1.csv`; `SHA256SUMS.txt` |
| `layerA/think4ever_peru_day1_layerA_FINAL/` | 13 | README; diccionario; manifiesto; 4 tablas de datos con registro de fuentes; 3 archivos de validación (incluido SHA256SUMS); 3 scripts |
| `layerB/think4ever_peru_day1_layerB_FINAL/` | 14 | README; diccionario; manifiesto; 6 tablas de datos con contraste y registro de fuentes; 2 archivos de validación; 3 scripts |
| `layerF/think4ever_peru_day1_layerF_FINAL/` | 41 | README; 4 documentos (EPEN, F9, evaluación ENAHO, copia de la auditoría); diccionario; manifiesto; 12 tablas de datos; 9 archivos de validación; 5 archivos internos de auditoría (no publicables); 8 scripts |
| `audit/` | 10 | 2 scripts de auditoría con sus resultados; 4 scripts de cierre (paso a FINAL, ajuste de redacción, hashes, control de cambios); `draft_to_final_change_control_pe.csv`; `draft_references_classification_pe.csv` |

**Lo que el paquete no contiene:** microdatos, identificadores de encuestados ni archivos fuente oficiales. La auditoría lo comprobó en los controles A5, B5 y E1.

## 3. Cambios del DRAFT al FINAL

El detalle archivo por archivo, con los hashes de antes y después, está en `audit/draft_to_final_change_control_pe.csv`.

**Datos (22 tablas):**
- 21 son idénticas byte a byte.
- `decisions_log_pe.csv` solo suma una fila: `CLOSE-PE-D1`, la autorización FINAL con su alcance. Las 14 filas anteriores no cambian.

**Resultados de validación (18 archivos):**
- 17 son idénticos.
- La copia de `audit_layer_f_checks_pe.csv` dentro de la capa F se igualó con la auditoría repetida en el FINAL. Solo cambia la evidencia del control E2 (de 38 a 40 entradas en SHA256SUMS). El resultado sigue siendo 60/60 PASS.

**Documentación (9 archivos):**
- Se cambió el estado a FINAL y el nombre del paquete.
- La auditoría v2 tiene una nueva sección 6 sobre el cierre.
- La verificación V7 (aprobación final) queda marcada como resuelta.
- No se cambió ninguna cifra.

**Scripts (8 archivos):**
- Se actualizaron rutas `_FINAL` y docstrings.
- La lista de decisiones del script de la capa F suma `CLOSE-PE-D1`.
- La lógica de cálculo no cambia.

**Metadatos de integridad (manifiestos, diccionario de F y SHA256SUMS):**
- Se regeneraron solo los hashes de los archivos modificados.
- En el diccionario de F solo cambia el conteo de filas del registro de decisiones (de 14 a 15).

**Archivos nuevos:** este informe, los 4 scripts de cierre y los 2 CSV de control.

## 4. Controles realizados

| Control | Resultado |
|---|---|
| Auditoría de A y B sobre el árbol FINAL, contra las fuentes originales (Innovation Graph `078fb62`, `results.csv` `2d1f6530…`, `ai.json`) | **22/22 PASS**, idéntica a la del DRAFT |
| Auditoría de F sobre el árbol FINAL (V1, controles de EPEN y ENAHO, hashes de las fuentes, ausencia de microdatos) | **60/60 PASS**, estable al repetirla |
| Regeneración de las tablas de F desde las salidas de cálculo (`work/f2/out`, `work/enaho/out`) | 11/11 tablas y 2/2 validaciones idénticas byte a byte; solo `decisions_log` cambia, por la fila autorizada |
| Identidad DRAFT → FINAL de datos y resultados | 21/22 tablas y 17/18 validaciones idénticas; las 2 diferencias son las explicadas en la sección 3 |
| Hashes por capa: `manifest.csv` y `validation/SHA256SUMS.txt` de A, B y F | Regenerados y verificados por las auditorías (A3/A4, B3/B4, E2) |
| Integridad del paquete integral (`SHA256SUMS.txt` y `manifest_peru_day1.csv`) | Verificada con `sha256sum -c` sobre el ZIP extraído (ver la sección 7) |
| Referencias a DRAFT (`audit/draft_references_classification_pe.csv`) | **0 referencias vigentes incorrectas**. Las que quedan son legítimas (ver la sección 5) |
| Valores aprobados | A1 907.052; A3 1.144.909; B1 52/59, B2 37/59, B3 25/57; Core 144.961,4; Adjacent 146.415,1; Extended 376.436,5; 13 personas 667.813,0: **sin cambios** |

## 5. Referencias a DRAFT que se conservan (legítimas)

Ninguna describe el estado vigente.

| Tipo | Dónde | Por qué se conserva |
|---|---|---|
| Nombre de la versión anterior | READMEs integral, de A y de B; sección 5 de la auditoría | Identifica el paquete DRAFT histórico, que tiene datos idénticos |
| Registro fechado de decisiones | `D-PE-10` y `D-PE-10b` (en `decisions_log` y en el script de F) | Son decisiones validadas, que no se modifican. Su estado ("Layer F remains DRAFT") describe el 9 de octubre por la tarde, y `CLOSE-PE-D1` registra el paso a FINAL |
| Contexto histórico | Línea 3 y sección 6 de la auditoría v2; conclusión de la auditoría F9 | Indican explícitamente que el texto se escribió en la etapa DRAFT |
| Pendiente resuelto | V7 en el informe EPEN | Marcado como "Resuelto" |
| Control de cambios | README integral; auditoría, sección 6 | Remiten a los archivos de control DRAFT → FINAL |
| Herramientas de cierre | Scripts en `audit/` y este informe | Operan o describen la transición |

## 6. Limitaciones que se mantienen

| # | Limitación | Situación |
|---|---|---|
| V5 | **F10 (trabajo desde casa) no está disponible** | No se publica ninguna estimación. Requiere una solicitud al INEI por la Ley 27806 |
| D‑03 / D‑04 | **A5 (canasta empresarial) y A4 (umbral de crecimiento) siguen provisionales** | `canonical_status = undetermined` en todas sus filas |
| V3 | **Diccionario de la base anual EPEN 2025 pendiente de archivo** | Las variables se validaron con 24 controles contra el INEI |
| V4 | **PDF del informe técnico EPEN anual 2025 pendiente de archivo** | Se leyó en inei.gob.pe y sus cifras coinciden; falta archivarlo con hash |
| A‑07 | **No se hizo la verificación opcional contra la web de Innovation Graph** | No verificable desde aquí. No se dio por aprobada |
| A‑04 | **No se hizo la conciliación opcional con `latam-country-breakdown-2026Q1.csv`** | No se recibió el archivo; `previous_t4e_value` queda vacío |
| B‑05 | **No se hizo el contraste opcional con valores anteriores de Think4ever para la capa B** | Sí se hizo el contraste con el agregado oficial (3/3 MATCH) |
| F‑21 | Plantilla `.xlsx` y JSON por capa | No se recibió la plantilla; las salidas están en CSV |
| — | Licencias de los microdatos del INEI | Solo se entregan agregados. Requiere verificación legal antes de publicar |

**Siguen vigentes los avisos de método:**
- Cuentas de GitHub ≠ personas.
- La encuesta de la capa B es autoseleccionada y su confianza es baja.
- Población ocupacional ≠ mercado potencial.
- Las capas no se suman, no se multiplican y no se combinan.
- Las personas 2, 4, 5 y 7 están suprimidas y la 9 es de baja precisión.

## 7. Verificación del ZIP

1. Extrae `think4ever_peru_day1_FINAL.zip`.
2. Desde la carpeta que contiene `think4ever_peru_day1_FINAL/`, ejecuta `sha256sum -c think4ever_peru_day1_FINAL/SHA256SUMS.txt`. Cada archivo de la carpeta debe dar OK, salvo el propio `SHA256SUMS.txt`.

El SHA‑256 del ZIP se entrega aparte, junto con el paquete, porque no puede estar dentro de él.
