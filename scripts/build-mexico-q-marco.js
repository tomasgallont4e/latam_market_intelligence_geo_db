'use strict';
// Layer Q (Mexico): state and municipal boundaries from INEGI Marco Geoestadístico (00ent / 00mun).
// The source is projected (Mexico ITRF2008 LCC, metres); this converts it to WGS84 lon/lat with the
// inverse Lambert Conformal Conic (2SP) read from the .prj, simplifies each ring like the Peru IGN
// boundaries (Douglas–Peucker, scripts/convert-peru-departments.js) and writes the Colombia-shaped
// geo_department_shape / geo_municipality_shape tables. ITRF2008 is treated as WGS84 (sub-metre
// difference, below the simplification tolerance).
// Usage: node scripts/build-mexico-q-marco.js <raw_dir> [tolerance_degrees=0.003]
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const { parse } = require('csv-parse/sync');

const [rawDir, toleranceArg] = process.argv.slice(2);
if (!rawDir) throw new Error('Usage: node scripts/build-mexico-q-marco.js <raw_dir> [tolerance_degrees]');
const TOLERANCE = Number(toleranceArg || 0.003);
const DECIMALS = 5;
const ROOT = path.join(__dirname, '..');
const CSV_DIR = path.join(ROOT, 'data', 'mexico', 'geodb', 'csv');
const LAYER_DIR = path.join(ROOT, 'data', 'mexico', 'outputs');
const MX_BBOX = { west: -119, east: -86, south: 14, north: 33 };

// ───────────── Projection: inverse LCC 2SP (EPSG method 9802) from the .prj ─────────────
function lccFromPrj(file) {
  const wkt = fs.readFileSync(file, 'utf8');
  if (!/PROJECTION\["Lambert_Conformal_Conic"\]/.test(wkt)) throw new Error(`Unexpected projection in ${file}`);
  const param = (name) => {
    const m = new RegExp(`PARAMETER\\["${name}",(-?[\\d.]+)\\]`).exec(wkt);
    if (!m) throw new Error(`Missing ${name} in ${file}`);
    return Number(m[1]);
  };
  const sph = /SPHEROID\["[^"]+",([\d.]+),([\d.]+)\]/.exec(wkt);
  const rad = Math.PI / 180;
  const a = Number(sph[1]); const f = 1 / Number(sph[2]); const e = Math.sqrt((2 * f) - (f * f));
  const lat1 = param('Standard_Parallel_1') * rad; const lat2 = param('Standard_Parallel_2') * rad;
  const lat0 = param('Latitude_Of_Origin') * rad; const lon0 = param('Central_Meridian') * rad;
  const FE = param('False_Easting'); const FN = param('False_Northing');
  const m = (p) => Math.cos(p) / Math.sqrt(1 - (e * e * Math.sin(p) ** 2));
  const t = (p) => Math.tan((Math.PI / 4) - (p / 2)) / (((1 - (e * Math.sin(p))) / (1 + (e * Math.sin(p)))) ** (e / 2));
  const n = (Math.log(m(lat1)) - Math.log(m(lat2))) / (Math.log(t(lat1)) - Math.log(t(lat2)));
  const F = m(lat1) / (n * (t(lat1) ** n));
  const r0 = a * F * (t(lat0) ** n);
  return {
    wkt,
    inverse([x, y]) {
      const dx = x - FE; const dy = r0 - (y - FN);
      const r = Math.sign(n) * Math.sqrt((dx * dx) + (dy * dy));
      const tp = (r / (a * F)) ** (1 / n);
      const theta = Math.atan2(dx, dy);
      let lat = (Math.PI / 2) - (2 * Math.atan(tp));
      for (let i = 0; i < 10; i += 1) {
        const s = e * Math.sin(lat);
        lat = (Math.PI / 2) - (2 * Math.atan(tp * (((1 - s) / (1 + s)) ** (e / 2))));
      }
      return [(theta / n + lon0) / rad, lat / rad];
    },
  };
}

