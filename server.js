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
});