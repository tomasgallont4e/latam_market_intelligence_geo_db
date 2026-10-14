'use strict';
// Loads the geodb-v2 CSVs (data/geodb-v2/csv) into MySQL 8 inside one transaction.
// - Codes are ALWAYS kept as strings (leading zeros intact) — csv-parse cast is off.
// - geo_municipality.point : ST_GeomFromText('POINT(lon lat)', 4326, 'axis-order=long-lat')
// - geo_zone.geometry      : ST_GeomFromGeoJSON(geojson, 1, 4326), Bogotá (11001), Medellín (05001), Cali (76001),
//                            Barranquilla (08001), Bucaramanga (68001)
//                            Medellín polygons: Alcaldía de Medellín, INTERNAL USE ONLY (license unconfirmed)
//                            Cali polygons: IDESC / DAP Cali (DIVIPOLA 2026, package says CC BY-SA 4.0), INTERNAL USE ONLY by project policy
//                            Barranquilla / Bucaramanga polygons: Alcaldías, INTERNAL USE ONLY (license unconfirmed)
// - geo_department_shape   : geojson stored as text, each value validated with ST_GeomFromGeoJSON
// - geo_department.point   : average of its municipalities' points
// - meta_sources.year      : from seed cfg_seed_meta_sources_years (+ 8 v2 tables)
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');
const pool = require('../db/pool');

const DEFAULT_CSV_DIR = path.join(__dirname, '..', 'data', 'geodb-v2', 'csv');
const SOURCE_FILE = 'data/geodb-v2/csv';
const BATCH_SIZE = 500;
const NO_POINT_MUNICIPALITIES = new Set(['27493']); // Nuevo Belén de Bajirá (approved exception)
const BOGOTA = '11001';
const MEDELLIN = '05001';
const CALI = '76001';
const BARRANQUILLA = '08001';
const BUCARAMANGA = '68001';
// Municipalities whose zone polygons are loaded. Medellín, Cali, Barranquilla and Bucaramanga:
// internal use only, commercial license not confirmed (see meta_sources and project memory #73).
const ZONE_GEOMETRY_MUNICIPALITIES = new Set([BOGOTA, MEDELLIN, CALI, BARRANQUILLA, BUCARAMANGA]);

// Overrides applied on top of meta_sources.csv (kept in code so reloads don't lose them).
const META_OVERRIDES = {
  geo_zone: {
    description: 'Zones inside Bogotá, Medellín, Cali, Barranquilla and Bucaramanga: 88 zones, all with boundaries — 20 Bogotá localidades, 21 Medellín comunas and corregimientos, 22 Cali comunas, 5 Barranquilla localidades, 20 Bucaramanga zones (17 comunas + 3 corregimientos; BUC-C1..BUC-C3 are PLACEHOLDER codes, not official). Medellín, Cali, Barranquilla and Bucaramanga polygons: INTERNAL USE ONLY — commercial-use license not confirmed.',
    source: 'Catastro Bogotá, datos abiertos de Bogotá ("Localidad. Bogotá D.C.", attribution required); Medellín polygons: Alcaldía de Medellín, VC_Limite_Politico_Admtivo (internal use only, license unconfirmed); Cali polygons: IDESC, Departamento Administrativo de Planeación – Alcaldía de Santiago de Cali, DIVIPOLA 2026, declared CC BY-SA 4.0 by the package (project policy unchanged: internal use only); Barranquilla polygons: Alcaldía de Barranquilla (internal use only, license unconfirmed); Bucaramanga polygons: Alcaldía de Bucaramanga (internal use only, license unconfirmed)',
  },
};

// Text appended to the source of a table from meta_sources.csv (keeps the original text).
const META_SOURCE_APPEND = {
  fact_companies_zone: 'Cali (CAL-01..CAL-22, 2025): Cámara de Comercio de Cali, tableros económicos 2025 (https://www.ccc.org.co/informacion-y-estudios-economicos/tableros-economicos/); company size measured by revenue, not comparable with Bogotá (assets)',
};

