// One-shot probe: hits the running service and checks DB connectivity.
// Usage: PROBE_PORT=<port> node scripts/probe-boot.js
const http = require('http');
const port = process.env.PROBE_PORT || process.argv[2] || '45051';
const paths = ['/', '/health', '/v1/acceptance', '/v1/tables', '/v1/batches/latest', '/api/map/departments'];

function get(p) {
  return new Promise((resolve) => {
    http.get({ host: '127.0.0.1', port, path: p, timeout: 15000 }, (res) => {
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => resolve({ p, status: res.statusCode, len: body.length, head: body.slice(0, 160) }));
    }).on('error', (e) => resolve({ p, error: e.message }));
  });
}

(async () => {
  let failed = false;
  for (const p of paths) {
    const r = await get(p);
    console.log(JSON.stringify(r));
    if (r.error || r.status >= 500) failed = true;
  }
  try {
    const mysql = require('mysql2/promise');
    const conn = await mysql.createConnection({
      host: process.env.DB_HOST, port: Number(process.env.DB_PORT || 3306),
      user: process.env.DB_USER, password: process.env.DB_PASSWORD, database: process.env.DB_NAME,
    });
    const [rows] = await conn.query('SELECT COUNT(*) AS n FROM geo_municipality');
    console.log('DB ok, geo_municipality rows =', rows[0].n);
    await conn.end();
  } catch (e) {
    console.log('DB error:', e.message);
    failed = true;
  }
  process.exit(failed ? 1 : 0);
})();