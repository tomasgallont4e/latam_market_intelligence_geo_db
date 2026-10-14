"""Peru Day 1 - closure audit of the Layer F package (read-only; writes only the audit CSV).

Usage: python3 -I audit_closure_layer_f_pe.py <package_dir> <raw_dir> <prev_f9_csv> <prev_f1_csv> <out_csv>
"""
import sys, os, csv, json, hashlib, re, glob
import pandas as pd, numpy as np

PKG, RAW, PREV_F9, PREV_F1, OUT = sys.argv[1:6]
D, V = os.path.join(PKG, "data"), os.path.join(PKG, "validation")
R = []
def rec(area, cid, control, evidence, ok, severity="", action=""):
    R.append(dict(area=area, check_id=cid, control=control, evidence=evidence, result="PASS" if ok else "FAIL", severity=("" if ok else severity), action=("" if ok else action)))
num = lambda s: pd.to_numeric(s, errors="coerce")

est = pd.read_csv(os.path.join(D, "f_persona_estimates_pe.csv"), dtype={"cno2015_codes": str})
inn = pd.read_csv(os.path.join(V, "internal_not_publishable", "f_persona_estimates_internal_pe.csv"), dtype={"cno2015_codes": str})
mp = pd.read_csv(os.path.join(D, "f_occupation_mapping_pe.csv"), dtype=str)
corr = pd.read_csv(os.path.join(D, "f_persona_correspondence_pe.csv"), dtype=str)

# ---------------- A. integrity
APPROVED = {1: "2511;2512;2513;2519;2521", 2: "2514;2515;2529", 3: "3126;3511;3512;3513;3514;3521;3522", 4: "1330", 5: "2163;2166",
            6: "2421;2422", 7: "2412", 8: "2120;2631;2632;3315;3317", 9: "2431;2432", 10: "2411",
            11: "2141;2142;2143;2144;2145;2146;2149;2151;2152;2153",
            12: "1211;1212;1213;1219;1221;1222;1223;1321;1322;1323;1324;1325;1326;1341;1342;1343;1344;1345;1346;1421", 13: "2311;2353"}
APPROVED_EST = {"P01": 67761.1, "P03": 75297.7, "P06": 85893.4, "P08": 50234.5, "P09": 4916.4, "P10": 94590.4, "P11": 169563.5, "P12": 51748.8,
                "P13": 60533.9, "RING_CORE": 144961.4, "RING_ADJACENT": 146415.1, "RING_EXTENDED": 376436.5, "ALL13": 667813.0, "COMB_P01_P02": 68323.4}
for p, codes in APPROVED.items():
    row = inn[inn.group_id == f"P{p:02d}"].iloc[0]
    c_row = corr[corr.template_persona_number == str(p)].iloc[0]
    ok = row.cno2015_codes == codes and c_row.cno2015_codes_primary == codes
    rec("A", f"A1_P{p:02d}", f"Persona {p} CNO codes = approved mapping", f"{row.cno2015_codes}", ok, "Critico", "Restore approved mapping")
for g, v in APPROVED_EST.items():
    x = float(inn[inn.group_id == g].employed.iloc[0])
    rec("A", f"A2_{g}", f"{g} estimate identical to approved value", f"{x} vs {v}", abs(x - v) < 0.05, "Critico", "Investigate change")
sets = {p: set(c.split(";")) for p, c in APPROVED.items()}
allc = [c for s in sets.values() for c in s]
rec("A", "A3_no_dup_codes", "No CNO code assigned to more than one persona", f"{len(allc)} codes, {len(set(allc))} unique", len(allc) == len(set(allc)), "Critico", "Fix mapping")
rings = {"RING_CORE": [1, 2, 3, 4], "RING_ADJACENT": [5, 6, 7, 8, 9], "RING_EXTENDED": [10, 11, 12, 13]}
for g, ps in rings.items():
    u = set().union(*[sets[p] for p in ps]); rc = set(inn[inn.group_id == g].cno2015_codes.iloc[0].split(";"))
    tot = sum(float(inn[inn.group_id == f"P{p:02d}"].employed.iloc[0]) for p in ps)
    rec("A", f"A4_{g}_codes", f"{g} code set = union of its personas", f"{len(rc)} codes", u == rc, "Critico", "Fix ring definition")
    rec("A", f"A4_{g}_additive", f"{g} = sum of persona estimates (incl. suppressed cells)", f"{float(inn[inn.group_id==g].employed.iloc[0]):.1f} vs sum {tot:.1f}",
        abs(float(inn[inn.group_id == g].employed.iloc[0]) - tot) < 0.5, "Critico", "Fix aggregation")
