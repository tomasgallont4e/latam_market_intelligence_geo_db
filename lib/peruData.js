'use strict';
// Read-only adapter for the supplied Peru consolidation. National facts stay
// national; persona geography is presented separately as a labelled model.
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..', 'data', 'peru-map');
const CONSOLIDATED_ROOT = path.join(__dirname, '..', 'data', 'peru', 'consolidado_geodb_2026-10-15');
let cache = null;
const read = (name) => JSON.parse(fs.readFileSync(path.join(ROOT, name), 'utf8'));
function parseCsv(text) {
  const rows = []; let row = []; let cell = ''; let quoted = false;
  for (let i = 0; i < text.length; i += 1) {
    const ch = text[i];
    if (ch === '"') {
      if (quoted && text[i + 1] === '"') { cell += '"'; i += 1; } else quoted = !quoted;
    } else if (ch === ',' && !quoted) { row.push(cell); cell = ''; }
    else if ((ch === '\n' || ch === '\r') && !quoted) {
      if (ch === '\r' && text[i + 1] === '\n') i += 1;
      row.push(cell); if (row.some((value) => value !== '')) rows.push(row); row = []; cell = '';
    } else cell += ch;
  }
  row.push(cell); if (row.some((value) => value !== '')) rows.push(row);
  const headers = (rows.shift() || []).map((header, index) => (index === 0 ? header.replace(/^\uFEFF/, '') : header));
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] || ''])));
}
const readConsolidatedCsv = (name) => parseCsv(fs.readFileSync(path.join(CONSOLIDATED_ROOT, name), 'utf8'));
const normalizeName = (value) => String(value || '').trim()
  // The IGN GeoJSON currently contains a few UTF-8 strings decoded as latin-1.
  .replace(/Ã±/g, 'ñ').replace(/Ã‘/g, 'Ñ').replace(/Ã¡/g, 'á').replace(/Ã©/g, 'é').replace(/Ã­/g, 'í').replace(/Ã³/g, 'ó').replace(/Ãº/g, 'ú')
  .normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase();
const peruDistrictKey = (department, province, district) => {
  const d = normalizeName(department);
  let p = normalizeName(province).replace(/^PROV\.\s*CONST\.\s*DEL\s+/, '');
  let x = normalizeName(district);
  if (x === 'RAYMONDI') x = 'RAIMONDI';
  return `${d}|${p}|${x}`;
};
const profilePersonaId = {
  'Software developers and analysts': 'P01',
  'Database, systems and network professionals': 'P02',
  'IT technicians and support': 'P03',
  'IT managers': 'P04',
  'Designers': 'P05',
  'Business and management analysts': 'P06',
  'Finance analysts': 'P07',
  'Data and research specialists': 'P08',
  'Marketing and advertising professionals': 'P09',
  'Accountants and auditors': 'P10',
  'Engineers (non-IT)': 'P11',
  'Business and operations managers': 'P12',
  'University and IT educators': 'P13'
};
const numeric = (value) => value === '' || value == null ? null : Number(value);

