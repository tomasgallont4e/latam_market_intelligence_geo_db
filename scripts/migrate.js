'use strict';
// Runs db/schema.sql idempotently (DROP IF EXISTS + CREATE) one statement at a time.
// Requires MySQL >= 8.0 (POINT SRID 4326 columns, axis-order option).
const fs = require('fs');
const path = require('path');
const pool = require('../db/pool');

function splitStatements(sql) {
  const noComments = sql
    .split(/\r?\n/)
    .filter((l) => !/^\s*--/.test(l))
    .join('\n');
  return noComments
    .split(/;\s*(?:\n|$)/)
    .map((s) => s.trim())
    .filter(Boolean);
}

async function main() {
  const [[{ v }]] = await pool.query('SELECT VERSION() AS v');
  const m = /^(\d+)\.(\d+)/.exec(v);
  const major = m ? Number(m[1]) : 0;
  if (/mariadb/i.test(v) || major < 8) {
    throw new Error(`MySQL >= 8.0 required, server reports ${v}`);
  }
  console.log(`Server version ${v} OK`);

  const sql = fs.readFileSync(path.join(__dirname, '..', 'db', 'schema.sql'), 'utf8');
  const stmts = splitStatements(sql);
  for (const s of stmts) {
    try {
      await pool.query(s);
    } catch (e) {
      console.error('FAILED statement:\n' + s.slice(0, 300));
      throw e;
    }
  }
  console.log(`Executed ${stmts.length} statements`);

  const [tables] = await pool.query(
    `SELECT table_name AS t FROM information_schema.tables
     WHERE table_schema = DATABASE() ORDER BY table_name`
  );
  console.log(`Tables (${tables.length}): ` + tables.map((r) => r.t).join(', '));

  const [codes] = await pool.query(
    `SELECT table_name AS t, column_name AS c, data_type AS d
     FROM information_schema.columns
     WHERE table_schema = DATABASE()
       AND column_name IN ('department_code','municipality_code','seat_municipality_code','zone_id','zone_code','localidad_code')
     ORDER BY table_name, column_name`
  );
  const bad = codes.filter((r) => r.d !== 'varchar');
  console.log(`DIVIPOLA code columns: ${codes.length}, non-VARCHAR: ${bad.length}`);
  if (bad.length) throw new Error('Non-VARCHAR code columns: ' + JSON.stringify(bad));

  await pool.end();
}

main().catch(async (e) => {
  console.error('Migration failed:', e.message);
  try { await pool.end(); } catch (_) { /* ignore */ }
  process.exit(1);
});