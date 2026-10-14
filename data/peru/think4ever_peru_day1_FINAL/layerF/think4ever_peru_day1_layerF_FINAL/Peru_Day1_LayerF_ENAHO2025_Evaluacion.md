# Perú Day 1, capa F: evaluación de ENAHO 2025 para F6, F9 y F10

**Think4ever · Market Research & Analytics · LATAM** · 9 de octubre de 2026 · Estado: **evaluación (D‑PE‑06), superada.** Los archivos se recibieron y procesaron. Los resultados están en `Peru_Day1_LayerF_ENAHO2025_Auditoria_F9.md`.

> **Correcciones tras recibir los archivos:** (1) el universo de la pregunta 558D2 y la ausencia de una pregunta de trabajo desde casa se confirmaron en el cuestionario 2025; (2) `ESTRSOCIAL` es el estrato socioeconómico del conglomerado (A–E urbano, más rural) según la Estratificación del Marco (mayo de 2026); (3) la muestra real de ENAHO por persona es de 119 a 325 registros.

**Alcance.** Este documento evalúa si ENAHO 2025 tiene las variables necesarias y si sus resultados son comparables con EPEN. No combina factores de expansión de ambas encuestas ni extrapola resultados de una a la otra.

## 1. Conclusión

| Indicador | ¿ENAHO 2025 lo resuelve? | Recomendación |
|---|---|---|
| **F9 Nivel socioeconómico** | **Sí.** Ingreso per cápita del hogar (Sumaria: `INGHOG2D` / `MIEPERHO`) y además `ESTRSOCIAL`, el estrato socioeconómico del marco censal | Incorporarlo como **perfil propio de ENAHO** (porcentajes dentro de cada grupo, con su propio n y su propio CV), solo para grupos con suficiente muestra |
| **F6 Geografía más detallada** | **Parcialmente.** Trae UBIGEO de 6 dígitos (departamento, provincia y distrito), pero ENAHO solo es representativa a nivel nacional, urbano/rural, región natural, departamento y Lima Metropolitana | Aporte marginal frente a EPEN, que ya da el departamento con 3 a 4 veces más muestra. **No usar ENAHO para provincias o distritos** con estas muestras. Como mucho, un corte por dominio (costa, sierra, selva y Lima Metropolitana) |
| **F10 Trabajo desde casa** | **No.** El cuestionario ENAHO 01A (versión 2024 verificada) no pregunta por lugar de trabajo ni teletrabajo. `P517` es la categoría de la **ocupación secundaria**, no el lugar de trabajo | F10 queda **sin dato** con fuentes públicas. La única fuente identificada es la pregunta **318A de EPEN 2025** ("¿en qué lugar realiza su trabajo?"), que **no viene** en la base pública. Hay que pedírsela al INEI |

## 2. Disponibilidad (evidencia)

| Elemento | Evidencia | Estado |
|---|---|---|
| Publicación de ENAHO 2025 | Resultados de pobreza 2025 publicados por el INEI en mayo de 2026. Un proyecto de terceros documenta los microdatos ENAHO 2025 con el **código de encuesta 1031**: `Enaho01-2025-200.csv` (115.145 filas), `Enaho01A-2025-300.csv` (104.446), `Enaho01a-2025-500.csv` (84.853 personas de 14 años y más) y `Sumaria-2025.csv` (33.702 hogares) | Confirmado por terceros; hay que descargarlo del INEI |
| Ocupación principal | `P505R4` en el módulo 500. En el módulo 200, el diccionario oficial de 2024 rotula `OCUPAC_R4` como "CNO 2015" | Por verificar en el diccionario 2025, pero es muy probable que sea **CNO 2015 a 4 dígitos**, el mismo clasificador que EPEN |
| Industria | `P506R4` (CIIU Rev.4) | Por verificar |
| Categoría ocupacional, sector y tamaño | `P507`, `P510`, `P512A` (rangos: hasta 20, 21–50, 51–100, 101–500, más de 500) y `P512B` (número exacto) | Disponibles |
| Ocupado y factor de expansión | `OCU500` y `FAC500A`, el factor anual del módulo de empleo | Disponibles |
| Diseño muestral | `CONGLOME`, `ESTRATO` (1–8), `DOMINIO` (1–8) y `UBIGEO` (6 dígitos) | Disponibles (diccionario oficial de 2024) |
| Ingresos | `I524A1`, `D529T`, `I530A`, `D536`, `I538A1`, `D540T`, `I541A`, `D543` y `D544T` | Disponibles |
| Nivel socioeconómico del hogar | Sumaria: `INGHOG2D`, `GASHOG2D`, `MIEPERHO`, `POBREZA`, `LINEA`, `ESTRSOCIAL` y `FACTOR07` | Disponibles. Falta la definición oficial de `ESTRSOCIAL` (6 categorías, al parecer A–E más rural, asignadas al conglomerado según el marco censal) |
| Lugar de trabajo o teletrabajo | No existe en el cuestionario 01A de 2024. Falta revisar el cuestionario 2025 | **No disponible** |

## 3. Comparabilidad con EPEN 2025

| Dimensión | EPEN 2025 (fuente principal) | ENAHO 2025 | Implicación |
|---|---|---|---|
| Clasificador de ocupación | CNO 2015 a 4 dígitos (verificado) | CNO 2015 a 4 dígitos (por verificar) | Si se confirma, se aplica **la misma correspondencia y las mismas exclusiones**, y las personas quedan definidas igual |
| Universo | Ocupados de 14 años y más, ocupación principal, residentes habituales | El mismo concepto (`OCU500` = 1) | Comparable en concepto |
| Muestra | 142.084 viviendas; 193.008 registros de ocupados | Unas 34.000 viviendas y 84.853 personas de 14 años y más | ENAHO tiene **unas 3,5 veces menos muestra** |
| Período | 12 meses, factor anual | 12 meses, factor anual | Comparable |
| Total oficial de ocupados | 17.575,2 mil (fuente oficial de empleo del INEI) | Propio; normalmente difiere de EPEN | **No se mezclan**: cada encuesta se reporta con su propio total |
| Varianza | Taylor (conglomerado × estrato por departamento) | Taylor (`CONGLOME` × `ESTRATO`/departamento) | Mismo método |