// Text appended at the END of a table's description (keeps the original text). db_mods.rar (Barranquilla / Bucaramanga).
const META_DESCRIPTION_APPEND = {
  fact_companies_zone: 'Barranquilla (5 BAQ- localidades) and Bucaramanga (20 BUC- zones) are listed with counts blank: no current file assigns firms to those zones.',
  fact_zone_context: 'Added: Bucaramanga 17 comunas and 3 corregimientos with 2021 population from the alcaldía file (Alcaldía de Bucaramanga, datos.gov.co kn95-8dei; duplicate polygon rows for the same barrio were not added) and Barranquilla 5 localidades with population blank. Persona counts by zone are blank.',
  fact_persona_profile_metro_2025: 'Bucaramanga A.M. (68001) and Barranquilla–Soledad (08001) are the August 2025–July 2026 average (survey_year 2026; DANE GEIH microdata, catalogues 853 and 900). Medellín and Cali remain the GEIH 2025 calendar year.',
  fact_geih2025_metro_summary: 'Bucaramanga A.M. (68001) and Barranquilla–Soledad (08001) are August 2025–July 2026 (survey_year 2026; DANE GEIH microdata, catalogues 853 and 900). Medellín and Cali remain calendar 2025.',
};

// Load order: geo_* first, then fact_*, then meta_sources.
const TABLE_ORDER = [
  'geo_department', 'geo_municipality', 'geo_zone', 'geo_department_shape',
  'fact_persona_profile', 'fact_persona_metro', 'fact_persona_department', 'fact_persona_segment',
  'fact_ict_by_sector', 'fact_schools_municipality', 'fact_higher_ed_municipality',
  'fact_saber11_department', 'fact_micro_department', 'fact_micro_national',
  'fact_companies_chamber', 'fact_companies_zone', 'fact_secop_department',
  'fact_vacancies_department', 'fact_developers_country', 'fact_dev_communities',
  'fact_tech_events', 'fact_em2021_localidad', 'fact_em2021_upz',
  'fact_zone_context', 'fact_persona_profile_metro_2025', 'fact_geih2025_metro_summary',
  'fact_persona_segment_metro_2025', 'fact_zone_indicator', 'meta_companies_zone', 'meta_geo_zone',
  'meta_sources',
];

// Seed cfg_seed_meta_sources_years (environment layer). The v2 entries after
// geo_department_shape were truncated in the design payload; their years come
// from diccionario.md ("Capas agregadas en la v2").
const META_YEARS = {
  geo_department: '2023',
  geo_municipality: '2023',
  geo_zone: '2026',
  fact_persona_profile: '2025',
  fact_persona_metro: '2025',
  fact_persona_department: '2025',
  fact_persona_segment: '2025',
  fact_ict_by_sector: '2025',
  fact_schools_municipality: '2025',
  fact_higher_ed_municipality: '2024',
  fact_micro_department: '2024',
  fact_micro_national: '2024',
  fact_companies_chamber: '2026',
  fact_companies_zone: 'Bogotá 2026 / Medellín 2022 / Cali 2025',
  fact_developers_country: '2026 Q1',
  geo_department_shape: '2018',
  fact_secop_department: '2025',
  fact_saber11_department: '2022',
  fact_vacancies_department: '2026',
  fact_em2021_localidad: '2021',
  fact_em2021_upz: '2021',
  fact_dev_communities: '2026',
  fact_tech_events: '2026',
  fact_zone_context: 'Medellín 2025 / Cali 2021',
  fact_persona_profile_metro_2025: '2025',
  fact_geih2025_metro_summary: '2025',
  fact_persona_segment_metro_2025: '2025',
  fact_zone_indicator: '2021',
  meta_companies_zone: '2025',
  meta_geo_zone: '2026',
};

