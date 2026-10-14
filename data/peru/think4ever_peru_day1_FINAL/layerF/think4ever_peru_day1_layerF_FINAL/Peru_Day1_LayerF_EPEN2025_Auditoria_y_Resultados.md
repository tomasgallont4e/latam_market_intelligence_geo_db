# Perú Day 1, capa F (EPEN 2025): auditoría metodológica y resultados

**Think4ever · Market Research & Analytics · LATAM** · Preparado el 9 de octubre de 2026 · Revisión 4 (12:40): V1 validado contra el informe oficial del INEI; F9 aprobado; varianza de ENAHO alineada con el INEI (D‑PE‑12) · Estado: **FINAL** (autorizado el 9 de octubre de 2026, 19:06, hora de Bogotá). No está cargado en la plataforma.

**Alcance.** Este documento cubre solo la capa F de Perú. Las capas A y B no se modificaron. No se usó ningún dato de Argentina ni de Chile: de esos países solo se reutilizó la disciplina metodológica (clases de mapeo, supresión y control contra totales oficiales).

**Unidad de medida.** Todas las cifras son **población ocupacional**: personas ocupadas cuya ocupación principal pertenece a la persona. No son TAM, SAM ni SOM, ni clientes de Think4ever.

---

## Resumen

| Aspecto | Conclusión |
|---|---|
| Archivo | EPEN 2025, Departamentos, base **anual** enero–diciembre: 471.438 registros y 132 variables, los 12 meses y los 24 departamentos más el Callao |
| Factor de expansión | **`FAC300_ANUAL`** (no `FAC_T300`). Reproduce exactamente los totales oficiales del INEI (diferencia de 0,0003 % en ocupados) |
| Clasificador de ocupación | `C308_COD` es **CNO 2015 a 4 dígitos**. Verificado empíricamente: el 100 % de los 438 códigos observados son grupos primarios válidos del CNO 2015, incluidos códigos que solo existen en la versión peruana |
| Correspondencia con CIUO‑08 | Es oficial y de **4 dígitos** (anexos 3 y 4 del CNO 2015), no de 2 dígitos como en Argentina. Las 13 personas tienen mapeo explícito |
| Controles contra el INEI | **24 de 24 pasan**. Incluyen ocupados por sexo, por tamaño de empresa (1–10, 11–50, 51+) y por rama, desempleados, desempleo urbano y rural, e informalidad (70,2 %), todos tomados directamente del informe técnico anual 2025 del INEI |
| Personas estimables | **9 de 13** se publican (8 con confianza media o alta y 1 con baja precisión). **4 se suprimen** por tener muy pocos casos: 2 (bases de datos y redes), 4 (gerentes de TI), 5 (diseñadores) y 7 (analistas financieros) |
| Anillos sin doble conteo | Core 144.961 · Adjacent 146.415 · Extended 376.436 · las 13 personas suman **667.813** (3,80 % de los ocupados) |
| Brechas | F9 (nivel socioeconómico) y F10 (trabajo desde casa) no existen en la base pública de EPEN y requieren ENAHO 2025. F6 llega solo a departamento |

---

## Qué miden estas cifras

| Concepto | Fuente | Qué es | Qué no es |
|---|---|---|---|
| **Población ocupacional** (F1–F8, F11) | EPEN 2025 | Personas ocupadas cuya ocupación principal pertenece a cada grupo, con su perfil laboral | Usuarios, compradores ni demanda |
| **Perfil socioeconómico** (F9) | ENAHO 2025, por separado | Porcentaje de cada grupo según el quintil de ingreso real per cápita de su hogar y el estrato de su conglomerado | Un conteo de personas, ni algo aplicable a los totales de EPEN |
| **Mercado potencial de Think4ever** | — | **No se estima en la capa F** | — |

## Verificaciones pendientes para cerrar la capa F

| # | Verificación | Estado | Qué falta |
|---|---|---|---|
| V1 | Contrastar el ingreso real per cápita medio con el informe oficial del INEI de pobreza monetaria 2016‑2025 | **VALIDADO** | 1.252,345 frente a 1.252,345 (cuadro I.17). Error estándar 12,33 frente a 12,08; IC 1.228,2–1.276,5 frente a 1.228,7–1.276,0. Además, 13 ámbitos, pobreza, pobreza extrema y gasto reproducidos a ≤ 0,001 |
| V2 | Especificación de conglomerados y estratos de ENAHO | **Verificada y alineada con el INEI** (D‑PE‑12) | — (reproduce los errores estándar oficiales a 1,000–1,048 veces; ninguna celda cambia de estado) |
| V3 | Diccionario de la base anual EPEN 2025 | Pendiente (bajo impacto) | Descargarlo del INEI; las variables ya se validaron con 24 controles |
| V4 | Informe técnico anual EPEN 2025 en PDF, para archivarlo con hash | Pendiente (bajo impacto) | Ya se leyó directamente en inei.gob.pe |
| V5 | F10 (trabajo desde casa) | **Pendiente de información oficial** | Variable C318A de EPEN (no pública); ENAHO 2025 no la tiene. No se producen estimaciones |
| V6 | Aprobación definitiva de F9 (D‑PE‑10b) | **Aprobada** | — |
| V7 | Revisión final del paquete y cambio de DRAFT a FINAL | **Resuelto**: FINAL autorizado el 9 de octubre de 2026, 19:06 (hora de Bogotá) | — |

