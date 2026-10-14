# Perú Day 1, capa F: auditoría de ENAHO 2025 y resultados de F9

**Think4ever · Market Research & Analytics · LATAM** · 9 de octubre de 2026 · Revisión 3 (12:40) · **V1 validado contra el informe oficial del INEI · F9 aprobado (D‑PE‑10b)** · **Capa F: FINAL** (autorizada el 9 de octubre de 2026, 19:06, hora de Bogotá). No está cargada en la plataforma.

> **Tres conceptos distintos que no deben confundirse:**
> 1. **Población ocupacional (F1, EPEN):** cuántas personas ocupadas tienen como ocupación principal la de cada grupo.
> 2. **Perfil socioeconómico (F9, ENAHO):** cómo se distribuyen esas ocupaciones según el ingreso real per cápita de su hogar o el estrato de su conglomerado. Son porcentajes dentro de cada grupo, no conteos.
> 3. **Mercado potencial de Think4ever:** **no se estima en esta capa.** Ninguna cifra de este documento representa usuarios, compradores, TAM, SAM ni SOM.

**Alcance.** Este documento audita los módulos 05 y 34 de ENAHO 2025 y calcula F9 (nivel socioeconómico).
- **ENAHO se mantiene separada de EPEN:** no se combinan sus factores de expansión ni se aplican porcentajes de ENAHO a los totales de EPEN.
- **No se modificaron** las capas A y B, otros países ni la plataforma.
- Todas las cifras son **población ocupacional**, no usuarios potenciales ni confirmados.

## 1. Resumen

| Aspecto | Conclusión |
|---|---|
| Archivos | Los dos ZIP están íntegros (`1031-Modulo05` y `1031-Modulo34`). Traen documentación oficial completa: diccionario 2025, ficha técnica, cuestionario del módulo 500, estratificación del marco, tabla CNO 2015 y el **do‑file oficial del INEI** para el ingreso real |
| Clasificador | El diccionario rotula `P505R4` como **"revisión CNO‑2015"**. El 100 % de los códigos de los ocupados son válidos en la tabla CNO 2015 del INEI, que tiene los mismos 473 códigos que el PDF ya usado. Se aplicó **la misma correspondencia** que en EPEN |
| Sumaria a usar | **`Sumaria-2025.csv` (8 grupos de gasto)**: el do‑file oficial del INEI usa variables que solo existen en esa versión. Las variables de ingreso del hogar son idénticas en las dos versiones (diferencia máxima de S/ 0,008) |
| Ingreso per cápita | Real y mensual, a precios de Lima (`ipcr_0`), replicado según la fórmula oficial: componentes / (12 × miembros × `ld` × `i00`). Se pondera por personas (`FACTOR07` × `MIEPERHO`) |
| Controles contra el INEI | **Contra el anexo oficial del INEI (21 de 21 cifras):** el ingreso real per cápita en los 13 ámbitos del cuadro I.17, la pobreza y la pobreza extrema (nacional, urbana y rural) y el gasto real per cápita se reproducen a ≤ 0,001 (gasto: 0,03). Nacional: **S/ 1.252,345, igual que la cifra oficial**. Controles adicionales tomados de la prensa: vulnerabilidad 32,75 % (32,8 %) y pobres extremos 1.621 mil (1.614 mil) |
| F9 | Calculado para 9 personas, los 3 anillos y el total de las 13. Las personas 2, 4, 7 y 9 se suprimen por muestra insuficiente. Las celdas Q1 y Q2 se suprimen casi siempre (CV > 30 %) |
| F10 | **No disponible en ENAHO 2025.** El cuestionario 2025 solo pregunta si el lugar de trabajo está en el mismo distrito (`P558D2`), no si se trabaja desde casa |
| Hallazgo clave | **Diseñadores (persona 5):** EPEN los codifica en CNO 3432 y ENAHO en 2163/2166. La suma de los tres códigos coincide en ambas encuestas (65,5 mil frente a 65,7 mil). Se resolvió con un grupo informativo (D‑PE‑09) |
| Varianza | **Alineada con el INEI (D‑PE‑12):** UPM = `CONGLOME`, sin estratos. Reproduce los errores estándar oficiales del cuadro I.17 a 1,000–1,048 veces (ver sección 5) |