// meta_sources.csv only lists the 15 v1 tables; the 8 v2 tables are registered
// from diccionario.md so that every table has a source and a year (memory #73).
const META_V2_ROWS = [
  { table_name: 'geo_department_shape', description: 'Department boundaries (polygons, WGS84, 3 decimals)', source: 'DANE Marco Geoestadístico, via John Guerra (gist 43c7656821069d00dcbc)' },
  { table_name: 'fact_secop_department', description: 'Public contracts for software and IT services signed in 2025, by department of the buyer', source: 'SECOP II (datos.gov.co jbjy-vk9h), secop-software.py' },
  { table_name: 'fact_saber11_department', description: 'Saber 11 (2022-2), grade 11 students by department of the school', source: 'ICFES (datos.gov.co kgxf-xxbe), saber11-colegios.py' },
  { table_name: 'fact_vacancies_department', description: 'Active job offers by keyword and department, snapshot of 2026-10-01 (national offers without department excluded)', source: 'Servicio Público de Empleo, Buscador de Empleo' },
  { table_name: 'fact_em2021_localidad', description: 'People in the 13 personas and household connectivity by localidad of Bogotá (2021)', source: 'DANE and SDP, Encuesta Multipropósito 2021, em2021-bogota-personas.py' },
  { table_name: 'fact_em2021_upz', description: 'People in the 13 personas by UPZ of Bogotá (2021); reliable = 30+ interviews', source: 'Encuesta Multipropósito 2021' },
  { table_name: 'fact_dev_communities', description: 'Technology Meetup groups with 300+ members (lifetime sign-ups), 2026-10-02', source: 'meetup.com group search' },
  { table_name: 'fact_tech_events', description: 'Main technology and AI events in Colombia, 2026 editions', source: 'Official event sites and press' },
  { table_name: 'fact_zone_context', description: '43 Medellín and Cali zones: residents (Medellín ECV 2025, Cali population ASIS 2021), household computer/tablet and internet, university adults. No persona counts by comuna (personas13 always empty).', source: 'Alcaldía de Medellín, Encuesta de Calidad de Vida 2025 (https://www.medellin.gov.co/es/wp-content/uploads/2022/08/ECV_2025.xlsx); Cali: ASIS 2021, Tabla 2 (DANE / DAP)' },
  { table_name: 'fact_persona_profile_metro_2025', description: 'Profile of the 13 personas by metropolitan area (Medellín A.M., Cali–Yumbo), annual average 2025: sample, age, income median (positive incomes), % women, % university. Work at home is not telework.', source: 'DANE GEIH 2025 (catalog 853, 12 months, FEX_C18, CIUO-4)' },
  { table_name: 'fact_geih2025_metro_summary', description: 'GEIH 2025 totals by metropolitan area (Medellín A.M., Cali–Yumbo). Domain totals: never repeat or split by comuna.', source: 'DANE GEIH 2025 (12 months, FEX_C18)' },
  { table_name: 'fact_persona_segment_metro_2025', description: 'Cali–Yumbo (76001 anchors the domain, includes Yumbo): 13 personas × buyer type, GEIH 2025 annual average, 60 rows. Domain totals: never split by comuna.', source: 'DANE GEIH 2025, dominio Cali–Yumbo, promedio anual; catálogo 853 (https://microdatos.dane.gov.co/index.php/catalog/853/get-microdata)' },
  { table_name: 'fact_zone_indicator', description: 'Cali comunas CAL-01..CAL-22: projected population 2021 by zone of residence (rows sum 2,174,660; not converted to 2025).', source: 'Cali ASIS 2021, Tabla 2, población proyectada DANE / Planeación (https://www.minsalud.gov.co/sites/rid/Lists/BibliotecaDigital/RIDE/VS/ED/PSP/asis-cali-distrito-2021.pdf)' },
  { table_name: 'meta_companies_zone', description: 'Per-zone provenance of fact_companies_zone for Cali (CAL-01..CAL-22): source, year, size basis (revenue), scope and status (activity by comuna unavailable).', source: 'Cámara de Comercio de Cali, tableros económicos 2025 (https://www.ccc.org.co/informacion-y-estudios-economicos/tableros-economicos/)' },
  { table_name: 'meta_geo_zone', description: 'Geometry provenance and license by municipality (Cali 76001). Package declares CC BY-SA 4.0; project policy unchanged: internal use only.', source: 'IDESC / Departamento Administrativo de Planeación – Alcaldía de Santiago de Cali, DIVIPOLA 2026 (https://mg-idesc.cali.gov.co/geonetwork/srv/api/records/f33097b6-33db-4bc8-8674-f9848b763fc0)' },
];

const NUMERIC_TYPES = new Set(['int', 'bigint', 'smallint', 'tinyint', 'mediumint', 'double', 'float', 'decimal']);

function readCsv(csvDir, table) {
  const file = path.join(csvDir, `${table}.csv`);
  if (!fs.existsSync(file)) throw new Error(`CSV not found: ${file}`);
  return parse(fs.readFileSync(file, 'utf8'), {
    columns: true,
    bom: true,
    skip_empty_lines: true,
    cast: false, // keep every value as a string — never Number() a code
    trim: false,
  });
}

function clean(v) {
  if (v === undefined || v === null) return null;
  const s = String(v).trim();
  return s === '' ? null : s;
}