## A. Auditoría metodológica

### A.1 Archivos recibidos (hashes SHA‑256)

| Archivo | Contenido verificado | Hash |
|---|---|---|
| `1001-Modulo76.zip` → `EPEN 2025 BD_Publicacion Dpto.csv` | Base anual: `ANIO` = 2025 y `MES` del 01 al 12 (entre 36.252 y 40.493 registros por mes). `CCDD` con 24 códigos (no hay 07: el Callao está dentro de 15, que se separa con `DIVISION_LIMA`) | zip `eea0b593…`; csv `4e72f9e5…` |
| `Diccionario.zip` | Diccionario de variables del **4.º trimestre** (oct–dic 2025, publicado en febrero de 2026), **no el de la base anual**. No documenta `CCDD`, `FAC300_ANUAL` ni `Informal_P`. Documenta `CODCIUDAD`/`NOMCIUDAD` y `FAC_T300`, que **no están** en la base anual. **¿Existe una versión anual?** El INEI sí publica diccionarios anuales para EPEN Departamentos: el de 2022 está en `inei.gob.pe/media/DATOS_ABIERTOS/EPEN_DEP/DICCIONARIO/2022/Diccionario.pdf` y define `FAC300_ANUAL` como "Factor anual nacional de empleo" y `CCDD` como "Código del departamento". No pude acceder al de 2025 en la misma ruta (`…/2025/…`), así que queda como solicitud abierta (REQ_INEI_EPEN_2025_ANUAL_DIC) | zip `ad73fa71…` |
| `Ficha_Tecnica.zip` | Ficha técnica de EPEN 2025 (enero de 2025) | zip `36cf216f…` |
| CNO 2015 (PDF, 472 páginas) | Estructura de 4 niveles con 473 grupos primarios. Anexos 3 (CNO→CIUO) y 4 (CIUO→CNO) en las págs. 425–472 | `3624406d…` |

### A.2 Población y cobertura
- **Población objetivo:** residentes habituales de viviendas particulares, de 14 años y más, en los 24 departamentos y el Callao. Se excluyen viviendas colectivas (cuarteles, hospitales, etc.).
- **Diseño muestral:** estratificado, probabilístico, de áreas, bietápico e independiente en cada departamento. La unidad primaria (UPM) es el conglomerado, de unas 140 viviendas; la secundaria es un segmento compacto de 4 viviendas (8 en el área rural). Muestra de 142.084 viviendas.
- **Niveles de inferencia anual:** nacional, urbano, rural, departamento y ciudad.
- **Universo de este análisis:** personas ocupadas (`OCUP300` = 1) con `FAC300_ANUAL` no vacío. Son **193.008 registros, 131.035 personas únicas y 17.575.150 ocupados**.

**Limitaciones geográficas**
- La base pública anual trae solo `CCDD` (departamento), `AREA` y `DIVISION_LIMA`.
- **No trae UBIGEO** de provincia o distrito, ni `CODCIUDAD`. Por eso F6 llega a departamento más Lima Metropolitana y Callao, no a ciudad.

### A.3 Variable de ocupación y clasificador
- **Variable:** `C308_COD` ("308. Cuál es la ocupación principal que desempeñó – Código"), de 4 caracteres.
- **Ni el diccionario ni la ficha nombran el clasificador.** Lo verifiqué empíricamente:
  - Los 438 códigos distintos (el 100 % de los registros y del peso) son grupos primarios válidos del CNO 2015.
  - Entre ellos hay aperturas que solo existen en la versión peruana: 0111–0320 (Fuerzas Armadas y Policía), 1150, 1325, 1326, 1421, 1499 y 2515.
  - No puede tratarse del CO 1995, que solo tiene 3 niveles.
  - 1.473 registros traen 3 caracteres: son códigos de Fuerzas Armadas y Policía que perdieron el cero inicial (por ejemplo, 220 → 0220). Se completan con ceros.
- **Industria (`C309_COD`):** sus divisiones de 2 dígitos son coherentes con CIIU Rev.4 (hay 58–63 y no hay 40 ni 67). Tampoco está documentado; se completan los ceros a la izquierda.

