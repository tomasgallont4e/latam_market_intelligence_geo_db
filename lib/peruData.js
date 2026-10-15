'use strict';
// Read-only adapter for the supplied Peru consolidation. It never allocates
// national facts or personas to a district.
const fs = require('fs');
const path = require('path');
const ROOT = path.join(__dirname, '..', 'data', 'peru-map');
let cache = null;
const read = (name) => JSON.parse(fs.readFileSync(path.join(ROOT, name), 'utf8'));

function load() {
  if (cache) return cache;
  const catalog = read('map_catalog.json');
  const indicators = read('fact_map_indicator.json');
  const personas = read('fact_persona_estimates_epen2025.json').filter((p) => p.group_type === 'persona');
  const initialSchools = read('geo_secondary_services_initial.json');
  cache = { catalog, indicators, personas, initialSchools, schools: null, departmentMap: null, districtFeatures: null };
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
  const { catalog, indicators } = load();
  return Object.entries(catalog.layers).map(([layer, info]) => {
    const rows = indicators.filter((r) => r.layer === layer);
    return { layer, status: info.data_status, records: info.records_in_map_metric,
      values: info.non_null_map_values, available: rows.filter((r) => r.value !== null && r.value !== '').length,
      note: info.data_reference };
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

function administrativeIndicators() {
  return [
    { key: 'ruc_tic_active', label: 'Empresas TIC activas', unit: 'RUC activos', source: { year: 2026 } },
    { key: 'secondary_target_students', label: 'Matrícula secundaria objetivo', unit: 'estudiantes', source: { year: 2025 } },
    { key: 'secondary_services', label: 'Servicios de secundaria', unit: 'servicios', source: { year: 2025 } },
    { key: 'secondary_all_students', label: 'Matrícula secundaria total', unit: 'estudiantes', source: { year: 2025 } }
  ];
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
  const rucByName = new Map((ruc.departments || []).map((row) => [String(row.department).trim().toUpperCase(), row]));
  const secondaryByCode = new Map(secondary.map((row) => [String(row.group_code).padStart(2, '0'), row]));
  const indicators = administrativeIndicators();
  const features = shapes.features.map((shape) => {
    const code = String(shape.properties.department_code).padStart(2, '0');
    const name = String(shape.properties.name).trim().toUpperCase();
    const business = rucByName.get(name);
    const education = secondaryByCode.get(code);
    return {
      type: 'Feature', id: code, geometry: shape.geometry,
      properties: {
        name: shape.properties.name, capital: shape.properties.capital,
        values: {
          ruc_tic_active: business ? business.active_ruc_tic : null,
          secondary_target_students: education ? education.target_students : null,
          secondary_services: education ? education.services : null,
          secondary_all_students: education ? education.all5_students : null
        }
      }
    };
  });
  attachPersonaEstimates(features, d.personas);
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
  const rucByUbigeo = new Map((ruc.districts || []).map((row) => [String(row.ubigeo), row]));
  const secondaryByUbigeo = new Map(secondary.map((row) => [String(row.group_code), row]));
  const features = shapes.features.map((shape) => {
    const ubigeo = String(shape.properties.ubigeo);
    const business = rucByUbigeo.get(ubigeo);
    const education = secondaryByUbigeo.get(ubigeo);
    return {
      type: 'Feature', id: ubigeo, geometry: shape.geometry,
      properties: {
        name: shape.properties.name, capital: shape.properties.capital,
        department: shape.properties.department, province: shape.properties.province, ubigeo,
        values: {
          ruc_tic_active: business ? business.active_ruc_tic : null,
          secondary_target_students: education ? education.target_students : null,
          secondary_services: education ? education.services : null,
          secondary_all_students: education ? education.all5_students : null
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
