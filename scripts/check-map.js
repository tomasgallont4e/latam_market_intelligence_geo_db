'use strict';
// Calls the map handler functions directly (no server) and prints counts.
const pool = require('../db/pool');
const data = require('../lib/mapData');
const cmp = require('../lib/compare');

function checkIndicators(name, payload) {
  const inds = payload.indicators || [];
  const withSrc = inds.filter((i) => i.source && i.source.source_name && i.source.year);
  console.log(`  indicators: ${inds.length} (with source/year: ${withSrc.length})`);
  for (const i of inds) console.log(`    - ${i.key}: ${i.label} | ${i.source.source_name} (${i.source.year})`);
  return inds.length > 0 && withSrc.length === inds.length;
}

function nonEmptyCounts(items, getValues, keys) {
  const out = {};
  for (const k of keys) out[k] = items.filter((it) => getValues(it)[k] !== null && getValues(it)[k] !== undefined && getValues(it)[k] !== 0).length;
  return out;
}

(async () => {
  let ok = true;
  try {
    const health = await data.getHealth();
    console.log('HEALTH', JSON.stringify(health));
    ok = ok && health.axis_check_ok;

    const dep = await data.getDepartments({});
    const depGeom = dep.features.filter((f) => f.geometry && f.geometry.coordinates).length;
    console.log(`\nDEPARTMENTS features: ${dep.features.length} (with geometry: ${depGeom})`);
    ok = checkIndicators('departments', dep) && ok;
    console.log('  non-empty per indicator:', JSON.stringify(nonEmptyCounts(dep.features, (f) => f.properties.values, dep.indicators.map((i) => i.key))));
    const bog = dep.features.find((f) => f.properties.department_code === '11');
    if (bog) console.log('  sample 11:', JSON.stringify(bog.properties));
    ok = ok && dep.features.length === 33 && depGeom === 33;

    const depP = await data.getDepartments({ persona: 'Software developers and analysts' });
    const sumP = depP.features.reduce((s, f) => s + (f.properties.values.personas || 0), 0);
    console.log(`  persona filter (Software developers and analysts) sum: ${sumP}`);

    const mun = await data.getMunicipalities({});
    const ll = mun.municipalities.filter((m) => Number.isFinite(m.lat) && Number.isFinite(m.lon));
    console.log(`\nMUNICIPALITIES with lat/lon: ${ll.length}`);
    ok = checkIndicators('municipalities', mun) && ok;
    console.log('  non-empty per indicator:', JSON.stringify(nonEmptyCounts(mun.municipalities, (m) => m.values, mun.indicators.map((i) => i.key))));
    console.log('  with events:', mun.municipalities.filter((m) => m.has_event).map((m) => `${m.name}(${m.events.length})`).join(', '));
    console.log('  27493 present?', mun.municipalities.some((m) => m.municipality_code === '27493'));
    const bogm = mun.municipalities.find((m) => m.municipality_code === '11001');
    if (bogm) console.log('  sample 11001:', JSON.stringify({ ...bogm, events: bogm.events.length }));
    ok = ok && ll.length >= 1000 && !mun.municipalities.some((m) => m.municipality_code === '27493');

    const loc = await data.getLocalidades();
    const locGeom = loc.features.filter((f) => f.geometry && f.geometry.coordinates).length;
    console.log(`\nLOCALIDADES features: ${loc.features.length} (with geometry: ${locGeom})`);
    ok = checkIndicators('localidades', loc) && ok;
    console.log('  non-empty per indicator:', JSON.stringify(nonEmptyCounts(loc.features, (f) => f.properties.values, loc.indicators.map((i) => i.key))));
    const first = loc.features[0];
    if (first) {
      const c = JSON.stringify(first.geometry.coordinates).match(/\[(-?\d+\.\d+),\s*(-?\d+\.\d+)\]/);
      console.log(`  ${first.id} first coord [lon,lat] = [${c && c[1]}, ${c && c[2]}]`);
    }
    ok = ok && loc.features.length === 20 && locGeom === 20;

    const per = await data.getPersonas();
    console.log(`\nPERSONAS: ${per.count} | source: ${per.source.source_name} (${per.source.year})`);
    ok = ok && per.count === 13;

    // ── Comparar: 2 departamentos ──
    const c = await cmp.compare({ level: 'department', ids: '11,05' });
    console.log(`\nCOMPARE ${c.level_label}: ${c.places.map((p) => `${p.name} (${p.code})`).join(' vs ')}`);
    const pad = (s, n) => String(s).padEnd(n).slice(0, n);
    const nf = new Intl.NumberFormat('es-CO', { maximumFractionDigits: 2 });
    console.log('  ' + pad('Indicador', 38) + c.places.map((p) => pad(p.name, 18)).join('') + 'Fuente y año');
    for (const ind of c.indicators) {
      console.log('  ' + pad(ind.label, 38) + ind.values.map((v) => pad(v === null ? 'n.a.' : nf.format(v), 18)).join('')
        + `${ind.source.source_name} (${ind.source.year})`);
    }
    const cWithVals = c.indicators.filter((i) => i.values.some((v) => v !== null)).length;
    const cWithSrc = c.indicators.filter((i) => i.source && i.source.source_name && i.source.year).length;
    console.log(`  indicators: ${c.indicators.length}, with values: ${cWithVals}, with source/year: ${cWithSrc}`);
    ok = ok && c.places.length === 2 && cWithVals > 0 && cWithSrc === c.indicators.length;

    const cl = await cmp.compare({ level: 'localidad', ids: 'BOG-01,BOG-02,BOG-03' });
    console.log(`  localidades compare: ${cl.places.map((p) => p.name).join(', ')} | ${cl.indicators.length} indicators`);

    for (const bad of [{ level: 'department', ids: '11' }, { level: 'department', ids: '11,11001' }, { level: 'x', ids: '1,2' }]) {
      try {
        await cmp.compare(bad);
        console.log('  expected 400 for', JSON.stringify(bad), '→ none');
        ok = false;
      } catch (e) {
        console.log(`  400 check ${JSON.stringify(bad)} → ${e.status}: ${e.message}`);
        ok = ok && e.status === 400;
      }
    }

    console.log(`\nRESULT: ${ok ? 'OK' : 'FAIL'}`);
  } catch (e) {
    console.error('ERROR', e);
    ok = false;
  } finally {
    await pool.end();
    process.exit(ok ? 0 : 1);
  }
})();