# Perú Day 1: auditoría final de cierre (v2, cierre conjunto)

**Think4ever · Market Research & Analytics · LATAM** · 9 de octubre de 2026 · **Estado: FINAL**: autorizado por Think4ever el 9 de octubre de 2026, 19:06, hora de Bogotá (sección 6). Este informe se emitió cuando los paquetes estaban en DRAFT.

**Contexto**
- **v1 (12:41):** capa F apta para FINAL; Perú Day 1 apto con condiciones C1–C3.
- **Aprobado por Think4ever:** la capa F, metodológicamente.
- **v2 (este documento):** verifica que C1 y C2 se resolvieron, vuelve a auditar A, B y F, y emite la recomendación de cierre conjunto.

**Alcance:** no se amplió la investigación. No se cambiaron indicadores, personas, anillos, otros países ni la plataforma.

## 1. Recomendación de cierre

| Alcance | Dictamen v1 | **Dictamen v2** |
|---|---|---|
| Capa A (GitHub) | Sin paquete (hallazgo mayor A‑02) | **APTO PARA FINAL**: 10/10 controles de auditoría y 13 validaciones internas pasan (1 no verificable, opcional); limitaciones documentadas |
| Capa B (Stack Overflow) | Sin paquete (hallazgo mayor B‑03) | **APTO PARA FINAL**: 12/12 controles de auditoría y 12/12 validaciones internas pasan; `b_reproduction_check` coincide con el agregado oficial |
| Capa F (EPEN + F9 ENAHO) | APTO PARA FINAL | **APTO PARA FINAL**: 60/60 de nuevo; datos idénticos a la entrega anterior |
| **Perú Day 1 completo** | Apto con condiciones (C1–C3) | **APTO PARA FINAL**: C1, C2 y C3 resueltas; sin hallazgos críticos ni mayores abiertos |

**Bloqueos restantes: ninguno.** Las limitaciones que quedan (sección 4) están documentadas y no invalidan ningún resultado. Ninguna se resuelve con la información disponible hoy, y ninguna requiere inventar cifras. **En la v2, el paso a FINAL quedaba a la espera de autorización expresa. Think4ever la concedió el 9 de octubre de 2026, 19:06, hora de Bogotá (sección 6).**

## 2. Controles ejecutados en esta ronda

| Control | Script o evidencia | Resultado |
|---|---|---|
| Auditoría de los paquetes A y B | `audit/audit_closure_ab_pe.py` → `audit/audit_layer_ab_checks_pe.csv` | **22/22 PASS** |
| Auditoría de la capa F (repetida) | `audit/audit_closure_layer_f_pe.py` → `audit/audit_layer_f_checks_pe.csv` | **60/60 PASS** |
| Validaciones internas del paquete A | `layerA/.../validation/a_validation_checks_pe.csv` y `a_reproduction_check_pe.csv` | 13 PASS y 1 NO VERIFICABLE (comparación con la web de Innovation Graph) |
| Validaciones internas del paquete B | `layerB/.../validation/b_validation_checks_pe.csv` | 12/12 PASS |
| Contraste B con el agregado oficial | `layerB/.../data/b_reproduction_check_pe.csv` | B1 78,496 % frente a 78,483 %; B2 47,103 % frente a 47,086 %; B3 30,938 % frente a 30,931 %: **MATCH** |
| Cruce de B con el paquete FINAL de Argentina | Mismo archivo y mismo motor | GLOBAL, BR, MX, CO, CL y AR: 158/158 filas idénticas por grupo |
| Re‑ejecución de los motores A y B desde las fuentes | Innovation Graph 078fb62; `results.csv` 2d1f6530… | 5/5 (A) y 3/3 (B) archivos idénticos byte a byte |
| Cambios no autorizados en A y B | Valores del paquete frente a las salidas del 8 de octubre, celda por celda | 0 celdas distintas en 1.978 filas (A: 232; B: 1.746). Solo se agregaron metadatos y se renombró `vs_latam_ex_pe` → `vs_regional_ex_focus`, con los valores sin cambios |
| Cambios no autorizados en F | Archivos de `data/`, `validation/` y `scripts/` frente al zip entregado antes | 34/34 idénticos |
| Valores aprobados | A1 907.052; A3 1.144.909; B1 52/59, B2 37/59, B3 25/57; Core 144.961,4; Adjacent 146.415,1; Extended 376.436,5; 13 personas 667.813,0 | Todos iguales |
| Hashes de las fuentes | Registros de las capas A, B y F frente a los archivos recibidos | A 8/8, B 2/2, F 17/17 |
| Integridad del paquete integral | `SHA256SUMS.txt` y `manifest_peru_day1.csv` | Verificado (sección 5) |