// ───────────── DBF / SHP readers (as in convert-peru-departments.js; DBF is UTF-8 per .cpg) ─────────────
function readDbf(file) {
  const bytes = fs.readFileSync(file);
  const decode = new TextDecoder('utf-8');
  const count = bytes.readUInt32LE(4); const headerLength = bytes.readUInt16LE(8); const recordLength = bytes.readUInt16LE(10);
  const fields = [];
  for (let offset = 32; bytes[offset] !== 0x0d; offset += 32) {
    fields.push({ name: bytes.toString('ascii', offset, offset + 11).replace(/\0/g, '').trim(), length: bytes[offset + 16] });
  }
  const rows = [];
  for (let index = 0; index < count; index += 1) {
    let cursor = headerLength + (index * recordLength);
    if (bytes[cursor] === 0x2a) continue;
    cursor += 1;
    const row = {};
    for (const field of fields) {
      row[field.name] = decode.decode(bytes.subarray(cursor, cursor + field.length)).replace(/\0/g, '').trim();
      cursor += field.length;
    }
    rows.push(row);
  }
  return rows;
}

function readShpRings(file) {
  const bytes = fs.readFileSync(file);
  const shapes = [];
  for (let offset = 100; offset < bytes.length;) {
    const start = offset + 8;
    const end = start + (bytes.readUInt32BE(offset + 4) * 2);
    const shapeType = bytes.readInt32LE(start);
    if ([5, 15, 25].includes(shapeType)) {
      const partsCount = bytes.readInt32LE(start + 36); const pointsCount = bytes.readInt32LE(start + 40);
      const partsStart = start + 44; const pointsStart = partsStart + (partsCount * 4);
      const starts = Array.from({ length: partsCount }, (_, i) => bytes.readInt32LE(partsStart + (i * 4)));
      const points = Array.from({ length: pointsCount }, (_, i) => [bytes.readDoubleLE(pointsStart + (i * 16)), bytes.readDoubleLE(pointsStart + (i * 16) + 8)]);
      shapes.push(starts.map((part, i) => points.slice(part, starts[i + 1] || points.length)));
    } else {
      shapes.push(null);
    }
    offset = end;
  }
  return shapes;
}

// ───────────── Geometry helpers ─────────────
function signedArea(ring) {
  let area = 0;
  for (let i = 0; i < ring.length - 1; i += 1) area += (ring[i][0] * ring[i + 1][1]) - (ring[i + 1][0] * ring[i][1]);
  return area / 2;
}

function squaredSegmentDistance(point, first, last) {
  let x = first[0]; let y = first[1];
  let dx = last[0] - x; let dy = last[1] - y;
  if (dx || dy) {
    const t = ((point[0] - x) * dx + (point[1] - y) * dy) / ((dx * dx) + (dy * dy));
    if (t > 1) { x = last[0]; y = last[1]; } else if (t > 0) { x += dx * t; y += dy * t; }
  }
  dx = point[0] - x; dy = point[1] - y;
  return (dx * dx) + (dy * dy);
}

function simplifyRing(ring, tolerance) {
  if (ring.length <= 4) return ring;
  const points = ring.slice(0, -1);
  const sqTolerance = tolerance * tolerance;
  const keep = new Uint8Array(points.length);
  keep[0] = 1; keep[points.length - 1] = 1;
  const stack = [[0, points.length - 1]];
  while (stack.length) {
    const [first, last] = stack.pop();
    let maxDistance = sqTolerance; let index = -1;
    for (let i = first + 1; i < last; i += 1) {
      const distance = squaredSegmentDistance(points[i], points[first], points[last]);
      if (distance > maxDistance) { index = i; maxDistance = distance; }
    }
    if (index !== -1) { keep[index] = 1; stack.push([first, index], [index, last]); }
  }
  const result = points.filter((_, i) => keep[i]);
  result.push(result[0]);
  return result;
}

const round = (p) => [Number(p[0].toFixed(DECIMALS)), Number(p[1].toFixed(DECIMALS))];