### A.4 Relación CNO 2015 ↔ CIUO‑08
- El CNO 2015 es una **adaptación** de la CIUO‑08: usa la misma estructura, pero varios códigos de 4 dígitos **no coinciden** con los de la CIUO‑08 (detalle en la sección B).
- Los anexos 3 y 4 dan la correspondencia oficial con un indicador de enlace: 0 = absoluto, 1 = relativo.
- **Lectura de los anexos:**
  - La capa de texto del PDF contiene copias ocultas de páginas vecinas, así que extraerlo por geometría mezcla filas. Por eso las filas se leyeron en el orden del flujo de contenido.
  - Resultado: 531 pares en el Anexo 3 y 536 en el Anexo 4; los 473 códigos CNO y 431 códigos CIUO.
  - Verifiqué visualmente las páginas 428, 429, 430 y 453 contra la tabla extraída: coinciden.
  - Hay 55 pares cuyos indicadores de enlace difieren entre los dos anexos. Solo uno afecta a las personas: CNO 1499, que queda excluido.

### A.5 Factor de expansión
`FAC300_ANUAL` es el factor correcto para la base anual:

| Control | Microdatos | INEI | Diferencia |
|---|---|---|---|
| Ocupados 2025 | 17.575.150 | 17.575.200 | −0,0003 % |
| Ocupados urbanos | 14.287.017 | 14.287.000 | +0,0001 % |
| Ocupados rurales | 3.288.133 | 3.288.100 | +0,001 % |
| Ocupados T1 2025 (4 × suma del trimestre) | 17.373.978 | 17.374.000 | −0,0001 % |
| Ocupados T4 2025 (4 × suma del trimestre) | 17.834.763 | 17.834.800 | −0,0002 % |
| Desempleo abierto | 4,88 % | 4,9 % | redondeo |
| Desempleo, hombres / mujeres | 4,19 % / 5,73 % | 4,2 % / 5,7 % | redondeo |
| Ingreso promedio de Lima Metropolitana (`ingtrabw` > 0) | S/ 2.486,0 | S/ 2.486,0 | 0 |
| Hombres / mujeres ocupados | 9.751,5 / 7.823,7 mil | 9.751,5 / 7.823,7 mil | 0,0 % |
| Ocupados en empresas de 1–10 / 11–50 / 51+ (`C317A`) | 12.601,3 / 1.381,4 / 3.592,4 mil | 12.601,3 / 1.381,4 / 3.592,4 mil | 0,0 % |
| Ocupados por rama (agropecuaria, pesca y minería / manufactura / construcción / comercio / servicios; CIIU Rev.4) | 4.219,7 / 1.518,4 / 1.169,7 / 3.335,2 / 7.332,2 mil | iguales | 0,0 % |
| Desempleados | 902,1 mil | 902,1 mil | 0,0 % |
| Desempleo urbano / rural | 5,66 % / 1,37 % | 5,7 % / 1,4 % | redondeo |
| Informalidad (`Informal_P` = 1) | 70,16 % | 70,2 % | redondeo |

**Fuente principal de control.** INEI, *Perú: Comportamiento de los Indicadores del Mercado Laboral a Nivel Nacional y en 27 Ciudades*, enero–diciembre 2025 y IV trimestre 2025 (febrero de 2026), leído directamente en `inei.gob.pe/media/MenuRecursivo/boletines/01-informe-tecnico-empleo-nacional.pdf`.
- El documento no indica número de informe técnico.
- Desde este entorno no se puede descargar el PDF, así que no tiene hash. Para archivarlo con hash, hay que adjuntarlo.
- Las notas de Andina y El Peruano se mantienen solo como corroboración: siguen siendo la fuente del T4, del desempleo por sexo y del ingreso de Lima.
- Estos controles también validan las variables que usan F4 (`C317A`) y F5 (`C309_COD` en CIIU Rev.4).

Qué implica:
- El factor ya produce el **promedio anual**, así que no se divide ni se promedian trimestres.
- La base anual basta y **no se necesitan los archivos trimestrales**.
- `FAC_T300`, identificado en la investigación preliminar, no existe en esta base.

### A.6 Diseño, varianza y estructura de panel
- **Estimación de la varianza:**
  - Linealización de Taylor para totales y proporciones.
  - UPM = `CONGLOMERADO`, que no cruza estratos.
  - Estrato = departamento × `ESTRATO`, lo que respeta la independencia del diseño por departamento: 143 estratos.
  - Un estrato con una sola UPM (Ucayali, `ESTRATO` 6) se fusiona con el estrato 5 del mismo departamento.
  - No se aplica corrección por población finita.
  - **Estos coeficientes de variación los calcula Think4ever** a partir de las variables oficiales de diseño. El INEI no publica coeficientes de variación por ocupación.