## 2. Auditoría

### 2.1 Archivos (SHA‑256 en `source_registry_layer_f_pe.csv`)

| Archivo | Contenido |
|---|---|
| `Enaho01a-2025-500.csv` | 84.853 personas de 14 años y más, de enero a diciembre (6.884–7.465 por mes), sin personas duplicadas y sin factores vacíos |
| `Sumaria-2025.csv` / `Sumaria-2025-12g.csv` | 33.702 hogares, sin duplicados. La versión 12g tiene otra desagregación del gasto |
| `Diccionario_2025.pdf` (381 págs.), `FichaTecnica.pdf` (33 págs.), `CED-01A-500-2025.pdf`, `Estratificacion_del_Marco.pdf`, `ENAHO-TABLA-CNO-2015.csv` | Documentación oficial |
| `ConstVarGasto-Metodologia actualizada_2025.zip` | Do‑file oficial y deflactores: `i00` = 1 en todos los departamentos para 2025 (año base); `ld` espacial entre 0,733 y 1,000 según dominio |

### 2.2 Diseño y factores
- **Muestra:** 36.594 viviendas (24.234 urbanas y 12.360 rurales) en 5.359 conglomerados, de las cuales 12.096 son de panel.
- **Inferencia anual:** nacional, urbano/rural, 24 departamentos, costa/sierra/selva por área, y Lima Metropolitana y Callao.
- **Panel:** el panel de ENAHO es entre años. Dentro de 2025 cada persona aparece una sola vez (registros = personas únicas).
- **Factores:**
  - Personas (empleo): `FAC500A`, "Factor de Expansión de Empleo/Ingresos".
  - Hogar: `FACTOR07`.
  - Población: `FACTOR07` × `MIEPERHO`, redondeado como en el do‑file.
- **Varianza:** linealización de Taylor con UPM = `CONGLOME` y **sin estratos**, alineada con el INEI (D‑PE‑12; sección 5). En total, 5.356 UPM con ocupados. La especificación con estratos departamento × `ESTRATO` se conserva como sensibilidad (`se_ratio_stratified_vs_main`).
  - Este esquema de estratos replica el que se usó con EPEN. El do‑file del INEI solo declara la UPM; añadir estratos suele reducir algo los errores estándar.

### 2.3 Universo y diferencias con EPEN
- **Universo:** residentes habituales (`P204` = 1 y `P205` = 2, o `P204` = 2 y `P206` = 1) ocupados (`OCU500` = 1). Son **56.914 registros y 18.153,3 mil ocupados**. Los 56.914 se enlazan con la Sumaria.
- **Diagnóstico frente a EPEN:** ENAHO estima **3,3 % más ocupados** que EPEN (17.575,2 mil). Son encuestas distintas, y EPEN sigue siendo la fuente oficial de F1.
- **`OCU500` = 0** (173 registros) no está documentado y queda fuera del universo.

### 2.4 Clasificación ocupacional y personas
- `P505R4` es CNO 2015 a 4 dígitos (según el diccionario y comprobado contra la tabla oficial). Se aplicaron **exactamente** los mismos códigos por persona, las mismas exclusiones (1499, 2312, 3313) y la misma composición de los anillos que en EPEN.
- **F1 de ENAHO, solo como diagnóstico** (`f1_enaho_diagnostic_pe.csv`):

