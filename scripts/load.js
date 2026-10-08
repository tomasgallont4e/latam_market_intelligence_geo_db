'use strict';
// CLI: node scripts/load.js  — loads data/geodb-v2/csv into MySQL and prints per-table counts.
const pool = require('../db/pool');
const { loadAll, TABLE_ORDER } = require('../lib/loader');

(async () => {
  const t0 = Date.now();
  try {
    const { batchId, rowsLoaded } = await loadAll();
    console.log('\nCOUNT(*) per table after load:');
    for (const t of ['country', ...TABLE_ORDER]) {
      const [[r]] = await pool.query(`SELECT COUNT(*) AS n FROM \`${t}\``);
      console.log(`  ${t.padEnd(30)} ${String(r.n).padStart(6)}`);
    }
    const [[bog]] = await pool.query(
      "SELECT municipality_code, name, ST_Latitude(point) AS lat, ST_Longitude(point) AS lon FROM geo_municipality WHERE municipality_code = '11001'");
    console.log(`\nAxis check Bogotá ${bog.municipality_code} ${bog.name}: lat=${bog.lat} lon=${bog.lon}`);
    const [[b]] = await pool.query('SELECT id, status, rows_loaded, started_at, finished_at FROM load_batch WHERE id = ?', [batchId]);
    console.log(`load_batch #${b.id} status=${b.status} rows_loaded=${b.rows_loaded} ${b.started_at} → ${b.finished_at}`);
    console.log(`Done in ${Date.now() - t0} ms (${rowsLoaded} rows).`);
    await pool.end();
    process.exit(0);
  } catch (err) {
    console.error(`LOAD FAILED${err.batchId ? ' (batch #' + err.batchId + ')' : ''}: ${err.message}`);
    await pool.end().catch(() => {});
    process.exit(1);
  }
})();