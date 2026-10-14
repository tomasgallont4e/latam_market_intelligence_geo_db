'use strict';
// scripts/load-peru.js — Perú Day 1 (capas A, B y F) → tablas pe_* + filas pe_* de meta_sources.
// Independiente de la app: server.js, el mapa y lib/loader.js NO lo importan, y no toca tablas de Colombia.
//
// Uso:
//   node scripts/load-peru.js --dry-run    sin base de datos: filas CSV vs manifiesto, SHA256, source_id
//   node scripts/load-peru.js              recrea las 20 tablas pe_*, registra meta_sources y valida
//   node scripts/load-peru.js --meta-only  solo vuelve a registrar las 20 filas pe_* de meta_sources
//                                          (necesario después de cada recarga de Colombia: v1/load
//                                          vacía meta_sources entera; las tablas pe_* no se tocan)
// Necesita DATABASE_URL o DB_* (en esta plataforma solo los recibe el servicio de la app).
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { parse } = require('csv-parse/sync');

const ROOT = path.join(__dirname, '..', 'data', 'peru', 'think4ever_peru_day1_FINAL');
const layerDir = (L) => path.join(ROOT, `layer${L}`, `think4ever_peru_day1_layer${L}_FINAL`);
const PROJECT_LICENSE = 'uso interno';
const BATCH = 200;
const NAME_RE = /^[A-Za-z0-9_]{1,64}$/;
const PE_RE = /^pe_[a-z0-9_]{1,61}$/;
const q = (id) => {
  if (!NAME_RE.test(id)) throw new Error(`Identificador no válido: ${id}`);
  return '`' + id + '`';
};

const LIC = `Licencia: ${PROJECT_LICENSE}`;
const SRC_A = `GitHub Innovation Graph (GitHub, https://github.com/github/innovationgraph, dataset 1.0.10); ${LIC}`;
const SRC_B = `Stack Overflow Developer Survey 2025 (Stack Overflow, https://survey.stackoverflow.co/); ${LIC}`;
const SRC_F = (what) => `INEI (Instituto Nacional de Estadística e Informática) – ${what}; ${LIC}`;
const EPEN = 'EPEN 2025 (Encuesta Permanente de Empleo Nacional, base anual departamentos)';
const ENAHO = 'ENAHO 2025 (Encuesta Nacional de Hogares)';
const CNO = 'CNO 2015 (Clasificador Nacional de Ocupaciones, anexos 3-4)';

const periodRange = (col) => (recs) => {
  const v = [...new Set(recs.map((r) => r[col]).filter(Boolean))].sort();
  if (!v.length) return null;
  return v.length === 1 ? v[0] : `${v[0]}–${v[v.length - 1]}`;
};