all13 = float(inn[inn.group_id == "ALL13"].employed.iloc[0]); s3 = sum(float(inn[inn.group_id == g].employed.iloc[0]) for g in rings)
rec("A", "A4_ALL13", "ALL13 = Core + Adjacent + Extended", f"{all13:.1f} vs {s3:.1f}", abs(all13 - s3) < 0.5, "Critico", "Fix aggregation")
ringcodes = set().union(*sets.values())
des = set(inn[inn.group_id == "INFO_DESIGN_2163_2166_3432"].cno2015_codes.iloc[0].split(";"))
rec("A", "A5_designers_outside", "Designers group: 3432 not in any persona/ring; group not additive; type informational",
    f"3432 in rings: {'3432' in ringcodes}; additive_to_ring={inn[inn.group_id=='INFO_DESIGN_2163_2166_3432'].additive_to_ring.iloc[0]}; type={inn[inn.group_id=='INFO_DESIGN_2163_2166_3432'].group_type.iloc[0]}",
    ("3432" not in ringcodes) and str(inn[inn.group_id == "INFO_DESIGN_2163_2166_3432"].additive_to_ring.iloc[0]) == "False"
    and inn[inn.group_id == "INFO_DESIGN_2163_2166_3432"].group_type.iloc[0] == "informational_outside_rings", "Mayor", "Separate group")
add = inn[inn.additive_to_ring.astype(str) == "True"].group_id.tolist()
rec("A", "A5_additive_flags", "Only the 13 personas are flagged additive", f"{len(add)} additive rows", sorted(add) == [f"P{p:02d}" for p in range(1, 14)], "Mayor", "Fix flags")
f9 = pd.read_csv(os.path.join(D, "f9_persona_socioeconomic_enaho_pe.csv")); f1 = pd.read_csv(os.path.join(D, "f1_enaho_diagnostic_pe.csv"))
rec("A", "A6_sources_separate", "ENAHO tables carry source=ENAHO only; EPEN estimates table has no ENAHO columns",
    f"f9 sources {sorted(f9.source.unique())}; f1 sources {sorted(f1.source.unique())}; EPEN cols with 'enaho': {[c for c in est.columns if 'enaho' in c.lower()]}",
    set(f9.source) == {"ENAHO 2025"} and set(f1.source) == {"ENAHO 2025"} and not [c for c in est.columns if "enaho" in c.lower()], "Mayor", "Separate sources")
rec("A", "A6_f1_diag_label", "ENAHO F1 labelled diagnostic, not replacing EPEN", f"use values: {sorted(f1.use.unique())}",
    all("diagnostic only" in u for u in f1.use.unique()), "Mayor", "Relabel")
dsg = pd.read_csv(os.path.join(D, "f_designers_informational_pe.csv"))
rec("A", "A6_designers_rows_by_source", "Designers table: one row per source per group, never combined", f"{dsg.groupby('group_id').source.nunique().to_dict()}",
    (dsg.groupby("group_id").source.nunique() == 2).all() and not dsg.source.str.contains("\\+|combined", regex=True).any(), "Mayor", "Separate")

# ---------------- B. statistical consistency
pub = est[est.publication_status != "suppressed_unreliable"]; sup = est[est.publication_status == "suppressed_unreliable"]
vals = ["employed", "se", "cv", "ci95_low", "ci95_high", "share_of_employed"]
rec("B", "B1_epen_suppressed_blank", "EPEN suppressed rows have blank values", f"{len(sup)} suppressed rows; non-blank cells: {int(sup[vals].notna().sum().sum())}",
    sup[vals].isna().all().all(), "Critico", "Blank suppressed values")
cvp = num(pub.cv); up = num(pub.unique_persons)
rec("B", "B1_epen_published_rule", "EPEN published rows: CV<=30% and >=30 unique persons", f"max CV {cvp.max():.3f}; min unique {int(up.min())}",
    (cvp <= 0.30).all() and (up >= 30).all(), "Critico", "Apply D-PE-03")
lp = pub[(cvp > 0.15)]
rec("B", "B1_epen_lowprec_flag", "EPEN rows with 15%<CV<=30% flagged publish_low_precision", f"{len(lp)} rows: {lp.group_id.tolist()}",
    (lp.publication_status == "publish_low_precision").all() and (pub[cvp <= 0.15].publication_status == "publish").all(), "Mayor", "Flag")
for nm in ["f_cno_code_counts_pe.csv", "f_occupation_mapping_pe.csv"]:
    t = pd.read_csv(os.path.join(D, nm)); n = "records" if "records" in t.columns else "sample_records"; w = "employed" if "employed" in t.columns else "weighted_employed"
    small = num(t[n]) < 30
    rec("B", f"B1_{nm}", f"{nm}: weighted value blank when <30 records", f"{int(small.sum())} small cells, non-blank {int(t.loc[small, w].notna().sum())}",
        t.loc[small, w].isna().all(), "Critico", "Blank small cells")
