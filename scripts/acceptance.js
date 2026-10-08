'use strict';
// CLI: node scripts/acceptance.js [batchId] — runs flow_validation on the latest
// (or given) load_batch and prints the acceptance totals table + axis test.
const pool = require('../db/pool');
const { validateBatch } = require('../lib/validation');

const fmt = (n) => {
  if (n === null || n === undefined) return '—';
  if (typeof n !== 'number') return String(n);
  const neg = n < 0; const s = String(Math.abs(Math.round(n))).replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return (neg ? '-' : '') + s;
};
const pad = (s, w, right) => (right ? String(s).padStart(w) : String(s).padEnd(w));

(async () => {
  try {
    const arg = process.argv[2] ? Number(process.argv[2]) : null;
    const r = await validateBatch(arg);
    const line = '─'.repeat(128);
    console.log(`\nPANEL DE ACEPTACIÓN — load_batch #${r.batchId}\n${line}`);
    console.log(pad('Tabla', 28) + pad('Comprobación', 44) + pad('Esperado', 12, 1) + pad('Real', 12, 1) + '  ' + pad('Tol.', 16) + pad('Dif.', 8, 1) + '  Estado');
    let group = null;
    for (const c of r.checks) {
      if (c.group !== group) {
        group = c.group;
        console.log(line + `\n${group === 'v1' ? 'TOTALES DE CARGA (v1)' : 'INTEGRIDAD GEOGRÁFICA (v2)'}`);
      }
      console.log(pad(c.table, 28) + pad(c.label.slice(0, 43), 44) + pad(fmt(c.expected), 12, 1) + pad(fmt(c.actual), 12, 1)
        + '  ' + pad(c.tolLabel, 16) + pad(fmt(c.difference), 8, 1) + '  ' + (c.ok ? 'OK' : 'FALLA'));
      for (const s of c.sub || []) {
        console.log(pad('', 4) + pad(`↳ ${s.label}`.slice(0, 68), 68) + pad(fmt(s.expected), 12, 1) + pad(fmt(s.actual), 12, 1)
          + '  ' + pad(s.maxPerPersona !== undefined ? `máx/persona ${s.maxPerPersona}` : '', 16) + pad(fmt(s.difference), 8, 1)
          + '  ' + (s.ok ? 'ok' : 'falla') + (s.codes ? `  [${s.codes.slice(0, 10).join(', ')}]` : ''));
      }
      if (c.detail) console.log(pad('', 4) + `· ${c.detail}`);
    }
    const a = r.axis;
    console.log(`${line}\nPRUEBA DE EJE — Bogotá (rule_axis_order)`);
    console.log(`  ${a.sql || ''}`);
    console.log(`  esperado lat ${a.expected.lat} / lon ${a.expected.lon} (±${a.expected.tolerance})`);
    console.log(`  real     ${a.actual ? `lat ${a.actual.lat.toFixed(6)} / lon ${a.actual.lon.toFixed(6)} (SRID ${a.actual.srid})` : '—'}  → ${a.ok ? 'OK' : 'FALLA'}`);
    console.log(`${line}\nEXCEPCIONES APROBADAS (severity info, no_geography_exception)`);
    for (const e of r.exceptions) console.log(`  · ${e.table}.${e.column} = ${e.code}: ${e.n} filas — ${e.message}`);
    if (r.missingSources.length) console.log(`  ! Sin fuente/año en meta_sources: ${r.missingSources.join(', ')}`);
    console.log(`${line}\nResultado: ${r.passed}/${r.total} comprobaciones superadas · eje ${a.ok ? 'OK' : 'FALLA'} · ${r.errors} errores · ${r.infos} excepciones`);
    console.log(`load_batch #${r.batchId} → status = ${r.status}`);
    await pool.end();
    process.exit(0);
  } catch (e) {
    console.error('ACCEPTANCE FAILED:', e.stack || e.message);
    await pool.end().catch(() => {});
    process.exit(1);
  }
})();