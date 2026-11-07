'use strict';
// Mexico acceptance checks on data/mexico/geodb/csv (no database): the file-adapter
// counterpart of lib/acceptance.js. Codes stay strings; every fact table must join to
// geo_department / geo_municipality; every table needs a meta_sources row.
// Usage: node scripts/check-mexico.js   (exit 1 when any check fails)
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

const CSV_DIR = path.join(__dirname, '..', 'data', 'mexico', 'geodb', 'csv');
const MX_BBOX = { south: 14, north: 33, west: -119, east: -86 };
// rule_axis_order: Ciudad de México (Cuauhtémoc) must read lat ≈ 19.44, lon ≈ -99.15.
const AXIS = { code: '09015', lat: 19.44, lon: -99.15, tol: 0.05 };

const read = (table) => {
  const file = path.join(CSV_DIR, `${table}.csv`);
  if (!fs.existsSync(file)) return null;
  const text = fs.readFileSync(file, 'utf8');
  return { bom: text.charCodeAt(0) === 0xfeff, rows: parse(text, { columns: true, skip_empty_lines: true, bom: true }) };
};

const checks = [];
const check = (id, label, expected, actual, ok = expected === actual) => checks.push({ id, label, expected, actual, ok });

const tables = fs.readdirSync(CSV_DIR).filter((f) => f.endsWith('.csv')).map((f) => f.slice(0, -4));
const data = Object.fromEntries(tables.map((t) => [t, read(t)]));
const dept = data.geo_department ? data.geo_department.rows : [];
const muni = data.geo_municipality ? data.geo_municipality.rows : [];
const deptCodes = new Set(dept.map((r) => r.department_code));
const muniCodes = new Set(muni.map((r) => r.municipality_code));

check('states', 'Estados (geo_department)', 32, dept.length);
check('states_unique', 'Códigos de estado únicos de 2 dígitos', dept.length, dept.filter((r) => /^\d{2}$/.test(r.department_code)).length
  , deptCodes.size === dept.length && dept.every((r) => /^\d{2}$/.test(r.department_code)));
check('municipalities_unique', 'Códigos de municipio únicos de 5 dígitos (estado + municipio)', muni.length,
  muni.filter((r) => /^\d{5}$/.test(r.municipality_code) && r.municipality_code.startsWith(r.department_code)).length,
  muniCodes.size === muni.length && muni.every((r) => /^\d{5}$/.test(r.municipality_code) && r.municipality_code.startsWith(r.department_code)));

const inBox = (r) => Number(r.lat) > MX_BBOX.south && Number(r.lat) < MX_BBOX.north && Number(r.lon) > MX_BBOX.west && Number(r.lon) < MX_BBOX.east;
check('municipality_points', 'Municipios con punto dentro de México', muni.length, muni.filter(inBox).length);
const wktOk = muni.filter((r) => {
  const m = /^POINT\((-?[\d.]+) (-?[\d.]+)\)$/.exec(r.wkt || '');
  return m && Math.abs(Number(m[1]) - Number(r.lon)) < 1e-5 && Math.abs(Number(m[2]) - Number(r.lat)) < 1e-5;
}).length;
check('municipality_wkt', 'WKT en orden lon lat, igual a lat/lon', muni.length, wktOk);
const axis = muni.find((r) => r.municipality_code === AXIS.code);
check('axis_order', `Punto de ${AXIS.code} en lat ${AXIS.lat} / lon ${AXIS.lon}`, true,
  !!axis && Math.abs(Number(axis.lat) - AXIS.lat) < AXIS.tol && Math.abs(Number(axis.lon) - AXIS.lon) < AXIS.tol);

// Boundaries: one valid WGS84 MultiPolygon per code (lib/acceptance.js "Polígonos de departamento válidos").
const validRing = (ring) => Array.isArray(ring) && ring.length >= 4
  && ring[0][0] === ring[ring.length - 1][0] && ring[0][1] === ring[ring.length - 1][1]
  && ring.every(([x, y]) => x > MX_BBOX.west && x < MX_BBOX.east && y > MX_BBOX.south && y < MX_BBOX.north);
const validShape = (text) => {
  try {
    const g = JSON.parse(text);
    return g.type === 'MultiPolygon' && g.coordinates.length > 0 && g.coordinates.every((poly) => poly.length > 0 && poly.every(validRing));
  } catch (_) { return false; }
};
for (const [table, codeCol, codes] of [['geo_department_shape', 'department_code', deptCodes], ['geo_municipality_shape', 'municipality_code', muniCodes]]) {
  if (!data[table]) continue;
  const rows = data[table].rows;
  const shapeCodes = new Set(rows.map((r) => r[codeCol]));
  check(`${table}_coverage`, `${table}: un polígono por código del catálogo`, codes.size, rows.length,
    rows.length === codes.size && shapeCodes.size === rows.length && [...codes].every((c) => shapeCodes.has(c)));
  check(`${table}_valid`, `${table}: polígonos WGS84 válidos y cerrados`, rows.length, rows.filter((r) => validShape(r.geojson)).length);
}

