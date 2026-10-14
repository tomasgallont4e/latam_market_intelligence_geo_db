#!/usr/bin/env node
'use strict';
/*
 * Pure-JS RAR helper (no system unrar/7z/bsdtar needed).
 *
 *   node scripts/rar.js list <file.rar>
 *   node scripts/rar.js extract <file.rar> <dir> [--force]
 *
 * - The archive is only ever read, never modified.
 * - Extraction is restricted to folders inside the project.
 * - Existing files are not overwritten unless --force is given.
 */
const fs = require('fs');
const path = require('path');
const { createExtractorFromData } = require('node-unrar-js');

const PROJECT_ROOT = path.resolve(__dirname, '..');

function usage() {
  console.error('Usage:\n  node scripts/rar.js list <file.rar>\n  node scripts/rar.js extract <file.rar> <dir> [--force]');
  process.exit(2);
}

async function openArchive(file) {
  if (!fs.existsSync(file)) throw new Error(`File not found: ${file}`);
  const buf = fs.readFileSync(file);
  const data = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
  return createExtractorFromData({ data });
}

function isInside(parent, child) {
  return child === parent || child.startsWith(parent + path.sep);
}

async function list(file) {
  const extractor = await openArchive(file);
  const { fileHeaders } = extractor.getFileList();
  let count = 0;
  let total = 0;
  for (const h of fileHeaders) {
    const isDir = Boolean(h.flags && h.flags.directory);
    const size = isDir ? '<dir>' : String(h.unpSize);
    const enc = h.flags && h.flags.encrypted ? ' [encrypted]' : '';
    console.log(`${size.padStart(10)}  ${h.time || ''}  ${h.name}${enc}`);
    if (!isDir) { count += 1; total += Number(h.unpSize) || 0; }
  }
  console.log(`${count} file(s), ${total} bytes`);
}

async function extract(file, dir, force) {
  const outDir = path.resolve(dir);
  if (!isInside(PROJECT_ROOT, outDir)) {
    throw new Error(`Refusing to extract outside the project: ${outDir}`);
  }
  const extractor = await openArchive(file);
  const { files } = extractor.extract();
  let written = 0;
  let skipped = 0;
  for (const f of files) {
    const h = f.fileHeader;
    const rel = String(h.name).replace(/\\/g, '/');
    const target = path.resolve(outDir, rel);
    if (!isInside(outDir, target) || target === outDir) {
      console.warn(`skip (unsafe path): ${h.name}`);
      skipped += 1;
      continue;
    }
    if (h.flags && h.flags.encrypted) {
      console.warn(`skip (encrypted): ${h.name}`);
      skipped += 1;
      continue;
    }
    if (h.flags && h.flags.directory) {
      fs.mkdirSync(target, { recursive: true });
      continue;
    }
    if (fs.existsSync(target) && !force) {
      console.warn(`skip (exists, use --force): ${path.relative(PROJECT_ROOT, target)}`);
      skipped += 1;
      continue;
    }
    fs.mkdirSync(path.dirname(target), { recursive: true });
    fs.writeFileSync(target, Buffer.from(f.extraction || new Uint8Array(0)));
    console.log(`wrote ${path.relative(PROJECT_ROOT, target)} (${h.unpSize} bytes)`);
    written += 1;
  }
  console.log(`${written} file(s) written, ${skipped} skipped`);
}

async function main() {
  const args = process.argv.slice(2);
  const force = args.includes('--force');
  const [cmd, file, dir] = args.filter((a) => a !== '--force');
  if (cmd === 'list' && file) return list(file);
  if (cmd === 'extract' && file && dir) return extract(file, dir, force);
  return usage();
}

main().catch((err) => {
  console.error(`rar.js error: ${err && err.message ? err.message : err}`);
  process.exit(1);
});