prof = pd.read_csv(os.path.join(D, "f_persona_profiles_pe.csv"))
bad = prof[(prof.small_cell.astype(str) == "True") & prof.value.notna()]
supg = set(sup.group_id)
bad2 = prof[prof.group_id.isin(supg) & prof.value.notna()]
rec("B", "B1_profiles", "EPEN profiles: small cells and suppressed groups blank", f"small-cell leaks {len(bad)}, suppressed-group leaks {len(bad2)}", len(bad) == 0 and len(bad2) == 0, "Critico", "Blank")
p9 = f9[f9.status.str.startswith("publish")]
rec("B", "B1_f9_rule", "F9 published cells CV<=30%; low precision iff 15%<CV<=30%; suppressed blank",
    f"{len(p9)} published (max CV {p9.cv.max():.3f}); suppressed with value: {int(f9[~f9.status.str.startswith('publish')].share.notna().sum())}",
    (p9.cv <= 0.30).all() and ((p9.cv > 0.15) == (p9.status == "publish_low_precision")).all() and f9[~f9.status.str.startswith("publish")].share.isna().all(),
    "Critico", "Apply D-PE-03")
g_sup = f1[f1.status == "suppressed_unreliable"]
rec("B", "B1_f1enaho_rule", "ENAHO F1: suppressed groups blank; published CV<=30% and n>=30",
    f"suppressed {len(g_sup)} (values present {int(g_sup.enaho_employed.notna().sum())}); published max CV {f1[f1.status!='suppressed_unreliable'].enaho_cv.max():.3f}",
    g_sup.enaho_employed.isna().all() and (f1[f1.status != "suppressed_unreliable"].enaho_cv <= 0.30).all() and (f1[f1.status != "suppressed_unreliable"].unique_persons >= 30).all(), "Critico", "Apply")
dpub = dsg[~dsg.status.str.contains("suppressed")]; dsup = dsg[dsg.status.str.contains("suppressed")]
rec("B", "B1_designers_rule", "Designers table: suppressed blank, published CV<=30%", f"published max CV {num(dpub.cv).max():.3f}; suppressed with value {int(dsup.employed.notna().sum())}",
    (num(dpub.cv) <= 0.30).all() and dsup.employed.isna().all(), "Critico", "Apply")
# D-PE-12: main spec PSU-only; sensitivity column is stratified
src = open(os.path.join(PKG, "scripts", "layer_f_enaho_f9_pe.py")).read()
main_psu = re.search(r'^sp = pd\.DataFrame\(\{"s": "all"', src, re.M) is not None
rec("B", "B2_dpe12_code", "ENAHO script main variance frame = PSU only (D-PE-12); stratified only as sensitivity",
    f"main PSU-only: {main_psu}; sensitivity column present: {'se_ratio_stratified_vs_main' in f9.columns}", main_psu and "se_ratio_stratified_vs_main" in f9.columns
    and "se_ratio_psu_only_vs_main" not in f9.columns, "Mayor", "Apply D-PE-12")
r = f9.se_ratio_stratified_vs_main.dropna()
rec("B", "B2_dpe12_values", "Published SE are PSU-only (stratified/main ratio <= ~1 except design-coincident cells)",
    f"stratified/main ratio: median {r.median():.3f}, p95 {r.quantile(.95):.3f}, max {r.max():.3f}", r.median() <= 1.0001, "Mayor", "Recompute")
v1 = pd.read_csv(os.path.join(V, "enaho_vs_inei_official_validation_pe.csv"))
nat = v1[(v1.table.str.startswith("I.17")) & (v1.domain == "Nacional")].iloc[0]
pub_ref = f1[f1.group_id == "REF_ALL_EMPLOYED"]
rec("B", "B2_se_vs_official", "PSU-only SE replicates official I.17 SE (13 domains) within 0-5%",
    f"PSU-only/official: {(v1.se_psu_only/v1.official_se).min():.3f}-{(v1.se_psu_only/v1.official_se).max():.3f}; national {nat.se_psu_only:.3f} vs {nat.official_se:.3f}",
    ((v1.se_psu_only / v1.official_se).dropna().between(0.99, 1.05)).all(), "Mayor", "Review spec")
pf9 = pd.read_csv(PREV_F9); pf1 = pd.read_csv(PREV_F1)
m9 = pf9.merge(f9, on=["group_id", "indicator", "category"], suffixes=("_o", "_n")); m1 = pf1.merge(f1, on="group_id", suffixes=("_o", "_n"))
rec("B", "B3_no_status_change", "No status change in 300 F9 cells and 25 ENAHO groups after D-PE-12",
    f"F9 cells compared {len(m9)}, changed {int((m9.status_o != m9.status_n).sum())}; F1 groups {len(m1)}, changed {int((m1.status_o != m1.status_n).sum())}; shares identical {bool((m9.share_o.fillna(-1).round(10)==m9.share_n.fillna(-1).round(10)).all())}",
    len(m9) == 300 and len(m1) == 25 and (m9.status_o == m9.status_n).all() and (m1.status_o == m1.status_n).all(), "Mayor", "Investigate")
