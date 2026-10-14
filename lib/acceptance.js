'use strict';
// Acceptance checks (rule_acceptance_totals, rule_tolerances, rule_axis_order,
// rule_approved_exceptions). READ-ONLY: computes every check; persistence lives
// in lib/validation.js. Each check returns expected / actual / difference / ok.
const pool = require('../db/pool');

const BOGOTA = '11001';
const MEDELLIN = '05001';
const CALI = '76001';
const BARRANQUILLA = '08001';
const BUCARAMANGA = '68001';
const REST = 'Rest of the country';
const AXIS_EXPECTED = { lat: 4.31, lon: -74.18, tolerance: 0.01 };
const PERSONA_TOL = 30;

const GEO_FACT_TABLES = [
  'geo_department', 'geo_municipality', 'geo_zone', 'geo_department_shape',
  'fact_persona_profile', 'fact_persona_metro', 'fact_persona_department', 'fact_persona_segment',
  'fact_ict_by_sector', 'fact_schools_municipality', 'fact_higher_ed_municipality',
  'fact_saber11_department', 'fact_micro_department', 'fact_micro_national',
  'fact_companies_chamber', 'fact_companies_zone', 'fact_secop_department',
  'fact_vacancies_department', 'fact_developers_country', 'fact_dev_communities',
  'fact_tech_events', 'fact_em2021_localidad', 'fact_em2021_upz',
  'fact_zone_context', 'fact_persona_profile_metro_2025', 'fact_geih2025_metro_summary',
  'fact_persona_segment_metro_2025', 'fact_zone_indicator', 'meta_companies_zone', 'meta_geo_zone',
];