// Published totals (layer R1), as in lib/acceptance.js rule_acceptance_totals.
const PUBLISHED = { denue_establishments: 6138075 }; // DENUE 05/2026 bulletin, exact
if (data.fact_companies_municipality) {
  const rows = data.fact_companies_municipality.rows;
  const sum = (k) => rows.reduce((s, r) => s + Number(r[k]), 0);
  check('denue_total', 'DENUE 05/2026: establecimientos = total publicado (exacto)', PUBLISHED.denue_establishments, sum('establishments'));
  check('denue_rows', 'fact_companies_municipality: una fila por municipio', muni.length, rows.length);
  check('denue_parts', 'Empresas, tiendas y TI ≤ establecimientos; TI = suma de sus códigos', rows.length, rows.filter((r) => {
    const n = (k) => Number(r[k]);
    return n('businesses') <= n('establishments') && n('shops_4711') <= n('establishments')
      && n('it_companies_active') === n('it_541510') + n('it_518210') + n('it_519290');
  }).length);
}

// Layer J zones: valid polygons, facts join geo_zone, zones equal their municipality's private businesses.
if (data.geo_zone && data.fact_companies_zone) {
  const zones = data.geo_zone.rows;
  const facts = data.fact_companies_zone.rows;
  const zoneIds = new Set(zones.map((z) => z.zone_id));
  const businesses = new Map((data.fact_companies_municipality ? data.fact_companies_municipality.rows : []).map((r) => [r.municipality_code, Number(r.businesses)]));
  check('zones', 'Zonas J: 16 alcaldías CMX + 16 municipios MTY', 32, zones.length,
    zones.length === 32 && zones.filter((z) => z.zone_id.startsWith('CMX-')).length === 16 && zoneIds.size === 32);
  check('zones_valid', 'geo_zone: polígonos WGS84 válidos y cerrados', zones.length, zones.filter((z) => validShape(z.geojson)).length);
  check('zones_join', 'fact_companies_zone.zone_id une con geo_zone', 0, facts.filter((f) => !zoneIds.has(f.zone_id)).length);
  const zoneMuni = new Map(zones.map((z) => [z.zone_id, z.municipality_code]));
  check('zones_equal_municipality', 'Empresas por zona = empresas privadas de su municipio', facts.length,
    facts.filter((f) => Number(f.companies_total) === businesses.get(zoneMuni.get(f.zone_id))).length);
  const parts = ['micro', 'medium_large', 'software_it', 'design', 'accounting_audit', 'management_consulting',
    'research_market_studies', 'higher_education_training', 'shops_4711', 'private_schools'];
  check('zones_parts', 'Cada indicador de zona ≤ total de la zona; micro + mediana/grande ≤ total', facts.length,
    facts.filter((f) => parts.every((k) => Number(f[k]) <= Number(f.companies_total))
      && Number(f.micro) + Number(f.medium_large) <= Number(f.companies_total)).length);
}

// Every code column in every table must join to its geography (lib/acceptance.js "Códigos sin unir").
for (const t of tables) {
  if (t === 'geo_department' || t === 'meta_sources') continue;
  const rows = data[t].rows;
  for (const [col, codes] of [['department_code', deptCodes], ['municipality_code', muniCodes]]) {
    if (!rows.length || !(col in rows[0])) continue;
    const bad = rows.filter((r) => r[col] !== '' && !codes.has(r[col])).map((r) => r[col]);
    check(`unjoined_${t}_${col}`, `${t}.${col} une con su tabla geográfica`, 0, bad.length);
  }
}

const meta = data.meta_sources ? data.meta_sources.rows : [];
const missingSource = tables.filter((t) => t !== 'meta_sources' && !meta.some((m) => m.table_name === t && m.source && m.year));
check('meta_sources', 'Tablas con fuente y año en meta_sources', 0, missingSource.length);
const withBom = tables.filter((t) => data[t].bom);
check('utf8_no_bom', 'CSV UTF-8 sin BOM', 0, withBom.length);

for (const c of checks) console.log(`${c.ok ? 'ok  ' : 'FAIL'} ${c.label}: esperado ${c.expected}, real ${c.actual}`);
if (missingSource.length) console.log('     sin fuente:', missingSource.join(', '));
const failed = checks.filter((c) => !c.ok).length;
console.log(`${checks.length - failed}/${checks.length} comprobaciones`);
process.exit(failed ? 1 : 0);