| Persona | ENAHO (registros) | ENAHO | EPEN | ENAHO / EPEN |
|---|---|---|---|---|
| 1 Desarrolladores | 119 | 60.991 | 67.761 | 0,90 |
| 3 Técnicos TIC | 143 | 77.314 | 75.298 | 1,03 |
| 5 Diseñadores | 123 | 60.305 | suprimido (9 reg.) | — |
| 6 Analistas de gestión | 146 | 61.314 | 85.893 | 0,71 |
| 8 Datos e investigación | 67 | 28.519 | 50.235 | 0,57 |
| 10 Contadores | 241 | 97.922 | 94.590 | 1,04 |
| 11 Ingenieros | 325 | 124.655 | 169.564 | 0,74 |
| 12 Gerentes | 122 | 33.713 | 51.749 | 0,65 |
| 13 Educadores | 180 | 48.520 | 60.534 | 0,80 |
| Anillo Core | 264 | 140.496 | 144.961 | 0,97 |
| Las 13 personas | 1.488 | 606.019 | 667.813 | 0,91 |

**Lectura.**
- **Coherentes:** los anillos Core y Adjacent, el total de las 13 y las personas 1, 3, 10 y 13 (los IC 95 % se solapan).
- **Diferencias mayores que las que explica el muestreo:** las personas **8, 11 y 12** y el anillo **Extended** (los IC no se solapan). La persona 6 queda en el límite (los IC apenas se tocan).
- La diferencia apunta a **prácticas de codificación distintas** entre los equipos de EPEN y ENAHO, aunque usen el mismo CNO 2015.
- El caso más claro son los diseñadores (persona 5): 2163 + 2166 + 3432 suman 65,5 mil en ENAHO y 65,7 mil en EPEN, pero repartidos en códigos distintos.
- **No se modificó ninguna cifra de EPEN.** La decisión queda abierta como D‑PE‑09.

## 3. F9: nivel socioeconómico (ENAHO 2025)

**Definiciones**
- **F9a. Quintil nacional de ingreso real per cápita del hogar.**
  - Los quintiles son de **población** (cada uno contiene el 20,0 % de las personas).
  - Puntos de corte en S/ por mes, a precios de Lima: **529,79 / 796,38 / 1.128,62 / 1.708,93**.
  - Para cada grupo se calcula el porcentaje de sus ocupados que vive en hogares de cada quintil (ponderado con `FAC500A`).
- **F9b. Estrato socioeconómico (`ESTRSOCIAL`).**
  - Estrato del conglomerado, asignado por el INEI a partir de indicadores censales de vivienda (método SISFOH): A = alto, B, C, D y E = bajo; y rural.
  - Es una medida **del área, no del hogar**. Por eso es complementaria y no sustituye al quintil.

**Reglas de precisión (D‑PE‑03)**
- Se suprime el grupo completo si tiene menos de 30 personas o si su total tiene un CV mayor a 30 %.
- Se suprime la celda si su CV es mayor a 30 %.
- Se marca con \* la baja precisión (CV de 15–30 %).

**Resultados.** Porcentaje (IC 95 %):

