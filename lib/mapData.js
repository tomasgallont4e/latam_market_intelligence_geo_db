'use strict';
// Read-only map data layer (rule_map_api_readonly): SELECT-only aggregates.
// GeoJSON is returned exactly as stored (WGS84, [lon, lat] order).
const pool = require('../db/pool');
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

// People per persona by zone (Bogotá localidades, EM 2021). Read from the CSV so the
// persona filter works on the zone layer without a DB reload.
const ZONE_PERSONA_CSV = path.join(__dirname, '..', 'data', 'geodb-v2', 'csv', 'fact_em2021_localidad_persona.csv');
// Rural zones kept out of the zone map (agreed 8-oct): Sumapaz has ~81 people in a huge polygon.
const EXCLUDED_ZONES = ['BOG-20'];
let zonePersonaCache = null;
function zonePersona() {
  if (!zonePersonaCache) {
    zonePersonaCache = new Map();
    try {
      const rows = parse(fs.readFileSync(ZONE_PERSONA_CSV, 'utf8'), { columns: true, skip_empty_lines: true });
      for (const r of rows) zonePersonaCache.set(`${r.zone_id}|${r.persona}`, Number(r.employed));
    } catch (e) {
      console.error('zone persona CSV not loaded:', e.message);
    }
  }
  return zonePersonaCache;
}

const VAC_DEV_KEYWORD = 'desarrollador';
const VAC_AI_KEYWORD = 'inteligencia artificial';
const REST_OF_COUNTRY = 'Rest of the country';
const NO_POINT_MUNI = '27493';

const num = (v) => (v === null || v === undefined ? null : Number(v));

async function q(sql, params = []) {
  const [rows] = await pool.query(sql, params);
  return rows;
}

let sourcesCache = null;
async function getSources() {
  if (!sourcesCache) {
    const rows = await q('SELECT table_name, source, year FROM meta_sources');
    sourcesCache = {};
    for (const r of rows) sourcesCache[r.table_name] = { source_name: r.source, year: r.year };
  }
  return sourcesCache;
}

function srcFor(sources, table) {
  return sources[table] || { source_name: null, year: null };
}

async function getPersonaList() {
  const rows = await q('SELECT persona, ring, employed FROM fact_persona_profile ORDER BY persona');
  return rows.map((r) => ({ persona: r.persona, ring: r.ring, employed: num(r.employed) }));
}

async function normalizePersona(persona) {
  if (!persona || persona === 'Todas' || persona === 'all') return null;
  const list = await getPersonaList();
  const hit = list.find((p) => p.persona === persona);
  if (!hit) {
    const err = new Error(`Persona desconocida: ${persona}`);
    err.status = 400;
    throw err;
  }
  return hit.persona;
}

function toMap(rows, key = 'k', val = 'v') {
  const m = new Map();
  for (const r of rows) m.set(String(r[key]), num(r[val]));
  return m;
}

function buildIndicators(defs, sources) {
  return defs.map((d) => ({ ...d, source: srcFor(sources, d.table) }));
}

