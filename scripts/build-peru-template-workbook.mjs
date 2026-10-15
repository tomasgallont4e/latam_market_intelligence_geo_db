import fs from 'node:fs/promises';
import fsSync from 'node:fs';
import path from 'node:path';
import { SpreadsheetFile, Workbook } from '@oai/artifact-tool';

const root = path.resolve(import.meta.dirname, '..');
const read = (file) => JSON.parse(fsSync.readFileSync(path.join(root, file), 'utf8'));
const national = read('data/peru-map/fact_map_indicator.json').concat(read('data/peru-map/fact_tuni_ingress_national_2025.json'));
const catalog = read('data/peru-map/map_catalog.json');
const status = read('thinkdocuments/peru_template_audit_2026-10-14.json');
const wb = Workbook.create();
const summary = wb.worksheets.add('Summary');
const indicators = wb.worksheets.add('Indicators');
const sources = wb.worksheets.add('Sources register');
const audit = wb.worksheets.add('Audit');
for (const s of [summary, indicators, sources, audit]) { s.showGridLines = false; s.getUsedRange?.(); }
summary.getRange('A2:G2').values = [['Think4Ever Perú · registro de investigación', '', '', '', '', '', '']]; summary.mergeCells('A2:G2');
summary.getRange('A4:B9').values = [['País','Perú'],['Corte del workbook','2026-10-15'],['Indicadores nacionales publicados',national.filter(x=>x.value!==null&&x.value!=='').length],['Capas definidas','A–R'],['Checks aprobados',status.passed],['Checks fallidos',status.failed]];
summary.getRange('A11:G14').values = [['Estado de cobertura','Detalle','','','','',''],['Mapas territoriales','25 departamentos; distritos cuando la fuente publica localización','','','','',''],['Pendientes no sustituidos','Capacidad/modalidad superior, universo legal de micronegocios, evidencia de patrocinios y aprobación de conciliación','','','','',''],['Uso','Los datos nacionales no se distribuyen artificialmente a territorios. Consulte Indicators y Sources register.','','','','','']];
const indRows = [['Layer','Metric ID','Indicator','Value','Unit','Period','Status','Source ID','Limitations']].concat(national.map(x=>[x.layer,x.metric_id,x.indicator,x.value,x.unit,x.period,x.status,x.source_id,x.limitations]));
indicators.getRangeByIndexes(0,0,indRows.length,indRows[0].length).values=indRows;
const sourceRows = [['Source ID','Layer(s)','Year / period','URL / file','Scope','Notes']];
for (const [layer, info] of Object.entries(catalog.layers)) sourceRows.push([`CATALOG_${layer}`,layer,info.data_reference.match(/20\d{2}/)?.[0]||'',info.data_reference,'Map status',info.data_status]);
sourceRows.push(['SUNEDU_TUNI_ENROLLMENT_2025_2','C/L','2025-2','https://www.tuni.pe/comunidad/estudiantes','territorial aggregate','Programme/local aggregate; no personal data published'],['SUNEDU_TUNI_GRADUATES_2024','C/L','2024','https://www.tuni.pe/comunidad/estudiantes#egresados','territorial aggregate','Programme/local aggregate; no personal data published'],['SUNEDU_TUNI_INGRESANTES_2025','C','2025','https://www.tuni.pe/comunidad/estudiantes#ingresantes','national aggregate','No local field, therefore never allocated geographically']);
sources.getRangeByIndexes(0,0,sourceRows.length,sourceRows[0].length).values=sourceRows;
const auditRows=[['Check','Result'],['Passed checks',status.passed],['Failed checks',status.failed],['Open items',status.not_completed.join(' | ')]];
audit.getRangeByIndexes(0,0,auditRows.length,2).values=auditRows;
for (const [s,r] of [[summary,'A2:G14'],[indicators,`A1:I${indRows.length}`],[sources,`A1:F${sourceRows.length}`],[audit,'A1:B4']]) { s.getRange(r).format.font={name:'Arial',size:10,color:'#18263D'}; }
for (const [s,h] of [[summary,'A2:G2'],[indicators,'A1:I1'],[sources,'A1:F1'],[audit,'A1:B1']]) { s.getRange(h).format={fill:'#173B72',font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},horizontalAlignment:'center',verticalAlignment:'center'}; }
summary.getRange('A2').format.font={name:'Arial',size:14,bold:true,color:'#FFFFFF'};
for (const s of [summary,indicators,sources,audit]) { s.getUsedRange().format.autofitColumns(); s.getUsedRange().format.autofitRows(); }
indicators.freezePanes.freezeRows(1); sources.freezePanes.freezeRows(1);
indicators.getRange(`D2:D${indRows.length}`).format.numberFormat='#,##0.0';
await wb.recalculate();
const outputDir=path.join(root,'thinkdocuments'); await fs.mkdir(outputDir,{recursive:true});
const preview=await wb.render({sheetName:'Summary',range:'A1:G14',scale:1.5,format:'png'}); await fs.writeFile(path.join(outputDir,'think4ever-peru-country-template-preview.png'),new Uint8Array(await preview.arrayBuffer()));
const out=await SpreadsheetFile.exportXlsx(wb); await out.save(path.join(outputDir,'think4ever-peru-country-template.xlsx'));
const check=await wb.inspect({kind:'table',range:'Indicators!A1:I10',include:'values,formulas',tableMaxRows:10,tableMaxCols:9}); console.log(check.ndjson);