// Every code column in fact_* (and geo_municipality) that must join its geo table.
// `exception` = SQL predicate (alias f) for approved 'sin geografía' rows.
const JOIN_RULES = [
  { table: 'geo_municipality', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_persona_metro', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code',
    exception: `f.municipality_code IS NULL AND f.metro_area = '${REST}'`, exceptionLabel: REST },
  { table: 'fact_persona_department', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_persona_segment', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code',
    exception: `f.municipality_code IS NULL AND f.city = '${REST}'`, exceptionLabel: REST },
  { table: 'fact_schools_municipality', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_schools_municipality', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_higher_ed_municipality', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_higher_ed_municipality', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_saber11_department', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_micro_department', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_companies_chamber', column: 'seat_municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.seat_municipality_code' },
  { table: 'fact_companies_chamber', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_companies_zone', column: 'zone_id', ref: 'geo_zone r ON r.zone_id = f.zone_id',
    exception: "f.zone_id = 'BOG-00'", exceptionLabel: 'BOG-00' },
  { table: 'fact_secop_department', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_vacancies_department', column: 'department_code', ref: 'geo_department r ON r.department_code = f.department_code' },
  { table: 'fact_dev_communities', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_tech_events', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_em2021_localidad', column: 'zone_id', ref: 'geo_zone r ON r.zone_id = f.zone_id' },
  { table: 'fact_em2021_upz', column: 'localidad_code',
    ref: `geo_zone r ON r.municipality_code = '${BOGOTA}' AND r.zone_code = f.localidad_code AND r.zone_id = CONCAT('BOG-', f.localidad_code)` },
  { table: 'fact_zone_context', column: 'zone_id', ref: 'geo_zone r ON r.zone_id = f.zone_id' },
  { table: 'fact_zone_context', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_persona_profile_metro_2025', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_geih2025_metro_summary', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_persona_segment_metro_2025', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
  { table: 'fact_zone_indicator', column: 'zone_id', ref: 'geo_zone r ON r.zone_id = f.zone_id' },
  { table: 'meta_companies_zone', column: 'zone_id', ref: 'geo_zone r ON r.zone_id = f.zone_id' },
  { table: 'meta_geo_zone', column: 'municipality_code', ref: 'geo_municipality r ON r.municipality_code = f.municipality_code' },
];

const num = (v) => (v === null || v === undefined ? null : Number(v));

async function scalar(sql, params = []) {
  const [rows] = await pool.query(sql, params);
  const r = rows[0] || {};
  return num(Object.values(r)[0]);
}

function check({ id, group, table, label, expected, actual, tolerance = 0, tolLabel, sub = [], detail = '' }) {
  const difference = actual === null ? null : actual - expected;
  const ok = difference !== null && Math.abs(difference) <= tolerance;
  return { id, group, table, label, expected, actual, difference, tolerance,
    tolLabel: tolLabel || (tolerance ? `±${tolerance}` : 'exacto'), ok, sub, detail };
}

async function unjoinedCodes() {
  const out = [];
  for (const r of JOIN_RULES) {
    const notExc = r.exception ? `AND NOT (${r.exception})` : '';
    const [rows] = await pool.query(
      `SELECT f.\`${r.column}\` AS code, COUNT(*) AS n
         FROM \`${r.table}\` f LEFT JOIN ${r.ref}
        WHERE r.\`${r.table === 'fact_em2021_upz' ? 'zone_id' : r.ref.split(' ')[3].split('.')[1]}\` IS NULL ${notExc}
        GROUP BY f.\`${r.column}\``);
    let excRows = 0;
    if (r.exception) excRows = await scalar(`SELECT COUNT(*) FROM \`${r.table}\` f WHERE ${r.exception}`);
    out.push({ ...r, unjoined: rows.map((x) => ({ code: x.code, n: Number(x.n) })),
      unjoinedRows: rows.reduce((s, x) => s + Number(x.n), 0), exceptionRows: excRows });
  }
  return out;
}

async function personaSums() {
  const dims = [
    { table: 'fact_persona_metro', label: 'Σ áreas metropolitanas' },
    { table: 'fact_persona_department', label: 'Σ departamentos' },
    { table: 'fact_persona_segment', label: 'Σ ciudad × tipo de comprador' },
  ];
  const res = [];
  for (const d of dims) {
    const [rows] = await pool.query(
      `SELECT p.persona, p.employed AS total, COALESCE(SUM(x.employed), 0) AS s
         FROM fact_persona_profile p LEFT JOIN \`${d.table}\` x ON x.persona = p.persona
        GROUP BY p.persona, p.employed`);
    let maxDiff = 0; let worst = null; let sum = 0;
    for (const r of rows) {
      const diff = Number(r.s) - Number(r.total);
      sum += Number(r.s);
      if (Math.abs(diff) > Math.abs(maxDiff)) { maxDiff = diff; worst = r.persona; }
    }
    res.push({ ...d, sum, maxDiff, worst, personas: rows.length });
  }
  return res;
}

async function departmentPolygons() {
  const [rows] = await pool.query(
    `SELECT s.department_code, s.geojson, d.department_code AS dep
       FROM geo_department_shape s LEFT JOIN geo_department d ON d.department_code = s.department_code`);
  const invalid = [];
  let valid = 0;
  for (const r of rows) {
    try {
      const [[g]] = await pool.query(
        `SELECT ST_GeometryType(g) AS t, ST_SRID(g) AS srid
           FROM (SELECT ST_GeomFromGeoJSON(?, 1, 4326) AS g) x`, [r.geojson]);
      const okType = /POLYGON/i.test(String(g.t));
      if (okType && Number(g.srid) === 4326 && r.dep) valid += 1;
      else invalid.push(`${r.department_code} (${g.t}, srid ${g.srid}${r.dep ? '' : ', sin geo_department'})`);
    } catch (e) {
      invalid.push(`${r.department_code} (${e.code || e.message})`);
    }
  }
  return { total: rows.length, valid, invalid };
}

async function axisTest() {
  const [[b]] = await pool.query(
    `SELECT municipality_code, name, ST_Latitude(point) AS lat, ST_Longitude(point) AS lon, ST_SRID(point) AS srid
       FROM geo_municipality WHERE municipality_code = ?`, [BOGOTA]);
  if (!b || b.lat === null) {
    return { ok: false, expected: AXIS_EXPECTED, actual: null, message: 'Bogotá (11001) sin punto' };
  }
  const lat = Number(b.lat); const lon = Number(b.lon);
  const ok = Math.abs(lat - AXIS_EXPECTED.lat) <= AXIS_EXPECTED.tolerance
    && Math.abs(lon - AXIS_EXPECTED.lon) <= AXIS_EXPECTED.tolerance;
  return { ok, expected: AXIS_EXPECTED, actual: { lat, lon, srid: Number(b.srid) }, name: b.name,
    sql: `SELECT ST_Latitude(point), ST_Longitude(point) FROM geo_municipality WHERE municipality_code = '${BOGOTA}'` };
}

async function exceptions() {
  const list = [];
  const add = (table, column, code, n, message) => { if (n > 0) list.push({ table, column, code, n, message }); };
  add('fact_persona_metro', 'metro_area', REST,
    await scalar(`SELECT COUNT(*) FROM fact_persona_metro WHERE municipality_code IS NULL AND metro_area = ?`, [REST]),
    `'${REST}' sin municipality_code (excepción aprobada, sin geografía)`);
  add('fact_persona_segment', 'city', REST,
    await scalar(`SELECT COUNT(*) FROM fact_persona_segment WHERE municipality_code IS NULL AND city = ?`, [REST]),
    `'${REST}' sin municipality_code (excepción aprobada, sin geografía)`);
  add('fact_companies_zone', 'zone_id', 'BOG-00',
    await scalar(`SELECT COUNT(*) FROM fact_companies_zone WHERE zone_id = 'BOG-00'`),
    'BOG-00 (Sin localidad) sin fila en geo_zone (excepción aprobada)');

  add('geo_municipality', 'point', '27493',
    await scalar(`SELECT COUNT(*) FROM geo_municipality WHERE municipality_code = '27493' AND point IS NULL`),
    'Nuevo Belén de Bajirá (27493) cargado sin punto; no aparece en el mapa');
  add('fact_em2021_upz', 'upz_code', 'UPZ',
    await scalar('SELECT COUNT(*) FROM fact_em2021_upz'),
    'UPZ de Bogotá sin polígono ni fila en geo_zone (excepción aprobada)');
  return list;
}

async function missingSources() {
  const [rows] = await pool.query('SELECT table_name, source, year FROM meta_sources');
  const by = new Map(rows.map((r) => [r.table_name, r]));
  return GEO_FACT_TABLES.filter((t) => !by.get(t) || !by.get(t).source || !by.get(t).year);
}

async function latestBatchId() {
  return scalar('SELECT MAX(id) FROM load_batch');
}

async function computeAcceptance() {
  const checks = [];
  const V1 = 'v1'; const V2 = 'v2';

  checks.push(check({ id: 'municipalities', group: V1, table: 'geo_municipality', label: 'Municipios',
    expected: 1123, actual: await scalar('SELECT COUNT(*) FROM geo_municipality') }));

  const polyCount = (muni) => scalar(`SELECT COUNT(*) FROM geo_zone WHERE municipality_code = ? AND geometry IS NOT NULL`, [muni]);
  const bogPoly = await polyCount(BOGOTA);
  const medPoly = await polyCount(MEDELLIN);
  const calPoly = await polyCount(CALI);
  const baqPoly = await polyCount(BARRANQUILLA);
  const bucPoly = await polyCount(BUCARAMANGA);
  const noGeom = await scalar('SELECT COUNT(*) FROM geo_zone WHERE geometry IS NULL');
  const zones = check({ id: 'zones', group: V1, table: 'geo_zone', label: 'Zonas urbanas',
    expected: 88, actual: await scalar('SELECT COUNT(*) FROM geo_zone'),
    sub: [
      { label: 'Bogotá, con polígono', filter: "municipality_code = '11001'", expected: 20, actual: bogPoly, difference: bogPoly - 20, ok: bogPoly === 20 },
      { label: 'Medellín, con polígono', filter: "municipality_code = '05001'", expected: 21, actual: medPoly, difference: medPoly - 21, ok: medPoly === 21 },
      { label: 'Cali, con polígono', filter: "municipality_code = '76001'", expected: 22, actual: calPoly, difference: calPoly - 22, ok: calPoly === 22 },
      { label: 'Barranquilla, con polígono', filter: "municipality_code = '08001'", expected: 5, actual: baqPoly, difference: baqPoly - 5, ok: baqPoly === 5 },
      { label: 'Bucaramanga, con polígono', filter: "municipality_code = '68001'", expected: 20, actual: bucPoly, difference: bucPoly - 20, ok: bucPoly === 20 },
      { label: 'Zonas sin geometría', filter: 'geometry IS NULL', expected: 0, actual: noGeom, difference: noGeom, ok: noGeom === 0 },
    ] });
  zones.ok = zones.ok && zones.sub.every((s) => s.ok);
  checks.push(zones);

  checks.push(check({ id: 'schools', group: V1, table: 'fact_schools_municipality', label: 'Colegios',
    expected: 11111, actual: await scalar('SELECT SUM(schools) FROM fact_schools_municipality') }));
  checks.push(check({ id: 'students_9_11', group: V1, table: 'fact_schools_municipality', label: 'Estudiantes grados 9–11',
    expected: 1732523, actual: await scalar('SELECT SUM(students_9_11) FROM fact_schools_municipality') }));
  checks.push(check({ id: 'higher_ed', group: V1, table: 'fact_higher_ed_municipality', label: 'Matrícula educación superior',
    expected: 2561707, actual: await scalar('SELECT SUM(students_total) FROM fact_higher_ed_municipality') }));
  const nPersonas = await scalar('SELECT COUNT(*) FROM fact_persona_profile');
  checks.push(check({ id: 'personas', group: V1, table: 'fact_persona_profile', label: 'Personas (13 personas)',
    expected: 1716675, actual: await scalar('SELECT SUM(employed) FROM fact_persona_profile'),
    detail: `${nPersonas} personas`,
    sub: [{ label: 'Número de personas', expected: 13, actual: nPersonas, difference: nPersonas - 13, ok: nPersonas === 13 }] }));
  checks[checks.length - 1].ok = checks[checks.length - 1].ok && nPersonas === 13;
  checks.push(check({ id: 'companies_bogota', group: V1, table: 'fact_companies_zone', label: 'Empresas Bogotá',
    expected: 465498, actual: await scalar("SELECT SUM(companies_total) FROM fact_companies_zone WHERE zone_id LIKE 'BOG-%'") }));
  checks.push(check({ id: 'companies_medellin', group: V1, table: 'fact_companies_zone', label: 'Empresas Medellín',
    expected: 109703, actual: await scalar("SELECT SUM(companies_total) FROM fact_companies_zone WHERE zone_id LIKE 'MED-%'") }));
  checks.push(check({ id: 'micro', group: V1, table: 'fact_micro_department', label: 'Micronegocios por departamento',
    expected: 5262313, actual: await scalar('SELECT SUM(micro_businesses) FROM fact_micro_department'), tolerance: 25 }));

  const ps = await personaSums();
  const totalEmployed = await scalar('SELECT SUM(employed) FROM fact_persona_profile');
  const worstDim = ps.reduce((a, b) => (Math.abs(b.maxDiff) > Math.abs(a.maxDiff) ? b : a), ps[0]);
  const psCheck = {
    id: 'persona_sums', group: V1, table: 'fact_persona_*', label: 'Σ por persona vs. total',
    expected: 0, actual: worstDim.maxDiff, difference: worstDim.maxDiff, tolerance: PERSONA_TOL,
    tolLabel: '±30 por persona', ok: ps.every((d) => Math.abs(d.maxDiff) <= PERSONA_TOL),
    detail: `máx. diferencia por persona ${worstDim.maxDiff} (${worstDim.worst}, ${worstDim.table})`,
    sub: ps.map((d) => ({ label: `${d.table} — ${d.label}`, expected: totalEmployed, actual: d.sum,
      difference: d.sum - totalEmployed, maxPerPersona: d.maxDiff, worst: d.worst, ok: Math.abs(d.maxDiff) <= PERSONA_TOL })),
  };
  checks.push(psCheck);

  const uj = await unjoinedCodes();
  const unjoinedTotal = uj.reduce((s, r) => s + r.unjoinedRows, 0);
  const ujCheck = check({ id: 'unjoined', group: V1, table: '* (todas las fact_)', label: 'Códigos sin unir',
    expected: 0, actual: unjoinedTotal,
    detail: `${uj.length} columnas de código revisadas; excepciones aprobadas excluidas`,
    sub: uj.filter((r) => r.unjoinedRows > 0).map((r) => ({ label: `${r.table}.${r.column}`, expected: 0,
      actual: r.unjoinedRows, difference: r.unjoinedRows, ok: false,
      codes: r.unjoined.map((c) => c.code === null ? 'NULL' : c.code) })) });
  checks.push(ujCheck);

  // ---------- v2 geographic integrity ----------
  const dp = await departmentPolygons();
  checks.push(check({ id: 'department_polygons', group: V2, table: 'geo_department_shape', label: 'Polígonos de departamento válidos',
    expected: 33, actual: dp.valid, detail: dp.invalid.length ? `inválidos: ${dp.invalid.join(', ')}` : `${dp.total} filas, ST_GeomFromGeoJSON long-lat SRID 4326` }));
  checks.push(check({ id: 'upz', group: V2, table: 'fact_em2021_upz', label: 'UPZ de Bogotá',
    expected: 96, actual: await scalar('SELECT COUNT(*) FROM fact_em2021_upz') }));
  checks.push(check({ id: 'em_localidad_join', group: V2, table: 'fact_em2021_localidad', label: 'Localidades que unen con polígono en geo_zone',
    expected: 20, actual: await scalar(
      `SELECT COUNT(*) FROM fact_em2021_localidad f JOIN geo_zone z ON z.zone_id = f.zone_id
        WHERE z.municipality_code = ? AND z.geometry IS NOT NULL`, [BOGOTA]) }));
  const vacTotal = await scalar('SELECT COUNT(*) FROM fact_vacancies_department');
  checks.push(check({ id: 'vacancies_department', group: V2, table: 'fact_vacancies_department', label: 'Filas con department_code válido',
    expected: vacTotal, actual: await scalar(
      'SELECT COUNT(*) FROM fact_vacancies_department f JOIN geo_department d ON d.department_code = f.department_code'),
    tolLabel: 'todas' }));
  const secTotal = await scalar('SELECT COUNT(*) FROM fact_secop_department');
  checks.push(check({ id: 'secop_department', group: V2, table: 'fact_secop_department', label: 'Filas con department_code válido',
    expected: secTotal, actual: await scalar(
      'SELECT COUNT(*) FROM fact_secop_department f JOIN geo_department d ON d.department_code = f.department_code'),
    tolLabel: 'todas' }));
  checks.push(check({ id: 'upz_localidad_join', group: V2, table: 'fact_em2021_upz', label: "UPZ que unen con su localidad (localidad_code = zone_code, 11001, 'BOG-'+zone_code)",
    expected: 96, actual: await scalar(
      `SELECT COUNT(*) FROM fact_em2021_upz f JOIN geo_zone z
          ON z.municipality_code = ? AND z.zone_code = f.localidad_code AND z.zone_id = CONCAT('BOG-', f.localidad_code)
        WHERE f.localidad_code REGEXP '^(0[1-9]|1[0-9]|20)$'`, [BOGOTA]) }));

  // ---------- Medellín / Cali (paquete think4ever personas) ----------
  const calZones = await scalar("SELECT COUNT(*) FROM fact_companies_zone WHERE zone_id LIKE 'CAL-%'");
  const cali = check({ id: 'companies_cali', group: V2, table: 'fact_companies_zone', label: 'Empresas Cali',
    expected: 94415, actual: await scalar("SELECT SUM(companies_total) FROM fact_companies_zone WHERE zone_id LIKE 'CAL-%'"),
    detail: 'Cali 2025, tamaño por ingresos (no comparable con Bogotá)',
    sub: [{ label: 'Zonas CAL-01..CAL-22', expected: 22, actual: calZones, difference: calZones - 22, ok: calZones === 22 }] });
  cali.ok = cali.ok && calZones === 22;
  checks.push(cali);

  const ctxRows = await scalar('SELECT COUNT(*) FROM fact_zone_context');
  const CTX_ROWS = 68; // 21 Medellín + 22 Cali + 20 Bucaramanga + 5 Barranquilla
  const ctx = check({ id: 'zone_context_join', group: V2, table: 'fact_zone_context', label: 'Contexto por zona que une con geo_zone',
    expected: CTX_ROWS, actual: await scalar(
      `SELECT COUNT(*) FROM fact_zone_context f JOIN geo_zone z
          ON z.zone_id = f.zone_id AND z.municipality_code = f.municipality_code`),
    sub: [{ label: 'Filas en fact_zone_context', expected: CTX_ROWS, actual: ctxRows, difference: ctxRows - CTX_ROWS, ok: ctxRows === CTX_ROWS }] });
  ctx.ok = ctx.ok && ctxRows === CTX_ROWS;
  checks.push(ctx);

  const profRows = await scalar('SELECT COUNT(*) FROM fact_persona_profile_metro_2025');
  const profPersona = await scalar(
    'SELECT COUNT(*) FROM fact_persona_profile_metro_2025 f JOIN fact_persona_profile p ON p.persona = f.persona');
  const PROF_ROWS = 52; // 13 personas × (Medellín, Cali 2025 + Bucaramanga, Barranquilla 2025-26)
  const prof = check({ id: 'persona_profile_metro', group: V2, table: 'fact_persona_profile_metro_2025', label: 'Perfiles GEIH que unen con geo_municipality',
    expected: PROF_ROWS, actual: await scalar(
      'SELECT COUNT(*) FROM fact_persona_profile_metro_2025 f JOIN geo_municipality m ON m.municipality_code = f.municipality_code'),
    sub: [
      { label: 'Filas en la tabla', expected: PROF_ROWS, actual: profRows, difference: profRows - PROF_ROWS, ok: profRows === PROF_ROWS },
      { label: 'Persona existe en fact_persona_profile', expected: PROF_ROWS, actual: profPersona, difference: profPersona - PROF_ROWS, ok: profPersona === PROF_ROWS },
    ] });
  prof.ok = prof.ok && prof.sub.every((s) => s.ok);
  checks.push(prof);

  checks.push(check({ id: 'no_persona_by_comuna', group: V2, table: 'fact_zone_context', label: 'Conteos de personas por comuna (Medellín / Cali)',
    expected: 0, actual: await scalar('SELECT COUNT(*) FROM fact_zone_context WHERE personas13 IS NOT NULL OR core_it IS NOT NULL'),
    detail: 'personas13 y core_it deben quedar vacíos: no se reparte GEIH por comuna' }));

  // ---------- Cali (paquete think4ever_cali_solo, README «Controles de aceptación del lote») ----------
  const calCount = (sql) => scalar(sql, [CALI]);
  const caliChecks = [
    { id: 'cali_persona_metro', table: 'fact_persona_metro', label: 'Cali: personas en fact_persona_metro (76001)', expected: 13,
      sql: 'SELECT COUNT(*) FROM fact_persona_metro WHERE municipality_code = ?' },
    { id: 'cali_profiles_join', table: 'fact_persona_profile_metro_2025', label: 'Cali: perfiles GEIH 2025 (76001) unidos a geo_municipality', expected: 13,
      sql: 'SELECT COUNT(*) FROM fact_persona_profile_metro_2025 f JOIN geo_municipality m ON m.municipality_code = f.municipality_code WHERE f.municipality_code = ?' },
    { id: 'cali_geih_summary', table: 'fact_geih2025_metro_summary', label: 'Cali: resumen GEIH 2025 (76001)', expected: 1,
      sql: 'SELECT COUNT(*) FROM fact_geih2025_metro_summary WHERE municipality_code = ?' },
    { id: 'cali_segment_metro_2025', table: 'fact_persona_segment_metro_2025', label: 'Cali: segmentos metro 2025 unidos a geo_municipality', expected: 60,
      sql: 'SELECT COUNT(*) FROM fact_persona_segment_metro_2025 f JOIN geo_municipality m ON m.municipality_code = f.municipality_code WHERE f.municipality_code = ?' },
    { id: 'cali_zone_indicator', table: 'fact_zone_indicator', label: 'Cali: indicadores por comuna unidos a geo_zone', expected: 22,
      sql: "SELECT COUNT(*) FROM fact_zone_indicator f JOIN geo_zone z ON z.zone_id = f.zone_id WHERE z.municipality_code = ? AND f.zone_id LIKE 'CAL-%'" },
    { id: 'cali_meta_companies_zone', table: 'meta_companies_zone', label: 'Cali: procedencia de empresas por comuna unida a geo_zone', expected: 22,
      sql: "SELECT COUNT(*) FROM meta_companies_zone f JOIN geo_zone z ON z.zone_id = f.zone_id WHERE z.municipality_code = ? AND f.zone_id LIKE 'CAL-%'" },
    { id: 'cali_meta_geo_zone', table: 'meta_geo_zone', label: 'Cali: licencia de geometría (meta_geo_zone 76001)', expected: 1,
      sql: 'SELECT COUNT(*) FROM meta_geo_zone f JOIN geo_municipality m ON m.municipality_code = f.municipality_code WHERE f.municipality_code = ?' },
    { id: 'cali_zone_context_join', table: 'fact_zone_context', label: 'Cali: contextos CAL unidos a geo_zone', expected: 22,
      sql: "SELECT COUNT(*) FROM fact_zone_context f JOIN geo_zone z ON z.zone_id = f.zone_id AND z.municipality_code = f.municipality_code WHERE f.municipality_code = ? AND f.zone_id LIKE 'CAL-%'" },
  ];
  for (const c of caliChecks) {
    checks.push(check({ id: c.id, group: V2, table: c.table, label: c.label, expected: c.expected, actual: await calCount(c.sql) }));
  }

  // ---------- Barranquilla / Bucaramanga (db_mods.rar; GEIH ago 2025 – jul 2026, survey_year 2026) ----------
  const newMetros = [
    { code: BARRANQUILLA, name: 'Barranquilla', prefix: 'BAQ', zones: 5 },
    { code: BUCARAMANGA, name: 'Bucaramanga', prefix: 'BUC', zones: 20 },
  ];
  for (const m of newMetros) {
    const p = m.prefix.toLowerCase();
    const items = [
      { id: `${p}_companies_zone_join`, table: 'fact_companies_zone', expected: m.zones,
        label: `${m.name}: zonas de fact_companies_zone unidas a geo_zone (${m.code}, conteos vacíos)`,
        sql: 'SELECT COUNT(*) FROM fact_companies_zone f JOIN geo_zone z ON z.zone_id = f.zone_id WHERE z.municipality_code = ? AND f.zone_id LIKE ?',
        params: [m.code, `${m.prefix}-%`] },
      { id: `${p}_zone_context_join`, table: 'fact_zone_context', expected: m.zones,
        label: `${m.name}: contextos por zona unidos a geo_zone (${m.code})`,
        sql: 'SELECT COUNT(*) FROM fact_zone_context f JOIN geo_zone z ON z.zone_id = f.zone_id AND z.municipality_code = f.municipality_code WHERE f.municipality_code = ?',
        params: [m.code] },
      { id: `${p}_profiles_join`, table: 'fact_persona_profile_metro_2025', expected: 13,
        label: `${m.name}: perfiles GEIH 2025-26 (${m.code}, survey_year 2026) unidos a geo_municipality`,
        sql: 'SELECT COUNT(*) FROM fact_persona_profile_metro_2025 f JOIN geo_municipality g ON g.municipality_code = f.municipality_code WHERE f.municipality_code = ? AND f.survey_year = ?',
        params: [m.code, '2026'] },
      { id: `${p}_geih_summary`, table: 'fact_geih2025_metro_summary', expected: 1,
        label: `${m.name}: resumen GEIH 2025-26 (${m.code}, survey_year 2026)`,
        sql: 'SELECT COUNT(*) FROM fact_geih2025_metro_summary f JOIN geo_municipality g ON g.municipality_code = f.municipality_code WHERE f.municipality_code = ? AND f.survey_year = ?',
        params: [m.code, '2026'] },
    ];
    for (const c of items) {
      checks.push(check({ id: c.id, group: V2, table: c.table, label: c.label, expected: c.expected, actual: await scalar(c.sql, c.params) }));
    }
  }

  const axis = await axisTest();
  const exc = await exceptions();
  const noSource = await missingSources();
  const passed = checks.filter((c) => c.ok).length;
  const accepted = passed === checks.length && axis.ok && noSource.length === 0;
  return { checks, passed, total: checks.length, axis, exceptions: exc, unjoined: uj, departmentPolygons: dp,
    missingSources: noSource, accepted };
}

module.exports = { computeAcceptance, latestBatchId, JOIN_RULES, AXIS_EXPECTED };