// Shapefile outer rings are clockwise, holes counter-clockwise. GeoJSON (RFC 7946): outer CCW, holes CW.
// Rings that collapse below 4 positions after simplification (islets narrower than the tolerance) are
// dropped; if every ring of a feature would vanish, its largest ring is kept unsimplified.
function toMultiPolygon(projectedRings, proj, stats) {
  const lonlat = projectedRings.map((ring) => ring.map(proj.inverse));
  const polygons = [];
  let outer = null;
  lonlat.forEach((raw) => {
    const ring = simplifyRing(raw, TOLERANCE).map(round);
    const clockwise = signedArea(raw) < 0;
    if (ring.length < 4 || signedArea(ring) === 0) { stats.dropped_rings += 1; if (clockwise) outer = null; return; }
    if (clockwise || !outer) {
      outer = [clockwise ? ring.slice().reverse() : ring];
      polygons.push(outer);
    } else {
      outer.push(ring.slice().reverse());
    }
  });
  if (!polygons.length) {
    const largest = lonlat.reduce((best, ring) => (Math.abs(signedArea(ring)) > Math.abs(signedArea(best)) ? ring : best));
    const ring = largest.map(round);
    polygons.push([signedArea(ring) < 0 ? ring.slice().reverse() : ring]);
    stats.kept_unsimplified += 1;
  }
  return { type: 'MultiPolygon', coordinates: polygons };
}

function pointInRing([x, y], ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, yi] = ring[i]; const [xj, yj] = ring[j];
    if (((yi > y) !== (yj > y)) && (x < ((xj - xi) * (y - yi)) / (yj - yi) + xi)) inside = !inside;
  }
  return inside;
}
const pointInMultiPolygon = (pt, mp) => mp.coordinates.some(([outer, ...holes]) => pointInRing(pt, outer) && !holes.some((h) => pointInRing(pt, h)));

function bounds(geometry) {
  const b = [Infinity, Infinity, -Infinity, -Infinity];
  for (const poly of geometry.coordinates) for (const ring of poly) for (const [x, y] of ring) {
    b[0] = Math.min(b[0], x); b[1] = Math.min(b[1], y); b[2] = Math.max(b[2], x); b[3] = Math.max(b[3], y);
  }
  return b;
}