async function tableColumns(conn, table) {
  const [rows] = await conn.query(
    `SELECT column_name AS col, data_type AS dt, extra AS extra
       FROM information_schema.columns
      WHERE table_schema = DATABASE() AND table_name = ?
      ORDER BY ordinal_position`, [table]);
  if (!rows.length) throw new Error(`Table ${table} does not exist in the DB`);
  return rows;
}

// Generic batched insert. `cols` = [{ name, expr }], expr defaults to '?'.
async function insertRows(conn, table, cols, rows) {
  if (!rows.length) return 0;
  const colList = cols.map((c) => `\`${c.name}\``).join(', ');
  const tuple = `(${cols.map((c) => c.expr || '?').join(', ')})`;
  let n = 0;
  for (let i = 0; i < rows.length; i += BATCH_SIZE) {
    const chunk = rows.slice(i, i + BATCH_SIZE);
    const sql = `INSERT INTO \`${table}\` (${colList}) VALUES ${chunk.map(() => tuple).join(', ')}`;
    const params = [];
    for (const r of chunk) params.push(...r);
    const [res] = await conn.query(sql, params);
    n += res.affectedRows;
  }
  return n;
}

// Plain tables: map CSV headers 1:1 onto table columns (names untranslated).
async function loadPlain(conn, table, records) {
  const dbCols = await tableColumns(conn, table);
  const byName = new Map(dbCols.map((c) => [c.col, c]));
  const headers = records.length ? Object.keys(records[0]) : [];
  const unknown = headers.filter((h) => !byName.has(h));
  if (unknown.length) throw new Error(`${table}: CSV columns not in table: ${unknown.join(', ')}`);
  const cols = headers.map((h) => ({ name: h }));
  const rows = records.map((r) => headers.map((h) => clean(r[h])));
  return insertRows(conn, table, cols, rows);
}

function validCoord(lat, lon) {
  const la = Number(lat); const lo = Number(lon);
  return Number.isFinite(la) && Number.isFinite(lo) && la >= -90 && la <= 90 && lo >= -180 && lo <= 180;
}

async function loadMunicipalities(conn, records) {
  const cols = ['municipality_code', 'department_code', 'name', 'lat', 'lon', 'wkt']
    .map((name) => ({ name }));
  cols.push({ name: 'point', expr: "ST_GeomFromText(?, 4326, 'axis-order=long-lat')" });
  let noPoint = 0;
  const rows = records.map((r) => {
    const code = clean(r.municipality_code);
    const lat = clean(r.lat); const lon = clean(r.lon);
    let pointWkt = null;
    if (!NO_POINT_MUNICIPALITIES.has(code) && lat !== null && lon !== null && validCoord(lat, lon)) {
      pointWkt = `POINT(${lon} ${lat})`; // long-lat, matching axis-order option
    } else noPoint += 1;
    return [code, clean(r.department_code), clean(r.name), lat, lon, clean(r.wkt), pointWkt];
  });
  const n = await insertRows(conn, 'geo_municipality', cols, rows);
  return { n, note: `${noPoint} without point` };
}

// Restores a leading zero lost by spreadsheet tools (e.g. '8001' -> '08001').
function normMuni(raw) {
  const m = clean(raw);
  return m && /^\d{4}$/.test(m) ? m.padStart(5, '0') : m;
}

// Pre-check before touching the DB: duplicated (municipality_code, zone_code) keys
// and duplicated zone_id in geo_zone.csv. Throws a clear message naming the zones in conflict,
// instead of failing mid-transaction with MySQL's "Duplicate entry ... uq_geo_zone_muni_code".
function checkZoneDuplicates(records) {
  const byKey = new Map();
  const byId = new Map();
  records.forEach((r, i) => {
    const line = i + 2; // +1 header, +1 base-1
    const zoneId = clean(r.zone_id) || `(sin zone_id, fila ${line})`;
    const key = `${normMuni(r.municipality_code)}-${clean(r.zone_code)}`;
    if (!byKey.has(key)) byKey.set(key, []);
    byKey.get(key).push(zoneId);
    if (clean(r.zone_id)) {
      if (!byId.has(zoneId)) byId.set(zoneId, []);
      byId.get(zoneId).push(line);
    }
  });
  const problems = [];
  for (const [key, ids] of byKey) {
    if (ids.length > 1) problems.push(`clave duplicada ${key} en ${ids.join(', ')}`);
  }
  for (const [id, lines] of byId) {
    if (lines.length > 1) problems.push(`zone_id duplicado ${id} en las filas ${lines.join(', ')}`);
  }
  if (problems.length) {
    throw new Error(`geo_zone.csv: ${problems.join('; ')}. Carga cancelada antes de modificar la base de datos.`);
  }
}

