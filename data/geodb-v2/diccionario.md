# Base geoespacial de Colombia (v2)

Llave geográfica: DIVIPOLA (departamento 2 dígitos, municipio 5 dígitos); zonas de Bogotá y Medellín con zone_id. Todo es agregado.

## geo_department

Departments of Colombia (DIVIPOLA, 2 digits).

Fuente: DANE DIVIPOLA  
Filas: 33

| Columna | Tipo |
|---|---|
| department_code | TEXT |
| name | TEXT |

## geo_municipality

Municipalities with a reference point (DIVIPOLA, 5 digits). Municipalities created after the coordinate source (Nuevo Belén de Bajirá, 2022) have no point yet.

Fuente: MinSalud DIVIPOLA municipalities with coordinates, datos.gov.co pqwj-3fi4  
Filas: 1123

| Columna | Tipo |
|---|---|
| municipality_code | TEXT |
| department_code | TEXT |
| name | TEXT |
| lat | REAL |
| lon | REAL |
| wkt | TEXT |

## geo_zone

Zones inside the two largest cities: Bogotá localidades (with boundaries) and Medellín comunas and corregimientos (code and name only).

Fuente: Catastro Bogotá, datos abiertos de Bogotá ("Localidad. Bogotá D.C."); Medellín codes from the city's official division  
Filas: 41

| Columna | Tipo |
|---|---|
| zone_id | TEXT |
| municipality_code | TEXT |
| zone_type | TEXT |
| zone_code | TEXT |
| name | TEXT |
| lat | REAL |
| lon | REAL |
| geojson | TEXT |
| wkt | TEXT |

## fact_persona_profile

One row per persona: national profile, 2025 annual average.

Fuente: DANE GEIH 2025 microdata (geih-personas-colombia.py)  
Filas: 13

| Columna | Tipo |
|---|---|
| persona | TEXT |
| ring | TEXT |
| isco_codes | TEXT |
| employed | INTEGER |
| interviews | INTEGER |
| pct_private_employee | REAL |
| pct_government_employee | REAL |
| pct_self_employed_or_employer | REAL |
| pct_firm_201_plus | REAL |
| pct_works_alone | REAL |
| pct_outside_tech_sector | REAL |
| pct_women | REAL |
| pct_university | REAL |
| median_age | REAL |
| median_income_cop | REAL |
| pct_stratum_4_6 | REAL |
| pct_works_from_home | REAL |

## fact_persona_metro

People per persona by metropolitan area of the capitals (municipality_code = capital); "Rest of the country" has no code.

Fuente: DANE GEIH 2025  
Filas: 379

| Columna | Tipo |
|---|---|
| persona | TEXT |
| municipality_code | TEXT |
| metro_area | TEXT |
| employed | INTEGER |

## fact_persona_department

People per persona by department.

Fuente: DANE GEIH 2025  
Filas: 411

| Columna | Tipo |
|---|---|
| persona | TEXT |
| department_code | TEXT |
| department | TEXT |
| employed | INTEGER |

## fact_persona_segment

Persona × city × who buys (direct cross-tabulation).

Fuente: DANE GEIH 2025  
Filas: 346

| Columna | Tipo |
|---|---|
| persona | TEXT |
| municipality_code | TEXT |
| city | TEXT |
| buyer_type | TEXT |
| employed | INTEGER |
| interviews | INTEGER |

## fact_ict_by_sector

IT staff (4 core personas) by industry of the employer.

Fuente: DANE GEIH 2025  
Filas: 12

| Columna | Tipo |
|---|---|
| sector | TEXT |
| employed | INTEGER |
| share_pct | REAL |

## fact_schools_municipality

Schools with grades 9 to 11 and their students, by municipality, 2025. reach_cap100 = students reachable with up to 100 per school.

Fuente: MEN enrolment 2025, datos.gov.co ngw5-c5nw (colegios-colombia.py)  
Filas: 1119

| Columna | Tipo |
|---|---|
| municipality_code | TEXT |
| department_code | TEXT |
| students_9_11 | INTEGER |
| students_g9 | INTEGER |
| students_g10 | INTEGER |
| students_g11 | INTEGER |
| students_public | INTEGER |
| students_rural | INTEGER |
| schools | INTEGER |
| schools_public | INTEGER |
| reach_cap100 | INTEGER |

## fact_higher_ed_municipality

Higher-education students (2024-2) by municipality where the programme is offered. Online programmes sit at the institution's headquarters: use on_campus for local presence.

Fuente: MEN SNIES Bases consolidadas 2024 (educacion-superior-colombia.py)  
Filas: 421

| Columna | Tipo |
|---|---|
| municipality_code | TEXT |
| department_code | TEXT |
| students_total | INTEGER |
| students_on_campus | INTEGER |
| students_ict_field | INTEGER |

## fact_micro_department

Micro-businesses (up to 9 people, formal and informal) by department, 2024 (24 departments and Bogotá).

Fuente: DANE EMICRON 2024 microdata (micronegocios-colombia.py)  
Filas: 25

| Columna | Tipo |
|---|---|
| department_code | TEXT |
| department | TEXT |
| micro_businesses | INTEGER |

## fact_micro_national

National distributions of micro-businesses (activity, formality, technology, place, owner).

Fuente: DANE EMICRON 2024  
Filas: 79

| Columna | Tipo |
|---|---|
| dimension | TEXT |
| category | TEXT |
| micro_businesses | INTEGER |
| pct | REAL |

## fact_companies_chamber