function load() {
  if (cache) return cache;
  const catalog = read('map_catalog.json');
  const indicators = [
    ...read('fact_map_indicator.json'),
    ...read('fact_tuni_ingress_national_2025.json')
  ];
  const personas = read('fact_persona_estimates_epen2025.json').filter((p) => p.group_type === 'persona');
  personas.unshift({ group_id: 'CORE_ICT', label: 'Núcleo TIC observado (P01–P04 combinado)', ring: 'Core', reference_year: 2025, observed_departmental: true });
  const initialSchools = read('geo_secondary_services_initial.json');
  const observedPersonaDepartments = read('fact_persona_department_epen2025.json');
  const enahoEmploymentDepartments = read('fact_enaho_employment_by_department_2025.json');
  const suneduUniversitiesDepartments = read('fact_sunedu_licensed_universities_by_department.json');
  const registeredLocalAddressesDepartments = read('fact_registered_local_addresses_by_department.json');
  const registeredLocalAddressesDistricts = read('fact_registered_local_addresses_by_district.json');
  const enahoConnectivityDepartments = read('fact_enaho_household_connectivity_by_department_2025.json');
  const higherEducationOfferDepartments = read('fact_higher_nonuniversity_offer_by_department_20260918.json');
  const suneduProgrammeDepartments = read('fact_sunedu_programmes_by_department_20240828.json');
  const mineduSnuEnrollmentDepartments = read('fact_minedu_snu_enrollment_by_department_2025.json');
  const tuniEnrollmentDepartments = read('fact_tuni_enrollment_by_department_2025_2.json');
  const tuniEnrollmentDistricts = read('fact_tuni_enrollment_by_district_2025_2.json');
  const tuniGraduatesDepartments = read('fact_tuni_graduates_by_department_2024.json');
  const tuniGraduatesDistricts = read('fact_tuni_graduates_by_district_2024.json');
  // This imported research is complementary to EPEN: it is a national ENAHO
  // profile for all 13 personas, never a territorial replacement or allocation.
  const nationalProfiles = readConsolidatedCsv('fact_persona_profile.csv').map((row) => ({
    ...row, group_id: profilePersonaId[row.persona] || null,
    employed: numeric(row.employed), interviews: numeric(row.interviews), pct_university: numeric(row.pct_university),
    median_age: numeric(row.median_age), median_income_pen: numeric(row.median_income_pen), pct_women: numeric(row.pct_women)
  }));
  const consolidatedSchools = readConsolidatedCsv('fact_schools_municipality.csv').map((row) => ({
    ...row, municipality_code: String(row.municipality_code), department_code: String(row.department_code).padStart(2, '0'),
    students_3_5: numeric(row.students_3_5), schools: numeric(row.schools),
    students: numeric(row.students_3_5), services: numeric(row.schools)
  }));
  const consolidatedMicroDepartments = readConsolidatedCsv('fact_micro_department.csv').map((row) => ({
    ...row, department_code: String(row.department_code).padStart(2, '0'), micro_businesses: numeric(row.micro_businesses)
  }));
  cache = { catalog, indicators, personas, observedPersonaDepartments, enahoEmploymentDepartments, suneduUniversitiesDepartments, registeredLocalAddressesDepartments, registeredLocalAddressesDistricts, enahoConnectivityDepartments, higherEducationOfferDepartments, suneduProgrammeDepartments, mineduSnuEnrollmentDepartments, tuniEnrollmentDepartments, tuniEnrollmentDistricts, tuniGraduatesDepartments, tuniGraduatesDistricts, nationalProfiles, consolidatedSchools, consolidatedMicroDepartments, initialSchools, schools: null, departmentMap: null, districtFeatures: null };
  return cache;
}

function allSchools() {
  const d = load();
  if (d.schools) return d.schools;
  const geo = read('geo_secondary_services_2025.geojson');
  d.schools = { type: 'FeatureCollection', features: geo.features.map((f) => ({
    type: 'Feature', id: f.id, geometry: f.geometry,
    properties: {
      service_id: f.properties.service_id, ubigeo: f.properties.ubigeo,
      students: f.properties.students, target_grades_students: f.properties.target_grades_students,
      management: f.properties.management, reference_year: f.properties.reference_year,
      source: f.properties.source
    }
  })) };
  return d.schools;
}

function layerSummary() {
  const { catalog, indicators, observedPersonaDepartments } = load();
  const observed = observedPersonaDepartments.filter((row) => row.publication_status === 'publish').length;
  return Object.entries(catalog.layers).map(([layer, info]) => {
    const rows = indicators.filter((r) => r.layer === layer);
    const hasObservedGeography = layer === 'G' || layer === 'H';
    const published = rows.filter((r) => r.value !== null && r.value !== '').length;
    return { layer, status: info.data_status, records: info.records_in_map_metric,
      values: info.non_null_map_values, available: hasObservedGeography ? observed : Math.max(published, Number(info.non_null_map_values) || 0),
      note: hasObservedGeography ? `${info.data_reference}; ${observed} estimaciones observadas P01–P04 por departamento (EPEN 2025)` : info.data_reference };
  });
}