// ───────────────────────── Departamentos ─────────────────────────
async function getDepartments({ persona } = {}) {
  const sources = await getSources();
  const p = await normalizePersona(persona);

  const shapes = await q(
    `SELECT s.department_code, COALESCE(d.name, s.name) AS name, s.geojson
       FROM geo_department_shape s
       LEFT JOIN geo_department d ON d.department_code = s.department_code
      ORDER BY s.department_code`
  );

  const personaSql = p
    ? ['SELECT department_code k, SUM(employed) v FROM fact_persona_department WHERE persona = ? GROUP BY department_code', [p]]
    : ['SELECT department_code k, SUM(employed) v FROM fact_persona_department GROUP BY department_code', []];

  const [personas, core, micro, schools, higher, secop, saber, vacDev, vacAi] = await Promise.all([
    q(personaSql[0], personaSql[1]),
    q(`SELECT pd.department_code k, SUM(pd.employed) v
         FROM fact_persona_department pd
         JOIN fact_persona_profile pp ON pp.persona = pd.persona
        WHERE pp.ring = 'core'
        GROUP BY pd.department_code`),
    q('SELECT department_code k, SUM(micro_businesses) v FROM fact_micro_department GROUP BY department_code'),
    q('SELECT department_code k, SUM(students_9_11) v FROM fact_schools_municipality GROUP BY department_code'),
    q('SELECT department_code k, SUM(students_on_campus) v FROM fact_higher_ed_municipality GROUP BY department_code'),
    q('SELECT department_code, SUM(contracts_2025) contracts, SUM(value_cop_2025) value FROM fact_secop_department GROUP BY department_code'),
    q('SELECT department_code k, computer_at_home_pct v FROM fact_saber11_department'),
    q('SELECT department_code k, SUM(offers) v FROM fact_vacancies_department WHERE keyword = ? GROUP BY department_code', [VAC_DEV_KEYWORD]),
    q('SELECT department_code k, SUM(offers) v FROM fact_vacancies_department WHERE keyword = ? GROUP BY department_code', [VAC_AI_KEYWORD]),
  ]);

  const mPers = toMap(personas), mCore = toMap(core), mMicro = toMap(micro), mSchools = toMap(schools),
    mHigher = toMap(higher), mSaber = toMap(saber), mDev = toMap(vacDev), mAi = toMap(vacAi);
  const mSecop = new Map(secop.map((r) => [String(r.department_code), r]));

  const defs = [
    { key: 'personas', label: p ? `Personas — ${p}` : 'Personas de las 13 personas', table: 'fact_persona_department', column: 'SUM(employed)', unit: 'ocupados' },
    { key: 'core_it', label: 'TI núcleo', table: 'fact_persona_department', column: "SUM(employed) WHERE fact_persona_profile.ring = 'core'", unit: 'ocupados' },
    { key: 'micro_businesses', label: 'Micronegocios', table: 'fact_micro_department', column: 'micro_businesses', unit: 'micronegocios' },
    { key: 'students_9_11', label: 'Estudiantes 9 a 11', table: 'fact_schools_municipality', column: 'SUM(students_9_11)', unit: 'estudiantes' },
    { key: 'students_on_campus', label: 'Educación superior', table: 'fact_higher_ed_municipality', column: 'SUM(students_on_campus)', unit: 'estudiantes' },
    { key: 'secop_value_bn', label: 'Compras públicas de software 2025', table: 'fact_secop_department', column: 'value_cop_2025 / 1e9', unit: 'miles de millones de COP' },
    { key: 'contracts_2025', label: 'Contratos de software 2025', table: 'fact_secop_department', column: 'contracts_2025', unit: 'contratos' },
    { key: 'computer_at_home_pct', label: 'Saber 11 con computador en casa (%)', table: 'fact_saber11_department', column: 'computer_at_home_pct', unit: '%' },
    { key: 'vacancies_dev', label: 'Vacantes de desarrollador', table: 'fact_vacancies_department', column: `offers WHERE keyword = '${VAC_DEV_KEYWORD}'`, unit: 'ofertas' },
    { key: 'vacancies_ai', label: 'Vacantes de IA', table: 'fact_vacancies_department', column: `offers WHERE keyword = '${VAC_AI_KEYWORD}'`, unit: 'ofertas' },
  ];

  const features = shapes.map((s) => {
    const code = String(s.department_code);
    const sec = mSecop.get(code);
    let geometry = null;
    try { geometry = JSON.parse(s.geojson); } catch (_) { geometry = null; }
    return {
      type: 'Feature',
      id: code,
      geometry,
      properties: {
        department_code: code,
        name: s.name,
        values: {
          personas: mPers.get(code) ?? null,
          core_it: mCore.get(code) ?? null,
          micro_businesses: mMicro.get(code) ?? null,
          students_9_11: mSchools.get(code) ?? null,
          students_on_campus: mHigher.get(code) ?? null,
          secop_value_bn: sec && sec.value !== null ? Math.round((Number(sec.value) / 1e9) * 100) / 100 : null,
          contracts_2025: sec ? num(sec.contracts) : null,
          computer_at_home_pct: mSaber.get(code) ?? null,
          vacancies_dev: mDev.get(code) ?? null,
          vacancies_ai: mAi.get(code) ?? null,
        },
      },
    };
  });

  return {
    type: 'FeatureCollection',
    layer: 'departments',
    persona: p,
    geometry_source: srcFor(sources, 'geo_department_shape'),
    attribution: ['© OpenStreetMap contributors', 'DANE Marco Geoestadístico'],
    indicators: buildIndicators(defs, sources),
    features,
  };
}

