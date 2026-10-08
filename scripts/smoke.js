'use strict';
// Smoke test for the demo. Usage: node scripts/smoke.js [port]
const http = require('http');
const port = process.env.PROBE_PORT || process.argv[2] || '45051';

function get(p) {
  return new Promise((resolve) => {
    http.get({ host: '127.0.0.1', port, path: p, timeout: 30000 }, (res) => {
      let body = '';
      res.on('data', (c) => (body += c));
      res.on('end', () => {
        let json = null;
        try { json = JSON.parse(body); } catch (_) {}
        resolve({ status: res.statusCode, body, json });
      });
    }).on('error', (e) => resolve({ status: 0, error: e.message, body: '' }));
  });
}

const results = [];
function check(name, ok, info) {
  results.push({ name, ok: !!ok });
  console.log(`${ok ? 'PASS' : 'FAIL'} | ${name}${info ? ' | ' + info : ''}`);
}
const keys = (o) => (o && typeof o === 'object' ? Object.keys(o).slice(0, 15).join(',') : String(o));
const feats = (j) => (j && (j.features || (j.geojson && j.geojson.features) || (j.data && j.data.features))) || [];

function firstCoord(g) {
  if (!g) return null;
  let c = g.coordinates;
  while (Array.isArray(c) && Array.isArray(c[0])) c = c[0];
  return c;
}

