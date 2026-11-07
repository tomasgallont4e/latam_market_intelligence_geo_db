# Base geoespacial de México (contrato de tablas)

Llave geográfica: INEGI Catálogo Único (estado 2 dígitos, municipio 5 dígitos = estado + municipio). Todo es agregado.

Las tablas copian la forma de Colombia (`data/geodb-v2/diccionario.md`). Regla de adaptación:

- **Mismo concepto, código nacional equivalente:** se conserva el nombre de columna de Colombia y se documenta el código mexicano (por ejemplo `shops_4711` = SCIAN 461110).
- **Unidad o escala distinta:** se renombra la columna para que no se lea como comparable (moneda, estratos, grados escolares).
- **Sin equivalente en Colombia:** tabla nueva, marcada como *añadida para México*.

Estado: capa Q completa. `geo_department` y `geo_municipality` (`scripts/build-mexico-q-catalogo.py`); `geo_department_shape` y `geo_municipality_shape` (`scripts/build-mexico-q-marco.js`). Capas D, J y N: `fact_companies_municipality`, `geo_zone` y `fact_companies_zone` (`scripts/build-mexico-denue.py`). Capas A y B: `fact_developers_country` y `fact_map_indicator` (`scripts/build-mexico-a-github.py`, `scripts/build-mexico-b-survey.py`). Capas F, G, H y M: `fact_persona_profile`, `fact_persona_department`, `fact_persona_metro`, `fact_persona_segment`, `fact_ict_by_sector`, `fact_micro_department` y `fact_micro_national` (`scripts/build-mexico-f-sinco-mapping.py`, `scripts/build-mexico-enoe.py`). El resto de tablas no tiene datos todavía. Comprobaciones: `node scripts/check-mexico.js`.

## geo_department
Estados. Fuente: INEGI Catálogo Único, entidades (archivo del 2025-12-12). Capa Q. Filas: 32.
| department_code | name |

## geo_municipality
Municipios con punto de referencia: coordenadas de la localidad cabecera (`CVE_CAB`); las 16 alcaldías de Ciudad de México no tienen clave de cabecera y usan su localidad 0001 (`decisions_log.csv`, D-MX-02). Fuente: INEGI Catálogo Único, municipios (2026-08-21) y localidades (2026-10-13). Capa Q. Filas: 2.478.
| municipality_code | department_code | name | lat | lon | wkt |

## geo_department_shape
Polígonos estatales (MultiPolygon WGS84 lon/lat, 5 decimales). Fuente: INEGI Marco Geoestadístico, `00ent`, reproyectado desde Mexico ITRF2008 LCC y simplificado para web (Douglas–Peucker 0,003°). Capa Q. Filas: 32.
| department_code | name | geojson |

## geo_municipality_shape — añadida para México
Polígonos municipales, mismo tratamiento que los estatales. Fuente: INEGI Marco Geoestadístico, `00mun`. Capa Q. Filas: 2.478.
| municipality_code | department_code | name | geojson |

Solo para visualización: cada anillo se simplifica por separado, así que los bordes vecinos pueden mostrar pequeños huecos o traslapes, y se omiten islotes más estrechos que la tolerancia.

## geo_zone
Zonas de las dos ciudades mayores (`decisions_log.csv`, D-MX-05): las 16 alcaldías de Ciudad de México (`CMX-<cve_mun>`, `zone_type` = `alcaldia`) y los 16 municipios de la Zona Metropolitana de Monterrey según *Metrópolis de México 2020* (`MTY-<cve_mun>`, `zone_type` = `municipio_metropolitano`). Cada zona es un municipio completo: `municipality_code` es el propio municipio, `geojson` su polígono y `lat`/`lon`/`wkt` su punto de referencia. Capa J. Filas: 32.
| zone_id | municipality_code | zone_type | zone_code | name | lat | lon | geojson | wkt |

