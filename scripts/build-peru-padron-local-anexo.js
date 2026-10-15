'use strict';
// Produces aggregate-only geography from SUNAT's public "Padrón reducido local anexo".
// The input is pipe-delimited and intentionally never copied to the repository: it
// contains individual RUC/address records. This builder only writes geographic counts.
const fs = require('fs');
const path = require('path');

const [inputFile, outDir] = process.argv.slice(2);
if (!inputFile || !outDir) {
  console.error('Usage: node scripts/build-peru-padron-local-anexo.js <padron_reducido_local_anexo.txt> <output-directory>');
  process.exit(1);
}
const content = fs.readFileSync(inputFile, 'latin1');
const lines = content.split(/\r?\n/);
const header = lines.shift().replace(/^\uFEFF/, '').split('|').map((value) => value.trim().toUpperCase());
const rucIndex = header.indexOf('RUC');
const ubigeoIndex = header.indexOf('UBIGEO');
if (rucIndex < 0 || ubigeoIndex < 0) throw new Error(`Expected RUC and UBIGEO headers; received: ${header.join(', ')}`);

const departments = new Map();
const districts = new Map();
let sourceRows = 0;
let acceptedRows = 0;
for (const line of lines) {
  if (!line.trim()) continue;
  sourceRows += 1;
  const values = line.split('|');
  const ruc = String(values[rucIndex] || '').trim();
  const ubigeo = String(values[ubigeoIndex] || '').trim();
  if (!/^\d{11}$/.test(ruc) || !/^\d{6}$/.test(ubigeo)) continue;
  acceptedRows += 1;
  const departmentCode = ubigeo.slice(0, 2);
  departments.set(departmentCode, (departments.get(departmentCode) || 0) + 1);
  districts.set(ubigeo, (districts.get(ubigeo) || 0) + 1);
}

const byDepartment = [...departments.entries()].sort().map(([department_code, registered_local_addresses]) => ({ department_code, registered_local_addresses }));
const byDistrict = [...districts.entries()].sort().map(([ubigeo, registered_local_addresses]) => ({ ubigeo, department_code: ubigeo.slice(0, 2), registered_local_addresses }));
const metadata = {
  country: 'PE', source: 'SUNAT Padrón reducido local anexo',
  scope: 'Public RUC locations with a valid UBIGEO; aggregate only',
  indicator: 'registered_local_addresses',
  caveat: 'This is a count of registered local-address records, not active firms, not unique firms, and not an ICT classification. The source has no CIIU/activity, status, legal form or size fields.',
  source_rows: sourceRows, accepted_rows: acceptedRows,
  departments: byDepartment.length, districts: byDistrict.length,
  generated_at: new Date().toISOString()
};
fs.mkdirSync(outDir, { recursive: true });
fs.writeFileSync(path.join(outDir, 'metadata.json'), JSON.stringify(metadata, null, 2));
fs.writeFileSync(path.join(outDir, 'registered_local_addresses_by_department.json'), JSON.stringify(byDepartment, null, 2));
fs.writeFileSync(path.join(outDir, 'registered_local_addresses_by_district.json'), JSON.stringify(byDistrict, null, 2));
console.log(JSON.stringify(metadata));