// table, layer, CSV (data/<file>.csv), year (string or function of records), source, description
const TABLES = [
  { table: 'pe_a_github_country_quarterly', layer: 'A', file: 'a_github_country_quarterly_pe', year: periodRange('period_label'), source: SRC_A,
    description: 'Peru (PE), Layer A: GitHub Innovation Graph metrics by quarter (developer accounts and other country metrics).' },
  { table: 'pe_a_github_languages', layer: 'A', file: 'a_github_languages_pe', year: periodRange('period_label'), source: SRC_A,
    description: 'Peru (PE), Layer A: programming languages by number of pushers and rank per quarter.' },
  { table: 'pe_a_github_indicators', layer: 'A', file: 'a_github_indicators_pe', year: periodRange('period_label'), source: SRC_A,
    description: 'Peru (PE), Layer A: indicators A1-A5 (latest quarter vs comparison quarter), method and validation status.' },
  { table: 'pe_b_survey_indicators', layer: 'B', file: 'b_survey_indicators_pe', year: '2025', source: SRC_B,
    description: 'Peru (PE), Layer B: AI adoption indicators among developers by comparison group (proportion, 95% CI, base flags).' },
  { table: 'pe_b_survey_distributions', layer: 'B', file: 'b_survey_distributions_pe', year: '2025', source: SRC_B,
    description: 'Peru (PE), Layer B: answer distributions by category for each indicator and comparison group.' },
  { table: 'pe_b_comparison_groups', layer: 'B', file: 'b_comparison_groups_pe', year: '2025', source: SRC_B,
    description: 'Peru (PE), Layer B: comparison groups (Peru, region, global), countries included and respondents.' },
  { table: 'pe_b_indicator_definitions', layer: 'B', file: 'b_indicator_definitions_pe', year: '2025', source: SRC_B,
    description: 'Peru (PE), Layer B: definitions of indicators B1-B5 (survey variable, question, numerator and denominator rules).' },
  { table: 'pe_b_reproduction_check', layer: 'B', file: 'b_reproduction_check_pe', year: '2025', source: `${SRC_B.replace(`; ${LIC}`, '')}, official aggregate ai.json; ${LIC}`,
    description: 'Peru (PE), Layer B: reproduction of the official Stack Overflow aggregates (official vs recomputed).' },
  { table: 'pe_f_persona_estimates', layer: 'F', file: 'f_persona_estimates_pe', year: '2025', source: SRC_F(EPEN),
    description: 'Peru (PE), Layer F: employed people by persona and ring, 2025 (estimate, SE, CV, 95% CI, publication status).' },
  { table: 'pe_f_persona_profiles', layer: 'F', file: 'f_persona_profiles_pe', year: '2025', source: SRC_F(EPEN),
    description: 'Peru (PE), Layer F: profile indicators of each persona group (weighted numerator/denominator, small-cell flags).' },
  { table: 'pe_f_persona_correspondence', layer: 'F', file: 'f_persona_correspondence_pe', year: '2025', source: SRC_F(`${EPEN} / ${CNO}`),
    description: 'Peru (PE), Layer F: the 13 personas mapped from ISCO-08 template codes to CNO 2015 codes, with 2025 employment.' },
  { table: 'pe_f_occupation_mapping', layer: 'F', file: 'f_occupation_mapping_pe', year: '2025', source: SRC_F(`${CNO} / ${EPEN}`),
    description: 'Peru (PE), Layer F: CNO 2015 occupation codes per persona and ring, link to CIUO-08 and cell status.' },
  { table: 'pe_f_cno_code_counts', layer: 'F', file: 'f_cno_code_counts_pe', year: '2025', source: SRC_F(EPEN),
    description: 'Peru (PE), Layer F: sample records and weighted employment by CNO 2015 code (publishable cells).' },
  { table: 'pe_cno2015_ciuo08_correspondence', layer: 'F', file: 'cno2015_ciuo08_correspondence', year: '2015', source: SRC_F(CNO),
    description: 'Peru (PE): official 4-digit correspondence CNO 2015 ↔ CIUO-08 (annexes 3 and 4).' },
  { table: 'pe_f9_persona_socioeconomic_enaho', layer: 'F', file: 'f9_persona_socioeconomic_enaho_pe', year: '2025', source: SRC_F(`${ENAHO}, Sumaria`),
    description: 'Peru (PE), Layer F9: socioeconomic shares by persona group (income quintile, etc.) with SE, CV and suppressed cells.' },
  { table: 'pe_f1_enaho_diagnostic', layer: 'F', file: 'f1_enaho_diagnostic_pe', year: '2025', source: SRC_F(`${ENAHO} / ${EPEN}`),
    description: 'Peru (PE), Layer F1: ENAHO vs EPEN employment by persona group. Diagnostic only: EPEN remains the F1 source.' },
  { table: 'pe_f_designers_informational', layer: 'F', file: 'f_designers_informational_pe', year: '2025', source: SRC_F(`${EPEN} / ${ENAHO}`),
    description: 'Peru (PE), Layer F: designer occupations, informational only (outside the rings; many cells suppressed).' },
  { table: 'pe_enaho_quintile_cutpoints', layer: 'F', file: 'enaho_quintile_cutpoints_pe', year: '2025', source: SRC_F(`${ENAHO}, Sumaria`),
    description: 'Peru (PE): ENAHO 2025 income quintile cut points (soles per month, Lima prices).' },
  { table: 'pe_decisions_log', layer: 'F', file: 'decisions_log_pe', year: '2026', source: `Think4ever, package decision log (Layer F, on INEI EPEN 2025 / ENAHO 2025 data); ${LIC}`,
    description: 'Peru (PE): methodological decisions of the Day 1 package (status, current / superseded).' },
];