| Grupo | Registros | Quintil 5 | Quintiles 4–5 | Quintil 3 | Estrato A | Estrato B | Estrato E |
|---|---|---|---|---|---|---|---|
| P1 Desarrolladores | 119 | 72,3 (61–83) | 81,9 (72–92) | 16,6 (7–26)\* | — | 10,8 (5–17)\* | 24,9 (14–36)\* |
| P3 Técnicos TIC | 143 | 48,5 (38–59) | 74,1 (64–84) | 15,2 (7–24)\* | — | 10,7 (4–17)\* | 22,8 (13–32)\* |
| P5 Diseñadores (ENAHO) | 123 | 49,1 (36–62) | 77,0 (66–89) | — | — | 15,9 (8–24)\* | 20,2 (10–30)\* |
| P6 Analistas de gestión | 146 | 68,4 (56–81) | 91,9 (84–99) | — | — | 16,1 (7–25)\* | 27,0 (14–40)\* |
| P8 Datos e investigación | 67 | 77,8 (64–92) | 84,4 (70–98) | — | — | — | — |
| P10 Contadores | 241 | 78,3 (70–87) | 90,0 (84–96) | — | 6,2 (3–9)\* | 10,0 (6–14)\* | 15,0 (9–21)\* |
| P11 Ingenieros | 325 | 75,0 (68–82) | 93,7 (90–97) | — | 5,7 (3–8)\* | 10,8 (7–15)\* | 27,0 (20–35) |
| P12 Gerentes | 122 | 96,7 (94–100) | 99,9 | — | — | — | 28,2 (16–40)\* |
| P13 Educadores | 180 | 83,3 (75–91) | 94,4 (90–98) | — | — | 18,1 (9–27)\* | 26,6 (16–38)\* |
| Personas 1+2 | 121 | 73,2 (63–84) | 82,5 (73–92) | 16,0 (7–25)\* | — | 11,1 (5–17)\* | 24,0 (14–35)\* |
| Anillo Core | 264 | 59,6 (52–67) | 77,9 (71–85) | 15,6 (9–22)\* | 3,5 (2–6)\* | 10,9 (6–16)\* | 23,4 (16–31)\* |
| Anillo Adjacent | 356 | 63,5 (56–71) | 84,7 (79–91) | 9,2 (4–14)\* | 5,8 (3–9)\* | 13,7 (9–19)\* | 22,3 (15–29)\* |
| Anillo Extended | 868 | 79,8 (76–84) | 93,3 (91–96) | 5,3 (3–8)\* | 6,1 (4–8)\* | 11,0 (8–14) | 23,2 (19–28) |
| Las 13 personas | 1.488 | 70,8 (67–74) | 87,4 (85–90) | 8,7 (6–11) | 5,4 (4–7)\* | 11,7 (9–15) | 23,0 (19–27) |
| **Todos los ocupados** | 56.914 | 25,3 (24–26) | 47,5 (46–49) | 19,9 (19–21) | 0,9 | 2,8 | 37,0 |

- **Suprimidos (grupo completo):** personas 2, 4, 7 y 9, el código informativo 3432 y el escenario restringido de la persona 8 (40 registros en ENAHO).
- **Confianza (plantilla):**
  - Baja (menos de 300 registros) en todas las personas, salvo la 11 (325, media).
  - Media en los anillos Core (264) y Adjacent (356).
  - Alta en el anillo Extended (868) y en el total de las 13 personas (1.488).
- **La persona 8 en ENAHO** tiene una composición distinta a la de EPEN: CNO 3317 suma 12,5 mil en ENAHO frente a 20,5 mil en EPEN, y los profesionales (2120, 2631, 2632) 14,3 mil frente a 29,0 mil. Su F9 describe la categoría tal como la codifica ENAHO.

**Lectura.** Unos 7 de cada 10 ocupados de las 13 personas viven en hogares del quintil más alto de ingreso per cápita, frente a 1 de cada 4 en el total de ocupados. El anillo Core está algo menos concentrado en el quintil 5 (60 %) que el Extended (80 %), por los técnicos TIC (49 %). `ESTRSOCIAL` discrimina poco: incluso en las personas profesionales, cerca de un cuarto vive en conglomerados del estrato E. Por eso se usa solo como indicador complementario.

## 4. Grupo informativo de diseñadores (D‑PE‑09, opción B aprobada)

**Qué es y qué no.** Es un grupo adicional formado por los códigos CNO 2163, 2166 y 3432, calculado por separado en EPEN y en ENAHO.
- **No forma parte** de las 13 personas ni de los anillos, y **no se suma** a ningún total de anillo.
- **La persona 5 no cambia:** en EPEN sigue suprimida, y la estimación de ENAHO (60.305) se mantiene como resultado separado de esa encuesta.
- Tabla: `data/f_designers_informational_pe.csv`.

**Definiciones del CNO 2015 y sus diferencias**