// ───────────────────────── Ciudades ─────────────────────────
async function getMunicipalities({ persona } = {}) {
  const sources = await getSources();
  const p = await normalizePersona(persona);

  const munis = await q(
    `SELECT m.municipality_code, m.department_code, m.name, m.lat, m.lon, d.name AS department_name
       FROM geo_municipality m
       LEFT JOIN geo_department d ON d.department_code = m.department_code
      WHERE m.lat IS NOT NULL AND m.lon IS NOT NULL AND m.municipality_code <> ?
      ORDER BY m.municipality_code`,
    [NO_POINT_MUNI]
  );

  const metroSql = p
    ? [`SELECT municipality_code k, SUM(employed) v, MAX(metro_area) metro FROM fact_persona_metro
         WHERE municipality_code IS NOT NULL AND metro_area <> ? AND persona = ? GROUP BY municipality_code`, [REST_OF_COUNTRY, p]]
    : [`SELECT municipality_code k, SUM(employed) v, MAX(metro_area) metro FROM fact_persona_metro
         WHERE municipality_code IS NOT NULL AND metro_area <> ? GROUP BY municipality_code`, [REST_OF_COUNTRY]];

  const [schools, higher, metro, chamber, meetup, events] = await Promise.all([
    q('SELECT municipality_code k, SUM(students_9_11) v FROM fact_schools_municipality GROUP BY municipality_code'),
    q('SELECT municipality_code k, SUM(students_on_campus) v FROM fact_higher_ed_municipality GROUP BY municipality_code'),
    q(metroSql[0], metroSql[1]),
    q('SELECT seat_municipality_code k, SUM(it_companies_active) v FROM fact_companies_chamber GROUP BY seat_municipality_code'),
    q('SELECT municipality_code k, SUM(members) v FROM fact_dev_communities WHERE municipality_code IS NOT NULL GROUP BY municipality_code'),
    q('SELECT municipality_code, name, date_2026, size FROM fact_tech_events ORDER BY date_2026, name'),
  ]);

  const mSchools = toMap(schools), mHigher = toMap(higher), mMetro = toMap(metro), mChamber = toMap(chamber), mMeetup = toMap(meetup);
  const metroName = new Map(metro.map((r) => [String(r.k), r.metro]));
  const evByMuni = new Map();
  for (const e of events) {
    const k = String(e.municipality_code);
    if (!evByMuni.has(k)) evByMuni.set(k, []);
    evByMuni.get(k).push({ name: e.name, date_2026: e.date_2026, size: e.size });
  }

  const defs = [
    { key: 'students_9_11', label: 'Estudiantes 9 a 11', table: 'fact_schools_municipality', column: 'SUM(students_9_11)', unit: 'estudiantes' },
    { key: 'students_on_campus', label: 'Educación superior', table: 'fact_higher_ed_municipality', column: 'SUM(students_on_campus)', unit: 'estudiantes' },
    { key: 'personas_metro', label: p ? `Personas — ${p} (área metropolitana)` : 'Personas de las 13 personas por área metropolitana', table: 'fact_persona_metro', column: 'SUM(employed)', unit: 'ocupados' },
    { key: 'it_companies_active', label: 'Empresas de TI activas', table: 'fact_companies_chamber', column: 'SUM(it_companies_active) por seat_municipality_code', unit: 'empresas' },
    { key: 'meetup_members', label: 'Miembros de Meetup', table: 'fact_dev_communities', column: 'SUM(members)', unit: 'miembros' },
    { key: 'tech_events', label: 'Eventos tech 2026', table: 'fact_tech_events', column: 'COUNT(*)', unit: 'eventos' },
  ];

  const municipalities = munis.map((m) => {
    const code = String(m.municipality_code);
    const ev = evByMuni.get(code) || [];
    return {
      municipality_code: code,
      department_code: m.department_code,
      department_name: m.department_name,
      name: m.name,
      lat: num(m.lat),
      lon: num(m.lon),
      metro_area: metroName.get(code) || null,
      has_event: ev.length > 0,
      events: ev,
      values: {
        students_9_11: mSchools.get(code) ?? null,
        students_on_campus: mHigher.get(code) ?? null,
        personas_metro: mMetro.get(code) ?? null,
        it_companies_active: mChamber.get(code) ?? null,
        meetup_members: mMeetup.get(code) ?? null,
        tech_events: ev.length,
      },
    };
  });

  return {
    layer: 'municipalities',
    persona: p,
    geometry_source: srcFor(sources, 'geo_municipality'),
    attribution: ['© OpenStreetMap contributors'],
    excluded: { municipality_code: NO_POINT_MUNI, metro_area: REST_OF_COUNTRY, reason: 'sin geografía' },
    indicators: buildIndicators(defs, sources),
    municipalities,
  };
}