## fact_persona_profile
Una fila por persona: perfil nacional, ENOE 2025 (suma de `fac_tri` de los 4 trimestres / 4; universo `r_def`=00, `c_res` 1 o 3, 15 a 98 años, ocupados). Ocupación SINCO 2019 asignada a las personas con `outputs/f_occupation_mapping_mx.csv` (D-MX-07 a D-MX-09). Capa F. Filas: 13. Fuente: `scripts/build-mexico-enoe.py`.
| persona | ring | isco_codes | employed | interviews | pct_private_employee | pct_government_employee | pct_self_employed_or_employer | pct_firm_251_plus | pct_works_alone | pct_outside_tech_sector | pct_women | pct_university | median_age | median_income_mxn | pct_stratum_3_4 | pct_works_from_home |

- `interviews`: registros de los 4 trimestres (la ENOE es un panel rotativo: una persona puede contar hasta 4 veces).
- `median_income_mxn` sustituye a `median_income_cop`: mediana ponderada de `ingocup` entre quienes declaran ingreso positivo.
- `pct_firm_251_plus` sustituye a `pct_firm_201_plus`: las bandas de tamaño de la ENOE (P3Q/P3L) cortan en 250 personas. Para empleadores y cuenta propia, el tamaño sale de P3D y P3G (insumos del `ambito2` de INEGI).
- `pct_outside_tech_sector`: sector tecnológico = SCIAN 51. La ENOE codifica la actividad con el SCIAN de hogares, donde los servicios de TI (5415) están dentro de 5411 con los servicios legales y contables, así que no se pueden separar: el porcentaje fuera de tecnología queda sobrestimado frente a la sección J de la CIIU (D-MX-10).
- `pct_stratum_3_4`: estrato socioeconómico ENOE (primer dígito de `est`: 1 bajo, 2 medio bajo, 3 medio alto, 4 alto), estratos 3 y 4; sustituye a `pct_stratum_4_6` (estrato de la factura eléctrica, solo Colombia).
- `pct_university`: nivel aprobado `cs_p13_1` profesional, maestría o doctorado.
- `pct_works_from_home`: vacío (no disponible, como en Perú). La ENOE solo pregunta dónde se trabaja (P4F) a negocios sin local, no a asalariados.
- Cada porcentaje usa solo respuestas válidas de su variable (no especificado excluido).
- `isco_codes`: códigos CIUO-08 de la plantilla; la correspondencia SINCO 2019 → CIUO-08 se publica aparte.

## fact_persona_department
Personas por estado. ENOE 2025. Capas F, G. Las filas de cada persona suman su total.
| persona | department_code | department | employed | interviews |

- `interviews` añadida para México, para mostrar la confianza de cada celda.

## fact_persona_metro
Personas por ciudad ENOE (`cd_a`, 39 ciudades), anclada al código de su municipio principal (Ciudad de México: 09015); el resto del país sin código ("Rest of the country"). Capas F, H. Las filas de cada persona suman su total.
| persona | municipality_code | metro_area | employed | interviews |

## fact_persona_segment
Persona × ciudad × tipo de comprador (cruce directo, nunca producto de porcentajes). Tipos: Government employee; Employee, firm 251+; Employee, firm 11-250; Employee, firm up to 10; Self-employed or employer; Other or unknown (Colombia corta en 200). ENOE 2025. Capa H. Las celdas de cada persona suman su total.
| persona | municipality_code | city | buyer_type | employed | interviews |

## fact_ict_by_sector
Personal TI (4 personas núcleo) por sector SCIAN del empleador; sector tecnológico = SCIAN 51 (ver la nota de `pct_outside_tech_sector`). Capa G. Suma = total de las 4 personas núcleo.
| sector | employed | share_pct |

## fact_schools_municipality
Escuelas con grados objetivo y sus estudiantes por municipio, ciclo 2025-2026. Grados objetivo: 3º de secundaria + 1º a 3º de media superior. Fuente: SEP Formato 911. Capa K.
| municipality_code | department_code | students_target | students_sec3 | students_ms1 | students_ms2 | students_ms3 | students_public | students_rural | schools | schools_public | reach_cap100 |

- Las columnas de grado sustituyen a `students_9_11`, `students_g9`… (Colombia tiene 3 grados objetivo; México tiene 4).
- Unidad "escuela" (plantel o clave de centro de trabajo): pendiente de decisión.

## fact_higher_ed_municipality
Matrícula de educación superior por municipio donde se ofrece el programa; la modalidad no escolarizada se registra en la sede. Fuente: SEP Formato 911 superior. Capas C, L.
| municipality_code | department_code | students_total | students_on_campus | students_ict_field |

