'use strict';
require('dotenv').config();

const path = require('path');
const express = require('express');

const app = express();
app.use(express.json());

// Static frontend served at "/" (proxy strips /run/<projectId> prefix).
app.use(express.static(path.join(__dirname, 'public')));

const mapData = require('./lib/mapData');
const mapRoutes = require('./routes/map');

async function health(req, res) {
  const h = await mapData.getHealth();
  res.status(h.status === 'ok' ? 200 : 503).json(h);
}
app.get('/health', health);
app.get('/api/health', health);

app.use(mapRoutes);
app.use(require('./routes/v1'));

const PORT = process.env.PORT;
if (!PORT) {
  console.error('PORT env var not set; the runtime must inject it.');
  process.exit(1);
}
app.listen(PORT, () => {
  console.log(`Geo DB Colombia listening on port ${PORT}`);
  if (process.env.RELOAD_ON_BOOT === '1') reloadOnBoot();
});

// One-off reload inside the service (which has the DB_* vars). Same loader +
// validation as POST /v1/load. Errors are logged; the server keeps running.
async function reloadOnBoot() {
  const t0 = Date.now();
  console.log('[reload-on-boot] RELOAD_ON_BOOT=1 → running loadAll()');
  try {
    const { loadAll } = require('./lib/loader');
    const r = await loadAll({ log: (m) => console.log('[reload-on-boot]', String(m)) });
    const v = r.validation;
    console.log(`[reload-on-boot] DONE batch #${r.batchId} rows=${r.rowsLoaded} `
      + (v ? `validation=${v.status} errors=${v.errors} passed=${v.passed}/${v.total}` : 'validation=skipped')
      + ` in ${Date.now() - t0} ms`);
  } catch (e) {
    console.error(`[reload-on-boot] FAILED${e.batchId ? ' (batch #' + e.batchId + ')' : ''}: ${e.message}`);
  }
}