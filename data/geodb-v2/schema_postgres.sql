-- Think4Ever, base geoespacial de Colombia v1 (PostgreSQL + PostGIS)
CREATE EXTENSION IF NOT EXISTS postgis;

-- Departments of Colombia (DIVIPOLA, 2 digits).
-- Source: DANE DIVIPOLA
CREATE TABLE geo_department (
  department_code text,
  name text
);

-- Municipalities with a reference point (DIVIPOLA, 5 digits). Municipalities created after the coordinate source (Nuevo Belén de Bajirá, 2022) have no point yet.
-- Source: MinSalud DIVIPOLA municipalities with coordinates, datos.gov.co pqwj-3fi4
CREATE TABLE geo_municipality (
  municipality_code text,
  department_code text,
  name text,
  lat double precision,
  lon double precision,
  geom geometry(Point, 4326)
);

-- Zones inside the two largest cities: Bogotá localidades (with boundaries) and Medellín comunas and corregimientos (code and name only).
-- Source: Catastro Bogotá, datos abiertos de Bogotá ("Localidad. Bogotá D.C."); Medellín codes from the city's official division
CREATE TABLE geo_zone (
  zone_id text,
  municipality_code text,
  zone_type text,
  zone_code text,
  name text,
  lat double precision,
  lon double precision,
  geom geometry(MultiPolygon, 4326)
);

-- One row per persona: national profile, 2025 annual average.
-- Source: DANE GEIH 2025 microdata (geih-personas-colombia.py)
CREATE TABLE fact_persona_profile (
  persona text,
  ring text,
  isco_codes text,
  employed bigint,
  interviews bigint,
  pct_private_employee double precision,
  pct_government_employee double precision,
  pct_self_employed_or_employer double precision,
  pct_firm_201_plus double precision,
  pct_works_alone double precision,
  pct_outside_tech_sector double precision,
  pct_women double precision,
  pct_university double precision,
  median_age double precision,
  median_income_cop double precision,
  pct_stratum_4_6 double precision,
  pct_works_from_home double precision
);

-- People per persona by metropolitan area of the capitals (municipality_code = capital); "Rest of the country" has no code.
-- Source: DANE GEIH 2025
CREATE TABLE fact_persona_metro (
  persona text,
  municipality_code text,
  metro_area text,
  employed bigint
);

-- People per persona by department.
-- Source: DANE GEIH 2025
CREATE TABLE fact_persona_department (
  persona text,
  department_code text,
  department text,
  employed bigint
);

-- Persona × city × who buys (direct cross-tabulation).
-- Source: DANE GEIH 2025
CREATE TABLE fact_persona_segment (
  persona text,
  municipality_code text,
  city text,
  buyer_type text,
  employed bigint,
  interviews bigint
);

-- IT staff (4 core personas) by industry of the employer.
-- Source: DANE GEIH 2025
CREATE TABLE fact_ict_by_sector (
  sector text,
  employed bigint,
  share_pct double precision
);

-- Schools with grades 9 to 11 and their students, by municipality, 2025. reach_cap100 = students reachable with up to 100 per school.
-- Source: MEN enrolment 2025, datos.gov.co ngw5-c5nw (colegios-colombia.py)
CREATE TABLE fact_schools_municipality (
  municipality_code text,
  department_code text,
  students_9_11 bigint,
  students_g9 bigint,
  students_g10 bigint,
  students_g11 bigint,
  students_public bigint,
  students_rural bigint,
  schools bigint,
  schools_public bigint,
  reach_cap100 bigint
);

-- Higher-education students (2024-2) by municipality where the programme is offered. Online programmes sit at the institution's headquarters: use on_campus for local presence.
-- Source: MEN SNIES Bases consolidadas 2024 (educacion-superior-colombia.py)
CREATE TABLE fact_higher_ed_municipality (
  municipality_code text,
  department_code text,
  students_total bigint,
  students_on_campus bigint,
  students_ict_field bigint
);

-- Micro-businesses (up to 9 people, formal and informal) by department, 2024 (24 departments and Bogotá).
-- Source: DANE EMICRON 2024 microdata (micronegocios-colombia.py)
CREATE TABLE fact_micro_department (
  department_code text,
  department text,
  micro_businesses bigint
);

-- National distributions of micro-businesses (activity, formality, technology, place, owner).
-- Source: DANE EMICRON 2024
CREATE TABLE fact_micro_national (
  dimension text,
  category text,
  micro_businesses bigint,
  pct double precision
);

-- Formal businesses by chamber of commerce: renewed in 2025 or 2026 (excluding non-profits and cooperatives), shops (ISIC 4711), and IT companies (ISIC 6201-6312, active). The chamber is located at its seat municipality (own mapping).
-- Source: RUES, datos.gov.co c82u-588k (rues-renovadas.py; build-colombia-city-layer.py)
CREATE TABLE fact_companies_chamber (
  chamber text,
  seat_municipality_code text,
  department_code text,
  businesses_renewed bigint,
  shops_4711_renewed bigint,
  it_companies_active bigint
);