- **Panel:**
  - La base trae las visitas de todo el año: 63.662 ocupados aparecen 2 o más veces, normalmente con 3 meses de diferencia.
  - El factor anual ya reparte el peso entre las visitas, de modo que las estimaciones puntuales no requieren ajuste.
  - Las visitas repetidas de una persona caen en la misma UPM, así que la varianza por UPM absorbe esa correlación.
  - Reporto **registros y personas únicas**. La persona única se identifica con conglomerado + vivienda + hogar + número de orden + sexo, porque `LLAVE_PANEL` cambia en 3.302 casos.
  - La confianza de la plantilla (F2) se calcula sobre personas únicas, que es lo más conservador.
  - Entre visitas, 26.833 personas cambian de código de ocupación (por cambio real o por variación en la codificación).
- **Registros sin factor:**
  - 14.399 ocupados (9.242 hogar‑mes, todos urbanos, sobre todo en Lima) tienen `FAC300_ANUAL` vacío.
  - Corresponden a hogares completos fuera de la ponderación anual. Lo más probable es que sean la submuestra de Lima para el trimestre móvil; no está documentado.
  - Se excluyen. Sin ellos el total coincide con el oficial.

### A.7 Valores faltantes y códigos especiales
- **Fuera del universo:** registros con `OCUP300` vacío (menores de 14 años y no residentes, `RESIDENT` 0 o 9) y con `OCUP300` de 2 a 4 (desempleados e inactivos).
- **`C311` (público o privado):** solo se pregunta a asalariados y practicantes (`C310` = 3, 7, 8). Su ausencia para el resto es estructural, no un faltante.
- **Ingreso (F8):** `INGTOTP` vale 0 para trabajadores familiares no remunerados y practicantes sin pago. La mediana se calcula sobre ingresos > 0.
- **Educación:** `C366` no tiene vacíos entre los ocupados.
- **Tamaño de empresa:** `C317A` (número exacto de trabajadores) no tiene vacíos entre los ocupados.
- **Sesgo de codificación:** el 99,1 % de los profesionales (gran grupo 2) tiene educación superior, y las personas 1, 6, 9 y 10 tienen un 100 % con título universitario. Esto indica que **la codificación del INEI usa el nivel educativo** para distinguir profesionales de técnicos. Así, F7 (porcentaje con título universitario) es en parte definitorio para las personas profesionales.

**Conclusión de la auditoría:** los archivos son adecuados y las estimaciones son representativas a nivel nacional en el sentido del diseño de EPEN. Se pasó a la etapa de cálculo.

---

## B. Tabla de correspondencias ocupacionales (13 personas)

Los nombres son los canónicos del Excel de personas; entre paréntesis, el alias de la plantilla. Los códigos CIUO‑08 vienen del Anexo 2 de la plantilla, y los códigos CNO 2015 salen de la correspondencia oficial del INEI.

