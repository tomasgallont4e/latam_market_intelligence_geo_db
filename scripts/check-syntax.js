'use strict';
const fs = require('fs');
const vm = require('vm');
let bad = 0;
for (const f of ['public/js/table_explorer.js', 'public/js/pages/table_explorer.js', 'lib/tables.js', 'routes/v1.js']) {
  try { new vm.Script(fs.readFileSync(f, 'utf8').replace(/^#!.*/, ''), { filename: f }); console.log('ok', f); }
  catch (e) { bad++; console.log('SYNTAX', f, e.message); }
}
try { require('../routes/v1'); console.log('ok require routes/v1'); } catch (e) { bad++; console.log('REQUIRE FAIL', e.message); }
process.exit(bad ? 1 : 0);