function getMap() {
  const d = load();
  // The map shell deliberately stays small. School points are fetched in
  // bounded viewport batches by getSchools(), rather than transferring the
  // 17 MB GeoJSON in the first request.
  const countryIndicators = d.indicators.filter((row) => row.scope_type === 'country');
  return { country: { code: 'PE', name: 'Perú', center: [-9.19, -75.02], zoom: 5 },
    catalog: { ...d.catalog, layer_summary: layerSummary() }, indicators: countryIndicators,
    personas: d.personas,
    persona_blocks: {
      observed: {
        source: 'INEI EPEN 2025, annual department microdata', geography: 'department', personas: ['P01', 'P02', 'P03', 'P04'],
        note: 'Observed departmental estimates. Small cells are suppressed.'
      },
      national_profile: {
        source: 'INEI ENAHO 2024, annual microdata', geography: 'country', profiles: d.nationalProfiles,
        note: 'National profile for all 13 personas. It is not a geographic allocation and does not replace EPEN observed estimates.'
      }
    },
    schools: {
      count: d.initialSchools.total,
      type: 'education_service_points',
      initial: d.initialSchools
    },
    warnings: ['Las métricas A–R y las personas son nacionales. No se distribuyen por departamento, provincia o distrito.', 'Los puntos representan servicios educativos secundarios. No son límites políticos ni una coropleta distrital.', 'Un valor nulo significa suprimido, no disponible o pendiente; nunca equivale a cero.'] };
}

