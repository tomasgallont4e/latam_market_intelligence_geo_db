'use strict';
// Aggregate the public MINEDU 2026 padron into an offer indicator.  This is
// institutional supply, not enrolment and not an ICT-programme count.
const fs = require('fs');
const path = require('path');
const root = path.join(__dirname, '..');
const input = JSON.parse(fs.readFileSync(path.join(root, 'data', 'peru', 'padron_20260918', 'padron_offer_by_department_level_20260918.json'), 'utf8'));
const levelCodes = new Set(['K0', 'M0', 'P0', 'S0', 'T0']);
const groups = new Map();
for (const row of input) {
  if (!levelCodes.has(row.level_code)) continue;
  const key = String(row.department).trim().toUpperCase();
  const value = groups.get(key) || { department: key, higher_nonuniversity_services: 0, active_higher_nonuniversity_services: 0, public_services: 0, private_services: 0, levels: {} };
  value.higher_nonuniversity_services += Number(row.services) || 0;
  value.active_higher_nonuniversity_services += Number(row.active_services) || 0;
  value.public_services += Number(row.public_services) || 0;
  value.private_services += Number(row.private_services) || 0;
  value.levels[row.level_code] = { name: row.level_name, services: Number(row.services) || 0, active_services: Number(row.active_services) || 0 };
  groups.set(key, value);
}
const rows = [...groups.values()].sort((a, b) => a.department.localeCompare(b.department, 'es')).map((row) => ({
  ...row, reference_date: '2026-09-18', source: 'MINEDU Padron web 20260918',
  scope: 'institutional_offer_not_enrollment',
  caveat: 'Includes K0, M0, P0, S0 and T0 only. Excludes universities and does not identify programme field, entrants, modality or ICT education.'
}));
const metadata = { country: 'PE', source: 'MINEDU Padron web 20260918', reference_date: '2026-09-18', level_codes: [...levelCodes], departments: rows.length, scope: 'institutional_offer_not_enrollment', caveat: rows[0]?.caveat };
const out = path.join(root, 'data', 'peru', 'day3_higher_education_offer'); fs.mkdirSync(out, { recursive: true });
fs.writeFileSync(path.join(out, 'metadata.json'), JSON.stringify(metadata, null, 2));
fs.writeFileSync(path.join(out, 'higher_nonuniversity_offer_by_department_20260918.json'), JSON.stringify(rows, null, 2));
console.log(JSON.stringify(metadata));