| # | Persona (anillo) | CIUO‑08 de la plantilla | CNO 2015 usados | Clase de mapeo | Justificación y advertencias |
|---|---|---|---|---|---|
| 1 | Software developers and analysts (Core) | 2511, 2512, 2513, 2514, 2519 | 2511, 2512, 2513, 2519, 2521 | Exacto a 4 dígitos | Los números no coinciden: CNO 2512 = CIUO 2514 y CNO 2521 ("soporte de sistemas") = CIUO 2511 según el INEI. CNO 2511 es el 82 % de la persona |
| 2 | Database, systems and network professionals (Core) | 2521, 2522, 2523, 2529 | 2514, 2515, 2529 | Exacto | **Solo 5 registros: se suprime.** Usar las personas 1 y 2 combinadas |
| 3 | ICT technicians and user support (Core) *(IT technicians and support)* | 3511–3514, 3521, 3522 | 3511–3514, 3521, 3522 y 3126 | Exacto | CNO 3126 (supervisores TIC) solo enlaza con CIUO 3514. CNO 3521 (técnicos de radiodifusión) es el 28 % de la persona; hay un subconjunto solo TIC (S3) |
| 4 | ICT managers (Core) *(IT managers)* | 1330 | 1330 | Exacto | **13 registros: se suprime.** CNO 1150 (directores generales TIC) enlaza con CIUO 1120, no con esta persona |
| 5 | Designers (Adjacent) *(Designers)* | 2163, 2166 | 2163, 2166 | Exacto, con subcobertura | **9 registros: se suprime.** En Perú la mayoría de diseñadores (de interiores, productos, moda, envases) se codifica en CNO 3432, que el INEI enlaza con CIUO 3432, fuera de la persona. Se reporta 3432 solo como dato informativo (63.189), **fuera de los anillos** |
| 6 | Business and management analysts (Adjacent) | 2421, 2422 | 2421, 2422 | Exacto, pero el alcance nacional es más amplio | CNO 2421 incluye expresamente "Administrador de Empresas" y "Otros administradores". Es más amplio que el concepto de la CIUO y no se puede separar a 4 dígitos |
| 7 | Finance and investment analysts (Adjacent) *(Finance analysts)* | 2412, 2413 | 2412 | Exacto (CNO no tiene 2413) | **19 registros: se suprime** |
| 8 | Data, statistics and research specialists (Adjacent) *(Data and research specialists)* | 2120, 2631, 2632, 3314 | 2120, 2631, 2632, 3315, 3317 | Oficial, pero incluye técnicos | CNO 3317 ("técnicos en economía": comercio, exportación, marketing) enlaza solo con CIUO 3314 y aporta el 41 % de la persona. Sin 3315 ni 3317 quedan 29.001. CNO 3313 (técnicos en contabilidad) se excluye porque su enlace principal es CIUO 3313 |
| 9 | Marketing and advertising professionals (Adjacent) | 2431, 2432 | 2431, 2432 | Exacto | 30 personas y CV de 24,5 %: **baja precisión** |
| 10 | Accountants and auditors (Extended) | 2411 | 2411 | Exacto | — |
| 11 | Engineers (non‑ICT) (Extended) | 2141–2146, 2149, 2151–2153 | Los mismos | Exacto | — |
| 12 | Business and operations managers (Extended) | 1211–1213, 1219, 1221–1223, 1321–1324, 1341–1346, 1349 | 1211–1223, 1321–1326, 1341–1346, 1421 | Exacto pero parcial | Las aperturas nacionales 1325, 1326 y 1421 enlazan con CIUO 1324. **CIUO 1349 no tiene un código CNO fiable**: CNO 1499 enlaza con 1349 en el Anexo 4 pero con 1439 en el Anexo 3, así que se excluye (sensibilidad: +5.213). CNO 1345 (directores de centros educativos, incluidos colegios) es el 39 % de la persona |
| 13 | Higher‑education and IT educators (Extended) *(University and IT educators)* | 2310, 2356 | 2311, 2353 | Enlaces relativos | CNO 2311 (profesores universitarios) tiene enlace relativo con CIUO 2310. CNO 2312 (CETPRO, no es educación superior) se excluye (+7.916). Los docentes de institutos superiores no universitarios no se pueden identificar por separado |

**Doble conteo:** ningún código CNO se repite entre personas; el script lo verifica con una aserción. La tabla completa por código, con los enlaces y su fuente en los anexos, está en `f_occupation_mapping_pe.csv`, y la correspondencia completa extraída en `cno2015_ciuo08_correspondence.csv`.

---

## C. Resultados de la capa F, Perú 2025

**Fuente y cálculo:** INEI, EPEN 2025 Departamentos, base anual. Ocupación principal, ocupados de 14 años y más, factor `FAC300_ANUAL` (promedio anual 2025), alcance nacional (urbano + rural).

### C.1 F1, F2 y F11: población por persona y por anillo

**Reglas de publicación (aprobadas, D‑PE‑03)**
- **Se suprime** la estimación si el CV es mayor a 30 % o si hay menos de 30 personas únicas.
  - En las tablas publicables (`data/`) los valores suprimidos quedan vacíos. Los valores completos se conservan solo en `validation/internal_not_publishable/`.
  - Las cifras suprimidas siguen formando parte de los agregados válidos (anillos, 1+2 combinadas, total de las 13).
  - Las tablas por código CNO dejan vacío el valor ponderado cuando hay menos de 30 registros.
  - **Advertencia:** restar agregados publicados reproduce valores suprimidos (por ejemplo, las personas 1+2 menos la persona 1). Esas diferencias no son fiables y no deben publicarse.
- **Baja precisión** si el CV está entre 15 % y 30 %.
- **Confianza de la plantilla:** alta con ≥1.000 personas únicas, media con 300–999 y baja con menos de 300.

