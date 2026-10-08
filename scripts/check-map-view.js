// Static check of the Mapa page: parse JS, verify required calls/constants and quintile logic.
'use strict';
const fs = require('fs');
const path = require('path');
const vm = require('vm');

const root = path.join(__dirname, '..');
const js = fs.readFileSync(path.join(root, 'public/js/map_view.js'), 'utf8');
const shim = fs.readFileSync(path.join(root, 'public/js/pages/map_view.js'), 'utf8');
const html = fs.readFileSync(path.join(root, 'public/pages/map_view.html'), 'utf8');
new vm.Script(js, { filename: 'map_view.js' });
new vm.Script(shim, { filename: 'pages/map_view.js' });

const must = ['api/map/departments', 'api/map/municipalities', 'api/map/localidades', 'api/personas',
  '#E9EEF7', '#B9C7E3', '#7F98C9', '#3F5E9E', '#11255A', '#DDDDDD', 'computeQuintiles', 'bindTooltip',
  'renderPlace', 'invalidateSize', 'n.a.', 'Haga clic en un lugar del mapa', 'filtro por persona no disponible en esta capa',
  "load_page('compare_view')".replace("'compare_view'", "('compare_view')").slice(0, 0) || 'compare_view', 'fitBounds', '27493'];
const missing = must.filter((m) => !js.includes(m));
const htmlMust = ['map-panel', 'map-canvas', 'id="map"', 'role="radiogroup"', 'aria-live="polite"', 'place-card', 'map-foot'];
const htmlMissing = htmlMust.filter((m) => !html.includes(m));
if (/fetch\(\s*['"]\//.test(js) || /api\(\s*['"]\//.test(js)) missing.push('absolute URL found');

// quintile logic
const sandbox = { window: {}, Intl, console };
vm.runInNewContext(js, sandbox);
const mv = sandbox.window.T4EMapView;
const q = mv._computeQuintiles([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, null]);
const classes = [1, 3, 5, 7, 10].map((v) => mv._classOf(q, v));
console.log('quintiles', JSON.stringify(q), 'classes', classes, 'null ->', mv._classOf(q, null));

console.log('missing in js:', missing);
console.log('missing in html:', htmlMissing);
process.exit(missing.length || htmlMissing.length ? 1 : 0);