## 3. Matriz de auditoría (actualizada)

| # | Componente | Control | Evidencia | Resultado | Severidad | Acción | Impacto en el cierre |
|---|---|---|---|---|---|---|---|
| **A‑02** | Paquete entregable de la capa A | Completitud (README, registro, diccionario, tablas, metodología, limitaciones, reproducción) | 11/11 componentes; 50 columnas documentadas; manifiesto y hashes verificados | **Aprobado (C1 resuelta)** | — | — | Ninguno |
| A‑01 | Reproducibilidad de A | Re‑ejecución y comparación de valores | Byte a byte; 0 celdas distintas; el método reproduce los FINAL de Argentina (25/25) y Chile (19/19) | Aprobado | — | — | Ninguno |
| A‑03 | A4 y A5 | Marca de provisional | `canonical_status = undetermined` en todas las filas de A4 y A5; documentado en el README | Observación | LC | Decisiones D‑03 y D‑04 de Think4ever | Ninguno |
| A‑04 | Conciliación interna | `latam-country-breakdown-2026Q1.csv` | No se recibió; `previous_t4e_value` queda vacío | No verificable | LC | Entregar el archivo si se quiere conciliar | Ninguno |
| A‑05 | Base débil de A3 | Documentación | El README muestra la serie: pushes por cuenta en el 1.er trimestre de 0,97, 0,85 y **0,79 en 2025** (mínimo de la serie) | Aprobado | — | — | Ninguno |
| A‑06 | Cuentas ≠ personas | Documentación | Explícito en el README (IP, cuentas inactivas o múltiples) | Aprobado | — | — | Ninguno |
| A‑07 | Comparación con la web de Innovation Graph | Control de la plantilla | La web no es accesible desde aquí; el repositorio es la fuente publicada | No verificable | LC | Opcional: revisión manual | Ninguno |
| **B‑03** | Paquete entregable de la capa B | Completitud | 12/12 componentes; 90 columnas documentadas | **Aprobado (C2 resuelta)** | — | — | Ninguno |
| **B‑04** | Convención de columnas | Renombre | `vs_regional_ex_focus` igual a la antigua `vs_latam_ex_pe` en las 1.422 filas | **Aprobado (resuelto)** | — | — | Ninguno |
| **B‑05** | Contraste con cifra publicada | `b_reproduction_check` | 3/3 MATCH con `ai.json`; 6 grupos idénticos a Argentina; valores previos de Perú no disponibles | **Aprobado (resuelto)** | — | — | Ninguno |
| B‑02 | Supresión | Celdas con n < 30 | 89 suprimidas (86 de Perú), 0 con valor; marcas según 50/30 | Aprobado | — | — | Ninguno |
| B‑06 | Muestra | n de Perú | 64 (46 profesionales); confianza baja; autoseleccionada | Observación | LC | Documentado | Ninguno |
| F‑01 a F‑25 | Capa F completa | 60 controles de la v1, repetidos | 60/60; datos idénticos a la entrega anterior; reproducción 18/18 (v1) | Aprobado | — | — | Ninguno |
| F‑12 | Varianza de EPEN | Robustez | 0/34 grupos cambian de estado con UPM sin estratos | Observación | LC | Documentado | Ninguno |
| F‑14, F‑15, F‑16 | V3, V4, V5 | Revisión documental | Diccionario anual EPEN y PDF del informe EPEN pendientes; F10 no disponible | Observación | LC | Ver sección 4 | **No bloquean** |
| F‑21 | Formato de la plantilla | Libro .xlsx y JSON por capa | El libro de la plantilla nunca se recibió; salidas en CSV (convención de Argentina) | Observación | Menor | Entregar la plantilla si se requiere la carga en ese formato | No bloquea la investigación |
| J‑01 | Alcance geográfico | Filtros | A: `PE`; B: Country = "Peru"; F: Perú nacional | Aprobado | — | — | Ninguno |
| J‑02 | Periodos | Documentación | A: 2026T1 frente a 2025T1; B: encuesta 2025; F: promedio 2025 (EPEN) y año 2025 (ENAHO). Cada README lo indica; el resumen ejecutivo los separa | **Aprobado (C3)** | — | — | Ninguno |
| J‑03 | Combinaciones inválidas | Revisión de todos los documentos | Ninguna suma ni producto entre capas; la prohibición está escrita en A, B y F | Aprobado | — | — | Ninguno |
| J‑04 | Conceptos | Revisión | Actividad en GitHub (A), encuestados (B), población ocupacional (F), perfil socioeconómico (F9): todos definidos; el mercado potencial no se estima | Aprobado | — | — | Ninguno |
| J‑05 | Clientes potenciales | Revisión | Ninguna cifra se presenta como clientes o mercado de Think4ever | Aprobado | — | — | Ninguno |

