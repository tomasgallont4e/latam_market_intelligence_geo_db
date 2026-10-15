'use strict';
// Reproducible Day-3 partial for Layer L from the already verified MINEDU
// Censo Educativo 2025 district aggregate.  This is intentionally not a
// university or ICT-program estimate.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const input = JSON.parse(fs.readFileSync(path.join(root, 'data', 'peru-map', 'fact_education_padron_district_2025.json'), 'utf8'));
const levels = new Set(['K0', 'L0', 'M0', 'P0', 'S0', 'T0']);
const byDept = new Map();
for (const row of input.filter((x) => levels.has(x.level_code))) {
  const code = String(row.ubigeo).slice(0, 2);
  const key = `${code}|${row.level_code}`;
  const current = byDept.get(key) || { department_code: code, department: row.department, level_code: row.level_code, level_name: row.level_name, services: 0, students: 0, men: 0, women: 0, districts: new Set() };
  current.services += Number(row.services) || 0; current.students += Number(row.students) || 0;
  current.men += Number(row.men) || 0; current.women += Number(row.women) || 0; current.districts.add(String(row.ubigeo));
  byDept.set(key, current);
}
const rows = [...byDept.values()].map((x) => ({ ...x, districts: x.districts.size, reference_year: 2025, source_id: 'MINEDU_CE2025_PADRON', geographic_level: 'department', scope: 'partial_nonuniversity_education', limitation: 'Excludes universities; level codes do not identify ICT field, modality, entrants, or programme.' }));
const out = path.join(root, 'data', 'peru', 'day3_l_partial'); fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'l_nonuniversity_by_department_2025.json'), JSON.stringify(rows, null, 2));
fs.writeFileSync(path.join(out, 'README.md'), '# Perú · Día 3 · capa L parcial\n\nAgregado departamental reproducible del padrón MINEDU/Censo Educativo 2025 para niveles no universitarios K0, L0, M0, P0, S0 y T0. No suma universidades ni identifica programas TIC, modalidad, ingresantes o formación profesional; no representa el total nacional de educación superior.\n');
console.log(JSON.stringify({ inputRows: input.length, outputRows: rows.length, departments: new Set(rows.map((x) => x.department_code)).size }));