const REGISTRY = {
  table: 'pe_source_registry', year: '2026',
  source: `Source registries of the Peru Day 1 package (layers A, B, F): GitHub, Stack Overflow, INEI; ${LIC}`,
  description: 'Peru (PE): union of the 3 source registries (layer, source_id, publisher, original license, license_status, project license).',
  files: { A: 'source_registry_layer_a_pe', B: 'source_registry_layer_b_pe', F: 'source_registry_layer_f_pe' },
};
const REG_COLS = ['layer', 'source_id', 'source_name', 'publisher', 'dataset_version', 'reference_period', 'url',
  'access_date', 'access_method', 'license', 'license_status', 'role', 'status', 'sha256', 'extra_json', 'project_license'];

// Text labels used by Layer F tables instead of a source_id.
const SOURCE_LABELS = {
  'EPEN 2025': ['SRC_INEI_EPEN_2025_DPTO'],
  'ENAHO 2025': ['SRC_INEI_ENAHO_2025_M05', 'SRC_INEI_ENAHO_2025_SUMARIA'],
};

// ---------- helpers ----------
function readCsv(file) {
  if (!fs.existsSync(file)) throw new Error(`No existe ${path.relative(ROOT, file)}`);
  const text = fs.readFileSync(file, 'utf8');
  const headers = parse(text, { bom: true, to_line: 1 })[0];
  const recs = parse(text, { columns: true, bom: true, skip_empty_lines: true, cast: false });
  for (const h of headers) if (!NAME_RE.test(h)) throw new Error(`${path.basename(file)}: cabecera no válida '${h}'`);
  return { headers, recs };
}

function clean(v) {
  if (v === undefined || v === null) return null;
  const s = String(v);
  return s.trim() === '' ? null : s;
}

const NUM = /^-?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/;
const FORCE_TEXT = /code|cno|ciuo|isco|qid|_id$/i; // classification codes and ids stay text

function columnDefs(headers, recs) {
  return headers.map((h) => {
    const vals = recs.map((r) => r[h]).filter((v) => v !== '' && v != null);
    const lead = vals.some((v) => /^-?0\d/.test(v));
    if (vals.length && !lead && !FORCE_TEXT.test(h) && vals.every((v) => NUM.test(v))) {
      const integer = vals.every((v) => /^-?\d+$/.test(v) && Math.abs(Number(v)) < 9e15);
      return { name: h, sql: integer ? 'BIGINT' : 'DOUBLE' };
    }
    let max = 1;
    for (const v of vals) max = Math.max(max, [...v].length);
    return { name: h, sql: max <= 170 ? `VARCHAR(${Math.min(255, Math.max(16, Math.ceil(max * 1.5)))})` : 'TEXT' };
  });
}

function sha256(file) {
  return crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
}

function checkSums(sumsFile, baseDir) {
  const out = { file: path.relative(ROOT, sumsFile), n: 0, ok: 0, bad: [], missing: [] };
  for (const line of fs.readFileSync(sumsFile, 'utf8').split(/\r?\n/)) {
    const m = line.match(/^([0-9a-f]{64})\s+\*?(.+)$/i);
    if (!m) continue;
    out.n += 1;
    const f = path.join(baseDir, m[2].trim());
    if (!fs.existsSync(f)) out.missing.push(m[2].trim());
    else if (sha256(f) === m[1].toLowerCase()) out.ok += 1;
    else out.bad.push(m[2].trim());
  }
  return out;
}

function manifestRows(L) {
  const f = path.join(layerDir(L), 'manifest.csv');
  const map = {};
  for (const r of parse(fs.readFileSync(f, 'utf8'), { columns: true, bom: true, skip_empty_lines: true })) {
    if (r.path && r.rows !== undefined && r.rows !== '') map[r.path.replace(/\\/g, '/')] = Number(r.rows);
  }
  return map;
}