Formal businesses by chamber of commerce: renewed in 2025 or 2026 (excluding non-profits and cooperatives), shops (ISIC 4711), and IT companies (ISIC 6201-6312, active). The chamber is located at its seat municipality (own mapping).

Fuente: RUES, datos.gov.co c82u-588k (rues-renovadas.py; build-colombia-city-layer.py)  
Filas: 58

| Columna | Tipo |
|---|---|
| chamber | TEXT |
| seat_municipality_code | TEXT |
| department_code | TEXT |
| businesses_renewed | INTEGER |
| shops_4711_renewed | INTEGER |
| it_companies_active | INTEGER |

## fact_companies_zone

Registered companies by zone: Bogotá (March 2026, active and renewed, size by assets) and Medellín (2022, no size). BOG-00 = no localidad recorded.

Fuente: SDDE and Cámara de Comercio de Bogotá, Dinámica empresarial; Cámara de Comercio de Medellín, datos.gov.co pb3w-3vmc  
Filas: 41

| Columna | Tipo |
|---|---|
| zone_id | TEXT |
| zone_name | TEXT |
| companies_total | INTEGER |
| micro | INTEGER |
| medium_large | INTEGER |
| software_it | INTEGER |
| design | INTEGER |
| accounting_audit | INTEGER |
| management_consulting | INTEGER |
| research_market_studies | INTEGER |
| higher_education_training | INTEGER |
| shops_4711 | INTEGER |
| private_schools | INTEGER |

## fact_developers_country

GitHub developers and organisations by Latin American country, Q1 2026.

Fuente: GitHub Innovation Graph (build-country-breakdown.py)  
Filas: 18

| Columna | Tipo |
|---|---|
| iso2 | TEXT |
| country | TEXT |
| developers | INTEGER |
| developers_yoy_pct | REAL |
| organizations | INTEGER |
| organizations_yoy_pct | REAL |
| pushes_per_dev | REAL |
| enterprise_lang_share_pct | REAL |

## meta_sources

Where every table comes from.

Fuente: This script  
Filas: 15

| Columna | Tipo |
|---|---|
| table_name | TEXT |
| description | TEXT |
| source | TEXT |

# Capas agregadas en la v2 (5-oct-2026)

## geo_department_shape

Department boundaries (polygons, WGS84, 3 decimals)

Fuente: DANE Marco Geoestadístico, via John Guerra (gist 43c7656821069d00dcbc)  
Filas: 33

| Columna | Tipo |
|---|---|
| department_code | TEXT |
| name | TEXT |
| geojson | TEXT |

## fact_secop_department

Public contracts for software and IT services signed in 2025, by department of the buyer

Fuente: SECOP II (datos.gov.co jbjy-vk9h), secop-software.py  
Filas: 32

| Columna | Tipo |
|---|---|
| department_code | TEXT |
| contracts_2025 | INTEGER |
| value_cop_2025 | INTEGER |

## fact_saber11_department

Saber 11 (2022-2), grade 11 students by department of the school

Fuente: ICFES (datos.gov.co kgxf-xxbe), saber11-colegios.py  
Filas: 33

| Columna | Tipo |
|---|---|
| department_code | TEXT |
| students_grade11 | INTEGER |
| math_mean | REAL |
| global_mean | REAL |
| computer_at_home_pct | REAL |
| internet_at_home_pct | REAL |

## fact_vacancies_department

Active job offers by keyword and department, snapshot of 2026-10-01 (national offers without department excluded)

Fuente: Servicio Público de Empleo, Buscador de Empleo  
Filas: 212

| Columna | Tipo |
|---|---|
| keyword | TEXT |
| department_code | TEXT |
| offers | INTEGER |

## fact_em2021_localidad

People in the 13 personas and household connectivity by localidad of Bogotá (2021)

Fuente: DANE and SDP, Encuesta Multipropósito 2021, em2021-bogota-personas.py  
Filas: 20

| Columna | Tipo |
|---|---|
| zone_id | TEXT |
| localidad | TEXT |
| population | INTEGER |
| employed | INTEGER |
| personas13 | INTEGER |
| core_it | INTEGER |
| personas13_per_1000_employed | REAL |
| core_it_per_1000_employed | REAL |
| hh_computer_pct | REAL |
| hh_internet_pct | REAL |
| telework_pct_of_employed | REAL |

## fact_em2021_upz

People in the 13 personas by UPZ of Bogotá (2021); reliable = 30+ interviews

Fuente: Encuesta Multipropósito 2021  
Filas: 96

| Columna | Tipo |
|---|---|
| upz_code | TEXT |
| upz_name | TEXT |
| localidad_code | TEXT |
| reliable | INTEGER |
| population | INTEGER |
| employed | INTEGER |
| personas13 | INTEGER |
| core_it | INTEGER |
| personas13_per_1000_employed | REAL |
| core_it_per_1000_employed | REAL |
| hh_computer_pct | REAL |
| hh_internet_pct | REAL |
| telework_pct_of_employed | REAL |

## fact_dev_communities

Technology Meetup groups with 300+ members (lifetime sign-ups), 2026-10-02

Fuente: meetup.com group search  
Filas: 44

| Columna | Tipo |
|---|---|
| municipality_code | TEXT |
| city | TEXT |
| platform | TEXT |
| name | TEXT |
| members | INTEGER |
| topic | TEXT |

## fact_tech_events

Main technology and AI events in Colombia, 2026 editions

Fuente: Official event sites and press  
Filas: 6

| Columna | Tipo |
|---|---|
| municipality_code | TEXT |
| city | TEXT |
| name | TEXT |
| date_2026 | TEXT |
| size | TEXT |
