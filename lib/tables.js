'use strict';
// Read-only table catalog + paginated row preview for the Explorador de tablas.
// Table and column names come ONLY from information_schema (strict whitelist);
// user input is never interpolated — searches use bound LIKE parameters.
const pool = require('../db/pool');

const PAGE_SIZE = 25;
const NAME_RE = /^[A-Za-z0-9_]{1,64}$/;
const GEOM_TYPES = new Set(['geometry', 'point', 'linestring', 'polygon', 'multipoint',
  'multilinestring', 'multipolygon', 'geometrycollection', 'geomcollection']);
const TEXT_TYPES = new Set(['char', 'varchar', 'tinytext', 'text', 'enum', 'set']);
const LONG_TYPES = new Set(['mediumtext', 'longtext', 'json', 'blob', 'mediumblob', 'longblob']);
const NUM_TYPES = new Set(['tinyint', 'smallint', 'mediumint', 'int', 'bigint', 'decimal', 'float', 'double', 'bit']);
const SYSTEM_TABLES = new Set(['load_batch', 'validation_issue', 'meta_sources']);
const GEOM_MAX = 90;
const LONG_MAX = 120;

function httpError(status, message) {
  const e = new Error(message);
  e.status = status;
  return e;
}

const q = (id) => '`' + id + '`'; // only ever called with whitelisted identifiers

let cache = null;
let cacheAt = 0;

async function catalog() {
  if (cache && Date.now() - cacheAt < 60000) return cache;
  const [cols] = await pool.query(
    `SELECT c.TABLE_NAME AS t, c.COLUMN_NAME AS c, c.DATA_TYPE AS dt, c.COLUMN_KEY AS ck
       FROM information_schema.COLUMNS c
       JOIN information_schema.TABLES tb
         ON tb.TABLE_SCHEMA = c.TABLE_SCHEMA AND tb.TABLE_NAME = c.TABLE_NAME
      WHERE c.TABLE_SCHEMA = DATABASE() AND tb.TABLE_TYPE = 'BASE TABLE'
      ORDER BY c.TABLE_NAME, c.ORDINAL_POSITION`);
  const map = new Map();
  for (const r of cols) {
    if (!NAME_RE.test(r.t) || !NAME_RE.test(r.c)) continue;
    if (!map.has(r.t)) map.set(r.t, { name: r.t, columns: [], pk: [] });
    const dt = String(r.dt).toLowerCase();
    const kind = GEOM_TYPES.has(dt) ? 'geom' : LONG_TYPES.has(dt) ? 'long'
      : TEXT_TYPES.has(dt) ? 'text' : NUM_TYPES.has(dt) ? 'num' : 'other';
    const t = map.get(r.t);
    t.columns.push({ name: r.c, type: dt, kind });
    if (r.ck === 'PRI') t.pk.push(r.c);
  }
  for (const t of map.values()) Object.assign(t, geoInfo(t));
  cache = map;
  cacheAt = Date.now();
  return map;
}

function geoInfo(t) {
  const names = new Set(t.columns.map((c) => c.name));
  const geomCols = t.columns.filter((c) => c.kind === 'geom' || c.name === 'geojson').map((c) => c.name);
  let level = null;
  const keys = [];
  if (names.has('zone_id')) { level = 'Localidad / comuna'; keys.push('zone_id'); }
  else if (names.has('localidad_code')) { level = 'UPZ → localidad'; keys.push('localidad_code'); }
  else if (names.has('municipality_code')) { level = 'Municipio'; keys.push('municipality_code'); }
  else if (names.has('department_code')) { level = 'Departamento'; keys.push('department_code'); }
  if (level && names.has('municipality_code') && !keys.includes('municipality_code')) keys.push('municipality_code');
  if (names.has('department_code') && !keys.includes('department_code') && level) keys.push('department_code');
  return { has_geo: !!level, geo_level: level, geo_columns: keys, geometry_columns: geomCols };
}

async function listTables() {
  const cat = await catalog();
  const [meta] = await pool.query('SELECT table_name, description, source, year FROM meta_sources');
  const metaMap = new Map(meta.map((m) => [m.table_name, m]));
  const tables = [];
  for (const t of cat.values()) {
    const [[c]] = await pool.query(`SELECT COUNT(*) AS n FROM ${q(t.name)}`);
    const m = metaMap.get(t.name) || null;
    tables.push({
      table_name: t.name,
      rows: Number(c.n),
      source_name: m ? m.source : null,
      year: m ? m.year : null,
      description: m ? m.description : null,
      registered: !!m,
      kind: SYSTEM_TABLES.has(t.name) ? 'system' : 'data',
      has_geo: t.has_geo,
      geo_level: t.geo_level,
      geo_columns: t.geo_columns,
      geometry_columns: t.geometry_columns,
      columns: t.columns.length,
    });
  }
  const sources = new Set(tables.filter((t) => t.source_name).map((t) => t.source_name));
  return {
    tables,
    totals: {
      tables: tables.length,
      registered: tables.filter((t) => t.registered).length,
      with_source_year: tables.filter((t) => t.source_name && t.year).length,
      rows: tables.reduce((s, t) => s + t.rows, 0),
      sources: sources.size,
      with_geo: tables.filter((t) => t.has_geo).length,
      no_geo: tables.filter((t) => !t.has_geo).length,
    },
  };
}