function finite(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

const allocationWeights = {
  Core: { ruc: 0.8, education: 0.2 },
  Adjacent: { ruc: 0.6, education: 0.4 },
  Extended: { ruc: 0.4, education: 0.6 }
};

function attachPersonaEstimates(features, personas) {
  const rucTotal = features.reduce((total, feature) => total + (Number(feature.properties.values.ruc_tic_active) || 0), 0);
  const educationTotal = features.reduce((total, feature) => total + (Number(feature.properties.values.secondary_target_students) || 0), 0);
  for (const feature of features) {
    const values = feature.properties.values;
    const rucShare = (Number(values.ruc_tic_active) || 0) / rucTotal;
    const educationShare = (Number(values.secondary_target_students) || 0) / educationTotal;
    const estimates = {};
    for (const persona of personas) {
      if (!Number.isFinite(Number(persona.employed))) {
        estimates[persona.group_id] = null;
        continue;
      }
      const weights = allocationWeights[persona.ring] || allocationWeights.Adjacent;
      estimates[persona.group_id] = Number(persona.employed) * ((weights.ruc * rucShare) + (weights.education * educationShare));
    }
    feature.properties.persona_estimates = estimates;
  }
}

function attachObservedPersonaDepartments(features, rows) {
  const lookup = new Map(rows.map((row) => [`${String(row.department_code).padStart(2, '0')}|${row.group_id}`, row]));
  for (const feature of features) {
    const observed = {};
    for (const persona of ['CORE_ICT', 'P01', 'P02', 'P03', 'P04']) {
      const row = lookup.get(`${String(feature.id).padStart(2, '0')}|${persona}`);
      observed[persona] = row && row.publication_status === 'publish' ? Number(row.employed) : null;
    }
    feature.properties.observed_persona_estimates = observed;
  }
}

function administrativeIndicators() {
  return [
    { key: 'ruc_tic_active', label: 'Empresas TIC activas', unit: 'RUC activos', source: { year: 2026 } },
    { key: 'ruc_6201', label: 'Desarrollo de software', unit: 'RUC activos', source: { year: 2026 } },
    { key: 'ruc_6202', label: 'Consultoría TI', unit: 'RUC activos', source: { year: 2026 } },
    { key: 'ruc_6209', label: 'Otros servicios TI', unit: 'RUC activos', source: { year: 2026 } },
    { key: 'ruc_6311', label: 'Procesamiento de datos', unit: 'RUC activos', source: { year: 2026 } },
    { key: 'ruc_6312', label: 'Portales web', unit: 'RUC activos', source: { year: 2026 } },
    { key: 'education_students_all', label: 'Matrícula educativa total', unit: 'estudiantes', source: { year: 2025 } },
    { key: 'education_services_all', label: 'Servicios educativos totales', unit: 'servicios', source: { year: 2025 } },
    { key: 'secondary_target_students', label: 'Matrícula secundaria objetivo', unit: 'estudiantes', source: { year: 2025 } },
    { key: 'secondary_services', label: 'Servicios de secundaria', unit: 'servicios', source: { year: 2025 } },
    { key: 'secondary_all_students', label: 'Matrícula secundaria total', unit: 'estudiantes', source: { year: 2025 } },
    { key: 'consolidated_secondary_students_3_5', label: 'Matrícula secundaria 3.º–5.º (consolidado)', unit: 'estudiantes', source: { year: 2025 } },
    { key: 'consolidated_secondary_schools', label: 'Colegios con matrícula 3.º–5.º (consolidado)', unit: 'colegios', source: { year: 2025 } },
    { key: 'enaho_employed_residents', label: 'Ocupados residentes (ENAHO)', unit: 'personas ocupadas', source: { year: 2025 } },
    { key: 'enaho2024_micro_businesses', label: 'Micronegocios (ENAHO)', unit: 'micronegocios estimados', source: { year: 2024 } },
    { key: 'enaho_employed_up_to_20_people', label: 'Ocupados en establecimientos de hasta 20 personas (ENAHO)', unit: 'personas ocupadas estimadas', source: { year: 2025 } },
    { key: 'enaho_employer_registered_sunat', label: 'Ocupados con empleador registrado en SUNAT (ENAHO)', unit: 'personas ocupadas estimadas', source: { year: 2025 } },
    { key: 'sunedu_licensed_universities', label: 'Universidades licenciadas (SUNEDU)', unit: 'universidades', source: { year: 2026 } },
    { key: 'registered_local_addresses', label: 'Establecimientos registrados con local (SUNAT)', unit: 'locales registrados', source: { year: 2026 } },
    { key: 'enaho_internet_household_rate', label: 'Hogares con internet (ENAHO)', unit: 'proporción de hogares', source: { year: 2025 } },
    { key: 'enaho_internet_households', label: 'Hogares con internet (ENAHO)', unit: 'hogares estimados', source: { year: 2025 } },
    { key: 'higher_nonuniversity_services', label: 'Oferta superior no universitaria (MINEDU)', unit: 'servicios educativos', source: { year: 2026 } },
    { key: 'sunedu_ict_programmes', label: 'Programas universitarios de informática (SUNEDU)', unit: 'programas ofertados', source: { year: 2024 } },
    { key: 'sunedu_university_programmes', label: 'Programas universitarios ofertados (SUNEDU)', unit: 'programas ofertados', source: { year: 2024 } },
    { key: 'minedu_snu_enrollment', label: 'Matrícula superior no universitaria (MINEDU)', unit: 'estudiantes matriculados', source: { year: 2025 } },
    { key: 'tuni_reported_enrollment', label: 'Matrícula superior reportada (TUNI/SUNEDU)', unit: 'estudiantes matriculados', source: { period: '2025-2' } },
    { key: 'tuni_ict_enrollment', label: 'Matrícula TIC reportada (TUNI/SUNEDU)', unit: 'estudiantes matriculados', source: { period: '2025-2' } },
    { key: 'tuni_reported_graduates', label: 'Egresados reportados (TUNI/SUNEDU)', unit: 'egresados', source: { year: 2024 } },
    { key: 'tuni_ict_graduates', label: 'Egresados TIC reportados (TUNI/SUNEDU)', unit: 'egresados', source: { year: 2024 } }
  ];
}

function aggregateEducation(rows, keyFor) {
  const result = new Map();
  for (const row of rows) {
    const key = keyFor(row);
    const current = result.get(key) || { students: 0, services: 0 };
    current.students += Number(row.students) || 0;
    current.services += Number(row.services) || 0;
    result.set(key, current);
  }
  return result;
}

function aggregateRuc(rows, keyFor) {
  const result = new Map();
  const keys = ['active_ruc_tic', 'ciiu_6201', 'ciiu_6202', 'ciiu_6209', 'ciiu_6311', 'ciiu_6312'];
  for (const row of rows) {
    const key = keyFor(row);
    const current = result.get(key) || Object.fromEntries(keys.map((metric) => [metric, 0]));
    for (const metric of keys) current[metric] += Number(row[metric]) || 0;
    result.set(key, current);
  }
  return result;
}

function getSchools(query = {}) {
  const schools = allSchools();
  const west = finite(query.west, -82);
  const east = finite(query.east, -68);
  const south = finite(query.south, -19);
  const north = finite(query.north, 1);
  const limit = Math.max(250, Math.min(3000, Math.floor(finite(query.limit, 2500))));
  const matching = schools.features.filter((feature) => {
    const point = feature.geometry && feature.geometry.coordinates;
    return point && point[0] >= west && point[0] <= east && point[1] >= south && point[1] <= north;
  });
  // When the viewport contains many services, sample evenly across the
  // filtered source so that the national view remains representative and fast.
  const step = Math.max(1, Math.ceil(matching.length / limit));
  const features = step === 1 ? matching : matching.filter((_, index) => index % step === 0).slice(0, limit);
  return {
    type: 'FeatureCollection',
    features,
    total: matching.length,
    returned: features.length,
    sampled: features.length < matching.length
  };
}

function getDepartmentMap() {
  const d = load();
  if (d.departmentMap) return d.departmentMap;
  const shapes = read('geo_departments_ign_2025.geojson');
  const ruc = read('fact_ruc_tic_district_202604.json');
  const secondary = read('fact_secondary_region_2025.json');
  const education = read('fact_education_padron_district_2025.json');
  const rucByName = new Map((ruc.departments || []).map((row) => [normalizeName(row.department), row]));
  const rucByDepartment = aggregateRuc(ruc.districts || [], (row) => String(row.ubigeo).slice(0, 2));
  const secondaryByCode = new Map(secondary.map((row) => [String(row.group_code).padStart(2, '0'), row]));
  const educationByCode = aggregateEducation(education, (row) => String(row.ubigeo).slice(0, 2));
  const enahoByCode = new Map(d.enahoEmploymentDepartments.map((row) => [String(row.department_code).padStart(2, '0'), row]));
  const suneduByName = new Map(d.suneduUniversitiesDepartments.map((row) => [normalizeName(row.department), row]));
  const localAddressesByCode = new Map(d.registeredLocalAddressesDepartments.map((row) => [String(row.department_code).padStart(2, '0'), row]));
  const connectivityByCode = new Map(d.enahoConnectivityDepartments.map((row) => [String(row.department_code).padStart(2, '0'), row]));
  const higherEducationOfferByName = new Map(d.higherEducationOfferDepartments.map((row) => [normalizeName(row.department), row]));
  const suneduProgrammeByName = new Map(d.suneduProgrammeDepartments.map((row) => [normalizeName(row.department), row]));
  const mineduSnuEnrollmentByName = new Map(d.mineduSnuEnrollmentDepartments.map((row) => [normalizeName(row.department), row]));
  const tuniEnrollmentByName = new Map(d.tuniEnrollmentDepartments.map((row) => [normalizeName(row.department), row]));
  const tuniGraduatesByName = new Map(d.tuniGraduatesDepartments.map((row) => [normalizeName(row.department), row]));
  const consolidatedSchoolsByDepartment = aggregateEducation(d.consolidatedSchools, (row) => row.department_code);
  const microBusinessesByDepartment = new Map(d.consolidatedMicroDepartments.map((row) => [row.department_code, row]));
  const indicators = administrativeIndicators();
  const features = shapes.features.map((shape) => {
    const code = String(shape.properties.department_code).padStart(2, '0');
    const name = normalizeName(shape.properties.name);
    const business = rucByName.get(name);
    const rucActivities = rucByDepartment.get(code);
    const education = secondaryByCode.get(code);
    const allEducation = educationByCode.get(code);
    const enaho = enahoByCode.get(code);
    const sunedu = suneduByName.get(name);
    const localAddresses = localAddressesByCode.get(code);
    const connectivity = connectivityByCode.get(code);
    const higherEducationOffer = higherEducationOfferByName.get(name);
    const suneduProgrammes = suneduProgrammeByName.get(name);
    const mineduSnuEnrollment = mineduSnuEnrollmentByName.get(name);
    const tuniEnrollment = tuniEnrollmentByName.get(name);
    const tuniGraduates = tuniGraduatesByName.get(name);
    const consolidatedSchool = consolidatedSchoolsByDepartment.get(code);
    const microBusinesses = microBusinessesByDepartment.get(code);
    return {
      type: 'Feature', id: code, geometry: shape.geometry,
      properties: {
        name: shape.properties.name, capital: shape.properties.capital,
        values: {
          ruc_tic_active: business ? business.active_ruc_tic : null,
          ruc_6201: rucActivities ? rucActivities.ciiu_6201 : null,
          ruc_6202: rucActivities ? rucActivities.ciiu_6202 : null,
          ruc_6209: rucActivities ? rucActivities.ciiu_6209 : null,
          ruc_6311: rucActivities ? rucActivities.ciiu_6311 : null,
          ruc_6312: rucActivities ? rucActivities.ciiu_6312 : null,
          education_students_all: allEducation ? allEducation.students : null,
          education_services_all: allEducation ? allEducation.services : null,
          secondary_target_students: education ? education.target_students : null,
          secondary_services: education ? education.services : null,
          secondary_all_students: education ? education.all5_students : null,
          enaho_employed_residents: enaho ? enaho.weighted_employed : null,
          enaho_employed_up_to_20_people: enaho ? enaho.weighted_employed_up_to_20_people : null,
          enaho_employer_registered_sunat: enaho ? enaho.weighted_employed_employer_registered_sunat : null,
          sunedu_licensed_universities: sunedu ? sunedu.licensed_universities : null,
          registered_local_addresses: localAddresses ? localAddresses.registered_local_addresses : null,
          enaho_internet_household_rate: connectivity ? connectivity.internet_household_rate : null,
          enaho_internet_households: connectivity ? connectivity.weighted_internet_households : null,
          higher_nonuniversity_services: higherEducationOffer ? higherEducationOffer.higher_nonuniversity_services : null,
          sunedu_ict_programmes: suneduProgrammes ? suneduProgrammes.unique_ict_programmes : null,
          sunedu_university_programmes: suneduProgrammes ? suneduProgrammes.unique_university_programmes : null,
          minedu_snu_enrollment: mineduSnuEnrollment ? mineduSnuEnrollment.students : null,
          tuni_reported_enrollment: tuniEnrollment ? tuniEnrollment.students : null,
          tuni_ict_enrollment: tuniEnrollment ? tuniEnrollment.ict_students : null,
          tuni_reported_graduates: tuniGraduates ? tuniGraduates.graduates : null,
          tuni_ict_graduates: tuniGraduates ? tuniGraduates.ict_graduates : null
          ,consolidated_secondary_students_3_5: consolidatedSchool ? consolidatedSchool.students : null
          ,consolidated_secondary_schools: consolidatedSchool ? consolidatedSchool.services : null
          ,enaho2024_micro_businesses: microBusinesses ? microBusinesses.micro_businesses : null
        }
      }
    };
  });
  attachPersonaEstimates(features, d.personas);
  attachObservedPersonaDepartments(features, d.observedPersonaDepartments);
  d.departmentMap = {
    type: 'FeatureCollection', layer: 'peru_departments', indicators, features,
    geometry_source: shapes.source,
    sources: {
      ruc_tic: ruc.source,
      secondary: 'MINEDU_CE2025_MATRICULA'
    },
    persona_allocation: {
      type: 'modelled_estimate',
      formula: 'national_persona_estimate × (ring-specific weighted share of active TIC RUC and secondary target enrollment)',
      weights: allocationWeights,
      limitations: 'Not an observed department-level persona estimate. Suppressed national personas remain null.'
    },
    observed_persona_estimates: {
      source: 'INEI EPEN 2025, annual department microdata, CNO 2015 → CIUO-08 correspondence',
      personas: ['CORE_ICT', 'P01', 'P02', 'P03', 'P04'],
      limitations: 'Observed annual department estimates for four ICT personas only. Cells with fewer than 30 sampled records are suppressed.'
    }
  };
  return d.departmentMap;
}

function boundsOf(geometry) {
  const result = [Infinity, Infinity, -Infinity, -Infinity];
  (function visit(node) {
    if (typeof node[0] === 'number') {
      result[0] = Math.min(result[0], node[0]); result[1] = Math.min(result[1], node[1]);
      result[2] = Math.max(result[2], node[0]); result[3] = Math.max(result[3], node[1]);
      return;
    }
    node.forEach(visit);
  }(geometry.coordinates));
  return result;
}

function buildDistrictFeatures() {
  const d = load();
  if (d.districtFeatures) return d.districtFeatures;
  const shapes = read('geo_districts_ign_2025.geojson');
  const ruc = read('fact_ruc_tic_district_202604.json');
  const secondary = read('fact_secondary_district_2025.json');
  const educationPadron = read('fact_education_padron_district_2025.json');
  const rucByUbigeo = new Map((ruc.districts || []).map((row) => [String(row.ubigeo), row]));
  const secondaryByUbigeo = new Map(secondary.map((row) => [String(row.group_code), row]));
  const educationByUbigeo = aggregateEducation(educationPadron, (row) => String(row.ubigeo));
  const localAddressesByUbigeo = new Map(d.registeredLocalAddressesDistricts.map((row) => [String(row.ubigeo), row]));
  const tuniEnrollmentByDistrict = new Map(d.tuniEnrollmentDistricts.map((row) => [peruDistrictKey(row.department, row.province, row.district), row]));
  const tuniGraduatesByDistrict = new Map(d.tuniGraduatesDistricts.map((row) => [peruDistrictKey(row.department, row.province, row.district), row]));
  const consolidatedSchoolsByDistrict = new Map(d.consolidatedSchools.map((row) => [row.municipality_code, row]));
  const features = shapes.features.map((shape) => {
    const ubigeo = String(shape.properties.ubigeo);
    const business = rucByUbigeo.get(ubigeo);
    const education = secondaryByUbigeo.get(ubigeo);
    const allEducation = educationByUbigeo.get(ubigeo);
    const localAddresses = localAddressesByUbigeo.get(ubigeo);
    const tuniEnrollment = tuniEnrollmentByDistrict.get(peruDistrictKey(shape.properties.department, shape.properties.province, shape.properties.name));
    const tuniGraduates = tuniGraduatesByDistrict.get(peruDistrictKey(shape.properties.department, shape.properties.province, shape.properties.name));
    const consolidatedSchool = consolidatedSchoolsByDistrict.get(ubigeo);
    return {
      type: 'Feature', id: ubigeo, geometry: shape.geometry,
      properties: {
        name: shape.properties.name, capital: shape.properties.capital,
        department: shape.properties.department, province: shape.properties.province, ubigeo,
        values: {
          ruc_tic_active: business ? business.active_ruc_tic : null,
          ruc_6201: business ? business.ciiu_6201 : null,
          ruc_6202: business ? business.ciiu_6202 : null,
          ruc_6209: business ? business.ciiu_6209 : null,
          ruc_6311: business ? business.ciiu_6311 : null,
          ruc_6312: business ? business.ciiu_6312 : null,
          education_students_all: allEducation ? allEducation.students : null,
          education_services_all: allEducation ? allEducation.services : null,
          secondary_target_students: education ? education.target_students : null,
          secondary_services: education ? education.services : null,
          secondary_all_students: education ? education.all5_students : null,
          registered_local_addresses: localAddresses ? localAddresses.registered_local_addresses : null,
          tuni_reported_enrollment: tuniEnrollment ? tuniEnrollment.students : null,
          tuni_ict_enrollment: tuniEnrollment ? tuniEnrollment.ict_students : null,
          tuni_reported_graduates: tuniGraduates ? tuniGraduates.graduates : null,
          tuni_ict_graduates: tuniGraduates ? tuniGraduates.ict_graduates : null
          ,consolidated_secondary_students_3_5: consolidatedSchool ? consolidatedSchool.students_3_5 : null
          ,consolidated_secondary_schools: consolidatedSchool ? consolidatedSchool.schools : null
        }
      },
      _bounds: boundsOf(shape.geometry)
    };
  });
  attachPersonaEstimates(features, d.personas);
  d.districtFeatures = { features, source: shapes.source };
  return d.districtFeatures;
}

function getDistrictMap(query = {}) {
  const d = buildDistrictFeatures();
  const west = finite(query.west, -82); const east = finite(query.east, -68);
  const south = finite(query.south, -19); const north = finite(query.north, 1);
  const limit = Math.max(100, Math.min(600, Math.floor(finite(query.limit, 450))));
  const matching = d.features.filter((feature) => {
    const b = feature._bounds;
    return b[0] <= east && b[2] >= west && b[1] <= north && b[3] >= south;
  });
  const step = Math.max(1, Math.ceil(matching.length / limit));
  const features = (step === 1 ? matching : matching.filter((_, index) => index % step === 0).slice(0, limit))
    .map(({ _bounds, ...feature }) => feature);
  return {
    type: 'FeatureCollection', layer: 'peru_districts', indicators: administrativeIndicators(), features,
    total: matching.length, returned: features.length, sampled: features.length < matching.length,
    geometry_source: d.source,
    persona_allocation: {
      type: 'modelled_estimate',
      formula: 'national_persona_estimate × (ring-specific weighted share of active TIC RUC and secondary target enrollment)',
      weights: allocationWeights,
      limitations: 'Not an observed district-level persona estimate. Suppressed national personas remain null.'
    }
  };
}
module.exports = { getMap, getSchools, getDepartmentMap, getDistrictMap, layerSummary };
