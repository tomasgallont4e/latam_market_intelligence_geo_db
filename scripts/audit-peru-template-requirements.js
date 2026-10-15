'use strict';
const fs=require('fs'),path=require('path');
const root=path.join(__dirname,'..');
const read=(file)=>JSON.parse(fs.readFileSync(path.join(root,file),'utf8'));
const layers='BCDEFGHIJKLMNOPQR'.split('');
const rows=[];
for(const layer of layers){
  const file=`data/peru-map/research_layers_B_R/layer_${layer}.json`;
  const source=read(file);
  for(const item of source.indicators||[]){
    const state=item.status||'unspecified';
    rows.push({layer,id:item.id,indicator:item.indicator,status:state,published_value:item.value!==null&&item.value!==undefined,period:item.period||null,source_ids:item.source_ids||[],limitation:item.limitation||null});
  }
}
const grouped=Object.fromEntries(layers.map(layer=>{const items=rows.filter(x=>x.layer===layer);return [layer,{requirements:items.length,published:items.filter(x=>x.published_value).length,pending:items.filter(x=>!x.published_value).length,statuses:[...new Set(items.map(x=>x.status))]}]}));
const output={country:'PE',generated_at:new Date().toISOString(),purpose:'Template requirement matrix. A missing value remains unavailable; it is not converted to zero.',summary:grouped,requirements:rows};
const out=path.join(root,'thinkdocuments','peru_template_requirements_matrix_2026-10-15.json');fs.writeFileSync(out,JSON.stringify(output,null,2));console.log(JSON.stringify({layers:grouped,requirements:rows.length}));
