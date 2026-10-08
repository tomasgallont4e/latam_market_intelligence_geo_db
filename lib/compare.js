'use strict';
// Comparar (rule_compare_same_level + rule_map_api_readonly): SELECT-only.
// Reuses the map indicator functions so the compare table shows exactly the
// same indicators, values and meta_sources source/year as the map.
const pool = require('../db/pool');
const data = require('./mapData');

const LEVELS = {
  department: 'Departamentos',
  municipality: 'Ciudades',
  localidad: 'Localidades de Bogotá',
};

function badRequest(msg) {
  const e = new Error(msg);
  e.status = 400;
  return e;
}

async function listPlaces(level) {
  if (!LEVELS[level]) throw badRequest('Nivel no válido. Use department, municipality o localidad.');
  let rows;
  if (level === 'department') {
    [rows] = await pool.query('SELECT department_code AS id, department_code AS code, name FROM geo_department ORDER BY name');
  } else if (level === 'municipality') {
    [rows] = await pool.query(
      `SELECT m.municipality_code AS id, m.municipality_code AS code, m.name, d.name AS parent
         FROM geo_municipality m LEFT JOIN geo_department d ON d.department_code = m.department_code
        ORDER BY m.name, d.name`
    );
  } else {
    [rows] = await pool.query(
      `SELECT zone_id AS id, zone_code AS code, name FROM geo_zone
        WHERE municipality_code = '11001' AND zone_type = 'localidad'
        ORDER BY zone_code`
    );
  }
  return {
    level,
    level_label: LEVELS[level],
    count: rows.length,
    places: rows.map((r) => ({ id: String(r.id), code: String(r.code), name: r.name, parent: r.parent || null })),
  };
}

function parseIds(ids) {
  const raw = Array.isArray(ids) ? ids.join(',') : String(ids || '');
  const out = [];
  for (const s of raw.split(',')) {
    const t = s.trim();
    if (t && !out.includes(t)) out.push(t);
  }
  return out;
}

async function compare({ level, ids, persona } = {}) {
  if (!LEVELS[level]) throw badRequest('Nivel no válido. Use department, municipality o localidad.');
  const list = parseIds(ids);
  if (list.length < 2 || list.length > 4) {
    throw badRequest('Seleccione de 2 a 4 lugares del mismo nivel.');
  }
  const catalog = await listPlaces(level);
  const byId = new Map(catalog.places.map((p) => [p.id, p]));
  const missing = list.filter((id) => !byId.has(id));
  if (missing.length) {
    throw badRequest(
      `Los lugares ${missing.join(', ')} no pertenecen al nivel «${LEVELS[level]}». Solo se comparan lugares del mismo nivel.`
    );
  }
  const places = list.map((id) => byId.get(id));

  let indicators;
  let valuesFor;
  let personaOut = null;
  let note = null;
  if (level === 'department') {
    const dep = await data.getDepartments({ persona });
    indicators = dep.indicators;
    personaOut = dep.persona;
    const m = new Map(dep.features.map((f) => [String(f.properties.department_code), f.properties.values]));
    valuesFor = (id) => m.get(id) || null;
  } else if (level === 'municipality') {
    const mun = await data.getMunicipalities({ persona });
    indicators = mun.indicators;
    personaOut = mun.persona;
    const m = new Map(mun.municipalities.map((x) => [String(x.municipality_code), x.values]));
    valuesFor = (id) => m.get(id) || null; // 27493 (sin geografía) → todo n.a.
  } else {
    const loc = await data.getLocalidades();
    indicators = loc.indicators;
    note = 'El filtro por persona no aplica a las localidades de Bogotá (fuente: Encuesta Multipropósito 2021).';
    const m = new Map(loc.features.map((f) => [String(f.properties.zone_id), f.properties.values]));
    valuesFor = (id) => m.get(id) || null;
  }

  const rows = indicators.map((ind) => ({
    key: ind.key,
    label: ind.label,
    unit: ind.unit,
    table: ind.table,
    column: ind.column,
    source: ind.source,
    values: places.map((p) => {
      const v = valuesFor(p.id);
      const x = v ? v[ind.key] : null;
      return x === undefined || x === null || Number.isNaN(Number(x)) ? null : Number(x);
    }),
  }));

  return {
    level,
    level_label: LEVELS[level],
    persona: personaOut,
    persona_note: note,
    places,
    indicators: rows,
    note: 'Todas las cifras son agregados; no hay datos personales.',
  };
}

module.exports = { compare, listPlaces, LEVELS };