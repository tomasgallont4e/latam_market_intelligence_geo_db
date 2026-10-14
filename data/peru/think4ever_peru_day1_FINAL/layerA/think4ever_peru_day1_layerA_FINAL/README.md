# Think4ever · Perú Day 1 · Capa A: desarrolladores en GitHub · **FINAL**

**Paquete:** `think4ever_peru_day1_layerA_FINAL` · **Preparado:** 9 de octubre de 2026 (condición C1 de la auditoría de cierre) · **País:** Perú (`PE`).
**Estado:** **FINAL**, autorizado por Think4ever el 9 de octubre de 2026, 19:06 (hora de Bogotá). No está cargado en la plataforma Think4ever. Versión anterior: `think4ever_peru_day1_layerA_DRAFT`, con datos idénticos.

> **Las cifras se tomaron tal cual de las salidas existentes, calculadas el 8 de octubre de 2026 y reproducidas byte a byte; ningún indicador se recalculó para este paquete.** Solo se agregaron columnas de metadatos (`source_id`, `dataset_version`, `reconciliation`, `previous_t4e_value`, `period_end_date`) y los booleanos se pasaron a minúsculas (`true`/`false`, convención de Argentina).

## 1. Qué mide esta capa (y qué no)
- **Mide** cuentas y actividad en GitHub **ubicadas en Perú por la IP más frecuente del día** (GitHub Innovation Graph). Lo incluido:
  - cuentas de desarrollador, incluidas las inactivas;
  - cuentas de organización;
  - git pushes del trimestre;
  - personas que hacen push en cada lenguaje.
- **Las cuentas no equivalen a personas.** Una persona puede tener varias cuentas, hay cuentas inactivas o automatizadas, y la ubicación por IP puede asignar un país distinto al de residencia, por ejemplo con VPN. No miden ocupados, desarrolladores profesionales ni usuarios o clientes potenciales de Think4ever.
- Los conteos por lenguaje son pertenencias: una cuenta cuenta en cada lenguaje en que hace push.
- **No se combina** con la capa B (encuesta) ni con la capa F (población ocupacional), que miden otras cosas en otros periodos.

## 2. Fuente
- **GitHub Innovation Graph**, versión del dataset **1.0.10** (`docs/datasheet.md`). Commit del repositorio `078fb62` (31 de agosto de 2026), el mismo que se usó para Argentina y Chile.
- **Archivos:** `developers.csv`, `organizations.csv`, `git_pushes.csv`, `repositories.csv` y `languages.csv`, filtrados con `iso2_code = PE`.
- **Licencia:** CC0.
- Hashes por archivo en `data/source_registry_layer_a_pe.csv`.

## 3. Metodología (la misma que en Argentina y Chile)
- A1–A3 se leen directamente de los archivos. El crecimiento compara **el mismo trimestre de un año contra el otro (2026T1 frente a 2025T1)**, para evitar la estacionalidad.
- **A4:** personas por lenguaje en 2026T1 frente a 2025T1, solo lenguajes de programación. Umbral mínimo de base **provisional** (D‑04): 5.000 × (pertenencias totales de Perú en 2025T1 / pertenencias totales de Colombia en 2025T1) = **1.766 personas**. Se muestra también la variante con base ≥ 1.000.
- **A5:** personas que hacen push en lenguajes empresariales sobre el total de pertenencias. La canasta de la plantilla es Java, C#, VB.NET, COBOL, PL/SQL, T‑SQL, ABAP, Apex, Groovy, Scala y Kotlin. La definición es **provisional** (D‑03).
- **Validación del método:** el mismo script reproduce exactamente los indicadores publicados en los paquetes FINAL de Argentina (25 de 25) y Chile (19 de 19). Ver `validation/a_validation_checks_pe.csv`.

## 4. Resultados de Perú (2026T1)