(async () => {
  // 1. health
  const h = await get('/health');
  console.log('health:', JSON.stringify(h.json).slice(0, 400));
  const hv = h.json || {};
  const ver = String(hv.mysql_version || hv.mysqlVersion || hv.version || (hv.db && hv.db.version) || '');
  const axis = hv.axis_check_ok ?? (hv.axis_check && hv.axis_check.ok) ?? hv.axisCheckOk;
  check('/health axis_check_ok=true & MySQL>=8', h.status === 200 && axis === true && parseFloat(ver) >= 8, `version=${ver} axis=${axis}`);

  // 2. departments
  const d = await get('/api/map/departments');
  const df = feats(d.json);
  console.log('departments keys:', keys(d.json), '| feature props:', df[0] && keys(df[0].properties));
  const c = firstCoord(df[0] && df[0].geometry);
  const lonlat = c && c[0] < -60 && c[0] > -82 && c[1] > -5 && c[1] < 14;
  const dj = JSON.stringify(d.json || {});
  const hasSrc = /"source/.test(dj) && /"year"/.test(dj);
  check('/api/map/departments 33 features [lon,lat] + source/year', d.status === 200 && df.length === 33 && lonlat && hasSrc, `n=${df.length} coord=${JSON.stringify(c)} srcYear=${hasSrc}`);

  // 3. persona filter
  const pr = await get('/api/personas');
  const plist = Array.isArray(pr.json) ? pr.json : (pr.json && (pr.json.personas || pr.json.items || pr.json.data)) || [];
  const p0 = plist[0] && (typeof plist[0] === 'string' ? plist[0] : plist[0].persona || plist[0].name);
  const dp = await get('/api/map/departments?persona=' + encodeURIComponent(p0 || ''));
  const changed = dp.status === 200 && JSON.stringify(feats(dp.json).map((f) => f.properties)) !== JSON.stringify(df.map((f) => f.properties));
  check('/api/map/departments?persona= changes values', changed, `personas=${plist.length} persona="${p0}"`);

  // 4. municipalities
  const m = await get('/api/map/municipalities');
  const mf = feats(m.json);
  const mlist = mf.length ? mf.map((f) => f.properties || {}) : (Array.isArray(m.json) ? m.json : (m.json && (m.json.cities || m.json.municipalities || m.json.items)) || []);
  console.log('municipalities keys:', keys(m.json), '| item keys:', keys(mlist[0]));
  const codes = mlist.map((x) => String(x.municipality_code || x.code || x.id));
  const withEv = mlist.filter((x) => x.has_event || x.hasEvent || (x.events && x.events.length) || x.event_count > 0);
  check('/api/map/municipalities excludes 27493 + events', m.status === 200 && mlist.length > 0 && !codes.includes('27493') && withEv.length > 0, `n=${mlist.length} withEvents=${withEv.length}`);

  // 5. localidades
  const l = await get('/api/map/localidades');
  const lf = feats(l.json);
  check('/api/map/localidades 20 features', l.status === 200 && lf.length === 20, `n=${lf.length}`);

  // 6. compare
  const cp = await get('/api/compare/places?level=department');
  const places = Array.isArray(cp.json) ? cp.json : (cp.json && (cp.json.places || cp.json.items || cp.json.data)) || [];
  console.log('compare places keys:', keys(cp.json), '| item:', JSON.stringify(places[0]));
  const pid = (x) => x && (x.id || x.code || x.department_code);
  const ids2 = places.slice(0, 2).map(pid).join(',');
  const c2 = await get(`/api/compare?level=department&ids=${ids2}`);
  const c1 = await get(`/api/compare?level=department&ids=${pid(places[0])}`);
  const cmix = await get(`/api/compare?level=department&ids=${pid(places[0])},05001`);
  console.log('compare 2:', c2.status, c2.body.slice(0, 200));
  console.log('compare 1:', c1.status, c1.body.slice(0, 200));
  console.log('compare mixed:', cmix.status, cmix.body.slice(0, 200));
  check('/api/compare 2 deps=200, 1 place=400, mixed=400', c2.status === 200 && c1.status === 400 && cmix.status === 400, `${c2.status}/${c1.status}/${cmix.status}`);

  // 7. acceptance
  const a = await get('/v1/acceptance');
  const checks = Array.isArray(a.json) ? a.json : (a.json && (a.json.checks || a.json.items || a.json.results)) || [];
  console.log('acceptance keys:', keys(a.json), '| check keys:', keys(checks[0]));
  for (const k of checks) {
    const st = k.status || (k.ok === true || k.pass === true ? 'green' : k.ok === false || k.pass === false ? 'red' : '?');
    console.log(`  ACC [${st}] ${k.id || k.key || k.name}: expected=${k.expected} actual=${k.actual}${k.label ? ' — ' + k.label : ''}`);
  }
  const hasEA = checks.length > 0 && checks.every((k) => 'expected' in k && 'actual' in k);
  check('/v1/acceptance checks with expected/actual', a.status === 200 && hasEA, `n=${checks.length}`);

  // 8. tables
  const t = await get('/v1/tables');
  const tl = Array.isArray(t.json) ? t.json : (t.json && (t.json.tables || t.json.items || t.json.data)) || [];
  console.log('tables keys:', keys(t.json), '| item keys:', keys(tl[0]));
  const factGeo = tl.filter((x) => /^(fact_|geo_)/.test(x.table_name || x.name || x.table || ''));
  const rowsOk = tl.every((x) => ('row_count' in x) || ('rows' in x) || ('rowCount' in x));
  const yearOk = tl.every((x) => 'year' in x);
  check('/v1/tables lists 27 tables with rows+year', t.status === 200 && (tl.length === 27 || factGeo.length === 27) && rowsOk && yearOk, `n=${tl.length} fact/geo=${factGeo.length} rows=${rowsOk} year=${yearOk}`);

  // 9. rows with leading zeros
  const r = await get('/v1/tables/geo_municipality/rows?q=BOG');
  const rl = Array.isArray(r.json) ? r.json : (r.json && (r.json.rows || r.json.items || r.json.data)) || [];
  console.log('rows sample:', JSON.stringify(rl.slice(0, 3)).slice(0, 400));
  const rj = JSON.stringify(rl);
  const zeros = /"department_code":"0\d"/.test(rj) || /"municipality_code":"0\d{4}"/.test(rj) || /"11001"/.test(rj);
  const typed = rl.length > 0 && rl.every((x) => typeof x.municipality_code === 'string' && x.municipality_code.length === 5);
  check('/v1/tables/geo_municipality/rows?q=BOG codes as zero-padded strings', r.status === 200 && rl.length > 0 && typed && zeros, `n=${rl.length}`);

  // 10. static
  const i = await get('/');
  const pv = await get('/pages/map_view.html');
  const pj = await get('/js/map_view.js');
  const sidebar = /sidebar|main-sidebar/.test(i.body) && /compare_view/.test(i.body) && /table_explorer/.test(i.body);
  const absUrls = (i.body.match(/(?:src|href)="\/[^/]/g) || []).length;
  check('GET / index.html with sidebar + map_view page/js', i.status === 200 && sidebar && pv.status === 200 && pj.status === 200, `index=${i.status} page=${pv.status} js=${pj.status} absUrlsInIndex=${absUrls}`);

  const failed = results.filter((x) => !x.ok).length;
  console.log(`\nSUMMARY: ${results.length - failed}/${results.length} passed`);
  process.exit(failed ? 1 : 0);
})();