| # | Persona | Registros / personas únicas / UPM | Ocupados 2025 | IC 95 % | CV | % de ocupados | Confianza (plantilla) | Estado |
|---|---|---|---|---|---|---|---|---|
| 1 | Software developers and analysts | 505 / 382 / 352 | **67.761** | 57.397–78.126 | 7,8 % | 0,39 % | media | publicar |
| 2 | Database, systems and network professionals | 5 / 5 / 5 | — | — | 62 % | — | baja | **suprimido** |
| 3 | ICT technicians and user support | 742 / 606 / 560 | **75.298** | 65.225–85.370 | 6,8 % | 0,43 % | media | publicar |
| 4 | ICT managers | 13 / 13 / 13 | — | — | 43 % | — | baja | **suprimido** |
| 5 | Designers (graphic, multimedia, product) | 9 / 9 / 9 | — | — | 38 % | — | baja | **suprimido** |
| 6 | Business and management analysts | 1.014 / 832 / 738 | **85.893** | 75.575–96.212 | 6,1 % | 0,49 % | media | publicar (alcance amplio) |
| 7 | Finance and investment analysts | 19 / 19 / 19 | — | — | 33 % | — | baja | **suprimido** |
| 8 | Data, statistics and research specialists (**categoría ocupacional amplia**) | 491 / 403 / 375 | **50.235** | 42.358–58.111 | 8,0 % | 0,29 % | media | publicar (D‑PE‑05) |
| 8r | *Escenario restringido a profesionales* (CNO 2120, 2631, 2632) | 326 / 255 | 29.001 | 23.049–34.952 | 10,5 % | 0,17 % | baja | escenario |
| 9 | Marketing and advertising professionals | 31 / 30 / 30 | **4.916** | 2.555–7.277 | 24,5 % | 0,03 % | baja | baja precisión |
| 10 | Accountants and auditors | 1.314 / 1.004 / 861 | **94.590** | 83.669–105.512 | 5,9 % | 0,54 % | alta | publicar |
| 11 | Engineers (non‑ICT) | 2.064 / 1.637 / 1.336 | **169.564** | 155.055–184.072 | 4,4 % | 0,96 % | alta | publicar |
| 12 | Business and operations managers | 726 / 594 / 514 | **51.749** | 43.947–59.551 | 7,7 % | 0,29 % | media | publicar |
| 13 | Higher‑education and IT educators | 1.021 / 732 / 632 | **60.534** | 52.434–68.634 | 6,8 % | 0,34 % | media | publicar |
| — | **Personas 1 + 2 combinadas** | 510 / 385 / 355 | **68.323** | 57.914–78.733 | 7,8 % | 0,39 % | media | lectura robusta |
| F11 | **Anillo Core (1–4)** | 1.265 / 975 | **144.961** | 129.509–160.414 | 5,4 % | 0,82 % | media | publicar |
| F11 | **Anillo Adjacent (5–9)** | 1.564 / 1.279 | **146.415** | 132.252–160.578 | 4,9 % | 0,83 % | alta | publicar, con advertencias de las personas 6 y 8 |
| F11 | **Anillo Extended (10–13)** | 5.125 / 3.935 | **376.437** | 353.637–399.236 | 3,1 % | 2,14 % | alta | publicar |
| — | **Las 13 personas** | 7.954 / 6.133 | **667.813** | 634.132–701.494 | 2,6 % | 3,80 % | alta | publicar |

**Notas sobre los anillos**
- Los totales por anillo son la suma de los códigos de sus personas, sin solapamiento.
- Incluyen las celdas suprimidas: estas se ocultan como cifra individual, pero sí forman parte del total. Así, el anillo Core incluye unas 1.900 personas de los grupos 2 y 4.
- El anillo Adjacent incluye la persona 6, de alcance amplio, y los técnicos de la persona 8. Sin 3315 ni 3317 sería unos 125.000.

**Persona 8 (D‑PE‑05, aprobada con advertencia).**
- **Cifra principal: 50.235.** Corresponde a la categoría ocupacional amplia. **Incluye técnicos**: CNO 3317, técnicos en economía (comercio, exportación, marketing), y CNO 3315, técnicos estadísticos. Por eso **no equivale exclusivamente a profesionales especializados en datos e investigación**.
- **Escenario restringido a profesionales: 29.001.**
- **Ninguna de las dos cifras representa usuarios potenciales ni confirmados.** Lo mismo vale para todas las cifras de la capa F.

**Sensibilidades** (en `f_persona_estimates_pe.csv`):

| ID | Cambio | Ocupados | CV |
|---|---|---|---|
| S3_ict_only | Persona 3 sin 3521 ni 3522 (radiodifusión y telecomunicaciones) | 53.239 | 8,0 % |
| S8_excl_3315_3317 | Persona 8 solo profesionales | 29.001 | 10,5 % |
| S8_add_3313 | Persona 8 + técnicos en contabilidad | 75.035 | 6,1 % |
| S12_add_1499 | Persona 12 + otros gerentes de servicios | 56.962 | 7,3 % |
| S13_add_2312 | Persona 13 + docentes de CETPRO | 68.450 | 6,5 % |
| S1_excl_2521 | Persona 1 sin soporte de sistemas | 67.310 | 7,8 % |
| INFO_3432 | Diseñadores y decoradores (fuera de los anillos) | 63.189 | 7,4 % |
| INFO_DESIGN_2163_2166_3432 | **Grupo informativo de diseñadores (D‑PE‑09)**: fuera de las 13 personas y de los anillos. ENAHO: 65.525 (CV 12,2 %), calculado por separado | 65.706 | 7,3 % |

### C.2 F3–F8: perfiles (porcentaje dentro de cada grupo; 2025)

