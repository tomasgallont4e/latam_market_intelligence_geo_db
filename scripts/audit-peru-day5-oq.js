'use strict';
const fs=require('fs'),path=require('path');const root=path.join(__dirname,'..');
const read=(p)=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const context=read('data/peru-map/fact_digital_context_erestel_2025.json');
const dept=read('data/peru-map/geo_departments_ign_2025.geojson');
const district=read('data/peru-map/geo_districts_ign_2025.geojson');
const out=path.join(root,'data','peru','day5_oq');fs.mkdirSync(out,{recursive:true});
const audit={country:'PE', day:5, O:{source:'ERESTEL 2025 / OSIPTEL', records:context.length, status:'published_context_indicators'}, Q:{department_features:dept.features.length,district_features:district.features.length,status:'IGN geometries with geographic keys'}, P:{status:'pending',reason:'No programme/sponsorship evidence supplied.'}, R:{status:'partial',reason:'Layer-specific reproducibility checks exist; a cross-layer business reconciliation is not yet approved.'}};
fs.writeFileSync(path.join(out,'o_digital_context_erestel_2025.json'),JSON.stringify(context,null,2));fs.writeFileSync(path.join(out,'audit.json'),JSON.stringify(audit,null,2));fs.writeFileSync(path.join(out,'README.md'),'# Perú · Día 5 · O/Q parcial\n\nContexto digital ERESTEL 2025 y auditoría de geografía IGN disponible. P y R no se infieren: requieren evidencia de programa y conciliación aprobada.\n');console.log(JSON.stringify(audit));
