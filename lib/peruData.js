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
  const profiles = read('fact_persona_profiles_2025.json');
  const rucTic = read('fact_ruc_tic_district_202604.json');
  const geo = read('geo_secondary_services_2025.geojson');
  const schools = { type: 'FeatureCollection', features: geo.features.map((f) => ({
    type: 'Feature', id: f.id, geometry: f.geometry,
    properties: {
      service_id: f.properties.service_id, ubigeo: f.properties.ubigeo,
      students: f.properties.students, target_grades_students: f.properties.target_grades_students,
      management: f.properties.management, reference_year: f.properties.reference_year,
      source: f.properties.source
    }
  })) };
  cache = { catalog, indicators, personas, profiles, rucTic, schools };
  return cache;
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
  return { country: { code: 'PE', name: 'Perú', center: [-9.19, -75.02], zoom: 5 },
    catalog: { ...d.catalog, layer_summary: layerSummary() }, indicators: d.indicators,
    personas: d.personas, profiles: d.profiles, ruc_tic: d.rucTic, schools: d.schools,
    warnings: ['Las métricas A–R y las personas son nacionales. No se distribuyen por departamento, provincia o distrito.', 'Los puntos representan servicios educativos secundarios. No son límites políticos ni una coropleta distrital.', 'Un valor nulo significa suprimido, no disponible o pendiente; nunca equivale a cero.'] };
}
module.exports = { getMap, layerSummary };