| Grupo | Asalariado privado / público / independiente / empleador | Empresa 201+ (solo, 1 persona) | Fuera de la sección J | Lima Metropolitana y Callao | Mujeres | Título universitario | Edad mediana | Ingreso mediano, ocupación principal (S/ al mes) | × todos los ocupados |
|---|---|---|---|---|---|---|---|---|---|
| P1 Software | 73,5 / 15,2 / 9,3 / 2,0 | 50,2 % (9,2 %) | 56,0 % | 70,9 % | 16,9 % | 100 %* | 38 | 4.000 | 3,1× |
| P3 Técnicos TIC | 57,1 / 11,9 / 27,4 / 2,1 | 28,2 % (26,6 %) | 69,2 % | 66,9 % | 14,4 % | 24,0 % | 32 | 2.000 | 1,5× |
| P6 Analistas de gestión | 61,8 / 15,1 / 10,3 / 12,2 | 31,5 % (8,9 %) | 98,7 % | 58,9 % | 46,8 % | 99,9 %* | 38 | 3.000 | 2,3× |
| P8 Datos e investigación | 53,2 / 28,3 / 17,1 / 0,7 | 49,5 % (15,4 %) | 99,0 % | 66,1 % | 43,3 % | 80,2 % | 37 | 3.000 | 2,3× |
| P9 Marketing (baja precisión) | 54,4 / 18,9 / 26,7 / 0,0 | 31,5 % (25,2 %) | 90,2 % | 73,2 % | 43,4 % | 100 %* | 31 | 2.600 | 2,0× |
| P10 Contadores | 52,5 / 16,8 / 26,0 / 4,6 | 29,8 % (24,6 %) | 99,4 % | 54,7 % | 49,0 % | 100 %* | 42 | 3.000 | 2,3× |
| P11 Ingenieros | 66,0 / 16,0 / 14,2 / 3,8 | 44,2 % (13,7 %) | 98,6 % | 51,0 % | 18,9 % | 99,7 %* | 36 | 4.000 | 3,1× |
| P12 Gerentes | 53,3 / 37,0 / 0,0 / 9,7 | 51,1 % (0,0 %) | 98,1 % | 52,0 % | 34,3 % | 85,3 % | 49 | 6.000 | 4,6× |
| P13 Educadores | 53,3 / 46,7 / 0,0 / 0,0 | 88,0 % (0,0 %) | 100 % | 38,6 % | 31,5 % | 94,3 % | 51 | 3.600 | 2,8× |
| Anillo Core | 64,8 / 13,3 / 18,8 / 2,3 | 38,8 % (18,3 %) | 62,6 % | 68,8 % | 15,4 % | 60,5 % | 35 | 2.800 | 2,2× |
| Todos los ocupados | 38,9 / 9,2 / 36,8 / 3,6 | 16,2 % (25,8 %) | 99,2 % | 32,0 % | 44,5 % | 15,1 % | 40 | 1.300 | 1,0× |

\* Porcentajes cercanos al 100 % por la regla de codificación del INEI (ver A.7).

**Notas sobre los perfiles**
- **F3:** "otros" (familiares, trabajadoras del hogar y practicantes no remunerados) completa el 100 %.
- **F4:** rangos de la plantilla construidos con el número exacto de trabajadores (`C317A`): solo, 2–10, 11–50, 51–200 y 201+. En el CSV están todos los rangos.
- **F5:** sección J de la CIIU Rev.4 (divisiones 58–63).
- **F6:** distribución completa por departamento en `f_persona_profiles_pe.csv`. Las celdas con menos de 30 registros se marcan como `small_cell` y quedan vacías.
- **F8:** mediana de `INGTOTP`, el ingreso mensual de la ocupación principal, imputado por el INEI y sobre ingresos > 0. Como medida comparable con el INEI se agrega `ingtrabw` (ingreso total del trabajo, con ingresos extraordinarios). Las medianas se agrupan en valores redondos (S/ 3.000, 4.000…), un efecto de cómo se reportan los ingresos. La inflación de 2025 fue baja, así que no se ajusta.

---

## D. Metodología reproducible

| Paso | Script | Qué hace |
|---|---|---|
| 1 | `scripts/parse_cno2015_annex.py <CNO2015.pdf> <out>` | Extrae los anexos 3 y 4 en el orden del flujo de contenido, elimina duplicados entre páginas, cruza ambas direcciones y escribe `cno2015_ciuo08_correspondence.csv` |
| 2 | `scripts/layer_f_epen_peru.py <EPEN csv> <corr csv> <out>` | Universo, controles contra el INEI, mapeo (con exclusiones documentadas), estimaciones con varianza por diseño, sensibilidades y perfiles F3–F8 |
| 3 | `scripts/build_layer_f_deliverables_pe.py <out> <entrega>` | Construye la tabla B y el registro de fuentes |

