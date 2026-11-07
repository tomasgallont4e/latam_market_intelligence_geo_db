'use strict';
// Read-only adapter for the Mexico tables in data/mexico (decision D-MX-01): Colombia-shaped CSVs read from
// files, served like Peru. National facts stay national; ENOE persona counts exist only by state (observed
// survey estimates) and are never split across municipalities.
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

const ROOT = path.join(__dirname, '..', 'data', 'mexico');
const CSV_DIR = path.join(ROOT, 'geodb', 'csv');
const OUT_DIR = path.join(ROOT, 'outputs');
// Same persona ids as Peru, keyed by the first ISCO code of each template persona.
const PERSONA_ID = { 2511: 'P01', 2521: 'P02', 3511: 'P03', 1330: 'P04', 2163: 'P05', 2421: 'P06', 2412: 'P07',
  2120: 'P08', 2431: 'P09', 2411: 'P10', 2141: 'P11', 1211: 'P12', 2310: 'P13' };
const CORE = ['P01', 'P02', 'P03', 'P04'];
const LAYER_NAMES = { A: 'Comunidad de desarrolladores', B: 'Uso de IA entre desarrolladores', C: 'Estudiantes TIC por ciudad', D: 'Empresas TIC por ciudad',
  E: 'Tipología de ciudades y población', F: 'Personas y empleo', G: 'Personal TI en cada industria', H: 'Segmentos: persona × ciudad × comprador',
  I: 'Precio frente al ingreso', J: 'Zonas de Ciudad de México y Monterrey', K: 'Escuelas: grados objetivo', L: 'Educación superior',
  M: 'Micronegocios', N: 'Empresas formales y tiendas', O: 'Contexto del país', P: 'Programa de bachillerato', Q: 'Geografía y claves', R: 'Comprobaciones y fuentes' };
// Layers drawn as territories; the rest are national indicator layers.
const GEOGRAPHIC_LAYERS = { C: 'Municipios y estados', D: 'Municipios y estados', E: 'Municipios', F: 'Estados', G: 'Nacional (ficha de persona)',
  H: 'Ciudades ENOE (ficha)', J: 'Zonas', K: 'Municipios y estados', L: 'Municipios y estados', M: 'Estados', N: 'Municipios y estados', Q: 'Mapa base' };

let cache = null;
const csv = (name) => parse(fs.readFileSync(path.join(CSV_DIR, `${name}.csv`), 'utf8'), { columns: true, skip_empty_lines: true });
const json = (name) => JSON.parse(fs.readFileSync(path.join(OUT_DIR, name), 'utf8'));
const num = (v) => (v === '' || v === null || v === undefined ? null : Number(v));

