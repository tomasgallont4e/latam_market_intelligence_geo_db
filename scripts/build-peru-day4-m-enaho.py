"""Layer M partial: ENAHO 2025 employed people by department, CIIU and reported size band.
Raw microdata stays local; output is aggregate only."""
import csv,json,os,sys
from collections import defaultdict
import pandas as pd
src,out=sys.argv[1:3];os.makedirs(out,exist_ok=True)
cols=['UBIGEO','P506R4','P507','P510','P510A1','P512A','P512B','OCU500','FAC500A']
d=pd.read_csv(src,sep=';',encoding='latin1',usecols=cols,dtype=str)
d['w']=pd.to_numeric(d.FAC500A.str.replace(',','.'),errors='coerce')
d=d[(d.OCU500=='1')&d.w.notna()].copy();d['department_code']=d.UBIGEO.str[:2];d['ciiu_section']=d.P506R4.str.zfill(4).str[:2]
g=d.groupby(['department_code','ciiu_section','P512A'],dropna=False).agg(weighted_employed=('w','sum'),sample_records=('w','size')).reset_index()
rows=[]
size_labels={'1':'Hasta 20 personas','2':'De 21 a 50 personas','3':'De 51 a 100 personas','4':'De 101 a 500 personas','5':'Más de 500 personas'}
for _,r in g.iterrows():
    code=r.P512A if r.P512A.strip() else None
    rows.append({'department_code':r.department_code,'ciiu_division_2digit':r.ciiu_section,'reported_size_band_code':code,'reported_size_band_label':size_labels.get(code),'weighted_employed':round(float(r.weighted_employed),1),'sample_records':int(r.sample_records),'period':'2025_annual','source_id':'INEI_ENAHO_2025_M05','scope':'employed_people_not_registered_firms','limitation':'P512A is the reported size of the respondent’s work/business/enterprise. This is employment, not a count of firms or a legal microenterprise universe.'})
with open(os.path.join(out,'m_enaho_employment_by_department_size_ciiu_2025.json'),'w',encoding='utf8') as f:json.dump(rows,f,ensure_ascii=False,indent=2)
summary=[]
for dept,a in d.groupby('department_code'):
    small=a[a.P512A=='1']; registered=a[a.P510A1.isin(['1','2'])]; unregistered=a[a.P510A1=='3']
    summary.append({'department_code':dept,'weighted_employed':round(float(a.w.sum()),1),'weighted_employed_up_to_20_people':round(float(small.w.sum()),1),'weighted_employed_employer_registered_sunat':round(float(registered.w.sum()),1),'weighted_employed_employer_not_registered_sunat':round(float(unregistered.w.sum()),1),'sample_records':int(len(a)),'sample_records_up_to_20_people':int(len(small)),'sample_records_employer_registered_sunat':int(len(registered)),'sample_records_employer_not_registered_sunat':int(len(unregistered)),'period':'2025_annual','source_id':'INEI_ENAHO_2025_M05','indicator':'Empleo ocupado ENAHO','definitions':{'weighted_employed_up_to_20_people':'Employed persons whose reported work/business/enterprise size is up to 20 persons (P512A=1).','weighted_employed_employer_registered_sunat':'Employed persons reporting the business/enterprise as registered with SUNAT (P510A1=1 or 2).','weighted_employed_employer_not_registered_sunat':'Employed persons reporting the business/enterprise as not registered/no RUC (P510A1=3).'},'limitation':'Persons employed by residence department; not firms or jobs located in the department. Registration and size are respondent reports and do not define a legal microenterprise universe.'})
with open(os.path.join(out,'m_enaho_employment_by_department_2025.json'),'w',encoding='utf8') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
with open(os.path.join(out,'metadata.json'),'w',encoding='utf8') as f:json.dump({'source_rows':len(d),'aggregate_rows':len(rows),'definition':'ENAHO employed people (OCU500=1), FAC500A weighted; grouped by residence department, reported CIIU and reported size-band code. P512A labels: 1 up to 20, 2 21–50, 3 51–100, 4 101–500, 5 over 500. P510A1 reports SUNAT registration of the business/enterprise.','not_measured':'firms, sales, legal formalization or a legal microenterprise universe'},f,ensure_ascii=False,indent=2)
print(json.dumps({'source_rows':len(d),'aggregate_rows':len(rows)}))
