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
  const perCity = { CMX: 16, MTY: 16, GDL: 7, EDM: 45 };
  check('zones', 'Zonas J: 16 alcaldías CMX + 16 MTY + 7 GDL + 45 EDM (Metrópolis 2020)', 84, zones.length,
    zones.length === 84 && zoneIds.size === 84 && Object.entries(perCity).every(([p, n]) => zones.filter((z) => z.zone_id.startsWith(p + '-')).length === n));
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

// National indicators (layers A and B): Peru's fact_map_indicator format, MX scope, nulls kept empty.
if (data.fact_map_indicator) {
  const rows = data.fact_map_indicator.rows;
  const a = rows.filter((r) => r.layer === 'A');
  const b = rows.filter((r) => r.layer === 'B');
  check('national_scope', 'fact_map_indicator: ámbito nacional MX en todas las filas', rows.length,
    rows.filter((r) => r.scope_type === 'country' && r.scope_id === 'MX').length);
  check('layer_a_rows', 'Capa A: 25 indicadores, todos con valor', 25, a.filter((r) => r.value !== '').length, a.length === 25 && a.every((r) => r.value !== ''));
  if (data.fact_developers_country) {
    const dev = data.fact_developers_country.rows.find((r) => r.iso2 === 'MX');
    const a1 = a.find((r) => r.metric_id === 'A1_developer_accounts');
    check('layer_a_benchmark', 'A1 = developers de fact_developers_country (MX)', dev && Number(dev.developers), a1 && Number(a1.value));
  }
  const proportionsOk = b.filter((r) => r.value === '' || (Number(r.value) >= 0 && Number(r.value) <= 1)).length;
  check('layer_b_proportions', 'Capa B: proporciones entre 0 y 1 o vacías (suprimidas)', b.length, proportionsOk, b.length > 0 && proportionsOk === b.length);
  const suppressedNotEmpty = b.filter((r) => /suppress=suppressed/.test(r.limitations) && r.value !== '').length;
  check('layer_b_suppressed', 'Capa B: celdas suprimidas sin valor (nunca cero)', 0, suppressedNotEmpty);
  check('layer_b_mexico', 'Capa B: 158 filas del grupo México (todos los encuestados)', 158, b.filter((r) => r.metric_id.includes(':country:MX:all_respondents:')).length);
  const oRows = rows.filter((r) => r.layer === 'O');
  if (oRows.length) {
    check('layer_o_verified', 'Capa O: datos verificados con valor o texto y fuente', oRows.filter((r) => r.status === 'verified').length,
      oRows.filter((r) => r.status === 'verified' && r.source_id && (r.value !== '' || r.limitations)).length);
    check('layer_o_not_checked_empty', 'Capa O: datos no verificados quedan vacíos (nunca cero)', 0,
      oRows.filter((r) => r.status === 'not_checked' && r.value !== '').length);
    check('layer_o_international', 'Capa O: O1 (FMI), O2 (Banxico) y O6 (DataReportal, StatCounter) verificados con valor', 9,
      oRows.filter((r) => /^O1_gdp|^O2_(spei|codi)|^O6_(fixed|mobile|internet_users_data|desktop)/.test(r.metric_id) && r.status === 'verified' && r.value !== '').length);
  }
  const pRows = rows.filter((r) => r.layer === 'P');
  if (pRows.length && data.fact_schools_municipality && data.fact_companies_municipality) {
    const pv = (id) => Number((pRows.find((r) => r.metric_id === id) || {}).value);
    const schools = data.fact_schools_municipality.rows.reduce((s, r) => s + Number(r.schools), 0);
    const biz = data.fact_companies_municipality.rows.reduce((s, r) => s + Number(r.businesses), 0);
    check('layer_p_schools', 'Capa P: escuelas = K1 (suma municipal)', schools, pv('P1_schools'));
    check('layer_p_per_school', 'Capa P: empresas por escuela = N1 ÷ K1', Math.round((biz / schools) * 10) / 10, pv('P3_businesses_per_school'));
    check('layer_p_assumption', 'Capa P: la conversión del 10 % está marcada como supuesto', 'assumption',
      (pRows.find((r) => r.metric_id === 'P1_paid_users_at_10pct') || {}).status);
  }
  const iRows = rows.filter((r) => r.layer === 'I');
  if (iRows.length) {
    const val = (id) => Number((iRows.find((r) => r.metric_id === id) || {}).value);
    check('layer_i_plans', 'Capa I: plan individual = USD 25 × FIX promedio 2025', Math.round(25 * val('I1_fix_2025_average') * 100) / 100, val('I1_plan_individual_mxn'));
    check('layer_i_min_wage', 'Capa I: salario mínimo mensual = 278,80 × 30,4', 8475.52, val('I3_min_wage_monthly_general'));
  }
}

