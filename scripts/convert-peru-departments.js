'use strict';
// Minimal SHP/DBF converter for the official WGS84 department boundaries.
// Usage: node scripts/convert-peru-departments.js <source-dir> <output-file> [DEPARTAMENTOS|DISTRITOS]
const fs = require('fs');
const path = require('path');

const [sourceDir, outputFile, shapeBase = 'DEPARTAMENTOS'] = process.argv.slice(2);
if (!sourceDir || !outputFile) throw new Error('Usage: node scripts/convert-peru-departments.js <source-dir> <output-file> [DEPARTAMENTOS|DISTRITOS]');

const decode = new TextDecoder('windows-1252');
const trim = (value) => value.replace(/\0/g, '').trim();

function readDbf(file) {
  const bytes = fs.readFileSync(file);
  const count = bytes.readUInt32LE(4);
  const headerLength = bytes.readUInt16LE(8);
  const recordLength = bytes.readUInt16LE(10);
  const fields = [];
  let offset = 32;
  while (bytes[offset] !== 0x0d) {
    fields.push({
      name: trim(bytes.toString('ascii', offset, offset + 11)),
      length: bytes[offset + 16]
    });
    offset += 32;
  }
  const rows = [];
  for (let index = 0; index < count; index += 1) {
    let cursor = headerLength + (index * recordLength);
    if (bytes[cursor] === 0x2a) continue;
    cursor += 1;
    const row = {};
    for (const field of fields) {
      row[field.name] = trim(decode.decode(bytes.subarray(cursor, cursor + field.length)));
      cursor += field.length;
    }
    rows.push(row);
  }
  return rows;
}

function signedArea(ring) {
  let area = 0;
  for (let index = 0; index < ring.length - 1; index += 1) {
    area += (ring[index][0] * ring[index + 1][1]) - (ring[index + 1][0] * ring[index][1]);
  }
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
  const result = points.filter((_, index) => keep[index]);
  result.push(result[0]);
  return result;
}

function ringsToMultiPolygon(rings) {
  const polygons = [];
  let outer = null;
  for (const rawRing of rings) {
    const ring = simplifyRing(rawRing, 0.003);
    const clockwise = signedArea(ring) < 0;
    if (clockwise || !outer) {
      outer = [clockwise ? ring.slice().reverse() : ring];
      polygons.push(outer);
    } else {
      outer.push(ring.slice().reverse());
    }
  }
  return { type: 'MultiPolygon', coordinates: polygons };
}

function readShp(file) {
  const bytes = fs.readFileSync(file);
  const geometries = [];
  let offset = 100;
  while (offset < bytes.length) {
    const contentLength = bytes.readUInt32BE(offset + 4) * 2;
    const start = offset + 8;
    const end = start + contentLength;
    const shapeType = bytes.readInt32LE(start);
    if ([5, 15, 25].includes(shapeType)) {
      const partsCount = bytes.readInt32LE(start + 36);
      const pointsCount = bytes.readInt32LE(start + 40);
      const partsStart = start + 44;
      const pointsStart = partsStart + (partsCount * 4);
      const starts = Array.from({ length: partsCount }, (_, index) => bytes.readInt32LE(partsStart + (index * 4)));
      const points = Array.from({ length: pointsCount }, (_, index) => [
        bytes.readDoubleLE(pointsStart + (index * 16)),
        bytes.readDoubleLE(pointsStart + (index * 16) + 8)
      ]);
      const rings = starts.map((part, index) => points.slice(part, starts[index + 1] || points.length));
      geometries.push(ringsToMultiPolygon(rings));
    } else {
      geometries.push(null);
    }
    offset = end;
  }
  return geometries;
}

const rows = readDbf(path.join(sourceDir, `${shapeBase}.dbf`));
const geometries = readShp(path.join(sourceDir, `${shapeBase}.shp`));
if (rows.length !== geometries.length) throw new Error(`DBF/SHP mismatch: ${rows.length}/${geometries.length}`);

const output = {
  type: 'FeatureCollection',
  source: {
    publisher: 'Instituto Geográfico Nacional del Perú (IGN)',
    dataset: shapeBase === 'DISTRITOS' ? 'Límites Distritales referenciales 1:100 000' : 'Límites Departamentales referenciales 1:100 000',
    downloaded_at: '2026-10-14',
    coordinate_reference_system: 'WGS 84'
  },
  features: rows.map((row, index) => ({
    type: 'Feature',
    id: row.UBIGEO || row.CODDEP,
    geometry: geometries[index],
    properties: row.UBIGEO
      ? { ubigeo: row.UBIGEO, department_code: row.CODDEP, department: row.DEPARTAMEN, province_code: row.CODPROV, province: row.PROVINCIA, district_code: row.CODDIST, name: row.DISTRITO, capital: row.CAPITAL }
      : { department_code: row.CODDEP, name: row.DEPARTAMEN, capital: row.CAPITAL }
  }))
};
fs.writeFileSync(outputFile, JSON.stringify(output));
console.log(JSON.stringify({ features: output.features.length, outputFile, bytes: fs.statSync(outputFile).size }));