| Código | Nivel | Definición resumida (CNO 2015) | Ocupaciones listadas |
|---|---|---|---|
| 2163 Diseñadores de productos y de prendas | Profesional (gran grupo 2) | Diseñan y desarrollan productos para su manufactura y preparan especificaciones para producción al por mayor | Diseñador de joyas, de moda, de muebles, industrial, de prendas y de vestimenta |
| 2166 Diseñadores gráficos y multimedia | Profesional (gran grupo 2) | Crean contenidos visuales y de audio para publicaciones, medios digitales, animación y publicidad | Animador gráfico, artista digital, diseñador multimedia, diseñador gráfico, ilustrador gráfico |
| 3432 Diseñadores y decoradores | Técnico (gran grupo 3) | Planean y diseñan interiores y también productos industriales u objetos, y participan en el acabado | Decorador de interiores, escaparatista, diseñador de envases, de alfombras, de telas, de moda, de joyas, de muebles, industrial, heraldista, **tatuador** |

**Diferencias que importan**
1. **Nivel de competencias:** 2163 y 2166 son profesionales; 3432 es de nivel técnico.
2. **Títulos repetidos dentro del propio CNO 2015:** "diseñador de moda", "de joyas", "de muebles" e "industrial" aparecen tanto en 2163 como en 3432. El clasificador deja margen para que cada equipo codifique distinto.
3. **3432 no menciona a los diseñadores gráficos**, pero incluye ocupaciones ajenas al diseño digital (decoradores, escaparatistas, tatuadores). Por eso el grupo informativo es **más amplio que la persona 5**.
4. **La práctica de codificación difiere entre encuestas y es verificable en los datos:**
   - **En EPEN**, el 100 % de los registros en 2163/2166 tiene título universitario, frente al 19,8 % en 3432. EPEN reserva los códigos profesionales para graduados y codifica al resto como 3432.
   - **En ENAHO**, los diseñadores se codifican como 2166 sin importar el nivel educativo: de 102 registros, solo 22 tienen superior universitaria completa o posgrado, y 46 tienen superior no universitaria completa.

**Estimaciones 2025 (cada encuesta por separado; nunca se combinan)**

| Grupo | Fuente | Registros (personas) | Ocupados | CV | IC 95 % | Estado |
|---|---|---|---|---|---|---|
| CNO 2163 | EPEN | 3 (3) | — | 60 % | — | suprimido |
| CNO 2163 | ENAHO | 21 (21) | — | — | — | suprimido |
| CNO 2166 | EPEN | 6 (6) | — | 49 % | — | suprimido |
| CNO 2166 | ENAHO | 102 (102) | 48.574 | 14,6 % | 34.642–62.506 | publicable (ENAHO) |
| CNO 3432 | EPEN | 507 (425) | 63.189 | 7,4 % | 54.024–72.354 | publicable |
| CNO 3432 | ENAHO | 13 (13) | — | — | — | suprimido |
| **Grupo 2163+2166+3432** | **EPEN** | 516 (434) | **65.706** | 7,3 % | 56.369–75.042 | publicable, informativo |
| **Grupo 2163+2166+3432** | **ENAHO** | 136 (136) | **65.525** | 12,4 % | 49.564–81.486 | publicable, informativo |
| Persona 5 (2163+2166) | EPEN | 9 (9) | — | 38 % | — | **suprimido (sin cambios)** |
| Persona 5 (2163+2166) | ENAHO | 123 (123) | 60.305 | 13,2 % | 44.663–75.947 | resultado separado de ENAHO |

**Lectura.** Las dos encuestas coinciden en el tamaño del grupo amplio (unos 65,5–65,7 mil, con IC que se solapan casi por completo). Difieren en **cómo** reparten a esas personas entre los tres códigos. Las dos cifras del grupo describen ocupaciones de diseño en sentido amplio, incluidos técnicos y decoradores. No son la persona 5 ni el mercado potencial.

