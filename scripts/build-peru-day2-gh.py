"""Build Peru Day 2 layers G and H from the reproducible INEI EPEN 2025 annual file.

This produces publishable department aggregates only.  It deliberately does not
pretend that EPEN's departmental annual domain is a city estimate: the template's
"city" dimension is represented by the available official territorial level and
is labelled ``department_proxy`` everywhere.

Usage:
  python build-peru-day2-gh.py EPEN_2025.csv cno_ciuo.csv output_dir
"""
import csv, json, os, sys
from collections import defaultdict
import pandas as pd

EPEN, CORR, OUT = sys.argv[1:4]
os.makedirs(OUT, exist_ok=True)

PERSONAS = {
    "P01": {"label": "Software developers and analysts", "ciuo": {"2511","2512","2513","2514","2519"}},
    "P02": {"label": "Database, systems and network professionals", "ciuo": {"2521","2522","2523","2529"}},
    "P03": {"label": "ICT technicians and user support", "ciuo": {"3511","3512","3513","3514","3521","3522"}},
    "P04": {"label": "ICT managers", "ciuo": {"1330"}},
}
DEPT = {"01":"Amazonas","02":"Ancash","03":"Apurimac","04":"Arequipa","05":"Ayacucho","06":"Cajamarca","08":"Cusco","09":"Huancavelica","10":"Huanuco","11":"Ica","12":"Junin","13":"La Libertad","14":"Lambayeque","15":"Lima (incl. Callao)","16":"Loreto","17":"Madre de Dios","18":"Moquegua","19":"Pasco","20":"Piura","21":"Puno","22":"San Martin","23":"Tacna","24":"Tumbes","25":"Ucayali"}
SECTION = {}
for a,b,s in [(1,3,"A"),(5,9,"B"),(10,33,"C"),(35,35,"D"),(36,39,"E"),(41,43,"F"),(45,47,"G"),(49,53,"H"),(55,56,"I"),(58,63,"J"),(64,66,"K"),(68,68,"L"),(69,75,"M"),(77,82,"N"),(84,84,"O"),(85,85,"P"),(86,88,"Q"),(90,93,"R"),(94,96,"S"),(97,98,"T"),(99,99,"U")]:
    for x in range(a,b+1): SECTION[f"{x:02d}"] = s

# Decisions inherited from the audited Day 1 layer-F mapping; prevent ambiguous
# or clearly out-of-scope links from becoming a geographic estimate.
EXCLUDE = {"1499","2312","3313"}

def primary_codes():
    by_cno = defaultdict(set)
    with open(CORR, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["cno"] not in EXCLUDE:
                by_cno[r["cno"]].add(r["ciuo"])
    out = {p:set() for p in PERSONAS}
    for c, ciuos in by_cno.items():
        hits = [p for p,x in PERSONAS.items() if x["ciuo"] & ciuos]
        # Never allocate one CNO code to more than one persona.
        if len(hits) == 1: out[hits[0]].add(c)
    return out

def rows_to_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]) if rows else ["empty"])
        w.writeheader()
        if rows: w.writerows(rows)

def add(rows, layer, metric, p, dept, category, amount, records, note):
    # Suppress small direct estimates rather than showing a false zero.
    value = round(float(amount), 1) if records >= 30 else None
    rows.append({"layer":layer,"metric_id":metric,"persona_id":p,"persona":PERSONAS[p]["label"],
                 "geographic_level":"department_proxy","department_code":dept,"department":DEPT.get(dept,dept),
                 "category":category,"value":value,"unit":"employed_people","period":"2025_annual",
                 "sample_records":int(records),"publication_status":"publish" if value is not None else "suppressed_n_lt_30",
                 "source_id":"SRC_INEI_EPEN_2025_DPTO","method_note":note})

