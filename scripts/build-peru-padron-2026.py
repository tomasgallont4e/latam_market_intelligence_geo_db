"""Aggregate MINEDU Padron web DBF without publishing institution-level contacts."""
import json, os, struct, sys
from collections import defaultdict

src, out = sys.argv[1:3]
os.makedirs(out, exist_ok=True)
with open(src, 'rb') as fh:
    head=fh.read(32); n, hlen, rlen=struct.unpack('<xxxxIHH20x',head)
    fields=[]; fh.seek(32)
    while True:
        b=fh.read(32)
        if b[0] == 13: break
        fields.append((b[:11].split(b'\0')[0].decode('latin1'), b[16]))
    # The terminator is one byte but was read in a 32-byte block above.
    # Seek to the DBF's declared first-record offset before parsing records.
    fh.seek(hlen)
    offsets={}; pos=1
    for name, size in fields: offsets[name]=(pos,size); pos+=size
    wanted=['COD_MOD','NIV_MOD','D_NIV_MOD','GESTION','D_GESTION','CODGEO','D_DPTO','ESTADO','D_ESTADO']
    rows=defaultdict(lambda: {'services':0,'active_services':0,'public_services':0,'private_services':0})
    for _ in range(n):
        b=fh.read(rlen)
        if not b or b[0:1] == b'*': continue
        def val(k):
            p,s=offsets[k]; return b[p:p+s].decode('cp850','replace').strip()
        dept=val('D_DPTO'); level=val('NIV_MOD')
        if not dept or not level: continue
        r=rows[(dept,level,val('D_NIV_MOD'))];r['services']+=1
        if val('ESTADO') in ('1','A','ACTIVO') or 'ACTIV' in val('D_ESTADO').upper():r['active_services']+=1
        if val('GESTION')=='1' or 'PUBLIC' in val('D_GESTION').upper():r['public_services']+=1
        if val('GESTION')=='2' or 'PRIVAD' in val('D_GESTION').upper():r['private_services']+=1
outrows=[{'department':a,'level_code':b,'level_name':c,'reference_date':'2026-09-18','source_id':'MINEDU_PADRON_WEB_20260918',**v,'scope':'institutional_offer_not_enrollment'} for (a,b,c),v in sorted(rows.items())]
with open(os.path.join(out,'padron_offer_by_department_level_20260918.json'),'w',encoding='utf-8') as f:json.dump(outrows,f,ensure_ascii=False,indent=2)
with open(os.path.join(out,'metadata.json'),'w',encoding='utf-8') as f:json.dump({'source':'MINEDU Padron web 20260918','source_records':n,'output_rows':len(outrows),'limitation':'Counts education services/programmes. It contains no enrollment, students, programme field, or university enrollment.'},f,ensure_ascii=False,indent=2)
print(json.dumps({'source_records':n,'output_rows':len(outrows)},ensure_ascii=False))