-- Registered companies by zone: Bogotá (March 2026, active and renewed, size by assets) and Medellín (2022, no size). BOG-00 = no localidad recorded.
-- Source: SDDE and Cámara de Comercio de Bogotá, Dinámica empresarial; Cámara de Comercio de Medellín, datos.gov.co pb3w-3vmc
CREATE TABLE fact_companies_zone (
  zone_id text,
  zone_name text,
  companies_total bigint,
  micro bigint,
  medium_large bigint,
  software_it bigint,
  design bigint,
  accounting_audit bigint,
  management_consulting bigint,
  research_market_studies bigint,
  higher_education_training bigint,
  shops_4711 bigint,
  private_schools bigint
);

-- GitHub developers and organisations by Latin American country, Q1 2026.
-- Source: GitHub Innovation Graph (build-country-breakdown.py)
CREATE TABLE fact_developers_country (
  iso2 text,
  country text,
  developers bigint,
  developers_yoy_pct double precision,
  organizations bigint,
  organizations_yoy_pct double precision,
  pushes_per_dev double precision,
  enterprise_lang_share_pct double precision
);

-- Where every table comes from.
-- Source: This script
CREATE TABLE meta_sources (
  table_name text,
  description text,
  source text
);

-- Load: \copy each table from csv/<table>.csv (CSV HEADER); for geo tables load wkt into a text column and set geom = ST_GeomFromText(wkt, 4326).
CREATE INDEX ON geo_municipality USING gist (geom);
CREATE INDEX ON geo_zone USING gist (geom);
-- ===== v2 (2026-10-05): layers from parts 8 and 9 =====
-- Department boundaries (polygons, WGS84, 3 decimals)
-- Source: DANE Marco Geoestadístico, via John Guerra (gist 43c7656821069d00dcbc)
CREATE TABLE geo_department_shape (
  department_code text,
  name text,
  geom geometry(MultiPolygon, 4326)
);

-- Public contracts for software and IT services signed in 2025, by department of the buyer
-- Source: SECOP II (datos.gov.co jbjy-vk9h), secop-software.py
CREATE TABLE fact_secop_department (
  department_code text,
  contracts_2025 bigint,
  value_cop_2025 bigint
);

-- Saber 11 (2022-2), grade 11 students by department of the school
-- Source: ICFES (datos.gov.co kgxf-xxbe), saber11-colegios.py
CREATE TABLE fact_saber11_department (
  department_code text,
  students_grade11 bigint,
  math_mean double precision,
  global_mean double precision,
  computer_at_home_pct double precision,
  internet_at_home_pct double precision
);

-- Active job offers by keyword and department, snapshot of 2026-10-01 (national offers without department excluded)
-- Source: Servicio Público de Empleo, Buscador de Empleo
CREATE TABLE fact_vacancies_department (
  keyword text,
  department_code text,
  offers bigint
);

-- People in the 13 personas and household connectivity by localidad of Bogotá (2021)
-- Source: DANE and SDP, Encuesta Multipropósito 2021, em2021-bogota-personas.py
CREATE TABLE fact_em2021_localidad (
  zone_id text,
  localidad text,
  population bigint,
  employed bigint,
  personas13 bigint,
  core_it bigint,
  personas13_per_1000_employed double precision,
  core_it_per_1000_employed double precision,
  hh_computer_pct double precision,
  hh_internet_pct double precision,
  telework_pct_of_employed double precision
);

-- People in the 13 personas by UPZ of Bogotá (2021); reliable = 30+ interviews
-- Source: Encuesta Multipropósito 2021
CREATE TABLE fact_em2021_upz (
  upz_code text,
  upz_name text,
  localidad_code text,
  reliable bigint,
  population bigint,
  employed bigint,
  personas13 bigint,
  core_it bigint,
  personas13_per_1000_employed double precision,
  core_it_per_1000_employed double precision,
  hh_computer_pct double precision,
  hh_internet_pct double precision,
  telework_pct_of_employed double precision
);

-- Technology Meetup groups with 300+ members (lifetime sign-ups), 2026-10-02
-- Source: meetup.com group search
CREATE TABLE fact_dev_communities (
  municipality_code text,
  city text,
  platform text,
  name text,
  members bigint,
  topic text
);

-- Main technology and AI events in Colombia, 2026 editions
-- Source: Official event sites and press
CREATE TABLE fact_tech_events (
  municipality_code text,
  city text,
  name text,
  date_2026 text,
  size text
);

-- geo_department_shape: load geojson as text and set geom = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(geojson), 4326)).