const sha256 = (file) => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const csvCell = (v) => (/[",\n]/.test(String(v)) ? `"${String(v).replace(/"/g, '""')}"` : String(v));

// ───────────── Build ─────────────
const catalogue = (table) => parse(fs.readFileSync(path.join(CSV_DIR, `${table}.csv`), 'utf8'), { columns: true });
const catStates = new Map(catalogue('geo_department').map((r) => [r.department_code, r]));
const catMunis = new Map(catalogue('geo_municipality').map((r) => [r.municipality_code, r]));

function build(base, codeField, expected) {
  const proj = lccFromPrj(path.join(rawDir, `${base}.prj`));
  const rows = readDbf(path.join(rawDir, `${base}.dbf`));
  const shapes = readShpRings(path.join(rawDir, `${base}.shp`));
  if (rows.length !== shapes.length) throw new Error(`${base}: DBF/SHP mismatch ${rows.length}/${shapes.length}`);
  const stats = { dropped_rings: 0, kept_unsimplified: 0 };
  const features = rows.map((row, i) => {
    if (!shapes[i]) throw new Error(`${base}: record ${i} (${row[codeField]}) is not a polygon`);
    return { code: row[codeField], row, geometry: toMultiPolygon(shapes[i], proj, stats) };
  });
  const errors = [];
  const codes = new Set(features.map((f) => f.code));
  if (features.length !== expected.size || codes.size !== features.length) errors.push(`${base}: ${features.length} features, ${codes.size} unique codes, catalogue has ${expected.size}`);
  for (const code of expected.keys()) if (!codes.has(code)) errors.push(`${base}: catalogue code ${code} has no polygon`);
  for (const f of features) {
    if (!expected.has(f.code)) errors.push(`${base}: polygon ${f.code} is not in the catalogue`);
    const [w, s, e, n] = bounds(f.geometry);
    if (w < MX_BBOX.west || e > MX_BBOX.east || s < MX_BBOX.south || n > MX_BBOX.north) errors.push(`${base}: ${f.code} outside Mexico (${w},${s},${e},${n})`);
  }
  return { features, stats, errors, source: { file: `${base}.shp`, shp_sha256: sha256(path.join(rawDir, `${base}.shp`)), dbf_sha256: sha256(path.join(rawDir, `${base}.dbf`)), crs: proj.wkt.match(/^PROJCS\["([^"]+)"/)[1] } };
}

const states = build('00ent', 'CVE_ENT', catStates);
const munis = build('00mun', 'CVEGEO', catMunis);
const errors = [...states.errors, ...munis.errors];

// Each municipality's own reference point (geo_municipality) should fall inside its polygon.
const munisByCode = new Map(munis.features.map((f) => [f.code, f]));
const outside = [];
for (const [code, m] of catMunis) {
  const f = munisByCode.get(code);
  if (f && m.lat && !pointInMultiPolygon([Number(m.lon), Number(m.lat)], f.geometry)) outside.push(code);
}
// Projection sanity: a gross axis or parameter error would put most points outside; allow a few seat
// points that sit on a simplified border.
if (outside.length > catMunis.size * 0.01) errors.push(`${outside.length} municipal reference points fall outside their own polygon`);
if (errors.length) { console.error(errors.slice(0, 40).join('\n')); process.exit(1); }

function writeTable(table, header, rows) {
  const lines = [header.join(',')].concat(rows.map((r) => header.map((h) => csvCell(r[h])).join(',')));
  fs.writeFileSync(path.join(CSV_DIR, `${table}.csv`), `${lines.join('\n')}\n`);
  return fs.statSync(path.join(CSV_DIR, `${table}.csv`)).size;
}
const deptBytes = writeTable('geo_department_shape', ['department_code', 'name', 'geojson'],
  states.features.sort((a, b) => a.code.localeCompare(b.code)).map((f) => ({ department_code: f.code, name: catStates.get(f.code).name, geojson: JSON.stringify(f.geometry) })));
const muniBytes = writeTable('geo_municipality_shape', ['municipality_code', 'department_code', 'name', 'geojson'],
  munis.features.sort((a, b) => a.code.localeCompare(b.code)).map((f) => ({ municipality_code: f.code, department_code: f.code.slice(0, 2), name: catMunis.get(f.code).name, geojson: JSON.stringify(f.geometry) })));

const nameDiffs = munis.features.filter((f) => f.row.NOMGEO !== catMunis.get(f.code).name).map((f) => ({ code: f.code, marco: f.row.NOMGEO, catalogue: catMunis.get(f.code).name }));
const layerFile = path.join(LAYER_DIR, 'layer_q_mx.json');
const layer = JSON.parse(fs.readFileSync(layerFile, 'utf8'));
layer.boundaries = {
  source_id: 'INEGI_MARCO_GEOESTADISTICO',
  sources: { states: states.source, municipalities: munis.source },
  output_crs: 'WGS 84 (EPSG:4326), lon/lat; ITRF2008 treated as WGS84',
  simplification: { method: 'Douglas–Peucker per ring', tolerance_degrees: TOLERANCE, decimals: DECIMALS },
  counts: { states: states.features.length, municipalities: munis.features.length },
  dropped_rings: { states: states.stats.dropped_rings, municipalities: munis.stats.dropped_rings },
  kept_unsimplified: { states: states.stats.kept_unsimplified, municipalities: munis.stats.kept_unsimplified },
  reference_points_outside_own_polygon: outside,
  name_differences_with_catalogue: nameDiffs,
  limitations: 'Web-display boundaries: simplified ring by ring, so neighbouring borders can show small gaps or overlaps. Islets narrower than the tolerance are dropped. Not for area or distance measurement.',
};
fs.writeFileSync(layerFile, `${JSON.stringify(layer, null, 2)}\n`);
console.log(JSON.stringify({ tolerance: TOLERANCE, states: states.features.length, municipalities: munis.features.length,
  dropped_rings: layer.boundaries.dropped_rings, kept_unsimplified: layer.boundaries.kept_unsimplified,
  points_outside: outside.length, name_diffs: nameDiffs.length, bytes: { geo_department_shape: deptBytes, geo_municipality_shape: muniBytes } }));