async function noGeomZones() {
  const [r] = await pool.query('SELECT zone_id FROM geo_zone WHERE geometry IS NULL');
  return new Set(r.map((x) => x.zone_id));
}

// Approved 'sin geografía' exceptions (memory #74).
function exceptionReason(row, zonesNoGeom) {
  if (row.metro_area === 'Rest of the country' || row.city === 'Rest of the country') {
    return 'Rest of the country · sin municipality_code';
  }
  if (row.zone_id === 'BOG-00') return 'BOG-00 · Sin localidad (sin fila en geo_zone)';
  if (row.municipality_code === '27493') return '27493 · Nuevo Belén de Bajirá, cargado sin punto';
  if (row.zone_id && zonesNoGeom.has(row.zone_id)) return 'Zona sin polígono en geo_zone';
  return null;
}

async function tableRows(tableParam, pageParam, qParam) {
  const name = String(tableParam || '');
  if (!NAME_RE.test(name)) throw httpError(400, 'Nombre de tabla no válido');
  const cat = await catalog();
  const t = cat.get(name);
  if (!t) throw httpError(404, `Tabla no encontrada: ${name}`);

  let page = parseInt(pageParam, 10);
  if (!Number.isFinite(page) || page < 1) page = 1;
  const search = String(qParam || '').trim().slice(0, 100);

  const select = t.columns.map((c) => {
    if (c.kind === 'geom') {
      return `LEFT(ST_AsText(${q(c.name)}, 'axis-order=long-lat'), ${GEOM_MAX + 1}) AS ${q(c.name)}`;
    }
    if (c.kind === 'long') return `LEFT(${q(c.name)}, ${LONG_MAX + 1}) AS ${q(c.name)}`;
    return q(c.name);
  }).join(', ');

  const params = [];
  let where = '';
  const searchCols = t.columns.filter((c) => c.kind === 'text');
  if (search && searchCols.length) {
    const like = '%' + search.replace(/[\\%_]/g, '\\$&') + '%';
    where = 'WHERE ' + searchCols.map((c) => `${q(c.name)} LIKE ?`).join(' OR ');
    searchCols.forEach(() => params.push(like));
  }
  const order = (t.pk.length ? t.pk : [t.columns[0].name]).map(q).join(', ');

  const [[cnt]] = await pool.query(`SELECT COUNT(*) AS n FROM ${q(name)} ${where}`, params);
  const total = Number(cnt.n);
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (page > pages) page = pages;
  const offset = (page - 1) * PAGE_SIZE;

  const [rows] = await pool.query(
    `SELECT ${select} FROM ${q(name)} ${where} ORDER BY ${order} LIMIT ${PAGE_SIZE} OFFSET ${offset}`, params);

  const zones = await noGeomZones();
  const truncated = [];
  let exc = 0;
  const out = rows.map((r) => {
    const row = {};
    for (const c of t.columns) {
      let v = r[c.name];
      const max = c.kind === 'geom' ? GEOM_MAX : c.kind === 'long' ? LONG_MAX : 0;
      if (max && typeof v === 'string' && v.length > max) {
        v = v.slice(0, max) + '…';
        if (!truncated.includes(c.name)) truncated.push(c.name);
      }
      if (Buffer.isBuffer(v)) v = '<binario>';
      row[c.name] = v;
    }
    const reason = exceptionReason(row, zones);
    if (reason) exc++;
    return { ...row, __is_exception: !!reason, __exception_reason: reason };
  });

  return {
    table: name,
    columns: t.columns.map((c) => ({ name: c.name, type: c.type, kind: c.kind })),
    search_columns: searchCols.map((c) => c.name),
    has_geo: t.has_geo,
    geo_level: t.geo_level,
    geo_columns: t.geo_columns,
    note: t.has_geo ? null
      : 'Tabla sin clave geográfica (excepción aprobada): se marca «sin geografía» y queda fuera del Mapa y de Comparar.',
    truncated_columns: truncated,
    q: search,
    page,
    page_size: PAGE_SIZE,
    pages,
    total,
    exceptions_on_page: exc,
    rows: out,
  };
}

module.exports = { listTables, tableRows, PAGE_SIZE };