async function loadZones(conn, records) {
  const cols = ['zone_id', 'municipality_code', 'zone_type', 'zone_code', 'name', 'lat', 'lon', 'geojson', 'wkt']
    .map((name) => ({ name }));
  cols.push({ name: 'geometry', expr: 'ST_GeomFromGeoJSON(?, 1, 4326)' });
  let withGeom = 0;
  let n = 0;
  // Row by row: polygons are large strings.
  for (const r of records) {
    const rawMuni = clean(r.municipality_code);
    // Safeguard: restore a leading zero lost by spreadsheet tools (e.g. '8001' -> '08001').
    const muni = rawMuni && /^\d{4}$/.test(rawMuni) ? rawMuni.padStart(5, '0') : rawMuni;
    const withGeometry = ZONE_GEOMETRY_MUNICIPALITIES.has(muni);
    // Medellín, Cali, Barranquilla and Bucaramanga polygons: internal use only, license unconfirmed.
    const geojson = withGeometry ? clean(r.geojson) : null;
    const wkt = withGeometry ? clean(r.wkt) : null;
    if (geojson) withGeom += 1;
    n += await insertRows(conn, 'geo_zone', cols, [[
      clean(r.zone_id), muni, clean(r.zone_type), clean(r.zone_code), clean(r.name),
      clean(r.lat), clean(r.lon), geojson, wkt, geojson,
    ]]);
  }
  return { n, note: `${withGeom} with polygon` };
}

async function loadDepartmentShapes(conn, records) {
  let invalid = [];
  const rows = [];
  for (const r of records) {
    const code = clean(r.department_code);
    const gj = clean(r.geojson);
    try {
      const [[v]] = await conn.query('SELECT ST_SRID(ST_GeomFromGeoJSON(?, 1, 4326)) AS srid', [gj]);
      if (Number(v.srid) !== 4326) invalid.push(code);
    } catch (e) {
      invalid.push(`${code} (${e.code || e.message})`);
    }
    rows.push([code, clean(r.name), gj]);
  }
  const n = await insertRows(conn, 'geo_department_shape',
    [{ name: 'department_code' }, { name: 'name' }, { name: 'geojson' }], rows);
  return { n, note: invalid.length ? `INVALID geojson: ${invalid.join(', ')}` : `${n} valid geojson`, invalid };
}

async function loadMetaSources(conn, records) {
  const byTable = new Map();
  for (const r of records) {
    byTable.set(clean(r.table_name), { description: clean(r.description), source: clean(r.source) });
  }
  for (const r of META_V2_ROWS) {
    if (!byTable.has(r.table_name)) byTable.set(r.table_name, { description: r.description, source: r.source });
  }
  for (const [t, v] of Object.entries(META_OVERRIDES)) byTable.set(t, { ...byTable.get(t), ...v });
  for (const [t, extra] of Object.entries(META_SOURCE_APPEND)) {
    const cur = byTable.get(t) || { description: null, source: null };
    byTable.set(t, { ...cur, source: cur.source ? `${cur.source}; ${extra}` : extra });
  }
  for (const [t, extra] of Object.entries(META_DESCRIPTION_APPEND)) {
    const cur = byTable.get(t) || { description: null, source: null };
    byTable.set(t, { ...cur, description: cur.description ? `${cur.description} ${extra}` : extra });
  }
  const rows = [...byTable.entries()].map(([t, v]) => [t, v.description, v.source, META_YEARS[t] || null]);
  const n = await insertRows(conn, 'meta_sources',
    [{ name: 'table_name' }, { name: 'description' }, { name: 'source' }, { name: 'year' }], rows);
  const missingYear = rows.filter((r) => !r[3]).map((r) => r[0]);
  return { n, note: missingYear.length ? `no year: ${missingYear.join(', ')}` : 'all with year' };
}

async function computeDepartmentPoints(conn) {
  const [res] = await conn.query(`
    UPDATE geo_department d
      JOIN (SELECT department_code,
                   AVG(ST_Longitude(point)) AS lon,
                   AVG(ST_Latitude(point))  AS lat
              FROM geo_municipality
             WHERE point IS NOT NULL
             GROUP BY department_code) m ON m.department_code = d.department_code
       SET d.point = ST_GeomFromText(CONCAT('POINT(', ROUND(m.lon, 7), ' ', ROUND(m.lat, 7), ')'), 4326, 'axis-order=long-lat')`);
  return res.affectedRows;
}

