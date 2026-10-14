# Perú Day 1: resumen ejecutivo

**Think4ever · Market Research & Analytics · LATAM** · 9 de octubre de 2026 · Estado: **FINAL**. Think4ever autorizó el cierre el 9 de octubre de 2026, 19:06 (hora de Bogotá). Es un cierre documental y metodológico; no aprueba estimaciones de mercado potencial ni recomendaciones comerciales.

**Ninguna cifra de este resumen es mercado potencial ni número de clientes de Think4ever.** Cada capa mide algo distinto, en un periodo distinto, con su propia fuente. **No se suman, no se multiplican y no se combinan entre sí.**

## 1. Las tres capas

| Capa | Qué mide | Fuente y periodo | Resultados principales | Confianza y límites |
|---|---|---|---|---|
| **A. Actividad de desarrolladores en GitHub** | Cuentas y actividad localizadas en Perú por IP. **Cuentas, no personas** | GitHub Innovation Graph v1.0.10; **2026T1 frente a 2025T1** | 907.052 cuentas de desarrollador (+39,6 %); 36.740 organizaciones (+24,0 %); 1.144.909 git pushes (+122,7 %, **inflado por una base 2025T1 débil**); 1,26 pushes por cuenta. Lenguajes principales: HTML, JavaScript, CSS, TypeScript y Python. Crecimiento más rápido (provisional): TypeScript, Dockerfile, Shell, Python. Lenguajes empresariales: 6,67 % (provisional) | Datos administrativos completos; A4 y A5 provisionales |
| **B. Adopción de IA entre desarrolladores** | Respuestas de encuestados autoseleccionados, sin ponderar | Stack Overflow Developer Survey **2025** | 64 encuestados (46 profesionales). Usa IA: 88,1 % (52/59). La usa a diario: 62,7 % (37/59). Usa agentes: 43,9 % (25/57). VS Code: 80 % (indicativo). Agentes externos: suprimido | **Baja**: describe a los encuestados, no a la población; comparaciones exploratorias |
| **F. Población ocupacional (13 personas)** | Ocupados cuya ocupación principal pertenece a cada persona | INEI EPEN 2025, **promedio anual 2025** | Core 144.961 · Adjacent 146.415 · Extended 376.437 · 13 personas 667.813 (3,8 % de los ocupados). Mayores: Ingenieros 169.564, Contadores 94.590, Analistas de gestión 85.893, Técnicos TIC 75.298, Desarrolladores 67.761 | Alta o media en la mayoría; personas 2, 4, 5 y 7 suprimidas; persona 9 de baja precisión |
| **F9. Perfil socioeconómico** | Porcentaje de cada grupo según el quintil nacional de ingreso real per cápita de su hogar | INEI ENAHO, **año 2025** (fuente separada) | 13 personas: 70,8 % en el quintil más alto, frente a 25,3 % del total de ocupados. Core 59,6 %; Desarrolladores 72,3 %; Técnicos TIC 48,5 % | Porcentajes, no conteos; validado contra el informe oficial del INEI |
| **Diseñadores (informativo)** | Ocupaciones de diseño en sentido amplio (CNO 2163, 2166 y 3432) | EPEN y ENAHO 2025, por separado | EPEN 65.706 · ENAHO 65.525 | Fuera de las personas y de los anillos; incluye técnicos y decoradores |

## 2. Qué se puede afirmar con respaldo
- **Base de desarrolladores en GitHub (A):** en Perú es amplia y crece rápido: las cuentas de desarrollador aumentaron un 39,6 % en un año, sobre todo con tecnologías web (HTML, JavaScript, TypeScript).
- **Uso de IA (B, confianza baja):** entre los encuestados peruanos de Stack Overflow, el uso de herramientas de IA es mayoritario. Su uso diario y el de agentes aparecen por encima del promedio global.
- **Núcleo TIC (F, anillo Core):** suma unas 145 mil personas ocupadas.
  - El 69 % trabaja en Lima Metropolitana y Callao.
  - Su ingreso mediano es unas 2,2 veces el del total de ocupados.
  - El 63 % trabaja fuera del sector de información y comunicaciones (sección J de la CIIU).
- **Nivel socioeconómico (F9):** las ocupaciones de las 13 personas se concentran en hogares del quintil de ingreso per cápita más alto.

## 3. Qué no se puede afirmar con esta evidencia
- Cuántos clientes o usuarios potenciales tiene Think4ever en Perú.
- Qué porcentaje de los ocupados usa IA. Eso exigiría combinar B con F, y no es válido.
- Cuántas personas hay detrás de las cuentas de GitHub.
- Cuántas personas trabajan desde casa (F10 no está disponible).
- Cifras individuales de gerentes TIC, profesionales de bases de datos y redes, analistas financieros o diseñadores dentro de las personas oficiales (muestra insuficiente). Para los diseñadores existe el grupo informativo.

## 4. Limitaciones principales
1. **Los periodos no son equivalentes:** A es 2026T1 frente a 2025T1; B es 2025; F es el promedio de 2025.
2. **Las fuentes no son comparables entre sí:** cuentas de una plataforma (A), una encuesta autoseleccionada (B) y encuestas de hogares oficiales (F).
3. **A4 y A5 son provisionales** (D‑03 y D‑04).
4. **La persona 6 es de alcance amplio** (incluye administradores de empresas). **La persona 8 incluye técnicos**: 50.235 en la categoría amplia frente a 29.001 solo profesionales.
5. **EPEN y ENAHO codifican algunas ocupaciones de forma distinta:** se mantienen separadas.
6. **F6 llega solo hasta departamento y F10 no está disponible.**

## 5. Documentos y paquetes
- **Paquetes:** `layerA/`, `layerB/` y `layerF/` dentro de `think4ever_peru_day1_FINAL.zip`, cada uno con README, fuentes y hashes, diccionario, tablas, validación y scripts.
- **Auditoría:** `Peru_Day1_Auditoria_Final_Cierre.md` (v2): matriz de hallazgos y recomendación de cierre.
