-- LATAM Market Intelligence - Geo DB Colombia (v2), MySQL 8 schema
-- Translated from data/geodb-v2/schema_postgres.sql + diccionario.md
-- CSV headers are authoritative: column names kept untranslated.
-- DIVIPOLA codes are VARCHAR (leading zeros). Spatial columns use SRID 4326.
-- Load geometry with ST_GeomFromText(wkt, 4326, 'axis-order=long-lat').
-- Idempotent: every table is dropped and recreated (children first).

SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS validation_issue;
DROP TABLE IF EXISTS load_batch;
DROP TABLE IF EXISTS meta_sources;
DROP TABLE IF EXISTS meta_geo_zone;
DROP TABLE IF EXISTS meta_companies_zone;
DROP TABLE IF EXISTS fact_zone_indicator;
DROP TABLE IF EXISTS fact_persona_segment_metro_2025;
DROP TABLE IF EXISTS fact_geih2025_metro_summary;
DROP TABLE IF EXISTS fact_persona_profile_metro_2025;
DROP TABLE IF EXISTS fact_zone_context;
DROP TABLE IF EXISTS fact_tech_events;
DROP TABLE IF EXISTS fact_dev_communities;
DROP TABLE IF EXISTS fact_em2021_upz;
DROP TABLE IF EXISTS fact_em2021_localidad;
DROP TABLE IF EXISTS fact_vacancies_department;
DROP TABLE IF EXISTS fact_saber11_department;
DROP TABLE IF EXISTS fact_secop_department;
DROP TABLE IF EXISTS fact_developers_country;
DROP TABLE IF EXISTS fact_companies_zone;
DROP TABLE IF EXISTS fact_companies_chamber;
DROP TABLE IF EXISTS fact_micro_national;
DROP TABLE IF EXISTS fact_micro_department;
DROP TABLE IF EXISTS fact_higher_ed_municipality;
DROP TABLE IF EXISTS fact_schools_municipality;
DROP TABLE IF EXISTS fact_ict_by_sector;
DROP TABLE IF EXISTS fact_persona_segment;
DROP TABLE IF EXISTS fact_persona_department;
DROP TABLE IF EXISTS fact_persona_metro;
DROP TABLE IF EXISTS fact_persona_profile;
DROP TABLE IF EXISTS geo_department_shape;
DROP TABLE IF EXISTS geo_zone;
DROP TABLE IF EXISTS geo_municipality;
DROP TABLE IF EXISTS geo_department;

SET FOREIGN_KEY_CHECKS = 1;

-- ===================== GEO =====================