**F9 del grupo (ENAHO):** quintil 5: 49,0 % (CV 12,6 %); quintiles 4–5: 77,4 %; quintil 4: 28,4 %\*. Estratos B, C, D y E solo con baja precisión.

## 5. Validación contra el informe oficial del INEI (V1) y especificación de la varianza

**Documentos oficiales registrados** (en `source_registry_layer_f_pe.csv`):
- **Informe técnico:** INEI, *Perú: Evolución de la Pobreza Monetaria, 2016‑2025* (425 págs.; PDF creado el 4 de mayo de 2026 y modificado el 5 de mayo de 2026; gob.pe 8088591). SHA‑256 `475cc9c6…de9c`.
  - Sección 2.2: "el ingreso real promedio per cápita mensual se situó en 1 252 soles".
  - El gasto real per cápita es de 920 soles.
  - El capítulo 9.2 describe la muestra como "estratificada, bietápica e independiente en cada departamento", pero **no especifica los estratos que se usan para calcular la varianza**.
- **Anexo estadístico en Excel** (ZIP, SHA‑256 `d17ba9bd…06c4`), con cinco libros que tienen sus propios hashes. Se usaron el cuadro I.17 (ingreso: indicador, error estándar, mínimo y máximo), el III.1 (pobreza), el III.4 (pobreza extrema) y el I.1 (gasto).

**V1. Ingreso real per cápita 2025 (cuadro I.17, nacional)**

| | INEI oficial | Think4ever (ENAHO 2025) | Diferencia |
|---|---|---|---|
| Media (S/ al mes, precios de Lima) | **1.252,345** | **1.252,345** | 0,0002 |
| Error estándar | 12,083 | 12,325 (UPM, sin estratos; especificación final) | +2,0 % |
| | | 11,600 (UPM + departamento × `ESTRATO`; especificación anterior) | −4,0 % |
| IC 95 % | 1.228,661 – 1.276,029 | 1.228,188 – 1.276,503 (final) | Casi idéntico |
| | | 1.229,6 – 1.275,1 (anterior) | 4 % más estrecho |

**El resto del anexo** (`validation/enaho_vs_inei_official_validation_pe.csv`, generado con `scripts/validate_enaho_vs_inei_official_pe.py`):
- **Medias del cuadro I.17 en los 13 ámbitos** (nacional, urbano, rural, costa, sierra, selva, sus partes urbana y rural, y Lima Metropolitana): todas iguales a las oficiales, con una diferencia máxima de S/ 0,0005.
- **Pobreza (III.1):** 25,66658 % (nacional), 23,41272 % (urbana) y 35,45473 % (rural). Idénticas a las oficiales.
- **Pobreza extrema (III.4):** 4,651361 %, 3,094793 % y 11,41128 %. Idénticas a las oficiales.
- **Gasto real per cápita (I.1):** 920,40 frente a 920,43 oficial.

**V2. Especificación de la varianza**
- **Hallazgo:** al comparar con los 13 errores estándar oficiales del cuadro I.17, la especificación anterior (estratos departamento × `ESTRATO`) daba errores **de 0,883 a 1,000 veces los oficiales** (mediana 0,954). Es decir, intervalos hasta 12 % más estrechos (Selva rural). En cambio, **UPM = `CONGLOME` sin estratos** (la convención del do‑file del INEI) reproduce los errores oficiales a **1,000–1,048 veces** (mediana 1,008).
- **Otras especificaciones probadas**, sin replicación exacta:
  - estratos `DOMINIO`: 12,03 en el total nacional;
  - UPM = `NCONGLOME` (conglomerado del marco): 12,33;
  - factor sin redondear: diferencia de 0,0002.
- **Decisión D‑PE‑12 (aplicada):** ENAHO usa **UPM = `CONGLOME` sin estratos**, alineada con el INEI y algo más conservadora. La especificación con estratos se conserva como sensibilidad.
- **Efecto:**
  - **ninguna** celda cambia de estado: 0 de 300 celdas de F9 y 0 de 25 grupos del F1 diagnóstico;
  - las estimaciones puntuales son idénticas;
  - los CV de los grupos aumentan ligeramente (por ejemplo, persona 1: de 12,4 % a 12,6 %; total de las 13: de 4,2 % a 4,6 %).
