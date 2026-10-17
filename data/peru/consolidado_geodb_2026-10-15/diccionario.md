# Base geoespacial de Perú (consolidado)

Llave geográfica: UBIGEO (departamento 2 dígitos, distrito 6 dígitos). Todo es agregado.

## geo_department
Departamentos del Perú (UBIGEO, 2 dígitos). Fuente: INEI proyecciones 2018-2026. Filas: 25.
| Columna | Tipo |
|---|---|
| department_code | TEXT |
| name | TEXT |

## geo_municipality
Distritos del Perú (UBIGEO, 6 dígitos) con población 2025. Fuente: IGN límites distritales 2022 + INEI proyecciones. Filas: 1.892.
**lat/lon en NULL**: las coordenadas de capital distrital requieren la fuente oficial (IGN capitales distritales o INEI centros poblados); no se calcularon centroides.
| Columna | Tipo |
|---|---|
| municipality_code | TEXT |
| department_code | TEXT |
| name | TEXT |
| lat | REAL (NULL) |
| lon | REAL (NULL) |

## fact_persona_profile
Una fila por persona: perfil nacional, ENAHO 2024 (promedio anual). Fuente: INEI ENAHO 2024 microdato (módulos 100/200/300/500). Filas: 13.
| Columna | Tipo |
|---|---|
| persona | TEXT |
| ring | TEXT |
| isco_codes | TEXT |
| employed | BIGINT |
| interviews | BIGINT |
| pct_private_employee | REAL |
| pct_government_employee | REAL |
| pct_self_employed_or_employer | REAL |
| pct_firm_201_plus | REAL |
| pct_works_alone | REAL |
| pct_outside_tech_sector | REAL |
| pct_women | REAL |
| pct_university | REAL |
| median_age | REAL |
| median_income_pen | REAL |
| pct_stratum_4_6 | REAL |
| pct_works_from_home | REAL |

**Nota**: pct_government_employee usa ISIC sección O (administración pública) como proxy de cota inferior; docentes y salud públicos (secciones P y Q) no se separan por gestión en ENAHO P507.

## fact_persona_department
Personas por persona por departamento. Fuente: ENAHO 2024. Filas: 228.
| persona | department_code | employed |

## fact_ict_by_sector
Core IT (4 personas) por rama de actividad (ISIC Rev 4, sección). Fuente: ENAHO 2024. Filas: 18.
| sector | employed | share_pct |

## fact_schools_municipality
Matrícula secundaria 3º-5º por distrito, 2025. Fuente: MINEDU SIAGIE Reporte Matrícula 2025. Filas: 1.848.
**students_rural en NULL** (área urbana/rural está en el padrón, no en SIAGIE).
| Columna | Tipo |
|---|---|
| municipality_code | TEXT |
| department_code | TEXT |
| students_3_5 | BIGINT |
| students_g3 | BIGINT |
| students_g4 | BIGINT |
| students_g5 | BIGINT |
| students_public | BIGINT |
| students_rural | BIGINT (NULL) |
| schools | BIGINT |
| schools_public | BIGINT |
| reach_cap100 | BIGINT |

## fact_micro_national
Micronegocios nacionales por dimensión (independientes P507=2 + empleadores P507=1). Fuente: ENAHO 2024. Filas: 21.
| dimension | category | micro_businesses | pct |

## fact_micro_department
Micronegocios por departamento. Fuente: ENAHO 2024. Filas: 25.
| department_code | micro_businesses |

## fact_developers_country
Desarrolladores GitHub Perú, Q1 2026. Fuente: GitHub Innovation Graph (capa A). Filas: 1.
| iso2 | country | developers | developers_yoy_pct | organizations | organizations_yoy_pct | pushes_per_dev | enterprise_lang_share_pct |

## fact_higher_ed_municipality — BLOQUEADO
Educación superior por distrito. SUNEDU solo publica visor TUNI (sin descarga). Solicitud formal pendiente (requests/solicitud_sunedu_matricula_agregada.md).

## fact_companies_chamber / fact_companies_zone — BLOQUEADO
Empresas formales por cámara/zona. El padrón RUC completo requiere Clave SOL (SUNAT). Solicitud formal pendiente. Sustituto: MTPE Leyendo Números (374.655 empresas por sector/región) en normalized/employment/.

## meta_sources
Procedencia de cada tabla. Filas: 12.

## Regla de carga
Códigos UBIGEO como TEXT con ceros a la izquierda. Ninguna ausencia se convierte en cero. Cargar con \copy (CSV HEADER). Para geo_municipality, cuando se obtengan las coordenadas oficiales, construir geom = ST_SetSRID(ST_MakePoint(lon,lat),4326).