// ---------- offline preparation + validation (no DB) ----------
function prepare() {
  if (!fs.existsSync(ROOT)) throw new Error(`No existe ${ROOT}: extrae think4ever_peru_day1_FINAL.zip en data/peru/`);
  const problems = [];
  const manifests = { A: manifestRows('A'), B: manifestRows('B'), F: manifestRows('F') };

  // 1. SHA256 (general list + one list per layer)
  // The general list uses paths relative to data/peru (they start with think4ever_peru_day1_FINAL/).
  const sums = [checkSums(path.join(ROOT, 'SHA256SUMS.txt'), path.dirname(ROOT))];
  for (const L of ['A', 'B', 'F']) sums.push(checkSums(path.join(layerDir(L), 'validation', 'SHA256SUMS.txt'), path.join(ROOT, `layer${L}`)));
  for (const s of sums) {
    if (s.ok !== s.n) problems.push(`SHA256 ${s.file}: ${s.ok}/${s.n} (distintos: ${s.bad.join(', ') || '-'}; faltan: ${s.missing.join(', ') || '-'})`);
  }

  // 2. Source registry
  const registry = [];
  for (const [L, file] of Object.entries(REGISTRY.files)) {
    const { recs } = readCsv(path.join(layerDir(L), 'data', `${file}.csv`));
    const expected = manifests[L][`data/${file}.csv`];
    if (expected !== undefined && expected !== recs.length) problems.push(`${file}: ${recs.length} filas, manifiesto ${expected}`);
    for (const r of recs) {
      const known = new Set(REG_COLS);
      const extra = {};
      for (const [k, v] of Object.entries(r)) if (!known.has(k) && v !== '') extra[k] = v;
      registry.push({
        layer: L, source_id: r.source_id, source_name: r.source_name, publisher: r.publisher,
        dataset_version: r.dataset_version, reference_period: r.reference_period, url: r.url,
        access_date: r.access_date, access_method: r.access_method, license: r.license,
        license_status: r.license_status, role: r.role, status: r.status, sha256: r.sha256,
        extra_json: Object.keys(extra).length ? JSON.stringify(extra) : null, project_license: PROJECT_LICENSE,
      });
    }
  }
  const regIds = new Set(registry.map((r) => r.source_id));

  // 3. Data tables: rows vs manifest, column types, source references
  const data = [];
  for (const t of TABLES) {
    if (!PE_RE.test(t.table)) throw new Error(`Nombre de tabla no permitido: ${t.table}`);
    const { headers, recs } = readCsv(path.join(layerDir(t.layer), 'data', `${t.file}.csv`));
    const expected = manifests[t.layer][`data/${t.file}.csv`];
    if (expected === undefined) problems.push(`${t.file}: no aparece en el manifiesto de la capa ${t.layer}`);
    else if (expected !== recs.length) problems.push(`${t.file}: ${recs.length} filas, manifiesto ${expected}`);
    const refs = new Set();
    if (headers.includes('source_id')) {
      for (const r of recs) if (r.source_id && !regIds.has(r.source_id)) refs.add(r.source_id);
    }
    if (headers.includes('source') && t.layer === 'F') {
      for (const r of recs) {
        const ids = SOURCE_LABELS[r.source];
        if (r.source && (!ids || !ids.some((id) => regIds.has(id)))) refs.add(r.source);
      }
    }
    if (refs.size) problems.push(`${t.file}: fuentes sin registro: ${[...refs].join(', ')}`);
    const year = typeof t.year === 'function' ? t.year(recs) : t.year;
    data.push({ ...t, headers, recs, cols: columnDefs(headers, recs), yearValue: year, manifest: expected });
  }
  return { data, registry, sums, problems };
}

// ---------- DB ----------
async function recreate(pool, table, colsSql) {
  if (!PE_RE.test(table)) throw new Error(`Solo se recrean tablas pe_*: ${table}`);
  await pool.query(`DROP TABLE IF EXISTS ${q(table)}`);
  await pool.query(`CREATE TABLE ${q(table)} (\`pe_row_id\` INT NOT NULL AUTO_INCREMENT PRIMARY KEY, ${colsSql}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4`);
}