// Layer F, G, H, M (ENOE 2025): 13 personas, parts add up, published employed totals (layer R1).
if (data.fact_persona_profile) {
  const profile = data.fact_persona_profile.rows;
  check('personas', 'Personas (13 personas, mismos nombres que Colombia)', 13, profile.length);
  const total = new Map(profile.map((p) => [p.persona, Number(p.employed)]));
  for (const t of ['fact_persona_department', 'fact_persona_metro', 'fact_persona_segment']) {
    if (!data[t]) continue;
    const sums = new Map();
    const cells = new Map();
    for (const r of data[t].rows) {
      sums.set(r.persona, (sums.get(r.persona) || 0) + Number(r.employed));
      cells.set(r.persona, (cells.get(r.persona) || 0) + 1);
    }
    // Each cell is rounded on its own, so the sum may differ from the total by at most one per cell.
    const ok = [...total].filter(([p, v]) => sums.has(p) && Math.abs(sums.get(p) - v) <= cells.get(p)).length;
    check(`${t}_adds_up`, `${t}: las celdas de cada persona suman su total`, profile.length, ok);
  }
  const fJson = path.join(__dirname, '..', 'data', 'mexico', 'outputs', 'layer_f_mx.json');
  if (fs.existsSync(fJson)) {
    const q = JSON.parse(fs.readFileSync(fJson, 'utf8')).checks.employed_vs_bulletins;
    const within = Object.values(q).filter((x) => Math.abs(x.difference_pct) <= 0.5).length;
    check('enoe_employed', 'ENOE 2025: ocupados por trimestre dentro de 0,5 % del boletín', 4, within);
    const mJson = path.join(__dirname, '..', 'data', 'mexico', 'outputs', 'layer_m_mx.json');
    if (fs.existsSync(mJson)) {
      const pos = Object.values(JSON.parse(fs.readFileSync(mJson, 'utf8')).check_position_totals_vs_bulletins || {}).flatMap((c) => Object.values(c));
      check('enoe_position', 'ENOE 2025: empleadores y cuenta propia por trimestre dentro de 1 % del boletín', 8, pos.filter((x) => x.within_1pct).length);
      const m4 = JSON.parse(fs.readFileSync(mJson, 'utf8')).M4_digital;
      if (m4) {
        const ind = Object.values(m4.indicators);
        check('m4_census', 'M4 (Censos 2024, ref. 2023): conteos ≤ unidades de 0 a 10 personas, periodo 2023', ind.length,
          ind.filter((x) => x.units >= 0 && x.units <= m4.micro_units_total).length, m4.period === '2023' && ind.every((x) => x.units <= m4.micro_units_total));
      }
    }
  }
  if (data.fact_ict_by_sector) {
    const core = ['Software developers and analysts', 'Database, systems and network professionals', 'ICT technicians and user support', 'ICT managers']
      .reduce((s, p) => s + (total.get(p) || 0), 0);
    const g1 = data.fact_ict_by_sector.rows.reduce((s, r) => s + Number(r.employed), 0);
    check('g1_core', 'G1: personal TI por sector = suma de las 4 personas núcleo', core, g1, Math.abs(core - g1) <= data.fact_ict_by_sector.rows.length);
  }
  const emptyFromHome = profile.every((p) => p.pct_works_from_home === '');
  check('f10_empty', 'F10 trabajo desde casa: vacío (no disponible), nunca cero', true, emptyFromHome);
}

// Layer K (SEP 911): published enrolment totals and internal consistency.
if (data.fact_schools_municipality) {
  const rows = data.fact_schools_municipality.rows;
  const kJson = path.join(__dirname, '..', 'data', 'mexico', 'outputs', 'layer_k_mx.json');
  if (fs.existsSync(kJson)) {
    const k = JSON.parse(fs.readFileSync(kJson, 'utf8'));
    const pub = Object.values(k.checks.enrolment_vs_principales_cifras);
    check('k_published', 'SEP 911: secundaria y media superior dentro de 1 % de Principales Cifras', pub.length, pub.filter((x) => x.within_1pct).length);
    check('k_target_total', 'K2: alumnos en grados objetivo = suma municipal', k.indicators.K2_students_target, rows.reduce((s, r) => s + Number(r.students_target), 0));
  }
  check('k_parts', 'Por municipio: grados suman el total; públicos, rurales y alcance ≤ total; escuelas públicas ≤ escuelas', rows.length, rows.filter((r) => {
    const v = (key) => Number(r[key]);
    return v('students_sec3') + v('students_ms1') + v('students_ms2') + v('students_ms3') === v('students_target')
      && v('students_public') <= v('students_target') && v('students_rural') <= v('students_target')
      && v('reach_cap100') <= v('students_target') && v('reach_cap100') <= 100 * v('schools') && v('schools_public') <= v('schools');
  }).length);
}