CREATE TABLE IF NOT EXISTS geo_department (
  department_code VARCHAR(2) NOT NULL,
  name VARCHAR(150) NOT NULL,
  point POINT SRID 4326 NULL COMMENT 'Average of its municipalities points (or NULL)',
  PRIMARY KEY (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS geo_municipality (
  municipality_code VARCHAR(5) NOT NULL,
  department_code VARCHAR(2) NOT NULL,
  name VARCHAR(150) NOT NULL,
  lat DOUBLE NULL,
  lon DOUBLE NULL,
  wkt TEXT NULL COMMENT 'POINT(lon lat) as in CSV',
  point POINT SRID 4326 NULL COMMENT 'NULL for 27493 Nuevo Belen de Bajira',
  PRIMARY KEY (municipality_code),
  KEY idx_geo_municipality_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS geo_zone (
  zone_id VARCHAR(10) NOT NULL,
  municipality_code VARCHAR(5) NOT NULL,
  zone_type VARCHAR(40) NOT NULL,
  zone_code VARCHAR(4) NOT NULL,
  name VARCHAR(150) NOT NULL,
  lat DOUBLE NULL,
  lon DOUBLE NULL,
  geojson LONGTEXT NULL,
  wkt LONGTEXT NULL,
  geometry GEOMETRY SRID 4326 NULL COMMENT 'Bogota localidades only, Medellin comunas without geometry (license)',
  PRIMARY KEY (zone_id),
  UNIQUE KEY uq_geo_zone_muni_code (municipality_code, zone_code),
  KEY idx_geo_zone_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS geo_department_shape (
  department_code VARCHAR(2) NOT NULL,
  name VARCHAR(150) NOT NULL,
  geojson LONGTEXT NOT NULL COMMENT 'GeoJSON WGS84 long-lat, validate with ST_GeomFromGeoJSON',
  PRIMARY KEY (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== PERSONAS (GEIH 2025) =====================

CREATE TABLE IF NOT EXISTS fact_persona_profile (
  persona VARCHAR(150) NOT NULL,
  ring VARCHAR(40) NULL,
  isco_codes VARCHAR(255) NULL,
  employed BIGINT NULL,
  interviews BIGINT NULL,
  pct_private_employee DOUBLE NULL,
  pct_government_employee DOUBLE NULL,
  pct_self_employed_or_employer DOUBLE NULL,
  pct_firm_201_plus DOUBLE NULL,
  pct_works_alone DOUBLE NULL,
  pct_outside_tech_sector DOUBLE NULL,
  pct_women DOUBLE NULL,
  pct_university DOUBLE NULL,
  median_age DOUBLE NULL,
  median_income_cop DOUBLE NULL,
  pct_stratum_4_6 DOUBLE NULL,
  pct_works_from_home DOUBLE NULL,
  PRIMARY KEY (persona)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_persona_metro (
  id INT NOT NULL AUTO_INCREMENT,
  persona VARCHAR(150) NOT NULL,
  municipality_code VARCHAR(5) NULL COMMENT 'NULL for Rest of the country',
  metro_area VARCHAR(150) NOT NULL,
  employed BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fpm_persona (persona),
  KEY idx_fpm_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_persona_department (
  id INT NOT NULL AUTO_INCREMENT,
  persona VARCHAR(150) NOT NULL,
  department_code VARCHAR(2) NULL,
  department VARCHAR(150) NULL,
  employed BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fpd_persona (persona),
  KEY idx_fpd_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_persona_segment (
  id INT NOT NULL AUTO_INCREMENT,
  persona VARCHAR(150) NOT NULL,
  municipality_code VARCHAR(5) NULL COMMENT 'NULL for Rest of the country',
  city VARCHAR(150) NOT NULL,
  buyer_type VARCHAR(150) NULL,
  employed BIGINT NULL,
  interviews BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fps_persona (persona),
  KEY idx_fps_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_ict_by_sector (
  id INT NOT NULL AUTO_INCREMENT,
  sector VARCHAR(255) NOT NULL,
  employed BIGINT NULL,
  share_pct DOUBLE NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== EDUCATION =====================

CREATE TABLE IF NOT EXISTS fact_schools_municipality (
  id INT NOT NULL AUTO_INCREMENT,
  municipality_code VARCHAR(5) NOT NULL,
  department_code VARCHAR(2) NOT NULL,
  students_9_11 BIGINT NULL,
  students_g9 BIGINT NULL,
  students_g10 BIGINT NULL,
  students_g11 BIGINT NULL,
  students_public BIGINT NULL,
  students_rural BIGINT NULL,
  schools BIGINT NULL,
  schools_public BIGINT NULL,
  reach_cap100 BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fsm_municipality (municipality_code),
  KEY idx_fsm_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_higher_ed_municipality (
  id INT NOT NULL AUTO_INCREMENT,
  municipality_code VARCHAR(5) NOT NULL,
  department_code VARCHAR(2) NOT NULL,
  students_total BIGINT NULL,
  students_on_campus BIGINT NULL,
  students_ict_field BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fhe_municipality (municipality_code),
  KEY idx_fhe_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_saber11_department (
  id INT NOT NULL AUTO_INCREMENT,
  department_code VARCHAR(2) NOT NULL,
  students_grade11 BIGINT NULL,
  math_mean DOUBLE NULL,
  global_mean DOUBLE NULL,
  computer_at_home_pct DOUBLE NULL,
  internet_at_home_pct DOUBLE NULL,
  PRIMARY KEY (id),
  KEY idx_fs11_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== BUSINESSES =====================

CREATE TABLE IF NOT EXISTS fact_micro_department (
  id INT NOT NULL AUTO_INCREMENT,
  department_code VARCHAR(2) NOT NULL,
  department VARCHAR(150) NULL,
  micro_businesses BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fmd_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_micro_national (
  id INT NOT NULL AUTO_INCREMENT,
  dimension VARCHAR(100) NOT NULL,
  category VARCHAR(255) NOT NULL,
  micro_businesses BIGINT NULL,
  pct DOUBLE NULL,
  PRIMARY KEY (id),
  KEY idx_fmn_dimension (dimension)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_companies_chamber (
  id INT NOT NULL AUTO_INCREMENT,
  chamber VARCHAR(150) NOT NULL,
  seat_municipality_code VARCHAR(5) NULL,
  department_code VARCHAR(2) NULL,
  businesses_renewed BIGINT NULL,
  shops_4711_renewed BIGINT NULL,
  it_companies_active BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fcc_municipality (seat_municipality_code),
  KEY idx_fcc_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_companies_zone (
  id INT NOT NULL AUTO_INCREMENT,
  zone_id VARCHAR(10) NOT NULL COMMENT 'BOG-00 = no localidad recorded (approved exception)',
  zone_name VARCHAR(150) NULL,
  companies_total BIGINT NULL,
  micro BIGINT NULL,
  medium_large BIGINT NULL,
  software_it BIGINT NULL,
  design BIGINT NULL,
  accounting_audit BIGINT NULL,
  management_consulting BIGINT NULL,
  research_market_studies BIGINT NULL,
  higher_education_training BIGINT NULL,
  shops_4711 BIGINT NULL,
  private_schools BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fcz_zone (zone_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_secop_department (
  id INT NOT NULL AUTO_INCREMENT,
  department_code VARCHAR(2) NOT NULL,
  contracts_2025 BIGINT NULL,
  value_cop_2025 BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fsd_department (department_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_vacancies_department (
  id INT NOT NULL AUTO_INCREMENT,
  keyword VARCHAR(150) NOT NULL,
  department_code VARCHAR(2) NOT NULL,
  offers BIGINT NULL,
  PRIMARY KEY (id),
  KEY idx_fvd_department (department_code),
  KEY idx_fvd_keyword (keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== TECH ECOSYSTEM =====================

CREATE TABLE IF NOT EXISTS fact_developers_country (
  id INT NOT NULL AUTO_INCREMENT,
  iso2 VARCHAR(2) NOT NULL,
  country VARCHAR(150) NOT NULL,
  developers BIGINT NULL,
  developers_yoy_pct DOUBLE NULL,
  organizations BIGINT NULL,
  organizations_yoy_pct DOUBLE NULL,
  pushes_per_dev DOUBLE NULL,
  enterprise_lang_share_pct DOUBLE NULL,
  PRIMARY KEY (id),
  KEY idx_fdc_iso2 (iso2)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_dev_communities (
  id INT NOT NULL AUTO_INCREMENT,
  municipality_code VARCHAR(5) NOT NULL,
  city VARCHAR(150) NULL,
  platform VARCHAR(60) NULL,
  name VARCHAR(255) NOT NULL,
  members BIGINT NULL,
  topic VARCHAR(100) NULL,
  PRIMARY KEY (id),
  KEY idx_fdcom_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_tech_events (
  id INT NOT NULL AUTO_INCREMENT,
  municipality_code VARCHAR(5) NOT NULL,
  city VARCHAR(150) NULL,
  name VARCHAR(255) NOT NULL,
  date_2026 VARCHAR(100) NULL,
  size VARCHAR(255) NULL,
  PRIMARY KEY (id),
  KEY idx_fte_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== BOGOTA EM2021 =====================

CREATE TABLE IF NOT EXISTS fact_em2021_localidad (
  id INT NOT NULL AUTO_INCREMENT,
  zone_id VARCHAR(10) NOT NULL,
  localidad VARCHAR(150) NULL,
  population BIGINT NULL,
  employed BIGINT NULL,
  personas13 BIGINT NULL,
  core_it BIGINT NULL,
  personas13_per_1000_employed DOUBLE NULL,
  core_it_per_1000_employed DOUBLE NULL,
  hh_computer_pct DOUBLE NULL,
  hh_internet_pct DOUBLE NULL,
  telework_pct_of_employed DOUBLE NULL,
  PRIMARY KEY (id),
  KEY idx_fel_zone (zone_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_em2021_upz (
  id INT NOT NULL AUTO_INCREMENT,
  upz_code VARCHAR(10) NOT NULL,
  upz_name VARCHAR(150) NULL,
  localidad_code VARCHAR(2) NOT NULL COMMENT '01-20 = geo_zone.zone_code with municipality_code 11001',
  reliable INT NULL,
  population BIGINT NULL,
  employed BIGINT NULL,
  personas13 BIGINT NULL,
  core_it BIGINT NULL,
  personas13_per_1000_employed DOUBLE NULL,
  core_it_per_1000_employed DOUBLE NULL,
  hh_computer_pct DOUBLE NULL,
  hh_internet_pct DOUBLE NULL,
  telework_pct_of_employed DOUBLE NULL,
  PRIMARY KEY (id),
  KEY idx_feu_upz (upz_code),
  KEY idx_feu_localidad (localidad_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== MEDELLIN / CALI (paquete think4ever personas) =====================
-- No persona counts by zone outside Bogotá: fact_zone_context.personas13 stays NULL.

CREATE TABLE IF NOT EXISTS fact_zone_context (
  id INT NOT NULL AUTO_INCREMENT,
  zone_id VARCHAR(10) NOT NULL,
  municipality_code VARCHAR(5) NOT NULL,
  zone_type VARCHAR(40) NULL,
  zone_name VARCHAR(150) NULL,
  reference_year INT NULL,
  population BIGINT NULL,
  employed BIGINT NULL,
  personas13 BIGINT NULL COMMENT 'Always NULL: no persona counts by zone outside Bogota',
  core_it BIGINT NULL,
  hh_computer_pct DOUBLE NULL,
  hh_internet_pct DOUBLE NULL,
  hh_computer_or_tablet_pct DOUBLE NULL,
  dwelling_internet_pct DOUBLE NULL,
  adults_university_pct DOUBLE NULL,
  population_18_34_pct DOUBLE NULL,
  telework_pct_of_employed DOUBLE NULL,
  source_id VARCHAR(64) NULL,
  personas_status VARCHAR(64) NULL,
  boundary_comparability VARCHAR(100) NULL,
  PRIMARY KEY (id),
  KEY idx_fzc_zone (zone_id),
  KEY idx_fzc_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_persona_profile_metro_2025 (
  id INT NOT NULL AUTO_INCREMENT,
  persona VARCHAR(150) NOT NULL,
  municipality_code VARCHAR(5) NOT NULL,
  metro_area VARCHAR(150) NULL,
  survey_year INT NULL,
  geographic_scope VARCHAR(40) NULL,
  employed BIGINT NULL,
  employed_unrounded DOUBLE NULL,
  sample_records INT NULL,
  sample_flag VARCHAR(64) NULL,
  months INT NULL,
  per_1000_employed DOUBLE NULL,
  median_age DOUBLE NULL,
  median_income_cop DOUBLE NULL,
  income_positive_records INT NULL,
  pct_women DOUBLE NULL,
  pct_university DOUBLE NULL,
  pct_private_employee DOUBLE NULL,
  pct_government_employee DOUBLE NULL,
  pct_self_employed_or_employer DOUBLE NULL,
  pct_firm_201_plus DOUBLE NULL,
  pct_workplace_at_home DOUBLE NULL,
  source_id VARCHAR(64) NULL,
  method VARCHAR(100) NULL,
  PRIMARY KEY (id),
  KEY idx_fppm_persona (persona),
  KEY idx_fppm_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_geih2025_metro_summary (
  id INT NOT NULL AUTO_INCREMENT,
  municipality_code VARCHAR(5) NOT NULL,
  metro_area VARCHAR(150) NULL,
  geographic_scope VARCHAR(40) NULL,
  survey_year INT NULL,
  employed BIGINT NULL,
  personas13 BIGINT NULL,
  core_it BIGINT NULL,
  personas13_per_1000_employed DOUBLE NULL,
  sample_employed_records INT NULL,
  sample_personas13_records INT NULL,
  source_id VARCHAR(64) NULL,
  PRIMARY KEY (id),
  KEY idx_fgms_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== CALI (paquete think4ever_cali_solo) =====================
-- GEIH figures are Cali–Yumbo domain totals: never split by comuna.

CREATE TABLE IF NOT EXISTS fact_persona_segment_metro_2025 (
  persona VARCHAR(150) NOT NULL,
  municipality_code VARCHAR(5) NOT NULL,
  city VARCHAR(150) NULL,
  buyer_type VARCHAR(150) NOT NULL,
  employed BIGINT NULL,
  interviews BIGINT NULL,
  survey_year INT NOT NULL,
  geographic_scope VARCHAR(40) NULL,
  source_id VARCHAR(64) NULL,
  PRIMARY KEY (persona, municipality_code, buyer_type, survey_year),
  KEY idx_fpsm_municipality (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fact_zone_indicator (
  zone_id VARCHAR(10) NOT NULL,
  indicator VARCHAR(64) NOT NULL,
  value DOUBLE NULL,
  unit VARCHAR(40) NULL,
  reference_year INT NOT NULL,
  source_id VARCHAR(64) NULL,
  method VARCHAR(150) NULL,
  geographic_scope VARCHAR(40) NULL,
  PRIMARY KEY (zone_id, indicator, reference_year)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meta_companies_zone (
  zone_id VARCHAR(10) NOT NULL,
  source_id VARCHAR(64) NULL,
  reference_year INT NULL,
  source_url VARCHAR(255) NULL,
  unit VARCHAR(64) NULL,
  size_basis VARCHAR(100) NULL,
  scope VARCHAR(64) NULL,
  status VARCHAR(100) NULL,
  PRIMARY KEY (zone_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS meta_geo_zone (
  municipality_code VARCHAR(5) NOT NULL,
  source VARCHAR(255) NULL,
  geometry_year INT NULL,
  license_status VARCHAR(150) NULL,
  attribution TEXT NULL,
  PRIMARY KEY (municipality_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ===================== META / LOAD / VALIDATION =====================

CREATE TABLE IF NOT EXISTS meta_sources (
  table_name VARCHAR(64) NOT NULL,
  description TEXT NULL,
  source TEXT NULL,
  year VARCHAR(64) NULL COMMENT 'Not in CSV, filled from seeds',
  PRIMARY KEY (table_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS load_batch (
  id INT NOT NULL AUTO_INCREMENT,
  source_file VARCHAR(255) NULL,
  status ENUM('running','validated','failed') NOT NULL DEFAULT 'running',
  rows_loaded INT NOT NULL DEFAULT 0,
  started_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  finished_at DATETIME NULL,
  notes TEXT NULL,
  PRIMARY KEY (id),
  KEY idx_load_batch_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS validation_issue (
  id INT NOT NULL AUTO_INCREMENT,
  batch_id INT NOT NULL,
  issue_type ENUM('unjoined_code','count_mismatch','total_mismatch','missing_source','no_geography_exception') NOT NULL,
  severity ENUM('error','info') NOT NULL DEFAULT 'error',
  table_name VARCHAR(64) NULL,
  column_name VARCHAR(64) NULL,
  code_value VARCHAR(64) NULL,
  expected_value VARCHAR(64) NULL,
  actual_value VARCHAR(64) NULL,
  message TEXT NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_vi_batch (batch_id),
  KEY idx_vi_severity (severity),
  CONSTRAINT fk_validation_issue_batch FOREIGN KEY (batch_id) REFERENCES load_batch (id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;