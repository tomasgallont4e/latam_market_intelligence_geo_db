"""Layer M partial: ENAHO 2025 employed people by department, CIIU and reported size band.
Raw microdata stays local; output is aggregate only."""
import csv,json,os,sys
from collections import defaultdict
import pandas as pd
src,out=sys.argv[1:3];os.makedirs(out,exist_ok=True)
cols=['UBIGEO','P506R4','P507','P510','P512A','P512B','OCU500','FAC500A']
d=pd.read_csv(src,sep=';',encoding='latin1',usecols=cols,dtype=str)
d['w']=pd.to_numeric(d.FAC500A.str.replace(',','.'),errors='coerce')
d=d[(d.OCU500=='1')&d.w.notna()].copy();d['department_code']=d.UBIGEO.str[:2];d['ciiu_section']=d.P506R4.str.zfill(4).str[:2]
g=d.groupby(['department_code','ciiu_section','P512A'],dropna=False).agg(weighted_employed=('w','sum'),sample_records=('w','size')).reset_index()
rows=[]
for _,r in g.iterrows():rows.append({'department_code':r.department_code,'ciiu_division_2digit':r.ciiu_section,'reported_size_band_code':r.P512A if r.P512A.strip() else None,'weighted_employed':round(float(r.weighted_employed),1),'sample_records':int(r.sample_records),'period':'2025_annual','source_id':'INEI_ENAHO_2025_M05','scope':'employed_people_not_registered_firms','limitation':'P512A code labels require dictionary validation; this is not a count of firms or microbusinesses.'})
with open(os.path.join(out,'m_enaho_employment_by_department_size_ciiu_2025.json'),'w',encoding='utf8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
with open(os.path.join(out,'metadata.json'),'w',encoding='utf8') as f:json.dump({'source_rows':len(d),'aggregate_rows':len(rows),'definition':'ENAHO employed people (OCU500=1), FAC500A weighted; grouped by residence department, reported CIIU and reported size-band code.','not_measured':'firms, sales, formalization or a legal microenterprise universe'},f,ensure_ascii=False,indent=2)
print(json.dumps({'source_rows':len(d),'aggregate_rows':len(rows)}))
