'use strict';
// Appends the db_mods rows (Barranquilla 08001 / Bucaramanga 68001) to the EXISTING CSVs in
// data/geodb-v2/csv, only for natural keys that do not exist yet. Existing rows are never
// modified or removed (user decision: keep current values on conflict).
// Usage: node scripts/merge-db-mods.js [--dry-run] [srcDir]   (srcDir default /tmp/db_mods/db_mods)
const fs = require('fs');
const path = require('path');
const { parse } = require('csv-parse/sync');

const args = process.argv.slice(2);
const DRY = args.includes('--dry-run');
const SRC = args.find((a) => !a.startsWith('--')) || '/tmp/db_mods/db_mods';
const DST = path.join(__dirname, '..', 'data', 'geodb-v2', 'csv');

const PLAN = [
  { table: 'fact_companies_zone', key: ['zone_id'], expected: 25, zoneCheck: true },
  { table: 'fact_zone_context', key: ['zone_id'], expected: 25, zoneCheck: true, emptyCols: ['personas13', 'core_it'] },
  { table: 'fact_geih2025_metro_summary', key: ['municipality_code', 'survey_year'], expected: 2 },
  { table: 'fact_persona_profile_metro_2025', key: ['persona', 'municipality_code', 'survey_year'], expected: 26 },
  // fact_persona_segment deliberately excluded (user decision): its 10 new BAQ/BUC rows break the ±30 per-persona margin.
];

// Only municipality codes get a lost leading zero restored ('8001' -> '08001'); years and other values stay as-is.
const norm = (v, col) => {
  const s = v === undefined || v === null ? '' : String(v).trim();
  return col === 'municipality_code' && /^\d{4}$/.test(s) ? s.padStart(5, '0') : s;
};
const keyOf = (r, cols) => cols.map((c) => norm(r[c], c)).join('|');

function readRaw(file) {
  if (!fs.existsSync(file)) throw new Error(`No existe: ${file}`);
  return fs.readFileSync(file, 'utf8');
}
function headerOf(text) {
  return text.replace(/^\uFEFF/, '').split(/\r?\n/, 1)[0].split(',').map((h) => h.trim());
}
function records(text) {
  return parse(text, { columns: true, bom: true, skip_empty_lines: true, cast: false, trim: false });
}
function csvCell(v) {
  const s = v === undefined || v === null ? '' : String(v);
  return /[",\r\n]|^\s|\s$/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

const errors = [];
const results = [];

const zoneIds = new Set(records(readRaw(path.join(DST, 'geo_zone.csv'))).map((r) => norm(r.zone_id)));

for (const p of PLAN) {
  const srcText = readRaw(path.join(SRC, `${p.table}.csv`));
  const dstFile = path.join(DST, `${p.table}.csv`);
  const dstText = readRaw(dstFile);
  const hSrc = headerOf(srcText);
  const hDst = headerOf(dstText);
  if (hSrc.join(',') !== hDst.join(',')) {
    errors.push(`${p.table}: cabeceras distintas\n  RAR : ${hSrc.join(',')}\n  PROY: ${hDst.join(',')}`);
    continue;
  }
  const cur = records(dstText);
  const inc = records(srcText);
  const curKeys = new Set(cur.map((r) => keyOf(r, p.key)));
  const seen = new Set();
  const fresh = [];
  let existing = 0;
  for (const r of inc) {
    const k = keyOf(r, p.key);
    if (seen.has(k)) { errors.push(`${p.table}: clave duplicada dentro del RAR ${k}`); continue; }
    seen.add(k);
    if (curKeys.has(k)) existing += 1; else fresh.push(r);
  }
  if (fresh.length !== p.expected) {
    errors.push(`${p.table}: ${fresh.length} filas nuevas, el plan confirmado esperaba ${p.expected}`);
  }
  if (p.zoneCheck) {
    const missing = fresh.map((r) => norm(r.zone_id)).filter((z) => !zoneIds.has(z));
    if (missing.length) errors.push(`${p.table}: zone_id sin fila en geo_zone.csv: ${missing.join(', ')}`);
  }
  if (p.emptyCols) {
    const filled = fresh.filter((r) => p.emptyCols.some((c) => norm(r[c]) !== ''));
    if (filled.length) errors.push(`${p.table}: ${filled.length} filas con ${p.emptyCols.join('/')} no vacíos`);
  }
  const munis = {};
  for (const r of fresh) {
    const m = norm(r.municipality_code, 'municipality_code') || (r.zone_id ? norm(r.zone_id).split('-')[0] : '?');
    munis[m] = (munis[m] || 0) + 1;
  }
  const extra = {};
  if (p.table === 'fact_persona_segment') {
    for (const r of fresh) extra[r.persona] = (extra[r.persona] || 0) + Number(norm(r.employed) || 0);
  }
  if (p.key.includes('survey_year')) {
    extra.survey_years = [...new Set(fresh.map((r) => norm(r.survey_year)))];
  }
  results.push({ p, dstFile, dstText, hDst, cur: cur.length, inc: inc.length, existing, fresh, munis, extra });
}

console.log(`Origen: ${SRC}\nDestino: ${DST}\nModo: ${DRY ? 'DRY-RUN (no se escribe nada)' : 'ESCRITURA'}\n`);
for (const r of results) {
  console.log(`== ${r.p.table}: actuales ${r.cur}, RAR ${r.inc}, ya existentes ${r.existing}, nuevas ${r.fresh.length} (plan ${r.p.expected})`);
  console.log(`   por municipio/prefijo: ${JSON.stringify(r.munis)}`);
  if (Object.keys(r.extra).length) console.log(`   extra: ${JSON.stringify(r.extra)}`);
}

if (errors.length) {
  console.error(`\nDETENIDO, no se ha escrito nada:\n- ${errors.join('\n- ')}`);
  process.exit(1);
}
if (DRY) { console.log('\nDry-run correcto: todo coincide con el plan.'); process.exit(0); }

for (const r of results) {
  const backup = r.dstFile.replace(/\.csv$/, '.before-db_mods.csv');
  if (fs.existsSync(backup)) { console.error(`Ya existe la copia ${backup}; no sobrescribo. Detenido.`); process.exit(1); }
}
for (const r of results) {
  const backup = r.dstFile.replace(/\.csv$/, '.before-db_mods.csv');
  fs.copyFileSync(r.dstFile, backup);
  const eol = r.dstText.includes('\r\n') ? '\r\n' : '\n';
  const lines = r.fresh.map((row) => r.hDst.map((h) => csvCell(row[h])).join(','));
  const prefix = r.dstText.endsWith('\n') ? '' : eol;
  fs.appendFileSync(r.dstFile, prefix + lines.join(eol) + eol, 'utf8');
  const after = records(fs.readFileSync(r.dstFile, 'utf8')).length;
  console.log(`${r.p.table}: copia ${path.basename(backup)}; +${r.fresh.length} filas; total ${after}`);
  if (after !== r.cur + r.fresh.length) { console.error(`${r.p.table}: total inesperado ${after}`); process.exit(1); }
}
console.log('\nFusión completada.');