async function insertRows(pool, table, cols, rows) {
  let n = 0;
  const colList = cols.map(q).join(', ');
  const tuple = `(${cols.map(() => '?').join(', ')})`;
  for (let i = 0; i < rows.length; i += BATCH) {
    const chunk = rows.slice(i, i + BATCH);
    const [res] = await pool.query(`INSERT INTO ${q(table)} (${colList}) VALUES ${chunk.map(() => tuple).join(', ')}`, chunk.flat());
    n += res.affectedRows;
  }
  return n;
}

async function loadTables(pool, data, registry) {
  for (const t of data) {
    await recreate(pool, t.table, t.cols.map((c) => `${q(c.name)} ${c.sql} NULL`).join(', '));
    await insertRows(pool, t.table, t.headers, t.recs.map((r) => t.headers.map((h) => clean(r[h]))));
  }
  const regSql = REG_COLS.map((c) => {
    if (c === 'layer') return '`layer` VARCHAR(1) NOT NULL';
    if (c === 'source_id') return '`source_id` VARCHAR(64) NOT NULL';
    if (c === 'project_license') return '`project_license` VARCHAR(32) NOT NULL';
    return `${q(c)} TEXT NULL`;
  }).join(', ') + ', UNIQUE KEY `uq_pe_source_registry` (`layer`, `source_id`)';
  await recreate(pool, REGISTRY.table, regSql);
  await insertRows(pool, REGISTRY.table, REG_COLS, registry.map((r) => REG_COLS.map((c) => clean(r[c]))));
}

function metaRows(data) {
  const rows = data.map((t) => [t.table, t.description, t.source, t.yearValue]);
  rows.push([REGISTRY.table, REGISTRY.description, REGISTRY.source, REGISTRY.year]);
  for (const r of rows) if (!PE_RE.test(r[0])) throw new Error(`meta_sources: solo filas pe_*: ${r[0]}`);
  return rows;
}

async function registerMeta(pool, rows) {
  const [res] = await pool.query(
    `INSERT INTO meta_sources (table_name, description, source, year) VALUES ${rows.map(() => '(?, ?, ?, ?)').join(', ')}
     ON DUPLICATE KEY UPDATE description = VALUES(description), source = VALUES(source), year = VALUES(year)`, rows.flat());
  return res.affectedRows;
}

async function colombiaSnapshot(pool) {
  const [tbls] = await pool.query(
    `SELECT table_name AS t FROM information_schema.tables
      WHERE table_schema = DATABASE() AND table_type = 'BASE TABLE' AND table_name NOT LIKE 'pe\\_%'
      ORDER BY table_name`);
  const counts = {};
  for (const { t } of tbls) {
    if (!NAME_RE.test(t)) continue;
    const [[r]] = await pool.query(`SELECT COUNT(*) AS n FROM ${q(t)}`);
    counts[t] = Number(r.n);
  }
  const [[m]] = await pool.query(
    `SELECT COUNT(*) AS n, COALESCE(SUM(CRC32(CONCAT_WS('|', table_name, description, source, year))), 0) AS crc
       FROM meta_sources WHERE table_name NOT LIKE 'pe\\_%'`);
  return { counts, metaRows: Number(m.n), metaCrc: String(m.crc) };
}

function compareSnapshots(a, b) {
  const diffs = [];
  // meta_sources total changes because of the pe_* rows; its Colombia rows are compared separately.
  for (const t of new Set([...Object.keys(a.counts), ...Object.keys(b.counts)])) {
    if (t === 'meta_sources') continue;
    if (a.counts[t] !== b.counts[t]) diffs.push(`${t}: ${a.counts[t]} → ${b.counts[t]}`);
  }
  if (a.metaRows !== b.metaRows || a.metaCrc !== b.metaCrc) diffs.push(`meta_sources (filas de Colombia): ${a.metaRows} → ${b.metaRows}, checksum ${a.metaCrc === b.metaCrc ? 'igual' : 'distinto'}`);
  return diffs;
}

