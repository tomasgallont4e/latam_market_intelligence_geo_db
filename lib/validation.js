'use strict';
// flow_validation: runs the acceptance checks over a load_batch, writes
// validation_issue rows (errors + 'sin geografía' info exceptions) and sets
// load_batch.status to 'validated' or 'failed'. Triggered by
// evt_post_load_validation (lib/loader.js hook) and by "Revalidar".
const pool = require('../db/pool');
const { computeAcceptance, latestBatchId } = require('./acceptance');

const MAX_CODE_ISSUES_PER_COLUMN = 50;
const s64 = (v) => (v === null || v === undefined ? null : String(v).slice(0, 64));

async function validateBatch(batchId) {
  const id = batchId || await latestBatchId();
  if (!id) throw new Error('No load_batch to validate');
  const [[batch]] = await pool.query('SELECT id FROM load_batch WHERE id = ?', [id]);
  if (!batch) throw new Error(`load_batch #${id} not found`);

  const result = await computeAcceptance();
  const issues = [];
  const err = (issue_type, table_name, column_name, code_value, expected_value, actual_value, message) =>
    issues.push({ issue_type, severity: 'error', table_name, column_name, code_value, expected_value, actual_value, message });

  for (const c of result.checks) {
    if (c.ok) continue;
    if (c.id === 'unjoined') continue; // detailed per code below
    const type = ['municipalities', 'zones', 'upz', 'department_polygons'].includes(c.id) ? 'count_mismatch' : 'total_mismatch';
    err(type, c.table, null, null, s64(c.expected), s64(c.actual),
      `${c.label}: esperado ${c.expected}, real ${c.actual} (diferencia ${c.difference}, tolerancia ${c.tolLabel})${c.detail ? ' — ' + c.detail : ''}`);
  }
  for (const r of result.unjoined) {
    for (const u of r.unjoined.slice(0, MAX_CODE_ISSUES_PER_COLUMN)) {
      err('unjoined_code', r.table, r.column, s64(u.code === null ? 'NULL' : u.code), '0', s64(u.n),
        `${r.table}.${r.column} = ${u.code === null ? 'NULL' : `'${u.code}'`} no une con su tabla geográfica (${u.n} filas)`);
    }
  }
  if (!result.axis.ok) {
    err('count_mismatch', 'geo_municipality', 'point', '11001',
      `${result.axis.expected.lat} / ${result.axis.expected.lon}`,
      result.axis.actual ? `${result.axis.actual.lat.toFixed(4)} / ${result.axis.actual.lon.toFixed(4)}` : null,
      'rule_axis_order: el punto de Bogotá no coincide con lat 4.31 / lon -74.18 (¿orden de ejes invertido?)');
  }
  for (const t of result.missingSources) {
    err('missing_source', 'meta_sources', 'table_name', t, null, null, `La tabla ${t} no tiene fuente y año en meta_sources`);
  }
  for (const e of result.exceptions) {
    issues.push({ issue_type: 'no_geography_exception', severity: 'info', table_name: e.table, column_name: e.column,
      code_value: s64(e.code), expected_value: null, actual_value: s64(e.n), message: `${e.message} — ${e.n} filas` });
  }

  const conn = await pool.getConnection();
  try {
    await conn.beginTransaction();
    await conn.query('DELETE FROM validation_issue WHERE batch_id = ?', [id]);
    for (const i of issues) {
      await conn.query(
        `INSERT INTO validation_issue (batch_id, issue_type, severity, table_name, column_name, code_value, expected_value, actual_value, message)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [id, i.issue_type, i.severity, i.table_name, i.column_name, i.code_value, i.expected_value, i.actual_value, i.message]);
    }
    const errors = issues.filter((i) => i.severity === 'error').length;
    const status = result.accepted && errors === 0 ? 'validated' : 'failed';
    const note = `Validación ${new Date().toISOString()}: ${result.passed}/${result.total} comprobaciones, eje ${result.axis.ok ? 'OK' : 'FALLA'}, ${errors} errores, ${issues.length - errors} excepciones aprobadas`;
    await conn.query(
      'UPDATE load_batch SET status = ?, finished_at = COALESCE(finished_at, NOW()), notes = ? WHERE id = ?',
      [status, note, id]);
    await conn.commit();
    conn.release();
    return { batchId: id, status, errors, infos: issues.length - errors, issues, ...result };
  } catch (e) {
    try { await conn.rollback(); } catch (_) { /* ignore */ }
    conn.release();
    throw e;
  }
}

module.exports = { validateBatch, run: validateBatch };