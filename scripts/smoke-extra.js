'use strict';
const http = require('http');
const port = process.env.PROBE_PORT || process.argv[2] || '45051';
const get = (p) => new Promise((r) => http.get({ host: '127.0.0.1', port, path: p }, (res) => { let b = ''; res.on('data', (c) => (b += c)); res.on('end', () => r({ s: res.statusCode, b })); }).on('error', (e) => r({ s: 0, b: e.message })));
(async () => {
  const r = await get('/v1/tables/geo_municipality/rows?q=05001');
  const j = JSON.parse(r.b); const rows = j.rows || j;
  const row = rows.find((x) => x.municipality_code === '05001');
  console.log('05001:', r.s, JSON.stringify(row).slice(0, 200));
  const l = JSON.parse((await get('/api/map/localidades')).b);
  const f = (l.features || [])[0];
  console.log('localidad sample:', JSON.stringify(f && f.properties).slice(0, 300));
  const t = JSON.parse((await get('/v1/tables')).b);
  const cz = t.tables.find((x) => x.table_name === 'fact_companies_zone');
  console.log('fact_companies_zone year:', JSON.stringify(cz && cz.year));
  process.exit(row && row.department_code === '05' ? 0 : 1);
})();