// Layers C and L (SEP 911 superior): published total, on campus within total, ICT field kept empty.
if (data.fact_higher_ed_municipality) {
  const rows = data.fact_higher_ed_municipality.rows;
  const lJson = path.join(__dirname, '..', 'data', 'mexico', 'outputs', 'layer_l_mx.json');
  if (fs.existsSync(lJson)) {
    const l = JSON.parse(fs.readFileSync(lJson, 'utf8')).check_total_vs_principales_cifras;
    check('l_published', 'SEP 911 superior: total dentro de 1 % de Principales Cifras', l.published, l.file_total, Math.abs(l.difference_pct) <= 1);
    check('l_total_sum', 'Educación superior: suma municipal = total nacional', l.file_total, rows.reduce((s, r) => s + Number(r.students_total), 0));
    const l5 = JSON.parse(fs.readFileSync(lJson, 'utf8')).indicators;
    const sum = (o) => Object.values(o || {}).reduce((s, v) => s + Number(v), 0);
    check('l5_tecnm', 'L5: TecNM exacto = unidades federales + descentralizadas (ANUIES)', l5.L5_tecnm_students, sum(l5.L5_tecnm_by_unit));
    const cap = l5.L5_capacitacion_para_el_trabajo || {};
    check('l5_capacitacion', 'L5: capacitación para el trabajo, 32 estados suman el total', cap.students, sum(cap.by_state),
      cap.students > 0 && Object.keys(cap.by_state || {}).length === 32 && sum(cap.by_state) === cap.students);
  }
  check('l_on_campus', 'Presencial ≤ total en cada municipio', rows.length, rows.filter((r) => Number(r.students_on_campus) <= Number(r.students_total)).length);
  check('c1_ict_le_total', 'Alumnos TIC ≤ total en cada municipio', rows.length,
    rows.filter((r) => r.students_ict_field !== '' && Number(r.students_ict_field) <= Number(r.students_total)).length);
  const cJson = path.join(__dirname, '..', 'data', 'mexico', 'outputs', 'layer_c_mx.json');
  if (fs.existsSync(cJson)) {
    const c1 = JSON.parse(fs.readFileSync(cJson, 'utf8')).indicators.C1_ict_students;
    check('c1_sum', 'C1: alumnos TIC = suma municipal', c1, rows.reduce((s, r) => s + Number(r.students_ict_field || 0), 0));
  }
}

// Layer E (CONAPO): positive population, one row per municipality, never zero-filled.
if (data.fact_population_municipality) {
  const rows = data.fact_population_municipality.rows;
  check('e_rows', 'Población 2024: filas únicas con valor positivo', rows.length,
    new Set(rows.filter((r) => Number(r.population) > 0 && r.year === '2024').map((r) => r.municipality_code)).size);
  check('e_coverage', 'Población 2024: municipios del catálogo con proyección (faltan solo los 3 más nuevos)', muni.length - 3, rows.length);
}

// Layer D3 (Censos Económicos 2024, reference year 2023): SCIAN 5415 strata add up to the total (D-MX-15).
const dJson = path.join(__dirname, '..', 'data', 'mexico', 'outputs', 'layer_d_mx.json');
if (fs.existsSync(dJson)) {
  const d3 = JSON.parse(fs.readFileSync(dJson, 'utf8')).indicators.D3_industry_census;
  if (d3) {
    const strata = Object.values(d3.by_stratum);
    check('d3_strata', 'D3: estratos de SCIAN 5415 suman unidades y personal, periodo 2023', d3.units,
      strata.reduce((s, x) => s + x.units, 0), d3.period === '2023' && strata.reduce((s, x) => s + x.people_employed, 0) === d3.people_employed);
  }
}

// Layer R: summary of every published-total check and of the sources register (scripts/build-mexico-r-checks.py).
const rJson = path.join(__dirname, '..', 'data', 'mexico', 'validation', 'r_checks_mx.json');
if (fs.existsSync(rJson)) {
  const r = JSON.parse(fs.readFileSync(rJson, 'utf8'));
  check('r1', 'R1: totales contra cifras publicadas (todos dentro de tolerancia)', r.R1_published_totals.total, r.R1_published_totals.passed);
  check('r2', 'R2: registro de fuentes completo (URL, periodo, archivo, hash, licencia, script)', r.R2_sources_register.sources, r.R2_sources_register.complete);
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
