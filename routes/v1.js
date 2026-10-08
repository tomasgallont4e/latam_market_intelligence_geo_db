'use strict';
// v1 data-quality API (Panel de aceptación):
//   GET  /v1/acceptance      → checks[], axis_test, all_green (lib/acceptance.js, read-only)
//   POST /v1/validate        → re-runs flow_validation on the latest load_batch
//   GET  /v1/batches/latest  → latest load_batch + issue counts
//   GET  /v1/issues          → validation_issue rows of a batch (?severity=error|info&batch_id=)
//   POST /v1/load            → reloads the 27 CSVs (lib/loader.js), then validates
//   GET  /v1/tables          → every table: COUNT(*), meta_sources source/year, has_geo
//   GET  /v1/tables/:table/rows?page=&q= → 25-row pages (whitelisted table names only)
const express = require('express');
const pool = require('../db/pool');
const { computeAcceptance } = require('../lib/acceptance');
const { validateBatch } = require('../lib/validation');
const { listTables, tableRows } = require('../lib/tables');

const router = express.Router();

// Only one write operation (validate / load) at a time.
let busy = null;

const wrap = (fn) => async (req, res) => {
  try {
    res.json(await fn(req, res));
  } catch (e) {
    console.error('[v1]', req.method, req.path, e.message);
    res.status(e.status || 500).json({ error: e.message });
  }
};

function httpError(status, message) {
  const e = new Error(message);
  e.status = status;
  return e;
}

async function latestBatch() {
  const [[b]] = await pool.query(
    `SELECT id, country_code, source_file, status, rows_loaded, started_at, finished_at, notes
       FROM load_batch ORDER BY id DESC LIMIT 1`);
  if (!b) return null;
  const [[c]] = await pool.query(
    `SELECT COALESCE(SUM(severity = 'error'), 0) AS errors,
            COALESCE(SUM(severity = 'info'), 0)  AS infos,
            MAX(created_at) AS last_validation
       FROM validation_issue WHERE batch_id = ?`, [b.id]);
  const [[prev]] = await pool.query(
    'SELECT id, status, finished_at FROM load_batch WHERE id < ? ORDER BY id DESC LIMIT 1', [b.id]);
  return {
    ...b,
    errors: Number(c.errors),
    infos: Number(c.infos),
    last_validation: c.last_validation,
    previous: prev || null,
  };
}

router.get('/v1/acceptance', wrap(async () => {
  const r = await computeAcceptance();
  const batch = await latestBatch();
  return {
    batch,
    checks: r.checks,
    passed: r.passed,
    total: r.total,
    failed: r.total - r.passed,
    axis_test: r.axis,
    exceptions: r.exceptions,
    missing_sources: r.missingSources,
    department_polygons: { total: r.departmentPolygons.total, valid: r.departmentPolygons.valid, invalid: r.departmentPolygons.invalid },
    join_columns_checked: r.unjoined.length,
    all_green: r.accepted,
    computed_at: new Date().toISOString(),
  };
}));

router.post('/v1/validate', wrap(async (req) => {
  if (busy) throw httpError(409, `Operación en curso: ${busy}`);
  busy = 'validate';
  try {
    const batchId = req.body && req.body.batch_id ? Number(req.body.batch_id) : null;
    const r = await validateBatch(batchId);
    return {
      batch_id: r.batchId,
      status: r.status,
      errors: r.errors,
      infos: r.infos,
      passed: r.passed,
      total: r.total,
      axis_ok: r.axis.ok,
      all_green: r.accepted,
    };
  } finally {
    busy = null;
  }
}));

router.get('/v1/batches/latest', wrap(async () => {
  const b = await latestBatch();
  if (!b) throw httpError(404, 'No hay ningún load_batch');
  return b;
}));

router.get('/v1/issues', wrap(async (req) => {
  const sev = req.query.severity ? String(req.query.severity) : '';
  if (sev && !['error', 'info'].includes(sev)) throw httpError(400, "severity debe ser 'error' o 'info'");
  let batchId = req.query.batch_id ? Number(req.query.batch_id) : null;
  if (!batchId) {
    const [[m]] = await pool.query('SELECT MAX(id) AS id FROM load_batch');
    batchId = m && m.id ? Number(m.id) : null;
  }
  if (!batchId) return { batch_id: null, issues: [], counts: { error: 0, info: 0 } };
  const params = [batchId];
  let where = 'batch_id = ?';
  if (sev) { where += ' AND severity = ?'; params.push(sev); }
  const [rows] = await pool.query(
    `SELECT id, batch_id, issue_type, severity, table_name, column_name, code_value,
            expected_value, actual_value, message, created_at
       FROM validation_issue WHERE ${where}
      ORDER BY FIELD(severity, 'error', 'info'), table_name, id LIMIT 500`, params);
  const [[c]] = await pool.query(
    `SELECT COALESCE(SUM(severity = 'error'), 0) AS e, COALESCE(SUM(severity = 'info'), 0) AS i
       FROM validation_issue WHERE batch_id = ?`, [batchId]);
  return { batch_id: batchId, severity: sev || null, counts: { error: Number(c.e), info: Number(c.i) }, issues: rows };
}));

router.get('/v1/tables', wrap(async () => listTables()));

router.get('/v1/tables/:table/rows', wrap(async (req) =>
  tableRows(req.params.table, req.query.page, req.query.q)));

router.post('/v1/load', wrap(async () => {
  if (busy) throw httpError(409, `Operación en curso: ${busy}`);
  busy = 'load';
  try {
    const { loadAll } = require('../lib/loader');
    const logs = [];
    const r = await loadAll({ log: (m) => logs.push(String(m)) });
    return {
      batch_id: r.batchId,
      rows_loaded: r.rowsLoaded,
      tables: r.report,
      validation: r.validation
        ? { status: r.validation.status, errors: r.validation.errors, infos: r.validation.infos, passed: r.validation.passed, total: r.validation.total }
        : null,
      log: logs.slice(-60),
    };
  } finally {
    busy = null;
  }
}));

module.exports = router;