**Muestra esperada por persona en ENAHO.** Es solo un orden de magnitud: escalé los registros de EPEN por la razón de muestras (≈0,29), y hay que verificarlo con los datos.

| Grupo | Registros aprox. | Publicable |
|---|---|---|
| Anillo Core | ≈ 360 | Probablemente sí |
| Ingenieros | ≈ 590 | Probablemente sí |
| Contadores | ≈ 370 | Probablemente sí |
| Analistas de gestión | ≈ 290 | Probablemente sí |
| Educadores | ≈ 290 | Probablemente sí |
| Técnicos TIC | ≈ 210 | Probablemente sí |
| Gerentes | ≈ 210 | Probablemente sí |
| Desarrolladores | ≈ 140 | Probablemente sí |
| Datos e investigación | ≈ 140 | Probablemente sí |
| Personas 2, 4, 5, 7 y 9 | Menos de 30 | **No** (suprimidas también en ENAHO) |

Los quintiles F9 para Desarrolladores y Datos e investigación tendrán CV altos. La regla de supresión aprobada (D‑PE‑03) se aplica sin cambios.

## 4. Método propuesto (pendiente de aprobación)

1. **Clasificador.** Verificar `P505R4` contra la lista CNO 2015, igual que con EPEN. Aplicar **la misma** tabla `f_occupation_mapping_pe.csv`.
2. **Control.** Calcular el total de ocupados de ENAHO 2025 con `FAC500A` y conciliarlo con la publicación del INEI basada en ENAHO, si la hay. Reportar también la diferencia frente a EPEN, **solo como diagnóstico**.
3. **F9:**
   - (a) Quintiles nacionales de ingreso per cápita del hogar: `INGHOG2D` / `MIEPERHO`, con cortes calculados sobre la **población** (`FACTOR07` × `MIEPERHO`).
   - (b) Distribución por `ESTRSOCIAL` como indicador complementario.
   - Ambos se expresan como **porcentajes dentro de cada grupo según ENAHO**, ponderados con `FAC500A`.
4. **F6.** Distribución por dominio (costa, sierra, selva, Lima Metropolitana) como dato de ENAHO, sin cortes por provincia o distrito.
5. **Presentación.** En una tabla separada (`f_persona_profiles_enaho_pe.csv`), con `source = ENAHO 2025` y su propio n, CV y estado de publicación. **Nunca se multiplican porcentajes de ENAHO por totales de EPEN.**
6. **Diagnóstico de coherencia.** Comparar las estimaciones F1 de ENAHO con las de EPEN para las personas publicables y reportar la diferencia (las cifras de EPEN no se reemplazan).

## 5. Archivos que necesito (descarga manual)

Desde https://proyectos.inei.gob.pe/microdatos/ → Consulta por encuestas → **ENAHO Metodología ACTUALIZADA** → 2025 → Anual:

| # | Archivo | Para qué |
|---|---|---|
| 1 | **Módulo 05, "Empleo e ingresos"** (`Enaho01a-2025-500`), en CSV o SPSS | Ocupación, factor `FAC500A` y diseño muestral |
| 2 | **Módulo 34, "Sumaria"** (`Sumaria-2025`) | F9 |
| 3 | **Diccionario ENAHO 2025** | Confirmar `P505R4`, `ESTRSOCIAL`, `FAC500A` y el universo de las preguntas |
| 4 | **Ficha técnica 2025** y **cuestionario ENAHO 01A 2025**. También están en https://www.gob.pe/en/institucion/inei/informes-publicaciones/3364523-national-household-survey-enaho-2025 | Confirmar que no hay pregunta de lugar de trabajo en 2025, y los niveles de inferencia |
| 5 | Opcional: módulo 02 (personas) | Solo si el módulo 05 no trae sexo o edad (normalmente sí los trae) |

**Para F10:** hay que hacer una solicitud de acceso a la información al INEI (Ley 27806) pidiendo la variable `C318A` (lugar de trabajo) de EPEN 2025, enlazable por `CONGLOMERADO`/`SELVIV`/`HOGAR`/`C201`/`MES`. Si no se obtiene, F10 queda declarado como no disponible.

## 6. Fuentes
- INEI, ENAHO 2024, cuestionario 01A: https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/DocumentosMetodologicos/2024-55/9_CUESTIONARIO-ENAHO01A.pdf
- INEI, ENAHO 2024, diccionario (`UBIGEO`, `ESTRATO`, `DOMINIO`, `CONGLOME`, `OCUPAC_R4` = CNO 2015): https://proyectos.inei.gob.pe/iinei/srienaho/Descarga/DocumentosMetodologicos/2024-55/20_Diccionario_2024.pdf
- INEI, ENAHO 2025, página de documentos: https://www.gob.pe/en/institucion/inei/informes-publicaciones/3364523-national-household-survey-enaho-2025
- Proyecto de terceros con la lista de archivos y columnas de ENAHO 2025 (no oficial): https://github.com/IchiSieben/enaho-ingresos-informalidad (`reports/inventario_columnas.csv`)
- EPEN 2025, ficha técnica (pregunta 318A, en el cuestionario pero no en la base pública), suministrada por Think4ever.