## fact_micro_department
Micronegocios por estado: trabajadores por cuenta propia y empleadores cuya unidad tiene hasta 10 personas (respaldo de la plantilla; ENAMIN se descontinuó en 2012). Las bandas de la ENOE dan 1, 2-5 y 6-10, así que el límite de 9 de la plantilla no se puede aplicar (D-MX-10). ENOE 2025. Capa M.
| department_code | department | micro_businesses |

## fact_micro_national
Distribuciones nacionales de micronegocios. Dimensiones: total, activity, position, owner_sex, owner_age, informal_sector, accounts (P4G), premises (P4E), site_without_premises (P4F), zone. Sin variables digitales (M4 no disponible en 2025). ENOE 2025. Capa M.
| dimension | category | micro_businesses | pct |

## fact_companies_municipality — añadida para México
Establecimientos DENUE 05/2026 por municipio, una fila por cada municipio del catálogo (0 = ningún establecimiento registrado, no un dato faltante). Sustituye a `fact_companies_chamber` (Colombia cuenta por cámara de comercio). DENUE no tiene marca de renovación ni distingue empresas de establecimientos. Fuente: `scripts/build-mexico-denue.py`. Capas D, N. Filas: 2.478.
| municipality_code | department_code | establishments | businesses | shops_4711 | it_companies_active | it_541510 | it_518210 | it_519290 |

- `establishments`: todos los registros; suma = 6.138.075, el total publicado.
- `businesses` (N1): universo privado, como el RUES de Colombia: sin asociaciones (SCIAN 813), cooperativas (razón social) ni sector público (SCIAN 93 y clases "sector público") (`decisions_log.csv`, D-MX-04).
- `shops_4711` = SCIAN 461110 (tiendas de abarrotes, ultramarinos y misceláneas).
- `it_companies_active` = SCIAN 2018 541510 + 518210 + 519290, también por separado (D-MX-03). DENUE usa SCIAN 2018; no hay código propio de software, así que la columna `software_companies` prevista no existe.

## fact_companies_zone
Empresas privadas DENUE 05/2026 (universo N1) por zona de `geo_zone`; cada zona suma lo mismo que `businesses` de su municipio. Mismas columnas que Colombia, con los grupos del anexo 3 de la plantilla traducidos a clases privadas SCIAN 2018 (D-MX-06). Tamaño por personal ocupado: `micro` = 0 a 10 personas, `medium_large` = 51 o más (Colombia mide por activos: comparable solo en dirección). Capa J. Filas: 32.
| zone_id | zone_name | companies_total | micro | medium_large | software_it | design | accounting_audit | management_consulting | research_market_studies | higher_education_training | shops_4711 | private_schools |

## fact_population_municipality — añadida para México
Población a mitad de año por municipio. Fuente: CONAPO, proyecciones municipales. Capa E.
| municipality_code | department_code | year | population |

## fact_developers_country
GitHub Innovation Graph, Q1 2026: la fila `MX` de `data/geodb-v2/csv/fact_developers_country.csv`, comprobada campo por campo contra el motor de la capa A (`scripts/build-mexico-a-github.py`). Capa A. Filas: 1.
| iso2 | country | developers | developers_yoy_pct | organizations | organizations_yoy_pct | pushes_per_dev | enterprise_lang_share_pct |

## fact_map_indicator — formato de Perú
Indicadores nacionales sin geografía (capas A, B, I, O, P), con `scope_type=country`, `scope_id=MX`. Mismas columnas y construcción que `data/peru-map/fact_map_indicator.csv`; un `value` vacío es una celda suprimida, nunca cero.
| layer | metric_id | scope_type | scope_id | group_id | persona_id | indicator | category | value | unit | period | comparison_period | numerator | denominator | status | source_id | method | limitations |

- Capa A (25 filas): motor de Perú `layer_a_country.py` sin cambios, 2026Q1 frente a 2025Q1 (`scripts/build-mexico-a-github.py`).
- Capa B: motor de Perú `layer_b_engine.py` sin cambios, encuesta 2025, México como país foco y sus grupos de comparación (`scripts/build-mexico-b-survey.py`).

## meta_sources
Fuente y año de cada tabla.
| table_name | description | source | year |