def main():
    codes = primary_codes()
    d = pd.read_csv(EPEN, dtype=str, keep_default_na=False)
    d["w"] = pd.to_numeric(d["FAC300_ANUAL"].str.replace(",","."), errors="coerce")
    d = d[(d.OCUP300 == "1") & d.w.notna()].copy()
    d["occ"] = d.C308_COD.str.zfill(4)
    d["dept"] = d.CCDD.str.zfill(2)
    d["section"] = d.C309_COD.str.zfill(4).str[:2].map(SECTION).fillna("unknown")
    d["size"] = pd.to_numeric(d.C317A, errors="coerce")
    d["size_band"] = pd.cut(d["size"], [-1,1,10,50,200,float("inf")], labels=["1_alone","2_10","11_50","51_200","201_plus"])
    d["buyer_proxy"] = "other_or_unpaid"
    d.loc[d.C310.eq("2"), "buyer_proxy"] = "government_employer"
    d.loc[d.C310.eq("1"), "buyer_proxy"] = "private_employer"
    d.loc[d.C310.isin(["3","7"]) & d.C311.isin(["4","5","6"]), "buyer_proxy"] = "private_employer"
    d.loc[d.C310.isin(["3","7"]) & d.C311.isin(["1","2","3"]), "buyer_proxy"] = "government_employer"

    g, h = [], []
    for p, pcodes in codes.items():
        x = d[d.occ.isin(pcodes)]
        for (dept, section), a in x.groupby(["dept","section"]):
            add(g,"G","G1_ict_personas_by_industry",p,dept,f"CIIU_section_{section}",a.w.sum(),len(a),"Annual EPEN 2025 department estimate.")
        y = x[x.section.ne("J")]
        for (dept, band), a in y.groupby(["dept","size_band"], observed=True):
            add(g,"G","G2_ict_outside_info_comm_by_employer_size",p,dept,str(band),a.w.sum(),len(a),"Excludes CIIU section J; annual department proxy.")
        z = x[x.buyer_proxy.eq("government_employer")]
        for (dept, section), a in z.groupby(["dept","section"]):
            add(g,"G","G3_ict_government_by_industry",p,dept,f"CIIU_section_{section}",a.w.sum(),len(a),"Government employer derived from EPEN C310/C311.")
        for (dept, buyer), a in x.groupby(["dept","buyer_proxy"]):
            add(h,"H","H1_persona_x_department_x_employer_proxy",p,dept,buyer,a.w.sum(),len(a),"Buyer is an employer-position proxy, not observed product demand.")
    # G4 is a meaningful comparison group, but never called ICT: all other employed people in government.
    core = set().union(*codes.values())
    other = d[(~d.occ.isin(core)) & d.buyer_proxy.eq("government_employer")]
    for dept, a in other.groupby("dept"):
        g.append({"layer":"G","metric_id":"G4_government_in_other_occupations","persona_id":"OTHER","persona":"Other occupations (not four ICT personas)","geographic_level":"department_proxy","department_code":dept,"department":DEPT.get(dept,dept),"category":"government_employer","value":round(float(a.w.sum()),1),"unit":"employed_people","period":"2025_annual","sample_records":int(len(a)),"publication_status":"publish","source_id":"SRC_INEI_EPEN_2025_DPTO","method_note":"Comparison only; not allocated to any Think4ever persona."})
    rows_to_csv(os.path.join(OUT,"g_employment_by_department_pe.csv"),g)
    rows_to_csv(os.path.join(OUT,"h_persona_department_employer_proxy_pe.csv"),h)
    # The runtime reads JSON and must not have to parse a research CSV.  Keep the
    # complete CSV alongside it as the reproducibility artifact.
    observed = []
    for p in PERSONAS:
        for dept, a in d[d.occ.isin(codes[p])].groupby("dept"):
            observed.append({"group_id":p,"department_code":dept,"department":DEPT.get(dept,dept),
                             "employed":round(float(a.w.sum()),1),"sample_records":int(len(a)),
                             "publication_status":"publish" if len(a) >= 30 else "suppressed_n_lt_30",
                             "source_id":"SRC_INEI_EPEN_2025_DPTO","reference_year":2025,
                             "geographic_level":"department_observed"})
    # The combined core is explicitly a combined group (not a fifth persona).
    # It provides the statistically usable departmental view when the four
    # individual occupations are too sparse to publish.
    core_codes = set().union(*codes.values())
    for dept, a in d[d.occ.isin(core_codes)].groupby("dept"):
        observed.append({"group_id":"CORE_ICT","department_code":dept,"department":DEPT.get(dept,dept),
                         "employed":round(float(a.w.sum()),1),"sample_records":int(len(a)),
                         "publication_status":"publish" if len(a) >= 30 else "suppressed_n_lt_30",
                         "source_id":"SRC_INEI_EPEN_2025_DPTO","reference_year":2025,
                         "geographic_level":"department_observed","combined_group":True})
    with open(os.path.join(OUT,"fact_persona_department_epen2025.json"),"w",encoding="utf-8") as f:
        json.dump(observed,f,ensure_ascii=False,indent=2)
    with open(os.path.join(OUT,"day2_gh_metadata.json"),"w",encoding="utf-8") as f:
        json.dump({"country":"PE","period":"2025 annual","source":"INEI EPEN departamentos, module 76","geography":"department_proxy","deviation_from_template":"The available weighted official file supports departments, not cities. No city-level claim is made.","buyer_definition":"Employer-position proxy from C310/C311; it is not demand, customers, TAM, SAM, or SOM.","input_records":len(d),"output_rows":{"G":len(g),"H":len(h)},"suppression_rule":"direct cells with fewer than 30 sampled records are null"},f,ensure_ascii=False,indent=2)
    print(json.dumps({"G":len(g),"H":len(h),"universe":len(d)},ensure_ascii=False))

if __name__ == "__main__": main()
