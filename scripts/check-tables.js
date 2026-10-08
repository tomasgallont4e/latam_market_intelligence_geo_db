'use strict';
const pool = require('../db/pool');
const { listTables, tableRows } = require('../lib/tables');

(async () => {
  const l = await listTables();
  console.log('totals', JSON.stringify(l.totals));
  for (const t of l.tables) console.log(t.table_name.padEnd(30), String(t.rows).padStart(8), t.has_geo ? 'geo ' + t.geo_level : 'sin geografía', '|', t.year);
  const tests = [
    ['fact_companies_zone', 1, 'BOG-00'],
    ['fact_persona_metro', 1, 'Rest'],
    ['geo_municipality', 1, '27493'],
    ['geo_zone', 1, ''],
    ['geo_zone', 2, ''],
    ['geo_department', 1, '11'],
    ['fact_ict_by_sector', 1, ''],
  ];
  for (const [t, p, s] of tests) {
    const r = await tableRows(t, p, s);
    const ex = r.rows.find((x) => x.__is_exception);
    console.log(`${t} p${p} q='${s}': total=${r.total} pages=${r.pages} rows=${r.rows.length} exc=${r.exceptions_on_page}`, ex ? ex.__exception_reason : '');
    const gcol = r.columns.find((c) => c.kind === 'geom');
    if (gcol) { const g = r.rows.find((x) => x[gcol.name]); console.log('  geom sample', gcol.name, g ? g[gcol.name] : null); }
  }
  for (const bad of ['meta_sources; DROP TABLE x', 'nope_table', '../x']) {
    try { await tableRows(bad, 1, ''); console.log('UNEXPECTED OK', bad); }
    catch (e) { console.log('rejected', JSON.stringify(bad), e.status, e.message); }
  }
  const inj = await tableRows('geo_department', 1, "x' OR '1'='1");
  console.log('injection-like search total =', inj.total);
  await pool.end();
})().catch(async (e) => { console.error(e); await pool.end(); process.exit(1); });