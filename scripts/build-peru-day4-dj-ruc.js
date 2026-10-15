'use strict';
// Day 4 reproducible D/J partial: active SUNAT RUC with TIC CIIU activities.
const fs = require('fs'), path = require('path');
const root = path.join(__dirname, '..');
const source = require(path.join(root, 'data', 'peru-map', 'fact_ruc_tic_district_202604.json'));
const activity = ['ciiu_6201', 'ciiu_6202', 'ciiu_6209', 'ciiu_6311', 'ciiu_6312'];
const byDepartment = new Map();
for (const r of source.districts) {
  const key = String(r.ubigeo).slice(0, 2);
  const current = byDepartment.get(key) || { department_code: key, department: r.department, active_ruc_tic: 0, districts_with_activity: 0, ...Object.fromEntries(activity.map((x) => [x, 0])) };
  current.active_ruc_tic += Number(r.active_ruc_tic) || 0;
  if (Number(r.active_ruc_tic) > 0) current.districts_with_activity++;
  for (const a of activity) current[a] += Number(r[a]) || 0;
  byDepartment.set(key, current);
}
const departments = [...byDepartment.values()].filter((x) => x.department !== 'NO DISPONIBLE').sort((a,b) => a.department_code.localeCompare(b.department_code));
const country = departments.reduce((a, x) => { a.active_ruc_tic += x.active_ruc_tic; for (const k of activity) a[k] += x[k]; return a; }, { active_ruc_tic: 0, ...Object.fromEntries(activity.map((x) => [x, 0])) });
const out = path.join(root, 'data', 'peru', 'day4_dj_ruc'); fs.mkdirSync(out, { recursive: true });
const metadata = { country: 'PE', period: source.source.period, source_id: source.source.source_id, universe: 'Active RUC with CIIU 6201, 6202, 6209, 6311 or 6312; fiscal UBIGEO', country_totals: country, department_rows: departments.length, district_rows: source.districts.length, limitations: 'RUC records are legal/tax registrations. They do not establish employment, revenue, firm size, physical operating location, buyers, or commercial zones.' };
fs.writeFileSync(path.join(out, 'd_tic_ruc_by_department_202604.json'), JSON.stringify(departments, null, 2));
fs.writeFileSync(path.join(out, 'j_tic_ruc_by_district_202604.json'), JSON.stringify(source.districts, null, 2));
fs.writeFileSync(path.join(out, 'metadata.json'), JSON.stringify(metadata, null, 2));
fs.writeFileSync(path.join(out, 'README.md'), '# Perú · Día 4 · D/J parcial\n\nAgregados del padrón RUC SUNAT entregado (abril de 2026). D cubre RUC TIC activos por departamento; J preserva la geografía distrital fiscal. No mide empleo, tamaño, ventas, demanda ni zonas comerciales, por lo que M/N y los indicadores de tamaño de J permanecen pendientes.\n');
console.log(JSON.stringify(metadata));
