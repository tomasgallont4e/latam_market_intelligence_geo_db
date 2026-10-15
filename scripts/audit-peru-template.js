'use strict';
const fs=require('fs'),path=require('path');const root=path.join(__dirname,'..');
const exists=(p)=>fs.existsSync(path.join(root,p));const read=(p)=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const checks=[
 ['day1_package','data/peru/think4ever_peru_day1_FINAL',exists('data/peru/think4ever_peru_day1_FINAL'),'A/B/F supplied final package'],
 ['day2_script','scripts/build-peru-day2-gh.py',exists('scripts/build-peru-day2-gh.py'),'G/H builder'],
 ['day2_observed','data/peru-map/fact_persona_department_epen2025.json',exists('data/peru-map/fact_persona_department_epen2025.json'),'EPEN departmental observed estimates'],
 ['day3_script','scripts/build-peru-day3-l-partial.js',exists('scripts/build-peru-day3-l-partial.js'),'L partial builder'],
 ['day3_data','data/peru/day3_l_partial/l_nonuniversity_by_department_2025.json',exists('data/peru/day3_l_partial/l_nonuniversity_by_department_2025.json'),'MINEDU non-university aggregates'],
 ['day3_sunedu','data/peru/day3_sunedu/sunedu_licensed_universities_by_department.json',exists('data/peru/day3_sunedu/sunedu_licensed_universities_by_department.json'),'SUNEDU licensed university inventory'],
 ['day4_script','scripts/build-peru-day4-dj-ruc.js',exists('scripts/build-peru-day4-dj-ruc.js'),'D/J RUC builder'],
 ['day4_data','data/peru/day4_dj_ruc/j_tic_ruc_by_district_202604.json',exists('data/peru/day4_dj_ruc/j_tic_ruc_by_district_202604.json'),'SUNAT RUC territorial aggregate'],
 ['day4_enaho','data/peru/day4_m_enaho/m_enaho_employment_by_department_2025.json',exists('data/peru/day4_m_enaho/m_enaho_employment_by_department_2025.json'),'ENAHO employed-resident aggregate'],
 ['day4_local_anexo','data/peru/day4_n_padron_local/registered_local_addresses_by_department.json',exists('data/peru/day4_n_padron_local/registered_local_addresses_by_department.json'),'SUNAT local-address geographic aggregate'],
 ['day5_script','scripts/audit-peru-day5-oq.js',exists('scripts/audit-peru-day5-oq.js'),'O/Q builder'],
 ['day5_data','data/peru/day5_oq/audit.json',exists('data/peru/day5_oq/audit.json'),'ERESTEL/IGN audit']
].map(([id,file,pass,note])=>({id,file,pass,note}));
const counts={day2_observed:exists('data/peru-map/fact_persona_department_epen2025.json')?read('data/peru-map/fact_persona_department_epen2025.json').length:0,day3_rows:exists('data/peru/day3_l_partial/l_nonuniversity_by_department_2025.json')?read('data/peru/day3_l_partial/l_nonuniversity_by_department_2025.json').length:0,day4_districts:exists('data/peru/day4_dj_ruc/j_tic_ruc_by_district_202604.json')?read('data/peru/day4_dj_ruc/j_tic_ruc_by_district_202604.json').length:0,day4_local_departments:exists('data/peru/day4_n_padron_local/registered_local_addresses_by_department.json')?read('data/peru/day4_n_padron_local/registered_local_addresses_by_department.json').length:0};
const report={country:'PE',generated_at:new Date().toISOString(),checks,counts,passed:checks.filter(x=>x.pass).length,failed:checks.filter(x=>!x.pass).length,not_completed:['C/L university and programme-level data','M/N business size or microbusiness universe','P programme/sponsorship evidence','R approved cross-layer reconciliation']};
const out=path.join(root,'thinkdocuments','peru_template_audit_2026-10-14.json');fs.writeFileSync(out,JSON.stringify(report,null,2));console.log(JSON.stringify(report));if(report.failed)process.exitCode=1;