async function runValidationHook(batchId, log) {
  let validator;
  try {
    validator = require('./validation');
  } catch (e) {
    if (e.code === 'MODULE_NOT_FOUND' && /validation/.test(e.message)) {
      log('validation: lib/validation.js not present yet — skipped');
      return null;
    }
    throw e;
  }
  const fn = validator.validateBatch || validator.run || validator.default;
  if (typeof fn !== 'function') { log('validation: no validateBatch() export — skipped'); return null; }
  log('validation: running…');
  return fn(batchId);
}

async function loadAll({ csvDir = DEFAULT_CSV_DIR, log = console.log } = {}) {
  const [batchRes] = await pool.query(
    "INSERT INTO load_batch (country_code, source_file, status, rows_loaded) VALUES ('CO', ?, 'running', 0)",
    [SOURCE_FILE]);
  const batchId = batchRes.insertId;
  log(`load_batch #${batchId} started (source ${SOURCE_FILE})`);

  const conn = await pool.getConnection();
  const report = [];
  let rowsLoaded = 0;
  try {
    // Seed country (idempotent)
    await conn.query(
      `INSERT INTO country (country_code, name, geo_code_scheme) VALUES ('CO', 'Colombia', 'DIVIPOLA')
       ON DUPLICATE KEY UPDATE name = VALUES(name), geo_code_scheme = VALUES(geo_code_scheme)`);

    // Parse everything first so a bad CSV fails before touching the DB.
    const data = {};
    for (const t of TABLE_ORDER) data[t] = readCsv(csvDir, t);

    // Fail early, with a readable message, if geo_zone.csv has duplicated keys or zone_id.
    checkZoneDuplicates(data.geo_zone);

    await conn.beginTransaction();
    // Reload replaces the previous data set (DELETE, not TRUNCATE, to stay transactional).
    for (const t of [...TABLE_ORDER].reverse()) await conn.query(`DELETE FROM \`${t}\``);

    for (const t of TABLE_ORDER) {
      const recs = data[t];
      let out;
      if (t === 'geo_municipality') out = await loadMunicipalities(conn, recs);
      else if (t === 'geo_zone') out = await loadZones(conn, recs);
      else if (t === 'geo_department_shape') out = await loadDepartmentShapes(conn, recs);
      else if (t === 'meta_sources') out = await loadMetaSources(conn, recs);
      else out = { n: await loadPlain(conn, t, recs) };
      if (out.n !== recs.length && t !== 'meta_sources') {
        throw new Error(`${t}: inserted ${out.n} of ${recs.length} CSV rows`);
      }
      rowsLoaded += out.n;
      report.push({ table: t, csv_rows: recs.length, inserted: out.n, note: out.note || '' });
      log(`  ${t.padEnd(30)} ${String(out.n).padStart(6)}${out.note ? '  (' + out.note + ')' : ''}`);
      if (t === 'geo_municipality') {
        // department point needs municipalities; geo_department already loaded
        const d = await computeDepartmentPoints(conn);
        log(`  geo_department.point computed for ${d} departments`);
      }
    }

    await conn.commit();
  } catch (err) {
    try { await conn.rollback(); } catch (_) { /* ignore */ }
    conn.release();
    await pool.query(
      "UPDATE load_batch SET status = 'failed', finished_at = NOW(), rows_loaded = 0, notes = ? WHERE id = ?",
      [String(err.message).slice(0, 2000), batchId]);
    err.batchId = batchId;
    throw err;
  }
  conn.release();

  await pool.query(
    'UPDATE load_batch SET rows_loaded = ?, finished_at = NOW(), notes = ? WHERE id = ?',
    [rowsLoaded, `Loaded ${report.length} tables from ${SOURCE_FILE}`, batchId]);
  log(`load_batch #${batchId}: ${rowsLoaded} rows loaded`);

  let validation = null;
  try {
    validation = await runValidationHook(batchId, log);
  } catch (e) {
    log(`validation error: ${e.message}`);
  }
  return { batchId, rowsLoaded, report, validation };
}

module.exports = { loadAll, TABLE_ORDER, META_YEARS };