| Indicador | Valor | Comparación |
|---|---|---|
| A1 Cuentas de desarrollador | **907.052** | +39,6 % frente a 649.794 (2025T1) |
| A2 Cuentas de organización | **36.740** | +24,0 % frente a 29.623; 24,7 cuentas de desarrollador por organización |
| A3 Git pushes | **1.144.909** | +122,7 % frente a 514.211 (**base débil**, ver sección 5); 1,26 pushes por cuenta |
| A4 Lenguajes más usados (personas que hacen push) | HTML 25.761 · JavaScript 21.138 · CSS 20.598 · TypeScript 10.376 · Python 9.986 | — |
| A4 Crecimiento más rápido (umbral 1.766, **provisional**) | TypeScript +98,0 % · Dockerfile +94,2 % · Shell +92,3 % · Python +83,5 % · JavaScript +45,0 % · Java +36,0 % | Variante ≥ 1.000: también entran Kotlin +54,3 % y C++ +52,0 % |
| A5 Lenguajes empresariales (**provisional**) | **6,67 %** (9.068 / 135.955) | Las dos variantes coinciden porque PL/SQL no aparece en los datos de Perú. Presentes: Java, C#, T‑SQL y Kotlin. Ausentes (menos de 100 personas): VB.NET, COBOL, PL/SQL, ABAP, Apex, Groovy y Scala |

## 5. Limitaciones
1. **Las cuentas no son personas** (sección 1).
2. **El crecimiento de pushes (+122,7 %) está inflado por una base débil.**
   - El primer trimestre es siempre el de menos pushes por cuenta: 0,97 en 2023T1, 0,85 en 2024T1 y **0,79 en 2025T1, el mínimo de toda la serie**. En 2025T1 los pushes cayeron 30,7 % frente a 2024T4.
   - Por eso la variación interanual exagera la tendencia. Para describir actividad es más estable usar pushes por cuenta (1,26 en 2026T1) y la serie trimestral (`a_github_country_quarterly_pe.csv`).
   - Pasó lo mismo en Argentina y Chile.
3. **A4 y A5 son provisionales:**
   - el umbral de crecimiento de A4 (D‑04) y la definición de A5 (D‑03) están pendientes de decisión de Think4ever;
   - se publican con `canonical_status = undetermined` y no deben tratarse como definitivos.
4. **Sin conciliación interna:** `latam-country-breakdown-2026Q1.csv` no se recibió (solicitud `REQ_T4E_LATAM_BREAKDOWN`), así que `previous_t4e_value` queda vacío.
5. **Comparación con la web de Innovation Graph: no verificable** desde este entorno. Los archivos `data/` del repositorio son la fuente publicada de esas cifras.
6. **Periodo:** 2026T1 frente a 2025T1. No coincide con el de la capa B (encuesta 2025) ni con el de la capa F (promedio 2025).

## 6. Archivos

| Ruta | Contenido |
|---|---|
| `data/a_github_indicators_pe.csv` | A1–A5 con método, numerador, denominador, variante y estado (canónico o indeterminado) |
| `data/a_github_languages_pe.csv` | Personas por lenguaje en 2025T1 y 2026T1; si entra en la canasta de A5; si cumple el umbral de A4 |
| `data/a_github_country_quarterly_pe.csv` | Serie 2020T1–2026T1 de cuentas, organizaciones, pushes y repositorios |
| `data/source_registry_layer_a_pe.csv` | Fuentes, versión, commit, hashes y solicitudes abiertas |
| `data_dictionary.csv` | Todas las columnas |
| `validation/a_validation_checks_pe.csv` | Método frente a Argentina y Chile, último trimestre, comparación interanual, coherencia entre A1 y la serie |
| `validation/a_reproduction_check_pe.csv` | Re‑ejecución byte a byte y valores del paquete idénticos a la salida existente |
| `scripts/` | `layer_a_country.py` (cálculo), `build_layer_ab_packages_pe.py` y `finalize_ab_packages_pe.py` (empaquetado y validación) |
| `manifest.csv`, `validation/SHA256SUMS.txt` | Inventario y hashes |

## 7. Reproducir
```
git clone https://github.com/github/innovationgraph && git -C innovationgraph checkout 078fb62
python3 -I scripts/layer_a_country.py innovationgraph <out_dir> PE      # writes layer_a_pe_*.csv (+ AR, CL for method check)
python3 -I scripts/build_layer_ab_packages_pe.py <out_dir> <work_b> innovationgraph results.csv ai.json <AR_FINAL> <CL_FINAL> <root>
```
Python 3.13 y pandas 3.0.5.