## 4. Pendientes que no bloquean (limitaciones documentadas)

| # | Pendiente | Tipo | Por qué no bloquea | Cómo cerrarlo, si se quiere |
|---|---|---|---|---|
| V3 | Diccionario de la base anual EPEN 2025 | LC | Las variables se validaron con 24 controles contra el INEI | Descargarlo del portal de microdatos del INEI |
| V4 | PDF del informe técnico EPEN anual 2025 | LC | Se leyó directamente en inei.gob.pe y todas sus cifras coinciden | Adjuntar el PDF para archivarlo con hash |
| V5 | F10, trabajo desde casa (C318A) | LC | F10 se declara no disponible; no hay estimación | Solicitud al INEI (Ley 27806) |
| D‑03 / D‑04 | Definición de A5 y umbral de A4 | LC | Publicados como provisionales | Decisión de Think4ever |
| REQ | `latam-country-breakdown-2026Q1.csv` | LC | Solo sirve para conciliar | Entregar el archivo |
| REQ | Valores anteriores de Think4ever para la capa B de Perú | LC | Opcional; se hizo el contraste con la cifra oficial | — |
| F‑21 | Plantilla `think4ever-country-template.xlsx` y JSON por capa | Menor | Se requiere para cargar en ese formato, no para la investigación | Entregar la plantilla |
| — | Licencias de los microdatos del INEI | LC | Solo se entregan agregados | Verificación legal, si se publica |

**No faltan archivos indispensables para ninguna verificación del cierre.** Los tres controles marcados como no verificables o no disponibles (la web de Innovation Graph, la tabla interna de LATAM y los valores previos de B) son de conciliación opcional. No se dieron por aprobados.

## 5. Paquete integral

- **Contenido:** `think4ever_peru_day1_FINAL.zip` (antes `think4ever_peru_day1_DRAFT.zip`) con `layerA/`, `layerB/` y `layerF/` (los tres paquetes completos), el resumen ejecutivo, este informe, `audit/` (scripts y resultados de auditoría), `manifest_peru_day1.csv` y `SHA256SUMS.txt`.
- **Sin datos sensibles:** ningún paquete contiene microdatos, identificadores de encuestados ni archivos fuente oficiales (controles A5, B5 y F‑23).


## 6. Cierre FINAL (9 de octubre de 2026, 19:06, hora de Bogotá)

- **Autorización:** Think4ever aceptó el dictamen de esta auditoría (v2) y autorizó el cierre de Perú Day 1 y de sus capas A, B y F como **FINAL**.
- **Alcance:** es un cierre documental y metodológico. **No aprueba** estimaciones de mercado potencial ni recomendaciones comerciales.
- **Qué se cambió:** solo estados y documentación. El detalle está en `Peru_Day1_Informe_Cierre_FINAL.md` y en `audit/draft_to_final_change_control_pe.csv`.
- **Qué no se cambió:** resultados, indicadores, personas, anillos, reglas de supresión ni decisiones metodológicas.
- **Contexto histórico:** las secciones 1 a 5 se escribieron cuando los paquetes estaban en DRAFT. Sus menciones a DRAFT describen esa etapa.
- **Limitaciones:** las de la sección 4 se mantienen sin cambios.
