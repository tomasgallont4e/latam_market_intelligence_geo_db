'use strict';
// Smoke check for routes/v1.js on an ephemeral port (not the service port).
const express = require('express');
const http = require('http');
const pool = require('../db/pool');

const app = express();
app.use(express.json());
app.use(require('../routes/v1'));

function req(server, method, path) {
  return new Promise((resolve, reject) => {
    const { port } = server.address();
    const r = http.request({ host: '127.0.0.1', port, method, path, headers: { 'Content-Type': 'application/json' } }, (res) => {
      let b = '';
      res.on('data', (c) => { b += c; });
      res.on('end', () => { try { resolve({ status: res.statusCode, body: JSON.parse(b) }); } catch (e) { reject(new Error(b.slice(0, 300))); } });
    });
    r.on('error', reject);
    if (method === 'POST') r.write('{}');
    r.end();
  });
}

const server = app.listen(0, async () => {
  let fail = 0;
  try {
    const v = await req(server, 'POST', '/v1/validate');
    console.log('POST /v1/validate', v.status, JSON.stringify(v.body));
    if (v.status !== 200) fail++;
    const a = await req(server, 'GET', '/v1/acceptance');
    console.log('GET /v1/acceptance', a.status, `passed ${a.body.passed}/${a.body.total} all_green=${a.body.all_green} axis=${a.body.axis_test && a.body.axis_test.ok}`);
    for (const c of a.body.checks || []) console.log(`   ${c.ok ? 'OK   ' : 'FALLA'} ${c.group} ${c.table} — ${c.label}: ${c.expected} vs ${c.actual}`);
    if (a.status !== 200) fail++;
    const b = await req(server, 'GET', '/v1/batches/latest');
    console.log('GET /v1/batches/latest', b.status, JSON.stringify({ id: b.body.id, status: b.body.status, rows: b.body.rows_loaded, errors: b.body.errors, infos: b.body.infos }));
    if (b.status !== 200) fail++;
    const i = await req(server, 'GET', '/v1/issues?severity=info');
    console.log('GET /v1/issues?severity=info', i.status, i.body.counts, i.body.issues && i.body.issues.length);
    if (i.status !== 200) fail++;
    const bad = await req(server, 'GET', '/v1/issues?severity=x');
    console.log('GET /v1/issues?severity=x', bad.status);
    if (bad.status !== 400) fail++;
  } catch (e) {
    console.error('ERROR', e.message); fail++;
  }
  server.close();
  await pool.end().catch(() => {});
  console.log(fail ? `FAILED (${fail})` : 'ALL OK');
  process.exit(fail ? 1 : 0);
});