- **EPEN** mantiene departamento × `ESTRATO` porque no hay errores estándar oficiales del INEI con los cuales calibrarla. Queda documentado como limitación.
- **Anidamiento:** los 5.359 conglomerados pertenecen a un solo departamento y un solo `ESTRATO`.
- **Limitaciones:**
  - El INEI no publica su especificación exacta de varianza.
  - En el área rural la primera etapa de muestreo es el centro poblado o el AER, y la base pública identifica el conglomerado, como en el do‑file oficial.
  - No se aplica corrección por población finita.

**Conclusión:** la revisión documental **no revela discrepancias en las estimaciones**. La única diferencia, en el cálculo del error estándar, quedó corregida con D‑PE‑12. **V1 queda validado y F9 aprobado (D‑PE‑10b).** En ese momento la capa F seguía en DRAFT. Think4ever autorizó su cierre como FINAL el 9 de octubre de 2026, 19:06 (hora de Bogotá).

## 6. F6 y F10 con ENAHO
- **F6:** ENAHO trae UBIGEO de 6 dígitos y `P558D2` (distrito donde se trabaja), pero solo es representativa hasta departamento y región. Con 119 a 325 registros por persona no se justifican cortes geográficos más finos. **No incorporé F6 desde ENAHO;** la geografía sigue siendo la de EPEN (departamento).
- **F10:** **no disponible.** La única vía es solicitar al INEI la variable `C318A` de EPEN (REQ_INEI_EPEN_2025_C318A).

## 7. Reproducibilidad
1. `scripts/enaho_sumaria_quintiles_pe.py <Sumaria-2025.csv> <deflactores_base2025_new.dta> <despacial_ldnew.dta> <out>`: calcula `ipcr_0`, los quintiles y los deciles, y ejecuta los controles de pobreza y gasto.
2. `scripts/layer_f_enaho_f9_pe.py <Enaho01a-2025-500.csv> <out>/hh_quintiles_LOCAL_ONLY.pkl <f_persona_estimates_internal_pe.csv> <ENAHO-TABLA-CNO-2015.csv> <out>`: calcula F9 y el F1 diagnóstico, con los mismos códigos que EPEN.
3. `scripts/build_layer_f_deliverables_pe.py <epen_out> <entrega>/data <enaho_out>`: arma el paquete.

El archivo de hogares con quintiles (`hh_quintiles_LOCAL_ONLY.pkl`) es microdato y **no** se incluye.

## 8. Pendientes y decisiones

| ID | Tema | Estado |
|---|---|---|
| D‑PE‑07 | Usar la Sumaria de 8 grupos | Aplicada (técnica) |
| D‑PE‑08 | F9 desde ENAHO como fuente separada; F1 de ENAHO solo como diagnóstico | Aplicada; pendiente de la validación final |
| D‑PE‑09 | Diseñadores: grupo informativo 2163 + 2166 + 3432 en ambas encuestas, fuera de los anillos (opción B) | **Aprobada como análisis informativo y aplicada** (sección 4) |
| D‑PE‑10 / 10b | F9 de ENAHO como fuente separada | **Aprobado** (tras validar V1) |
| D‑PE‑12 | Varianza de ENAHO alineada con el INEI (UPM sin estratos) | **Aplicada** |
| D‑PE‑11 | F6 = geografía de EPEN; F10 = pendiente de información oficial | **Aprobada** |
| V1 | Contraste del ingreso real per cápita con el informe oficial del INEI | **VALIDADO**: 1.252,345 en ambos; intervalos casi idénticos (sección 5) |
| REQ | `C318A` de EPEN para F10 | Abierta |