# ---------------- C. official validation
rec("C", "C1_V1", "V1: 21 official figures reproduced (I.17 x13, III.1 x3, III.4 x3, I.1 national)",
    f"PASS {int((v1.status=='PASS').sum())}, NOT_COMPUTED {int((v1.status=='NOT_COMPUTED').sum())}, FAIL {int((v1.status=='FAIL').sum())}; national {nat.estimate:.3f} vs {nat.official}",
    int((v1.status == "PASS").sum()) == 20 and int((v1.status == "FAIL").sum()) == 0, "Critico", "Investigate")
ec = pd.read_csv(os.path.join(V, "f_employed_totals_check_pe.csv")); sc = pd.read_csv(os.path.join(V, "enaho_sumaria_checks_pe.csv"))
rec("C", "C2_epen_controls", "EPEN controls vs INEI (employment report 2025)", f"{int((ec.status=='PASS').sum())}/{len(ec)} PASS", (ec.status == "PASS").all(), "Critico", "Investigate")
rec("C", "C3_enaho_controls", "ENAHO Sumaria controls (poverty, expenditure, vulnerability)", f"{int((sc.status=='PASS').sum())} PASS, {int((sc.status=='INFO').sum())} INFO, {int((sc.status=='FAIL').sum())} FAIL", (sc.status != "FAIL").all(), "Critico", "Investigate")
# registry hashes vs files on disk
reg = pd.read_csv(os.path.join(D, "source_registry_layer_f_pe.csv"), dtype=str).fillna("")
H = {}
for f in glob.glob(os.path.join(RAW, "**", "*"), recursive=True):
    if os.path.isfile(f) and os.path.getsize(f) < 400_000_000:
        H[hashlib.sha256(open(f, "rb").read()).hexdigest()] = os.path.relpath(f, RAW)
full_hashes = set(re.findall(r"\b[0-9a-f]{64}\b", " ".join(reg.sha256.tolist() + reg.zip_sha256.tolist())))
upl = "/root/.claude/uploads/354e8a61-2f41-59b6-b0f9-6e3afd91e5c0"
for f in glob.glob(os.path.join(upl, "*")):
    H.setdefault(hashlib.sha256(open(f, "rb").read()).hexdigest(), "upload:" + os.path.basename(f))
miss = [h[:12] for h in full_hashes if h not in H]
rec("C", "C4_registry_hashes", "Every full SHA-256 in the source registry matches a file actually received",
    f"{len(full_hashes)} full hashes in registry; unmatched: {miss}", not miss, "Mayor", "Correct registry")
reqs = reg[reg.source_id.str.startswith("REQ_")][["source_id", "access"]].values.tolist()
rec("C", "C5_open_requests", "Open requests listed in registry", "; ".join(f"{a}" for a, b in reqs), True)

# ---------------- E. package hygiene
ids = {"CONGLOMERADO", "CONGLOME", "CODPERSO", "LLAVE_PANEL", "SELVIV", "VIVIENDA", "C201", "UBIGEO"}
leaks = []
for f in glob.glob(os.path.join(PKG, "**", "*.csv"), recursive=True):
    cols = set(pd.read_csv(f, nrows=0).columns)
    if cols & ids:
        leaks.append(os.path.basename(f))
big = [os.path.basename(f) for f in glob.glob(os.path.join(PKG, "**", "*"), recursive=True) if os.path.isfile(f) and (os.path.getsize(f) > 5_000_000 or f.endswith((".pkl", ".sav", ".dta", ".xlsx")))]
rec("E", "E1_no_microdata", "No respondent identifiers, microdata or official source files inside the package", f"id-column files {leaks}; large/raw files {big}", not leaks and not big, "Critico", "Remove")
sums = open(os.path.join(V, "SHA256SUMS.txt")).read().split("\n")
badh = []
for l in sums:
    if not l.strip():
        continue
    h, p = l.split("  ", 1); fp = os.path.join(os.path.dirname(PKG), p)
    if not os.path.exists(fp) or hashlib.sha256(open(fp, "rb").read()).hexdigest() != h:
        badh.append(p)
rec("E", "E2_sha256sums", "SHA256SUMS.txt verifies against package files", f"{len([l for l in sums if l.strip()])} entries; mismatches {badh}", not badh, "Mayor", "Regenerate hashes")
pd.DataFrame(R).to_csv(OUT, index=False)
print(pd.DataFrame(R)[["check_id", "result", "evidence"]].to_string(max_colwidth=120))
print("PASS", sum(r["result"] == "PASS" for r in R), "FAIL", sum(r["result"] == "FAIL" for r in R))