**Detalles del cálculo**
- **Filtros:** `OCUP300` = 1 y `FAC300_ANUAL` no vacío. `C308_COD` y `C309_COD` se completan con ceros a 4 dígitos.
- **Ponderación:** `FAC300_ANUAL` sin transformar.
- **Varianza:** Taylor con UPM `CONGLOMERADO` y estrato `CCDD`×`ESTRATO` (fusión 25_6→25_5); IC 95 % con z = 1,96.
- **Reproducción:** ejecuté todo el proceso desde cero en otra carpeta y los resultados son **idénticos byte a byte**.
- **Microdatos:** los crudos se quedan en local y no se incluyen en el paquete.
- **Hash** de la correspondencia extraída: `dd8c64b5…`.

---

## E. Pendientes y limitaciones

| # | Tema | Impacto | Cómo resolverlo |
|---|---|---|---|
| E1 | **F9 (nivel socioeconómico)** no existe en EPEN | **Resuelto con ENAHO 2025, como fuente separada** | Ver `Peru_Day1_LayerF_ENAHO2025_Auditoria_F9.md` y `data/f9_persona_socioeconomic_enaho_pe.csv` |
| E2 | **F10 (trabajo desde casa):** la pregunta 318A está en el cuestionario EPEN 2025 pero **no en la base pública**. **ENAHO 2025 tampoco la tiene** (verificado en el cuestionario 2025) | F10 queda sin dato | Solicitar al INEI la variable C318A de EPEN (Ley 27806) |
| E3 | El diccionario recibido es el del 4.º trimestre. El INEI publica diccionarios anuales (el de 2022 está verificado), pero el de 2025 no fue accesible desde aquí | Bajo: `FAC300_ANUAL` y `CCDD` se validaron con 24 controles | Descargar el diccionario de "EPEN – Departamentos 2025 – Anual" |
| E4 | El clasificador de `C308_COD` y `C309_COD` no está documentado por escrito | Bajo: verificación empírica al 100 % | Opcional: confirmarlo con el INEI |
| E5 | Personas 2, 4, 5 y 7 suprimidas. **En la persona 5 es un efecto de codificación de EPEN** (ENAHO usa 2163/2166; ver D‑PE‑09) | No hay cifras individuales | Personas 2, 4 y 7: limitación de muestra (también en ENAHO). Usar las personas 1+2 combinadas. Persona 5: sin cambios (suprimida en EPEN); grupo informativo de diseñadores según D‑PE‑09 |
| E6 | La persona 6 es amplia (incluye administradores de empresas) y la 8 incluye técnicos | Sobreestima esas personas respecto del concepto de la CIUO | Decisión de Think4ever: mantener la correspondencia oficial (lo recomendado) o adoptar la sensibilidad S8 como cifra principal |
| E7 | F6 no llega a provincia, distrito ni ciudad (sin UBIGEO ni `CODCIUDAD` en la base anual) | No hay zonas de Lima ni Arequipa | ENAHO trae UBIGEO, con menor muestra |
| E8 | ~~Totales de control tomados de la prensa~~ **Resuelto:** el informe técnico anual 2025 del INEI se leyó directamente | Queda solo el hash del PDF | Adjuntar el PDF si se quiere archivar con hash |
| E9 | Los CV son de Think4ever, no publicados por el INEI | — | Quedan etiquetados así en los datos |
| E10 | Licencia de los microdatos del INEI | No se asume redistribución | Solo se entregan agregados |

**Decisiones (registro en `data/decisions_log_pe.csv`)**

| ID | Decisión | Estado (9 de octubre de 2026) |
|---|---|---|
| D‑PE‑03 | Supresión con CV > 30 % o menos de 30 personas únicas; baja precisión con CV de 15–30 % | **Aprobada y aplicada** |
| D‑PE‑04 | Exclusión de CNO 1499, 2312 y 3313, conservando las sensibilidades | **Aprobada** |
| D‑PE‑05 | Persona 8: 50.235 como cifra principal (categoría amplia) y 29.001 como escenario de profesionales | **Aprobada con advertencia** |
| D‑PE‑06 | ENAHO 2025 para F6, F9 y F10 | Evaluada; **F9 calculado** como fuente separada (D‑PE‑08). F6 se mantiene con EPEN y F10 no está disponible |
| D‑PE‑07 | Sumaria de 8 grupos para los quintiles | Aplicada |
| D‑PE‑09 | Diseñadores: grupo informativo 2163 + 2166 + 3432 (opción B) | **Aprobada como análisis informativo** |
| D‑PE‑10 / 10b | F9 de ENAHO como fuente separada | **Aprobado** |
| D‑PE‑12 | Varianza de ENAHO alineada con el INEI (UPM sin estratos) | **Aplicada** |
| D‑PE‑11 | F6 = EPEN; F10 pendiente de información oficial | **Aprobada** |