// ───────────────────────── Bogotá por localidad ─────────────────────────
async function getLocalidades({ persona } = {}) {
  const sources = await getSources();
  const p = await normalizePersona(persona);

  let zones;
  try {
    zones = await q(
      `SELECT zone_id, municipality_code, zone_code, name, lat, lon, COALESCE(geojson, ST_AsGeoJSON(geometry)) AS geojson
         FROM geo_zone
        WHERE zone_type IN ('localidad', 'comuna', 'corregimiento')
          AND (geojson IS NOT NULL OR geometry IS NOT NULL)
        ORDER BY zone_id`
    );
  } catch (_) {
    zones = await q(
      `SELECT zone_id, municipality_code, zone_code, name, lat, lon, geojson FROM geo_zone
        WHERE zone_type IN ('localidad', 'comuna', 'corregimiento') AND geojson IS NOT NULL ORDER BY zone_id`
    );
  }

  const [em, comp] = await Promise.all([
    q('SELECT zone_id, localidad, employed, personas13, personas13_per_1000_employed, core_it, hh_computer_pct FROM fact_em2021_localidad'),
    q("SELECT zone_id k, SUM(software_it) v FROM fact_companies_zone WHERE zone_id <> 'BOG-00' GROUP BY zone_id"),
  ]);
  const mEm = new Map(em.map((r) => [String(r.zone_id), r]));
  const mComp = toMap(comp);
  const zp = p ? zonePersona() : null;
  zones = zones.filter((z) => !EXCLUDED_ZONES.includes(String(z.zone_id)));

  const defs = [
    p
      ? { key: 'personas13', label: `Personas — ${p}`, table: 'fact_em2021_localidad_persona', column: 'employed WHERE persona', unit: 'ocupados' }
      : { key: 'personas13', label: 'Personas de las 13 personas', table: 'fact_em2021_localidad', column: 'personas13', unit: 'ocupados' },
    p
      ? { key: 'personas13_per_1000_employed', label: `${p} por 1.000 ocupados`, table: 'fact_em2021_localidad_persona', column: 'employed / fact_em2021_localidad.employed × 1000', unit: 'por 1.000 ocupados' }
      : { key: 'personas13_per_1000_employed', label: 'Por 1.000 ocupados', table: 'fact_em2021_localidad', column: 'personas13_per_1000_employed', unit: 'por 1.000 ocupados' },
    { key: 'core_it', label: 'TI núcleo', table: 'fact_em2021_localidad', column: 'core_it', unit: 'ocupados' },
    { key: 'software_it', label: 'Empresas de software y TI', table: 'fact_companies_zone', column: "software_it (excluye BOG-00)", unit: 'empresas' },
    { key: 'hh_computer_pct', label: 'Hogares con computador (%)', table: 'fact_em2021_localidad', column: 'hh_computer_pct', unit: '%' },
  ];

  const features = zones.map((z) => {
    const id = String(z.zone_id);
    const e = mEm.get(id) || {};
    let geometry = null;
    try { geometry = typeof z.geojson === 'string' ? JSON.parse(z.geojson) : z.geojson; } catch (_) { geometry = null; }
    return {
      type: 'Feature',
      id,
      geometry,
      properties: {
        zone_id: id,
        municipality_code: z.municipality_code ? String(z.municipality_code) : null,
        zone_code: z.zone_code,
        name: z.name,
        lat: num(z.lat),
        lon: num(z.lon),
        values: {
          personas13: p ? (e.zone_id === undefined ? null : (zp.get(`${id}|${p}`) ?? 0)) : num(e.personas13),
          personas13_per_1000_employed: p
            ? (e.zone_id === undefined || !Number(e.employed) ? null : Math.round(((zp.get(`${id}|${p}`) ?? 0) / Number(e.employed)) * 10000) / 10)
            : num(e.personas13_per_1000_employed),
          core_it: num(e.core_it),
          software_it: mComp.get(id) ?? null,
          hh_computer_pct: num(e.hh_computer_pct),
        },
      },
    };
  });

  return {
    type: 'FeatureCollection',
    layer: 'localidades',
    persona: p,
    persona_note: 'Personas por zona solo en Bogotá (Encuesta Multipropósito 2021). Sumapaz (rural) no se dibuja.',
    excluded_zones: EXCLUDED_ZONES,
    geometry_source: srcFor(sources, 'geo_zone'),
    attribution: ['© OpenStreetMap contributors', 'Catastro Bogotá (datos abiertos)'],
    indicators: buildIndicators(defs, sources),
    features,
  };
}

// ───────────────────────── Personas ─────────────────────────
async function getPersonas() {
  const sources = await getSources();
  const personas = await getPersonaList();
  return { source: srcFor(sources, 'fact_persona_profile'), count: personas.length, personas };
}

// ───────────────────────── Health ─────────────────────────
async function getHealth() {
  const out = { status: 'ok', mysql_version: null, axis_check_ok: false };
  try {
    const [v] = await q('SELECT VERSION() AS v');
    out.mysql_version = v.v;
    const rows = await q(
      `SELECT lat, lon, ST_Latitude(point) AS plat, ST_Longitude(point) AS plon
         FROM geo_municipality WHERE municipality_code = '11001'`
    );
    if (rows.length) {
      const r = rows[0];
      out.axis_check = { lat: num(r.lat), lon: num(r.lon), point_lat: num(r.plat), point_lon: num(r.plon) };
      out.axis_check_ok = r.plat !== null && Math.abs(r.plat - r.lat) < 0.001 && Math.abs(r.plon - r.lon) < 0.001
        && Number(r.plat) > 0 && Number(r.plon) < 0;
    }
  } catch (e) {
    out.status = 'degraded';
    out.error = e.message;
  }
  return out;
}

module.exports = { getDepartments, getMunicipalities, getLocalidades, getPersonas, getHealth };