function finite(value, fallback) {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function boundsOf(geometry) {
  const b = [Infinity, Infinity, -Infinity, -Infinity];
  (function visit(node) {
    if (typeof node[0] === 'number') {
      b[0] = Math.min(b[0], node[0]); b[1] = Math.min(b[1], node[1]);
      b[2] = Math.max(b[2], node[0]); b[3] = Math.max(b[3], node[1]);
      return;
    }
    node.forEach(visit);
  }(geometry.coordinates));
  return b;
}

function sumBy(rows, keyFn, fields) {
  const out = new Map();
  for (const r of rows) {
    const k = keyFn(r);
    const cur = out.get(k) || Object.fromEntries(fields.map((f) => [f, 0]));
    for (const f of fields) cur[f] += Number(r[f]) || 0;
    out.set(k, cur);
  }
  return out;
}

function load() {
  if (cache) return cache;
  const profile = csv('fact_persona_profile').map((r) => ({
    ...r, group_id: PERSONA_ID[r.isco_codes.split(' ')[0]], employed: num(r.employed), interviews: num(r.interviews),
    median_income_mxn: num(r.median_income_mxn), pct_university: num(r.pct_university), pct_women: num(r.pct_women),
  }));
  const idOf = new Map(profile.map((p) => [p.persona, p.group_id]));
  const companies = csv('fact_companies_municipality');
  const schools = csv('fact_schools_municipality');
  const higher = csv('fact_higher_ed_municipality');
  const population = csv('fact_population_municipality');
  cache = {
    states: csv('geo_department'),
    municipalities: csv('geo_municipality'),
    profile, idOf,
    personaState: csv('fact_persona_department').map((r) => ({ ...r, group_id: idOf.get(r.persona) })),
    personaMetro: csv('fact_persona_metro').map((r) => ({ ...r, group_id: idOf.get(r.persona) })),
    micro: new Map(csv('fact_micro_department').map((r) => [r.department_code, num(r.micro_businesses)])),
    companies: new Map(companies.map((r) => [r.municipality_code, r])),
    schools: new Map(schools.map((r) => [r.municipality_code, r])),
    higher: new Map(higher.map((r) => [r.municipality_code, r])),
    population: new Map(population.map((r) => [r.municipality_code, num(r.population)])),
    byState: {
      companies: sumBy(companies, (r) => r.department_code, ['establishments', 'businesses', 'it_companies_active', 'shops_4711']),
      schools: sumBy(schools, (r) => r.department_code, ['students_target', 'schools', 'reach_cap100']),
      higher: sumBy(higher, (r) => r.department_code, ['students_total', 'students_on_campus', 'students_ict_field']),
      population: sumBy(population, (r) => r.department_code, ['population']),
    },
    indicators: csv('fact_map_indicator'),
    zones: csv('geo_zone'),
    zoneFacts: new Map(csv('fact_companies_zone').map((r) => [r.zone_id, r])),
    stateShapes: null, municipalFeatures: null, stateMap: null,
  };
  return cache;
}

function stateShapes() {
  const d = load();
  if (!d.stateShapes) d.stateShapes = csv('geo_department_shape').map((r) => ({ code: r.department_code, name: r.name, geometry: JSON.parse(r.geojson) }));
  return d.stateShapes;
}

// Values shared by states and municipalities (DENUE 05/2026, SEP 911 2024-2025, ANUIES, CONAPO 2024).
function territorialIndicators() {
  return [
    { key: 'it_companies_active', label: 'Establecimientos TI (DENUE)', unit: 'establecimientos', source: { year: '05/2026' } },
    { key: 'businesses', label: 'Empresas privadas (DENUE)', unit: 'establecimientos', source: { year: '05/2026' } },
    { key: 'establishments', label: 'Establecimientos totales (DENUE)', unit: 'establecimientos', source: { year: '05/2026' } },
    { key: 'shops_4711', label: 'Tiendas de abarrotes (DENUE)', unit: 'establecimientos', source: { year: '05/2026' } },
    { key: 'students_target', label: 'Alumnos en grados objetivo (3º sec. + media superior)', unit: 'estudiantes', source: { year: '2024-2025' } },
    { key: 'schools', label: 'Escuelas con grados objetivo (CCT)', unit: 'escuelas', source: { year: '2024-2025' } },
    { key: 'reach_cap100', label: 'Alumnos alcanzables (tope de 100 por escuela)', unit: 'estudiantes', source: { year: '2024-2025' } },
    { key: 'students_on_campus', label: 'Educación superior presencial', unit: 'estudiantes', source: { year: '2024-2025' } },
    { key: 'students_ict_field', label: 'Estudiantes TIC (campo amplio)', unit: 'estudiantes', source: { year: '2024-2025' } },
    { key: 'population', label: 'Población', unit: 'habitantes', source: { year: 2024 } },
  ];
}

function stateIndicators() {
  return [
    { key: 'core_it', label: 'TI núcleo (P01–P04, ENOE)', unit: 'personas ocupadas', source: { year: 2025 } },
    { key: 'personas13', label: 'Las 13 personas (ENOE)', unit: 'personas ocupadas', source: { year: 2025 } },
    ...territorialIndicators(),
    { key: 'micro_businesses', label: 'Micronegocios (ENOE, hasta 10 personas)', unit: 'micronegocios', source: { year: 2025 } },
  ];
}

function municipalValues(code) {
  const d = load();
  const c = d.companies.get(code) || {};
  const s = d.schools.get(code) || {};
  const h = d.higher.get(code) || {};
  return {
    it_companies_active: num(c.it_companies_active), businesses: num(c.businesses), establishments: num(c.establishments), shops_4711: num(c.shops_4711),
    // A municipality absent from the school or higher-education tables has no such schools: an observed zero.
    students_target: s.students_target !== undefined ? num(s.students_target) : 0, schools: s.schools !== undefined ? num(s.schools) : 0,
    reach_cap100: s.reach_cap100 !== undefined ? num(s.reach_cap100) : 0,
    students_on_campus: h.students_on_campus !== undefined ? num(h.students_on_campus) : 0,
    students_ict_field: h.students_ict_field !== undefined ? num(h.students_ict_field) : 0,
    population: d.population.has(code) ? d.population.get(code) : null,
  };
}

function getStateMap() {
  const d = load();
  if (d.stateMap) return d.stateMap;
  const persona = new Map();
  for (const r of d.personaState) {
    const k = r.department_code;
    const cur = persona.get(k) || { estimates: {}, interviews: {} };
    cur.estimates[r.group_id] = num(r.employed);
    cur.interviews[r.group_id] = num(r.interviews);
    persona.set(k, cur);
  }
  const features = stateShapes().map((s) => {
    const p = persona.get(s.code) || { estimates: {}, interviews: {} };
    const c = d.byState.companies.get(s.code) || {};
    const sc = d.byState.schools.get(s.code) || {};
    const h = d.byState.higher.get(s.code) || {};
    const pop = d.byState.population.get(s.code) || {};
    const total = Object.values(p.estimates).reduce((a, b) => a + (b || 0), 0);
    return {
      type: 'Feature', id: s.code, geometry: s.geometry,
      properties: {
        name: s.name, department_code: s.code,
        values: {
          core_it: CORE.reduce((a, id) => a + (p.estimates[id] || 0), 0), personas13: total,
          it_companies_active: c.it_companies_active ?? null, businesses: c.businesses ?? null, establishments: c.establishments ?? null, shops_4711: c.shops_4711 ?? null,
          students_target: sc.students_target ?? 0, schools: sc.schools ?? 0, reach_cap100: sc.reach_cap100 ?? 0,
          students_on_campus: h.students_on_campus ?? 0, students_ict_field: h.students_ict_field ?? 0,
          population: pop.population ?? null, micro_businesses: d.micro.get(s.code) ?? null,
        },
        observed_persona_estimates: p.estimates, persona_interviews: p.interviews,
      },
    };
  });
  d.stateMap = {
    type: 'FeatureCollection', layer: 'mexico_states', indicators: stateIndicators(), features,
    geometry_source: 'INEGI Marco Geoestadístico (00ent), WGS84, simplificado para web',
    observed_persona_estimates: {
      source: 'INEGI ENOE 2025, promedio de los cuatro trimestres; ocupación SINCO 2019 → CIUO-08', personas: d.profile.map((p) => p.group_id),
      limitations: 'Estimaciones observadas por estado. Cada celda lleva su número de entrevistas; con menos de 100 es indicativa.',
    },
  };
  return d.stateMap;
}

function municipalFeatures() {
  const d = load();
  if (!d.municipalFeatures) {
    const names = new Map(d.states.map((s) => [s.department_code, s.name]));
    d.municipalFeatures = csv('geo_municipality_shape').map((r) => {
      const geometry = JSON.parse(r.geojson);
      return {
        type: 'Feature', id: r.municipality_code, geometry,
        properties: { name: r.name, department: names.get(r.department_code) || '', municipality_code: r.municipality_code, values: municipalValues(r.municipality_code) },
        _bounds: boundsOf(geometry),
      };
    });
  }
  return d.municipalFeatures;
}

function getMunicipalityMap(query = {}) {
  const all = municipalFeatures();
  const west = finite(query.west, -119); const east = finite(query.east, -86);
  const south = finite(query.south, 14); const north = finite(query.north, 33);
  const limit = Math.max(100, Math.min(800, Math.floor(finite(query.limit, 600))));
  const matching = all.filter((f) => f._bounds[0] <= east && f._bounds[2] >= west && f._bounds[1] <= north && f._bounds[3] >= south);
  // Too many polygons in view: sample evenly, as Peru's district layer does.
  const step = Math.max(1, Math.ceil(matching.length / limit));
  const features = (step === 1 ? matching : matching.filter((_, i) => i % step === 0).slice(0, limit)).map(({ _bounds, ...f }) => f);
  return {
    type: 'FeatureCollection', layer: 'mexico_municipalities', indicators: territorialIndicators(), features,
    total: matching.length, returned: features.length, sampled: features.length < matching.length,
    geometry_source: 'INEGI Marco Geoestadístico (00mun), WGS84, simplificado para web',
    note: 'Las personas de la ENOE no se publican por municipio: la encuesta representa estados y 39 ciudades.',
  };
}

function getZoneMap() {
  const d = load();
  const indicators = [
    { key: 'companies_total', label: 'Empresas privadas', unit: 'establecimientos' },
    { key: 'software_it', label: 'Software y TI', unit: 'establecimientos' },
    { key: 'medium_large', label: 'Medianas y grandes (51+ personas)', unit: 'establecimientos' },
    { key: 'design', label: 'Diseño', unit: 'establecimientos' },
    { key: 'accounting_audit', label: 'Contabilidad y auditoría', unit: 'establecimientos' },
    { key: 'management_consulting', label: 'Consultoría en administración', unit: 'establecimientos' },
    { key: 'research_market_studies', label: 'Investigación y estudios de mercado', unit: 'establecimientos' },
    { key: 'higher_education_training', label: 'Educación superior y capacitación', unit: 'establecimientos' },
    { key: 'private_schools', label: 'Escuelas privadas', unit: 'establecimientos' },
    { key: 'shops_4711', label: 'Tiendas de abarrotes', unit: 'establecimientos' },
  ].map((x) => ({ ...x, source: { year: 'DENUE 05/2026' } }));
  const features = d.zones.map((z) => {
    const f = d.zoneFacts.get(z.zone_id) || {};
    return {
      type: 'Feature', id: z.zone_id, geometry: JSON.parse(z.geojson),
      properties: { name: z.name, zone_id: z.zone_id, city: z.zone_id.startsWith('CMX') ? 'Ciudad de México' : 'Zona Metropolitana de Monterrey',
        values: Object.fromEntries(indicators.map((x) => [x.key, num(f[x.key])])) },
    };
  });
  return { type: 'FeatureCollection', layer: 'mexico_zones', indicators, features,
    note: 'Ciudad de México por alcaldía y la Zona Metropolitana de Monterrey por municipio (Metrópolis de México 2020). Universo: empresas privadas.' };
}

function layerSummary() {
  const d = load();
  const rPath = path.join(ROOT, 'validation', 'r_checks_mx.json');
  const r = fs.existsSync(rPath) ? JSON.parse(fs.readFileSync(rPath, 'utf8')) : null;
  return Object.keys(LAYER_NAMES).map((layer) => {
    if (layer === 'R') {
      return { layer, name: LAYER_NAMES.R, geography: 'Validación', national_values: 0,
        status: r ? `${r.R1_published_totals.passed}/${r.R1_published_totals.total} totales publicados; ${r.R2_sources_register.complete}/${r.R2_sources_register.sources} fuentes completas` : 'pending' };
    }
    const rows = d.indicators.filter((r) => r.layer === layer);
    const values = rows.filter((r) => r.value !== '').length;
    return { layer, name: LAYER_NAMES[layer], geography: GEOGRAPHIC_LAYERS[layer] || 'Nacional', national_values: values,
      status: rows.length ? (values ? 'populated' : 'pending') : (GEOGRAPHIC_LAYERS[layer] ? 'territorial' : 'pending') };
  });
}

function getMap() {
  const d = load();
  // Layer B keeps only Mexico's own rows; the comparison groups stay in the outputs, not in the map selector.
  const indicators = d.indicators.filter((r) => r.layer !== 'B' || r.group_id === 'MX');
  return {
    country: { code: 'MX', name: 'México', center: [23.6, -102.5], zoom: 5 },
    national_geometry: { type: 'FeatureCollection', source: 'INEGI Marco Geoestadístico (00ent)',
      features: stateShapes().map((s) => ({ type: 'Feature', geometry: s.geometry, properties: {} })) },
    catalog: { layer_summary: layerSummary() },
    indicators,
    personas: d.profile.map((p) => ({ group_id: p.group_id, label: p.persona, ring: p.ring, employed: p.employed, interviews: p.interviews, reference_year: 2025 })),
    persona_blocks: {
      national_profile: { source: 'INEGI ENOE 2025 (promedio anual)', geography: 'country', profiles: d.profile,
        note: 'Perfil nacional de las 13 personas. Por estado se muestran las estimaciones observadas de la misma encuesta.' },
    },
    warnings: [
      'Los indicadores nacionales (A, B, I, O, P) no se reparten por estado o municipio.',
      'Las personas (ENOE) se publican por estado y nunca por municipio.',
      'Un valor nulo significa no disponible o pendiente; nunca equivale a cero.',
    ],
  };
}

module.exports = { getMap, getStateMap, getMunicipalityMap, getZoneMap, layerSummary };
