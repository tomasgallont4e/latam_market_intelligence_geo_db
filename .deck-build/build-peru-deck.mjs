import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Presentation, PresentationFile } from '@oai/artifact-tool';

const outputDir = fileURLToPath(new URL('../thinkdocuments/deck-output/', import.meta.url));
const out = path.join(outputDir, 'Think4Ever_Peru_market_research_2026-10-15.pptx');
const deck = Presentation.create({slideSize:{width:1280,height:720}});
const navy='#173B72', ink='#18263D', muted='#50657F', pale='#EDF3FA', orange='#F58220';
function box(slide,text,left,top,width,height,size=22,color=ink,bold=false){const x=slide.shapes.add({geometry:'textbox',position:{left,top,width,height},fill:'none',line:{style:'solid',fill:'none',width:0}});x.text=text;x.text.style={fontFamily:'Arial',fontSize:size,color,bold};return x;}
function page(title,kicker,body,foot='Fuentes y periodos en el workbook de Perú'){const s=deck.slides.add();s.background.fill='#FFFFFF';box(s,kicker,72,50,600,24,14,orange,true);box(s,title,72,88,1080,58,34,navy,true);const line=s.shapes.add({geometry:'rect',position:{left:72,top:158,width:1136,height:2},fill:navy,line:{style:'solid',fill:navy,width:0}});box(s,body,72,205,1050,350,22,ink,false);box(s,foot,72,660,1040,20,12,muted,false);return s;}
const cover=deck.slides.add();cover.background.fill=navy;box(cover,'think4ever',72,70,300,44,30,'#FFFFFF',true);box(cover,'Perú\nMarket Research & Analytics',72,182,760,140,46,'#FFFFFF',true);box(cover,'Corte de datos: 15 de octubre de 2026',76,360,620,30,20,'#DCE7F4');box(cover,'Indicadores publicados, fuentes y límites de cobertura',76,404,760,28,18,'#DCE7F4');
page('Perú: cobertura de datos','RESUMEN','El estudio reúne indicadores nacionales, 25 departamentos y capas distritales cuando la fuente incluye UBIGEO.\n\n19 checks técnicos aprobados. Las fuentes con universos, años o definiciones incompatibles no se consolidan en un total artificial.');
page('Desarrolladores y actividad digital','CAPAS A Y B','GitHub Innovation Graph y Stack Overflow alimentan los indicadores nacionales de desarrolladores, organizaciones, actividad y uso de tecnología.\n\nEl workbook conserva valor, periodo, fuente y limitación por cada métrica. Las tasas se comparan contra el mismo trimestre del año anterior.');
page('Educación superior y talento','CAPAS C Y L','TUNI/SUNEDU: matrícula reportada 2025-2 por departamento y distrito; egresados 2024 por departamento y distrito; ingresantes 2025 sólo a escala nacional.\n\nMINEDU: matrícula y oferta superior no universitaria por departamento. Modalidad y capacidad comparables no tienen todavía una fuente nacional homogénea.');
page('Empleo, empresas y territorio','CAPAS D, F, G, H, J, M Y N','EPEN y ENAHO sostienen mediciones de empleo y perfiles ocupacionales. SUNAT agrega RUC TIC por CIIU y ubicación fiscal, además de locales registrados con UBIGEO.\n\nLos registros RUC no equivalen a empleo, ventas, tamaño legal, empresas únicas ni demanda comercial.');
page('Escuelas y contexto digital','CAPAS K Y O','El mapa carga 15.700 servicios educativos secundarios y sus agregados territoriales. ERESTEL/OSIPTEL aporta indicadores de contexto digital.\n\nLos escenarios de patrocinio permanecen fuera de los resultados hasta contar con supuestos y evidencia aprobados.');
page('Geografía, auditoría y límites','CAPAS Q Y R','IGN aporta límites departamentales y distritales. La auditoría confirma cobertura de los indicadores territoriales publicados en los 25 departamentos.\n\nPendientes: capacidad y modalidad superior; universo legal de micronegocios; patrocinios; conciliación aprobada de negocio entre fuentes.','Ver detalle reproducible en el workbook, scripts y JSON del repositorio');
await fs.mkdir(outputDir,{recursive:true});
const pptx=await PresentationFile.exportPptx(deck);await pptx.save(out);
for(const [i,s] of deck.slides.items.entries()){const png=await deck.export({slide:s,format:'png',scale:1});await fs.writeFile(path.join(outputDir,`slide-${i+1}.png`),new Uint8Array(await png.arrayBuffer()));}