async function verify(pool, data, registry, meta) {
  const problems = [];
  const lines = [];
  for (const t of [...data, { table: REGISTRY.table, recs: registry, manifest: registry.length }]) {
    let n = null;
    try { const [[r]] = await pool.query(`SELECT COUNT(*) AS n FROM ${q(t.table)}`); n = Number(r.n); } catch (e) { problems.push(`${t.table}: ${e.code || e.message}`); }
    const ok = n === t.recs.length;
    if (!ok && n !== null) problems.push(`${t.table}: ${n} filas en la base, CSV ${t.recs.length}`);
    lines.push(`  ${t.table.padEnd(36)} CSV ${String(t.recs.length).padStart(5)}  manifiesto ${String(t.manifest ?? '-').padStart(5)}  base ${String(n ?? '-').padStart(5)}  ${ok ? 'OK' : 'FALLA'}`);
  }
  const names = meta.map((r) => r[0]);
  const [ms] = await pool.query(`SELECT table_name, source, year FROM meta_sources WHERE table_name IN (${names.map(() => '?').join(', ')})`, names);
  const by = new Map(ms.map((r) => [r.table_name, r]));
  for (const n of names) {
    const r = by.get(n);
    if (!r || !r.source || !r.year) problems.push(`meta_sources sin fuente/año: ${n}`);
    else if (!r.source.includes(LIC)) problems.push(`meta_sources sin '${LIC}': ${n}`);
  }
  lines.push(`  meta_sources pe_*: ${by.size}/${names.length} con fuente, año y '${LIC}'`);
  return { problems, lines };
}

// ---------- main ----------
(async () => {
  const args = new Set(process.argv.slice(2));
  const dryRun = args.has('--dry-run');
  const metaOnly = args.has('--meta-only');
  let pool = null;
  let exitCode = 0;
  try {
    const { data, registry, sums, problems } = prepare();
    console.log('PERÚ DAY 1 — validación del paquete (sin base de datos)');
    for (const s of sums) console.log(`  SHA256 ${s.file.padEnd(70)} ${s.ok}/${s.n}`);
    for (const t of data) console.log(`  ${t.file.padEnd(36)} → ${t.table.padEnd(36)} ${String(t.recs.length).padStart(5)} filas (manifiesto ${t.manifest ?? '-'}), ${t.headers.length} columnas`);
    console.log(`  source registry A+B+F → ${REGISTRY.table}: ${registry.length} filas`);
    if (problems.length) {
      console.error('\nPAQUETE NO VÁLIDO, no se carga nada:\n  - ' + problems.join('\n  - '));
      process.exit(1);
    }
    console.log('  Paquete OK: SHA256, filas = manifiesto, source_id registrados.');
    if (dryRun) {
      for (const t of data) console.log(`  ${t.table}: ${t.cols.map((c) => `${c.name} ${c.sql}`).join(', ')}`);
      process.exit(0);
    }

    try {
      pool = require('../db/pool');
    } catch (e) {
      console.error(`\nNO SE PUEDE CONECTAR: ${e.message}`);
      console.error('En esta plataforma solo el servicio de la app recibe las credenciales. Ver data/peru/README.md.');
      process.exit(2);
    }

    const before = await colombiaSnapshot(pool);
    const meta = metaRows(data);
    if (!metaOnly) {
      await loadTables(pool, data, registry);
      console.log(`\nCargadas ${data.length + 1} tablas pe_*.`);
    }
    await registerMeta(pool, meta);
    console.log(`meta_sources: ${meta.length} filas pe_* registradas (${LIC}).`);

    const after = await colombiaSnapshot(pool);
    const v = await verify(pool, data, registry, meta);
    const diffs = compareSnapshots(before, after);
    console.log('\nVALIDACIÓN EN BASE DE DATOS');
    v.lines.forEach((l) => console.log(l));
    console.log(`  Colombia: ${Object.keys(before.counts).length} tablas, ${before.metaRows} filas en meta_sources → ${diffs.length ? 'CAMBIOS: ' + diffs.join('; ') : 'sin cambios'}`);
    const all = [...v.problems, ...diffs.map((d) => `Colombia cambió: ${d}`)];
    if (all.length) {
      console.error('\nRESULTADO: FALLA\n  - ' + all.join('\n  - '));
      exitCode = 1;
    } else {
      console.log('\nRESULTADO: OK — Perú cargado y validado; Colombia sin cambios.');
    }
  } catch (e) {
    console.error(`LOAD-PERU FAILED: ${e.stack || e.message}`);
    exitCode = 1;
  }
  if (pool) await pool.end().catch(() => {});
  process.exit(exitCode);
})();
