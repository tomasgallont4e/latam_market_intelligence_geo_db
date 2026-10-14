"""Layer F - Peru - F9 (socioeconomic level) from INEI ENAHO 2025, kept SEPARATE from EPEN.

Inputs
  <m500_csv>     Enaho01a-2025-500.csv (module 05, empleo e ingresos)
  <hh_pkl>       hh_quintiles_LOCAL_ONLY.pkl from enaho_sumaria_quintiles_pe.py (Sumaria 8g, ipcr_0, quintiles)
  <epen_est_csv> f_persona_estimates_internal_pe.csv (EPEN run) - ONLY to reuse the identical CNO 2015 code sets per group
  <cno_table>    ENAHO-TABLA-CNO-2015.csv (INEI)
  <out_dir>

Universe: resident household members (P204=1 & P205=2, or P204=2 & P206=1), OCU500 = 1 (employed), main occupation
P505R4 (CNO 2015, 4 digits; 3-digit armed-forces codes zero-padded). Weight FAC500A (person employment factor).
F9a: share of each group in national POPULATION quintiles of real per-capita monthly household income (ipcr_0, INEI do-file).
F9b: share by ESTRSOCIAL (INEI frame stratum of the conglomerate: A-E urban, 6 = rural; Estratificacion del Marco, may 2026).
F1_diag: ENAHO employed per group - diagnostic only, never replaces EPEN F1.
Precision: Taylor linearisation, PSU = CONGLOME, no strata (D-PE-12: aligned with INEI; reproduces official I.17 SEs at
1.000-1.048x). Sensitivity: strata = department x ESTRATO (singletons collapsed), reported as se_ratio_stratified_vs_main.
Rules (approved D-PE-03): group suppressed if unique persons < 30 or group-total CV > 30%; cell suppressed if CV > 30%;
CV 15-30% = low precision.
"""
import sys, os, json, hashlib
import numpy as np, pandas as pd

M500, HH, EST, CNO, OUT = sys.argv[1:6]
os.makedirs(OUT, exist_ok=True)
Z = 1.959964

def num(x):
    return pd.to_numeric(x.astype(str).str.replace(",", ".", regex=False).str.strip(), errors="coerce")

cols = ["CONGLOME", "VIVIENDA", "HOGAR", "CODPERSO", "UBIGEO", "ESTRATO", "P204", "P205", "P206", "P505R4", "OCU500", "FAC500A"]
d = pd.read_csv(M500, sep=";", encoding="latin-1", dtype=str, keep_default_na=False, usecols=cols)
d = d.apply(lambda c: c.str.strip())
d["w"] = num(d.FAC500A)
res = ((d.P204 == "1") & (d.P205 == "2")) | ((d.P204 == "2") & (d.P206 == "1"))
U = d[res & (d.OCU500 == "1")].copy()
U["occ"] = U.P505R4.str.zfill(4)
cno = set(pd.read_csv(CNO, encoding="latin-1", dtype=str).iloc[:, 0].str.strip().str.zfill(4))
valid_share = float(U.w[U.occ.isin(cno)].sum() / U.w.sum())
hh = pd.read_pickle(HH)
U = U.merge(hh[["CONGLOME", "VIVIENDA", "HOGAR", "quintil_ipcr", "ESTRSOCIAL", "ipcr_0"]], on=["CONGLOME", "VIVIENDA", "HOGAR"], how="left")
unmatched = int(U.quintil_ipcr.isna().sum())
U = U[U.quintil_ipcr.notna()].reset_index(drop=True)
U["dep"] = U.UBIGEO.str[:2].replace({"07": "15"})
U["stratum"] = U.dep + "_" + U.ESTRATO
log = []
while True:
    n = U.groupby("stratum").CONGLOME.nunique()
    single = n[n < 2]
    if single.empty:
        break
    s = single.index[0]; dep, est = s.split("_")
    cands = sorted(x for x in n.index if x.startswith(dep + "_") and x != s)
    tgt = min(cands, key=lambda x: abs(int(x.split("_")[1]) - int(est)))
    U.loc[U.stratum == s, "stratum"] = tgt; log.append(f"{s}->{tgt}")
w = U.w.values
sp = pd.DataFrame({"s": "all", "p": U.CONGLOME.values})   # main (D-PE-12): PSU only, as INEI

sp_alt = pd.DataFrame({"s": U.stratum.values, "p": U.CONGLOME.values})   # sensitivity: strata = department x ESTRATO

def var(u, frame=None):
    frame = sp if frame is None else frame
    t = frame.assign(u=u).groupby(["s", "p"])["u"].sum().reset_index()
    v = 0.0
    for _, g in t.groupby("s"):
        k = len(g)
        if k > 1:
            z = g.u.values; v += k / (k - 1) * ((z - z.mean()) ** 2).sum()
    return v

def total(y, frame=None):
    Y = float((w * y).sum()); return Y, var(w * y, frame) ** 0.5

def ratio(y, x, frame=None):
    X = float((w * x).sum())
    if X == 0:
        return None, None
    R = float((w * y).sum()) / X
    return R, var(w * (y - R * x), frame) ** 0.5 / X

est = pd.read_csv(EST, dtype={"cno2015_codes": str})
groups = est[est.group_type.isin(["persona", "ring_total", "combined_total", "combined_group", "informational_outside_rings", "reference"])
             | est.group_id.isin(["S8_excl_3315_3317"])]
occ = U.occ.values
pkey = (U.CONGLOME + U.VIVIENDA + U.HOGAR + U.CODPERSO).values
F1, F9 = [], []
ESTR = {1: "A", 2: "B", 3: "C", 4: "D", 5: "E", 6: "Rural"}
for _, r in groups.iterrows():
    gid = r.group_id
    codes = set(occ) if gid == "REF_ALL_EMPLOYED" else set(str(r.cno2015_codes).split(";"))
    m = np.isin(occ, sorted(codes)).astype(float)
    nrec, nuni = int(m.sum()), int(len(set(pkey[m == 1])))
    Y, se = total(m)
    cv = se / Y if Y else None
    _, se_alt = total(m, sp_alt)
    gsup = (nuni < 30) or (cv is None) or (cv > 0.30)
    F1.append(dict(source="ENAHO 2025", group_id=gid, template_persona_number=r.template_persona_number, label=r.label,
                   records=nrec, unique_persons=nuni, enaho_employed=round(Y, 1) if not gsup else None,
                   enaho_cv=cv if not gsup else None,
                   enaho_ci95_low=(round(Y - Z * se, 1) if not gsup else None), enaho_ci95_high=(round(Y + Z * se, 1) if not gsup else None),
                   se_ratio_stratified_vs_main=(se_alt / se if se else None), epen_employed_2025=(r.employed if r.publication_status != "suppressed_unreliable" else None),
                   enaho_vs_epen_ratio=(Y / r.employed if (not gsup and r.publication_status != "suppressed_unreliable" and r.employed) else None),
                   status="suppressed_unreliable" if gsup else ("diagnostic_low_precision" if cv > 0.15 else "diagnostic"),
                   use="diagnostic only - EPEN remains the F1 source; do not combine"))
    for ind, var_, cats in [("F9a_income_quintile", U.quintil_ipcr.astype(int).values, [1, 2, 3, 4, 5]),
                            ("F9b_estrato_socioeconomico", U.ESTRSOCIAL.astype(int).values, [1, 2, 3, 4, 5, 6])]:
        for c in cats + (["Q4_Q5"] if ind.startswith("F9a") else []):
            y = m * (np.isin(var_, [4, 5]) if c == "Q4_Q5" else (var_ == c))
            R, s_ = ratio(y, m)
            ccv = (s_ / R) if (R and R > 0) else None
            _, s_alt = ratio(y, m, sp_alt)
            ncell = int(y.sum())
            if gsup:
                st = "suppressed_group"
            elif R is None or ccv is None or ccv > 0.30:
                st = "suppressed_cell"
            else:
                st = "publish_low_precision" if ccv > 0.15 else "publish"
            pub = st.startswith("publish")
            F9.append(dict(source="ENAHO 2025", group_id=gid, indicator=ind,
                           category=("Q" + str(c) if isinstance(c, int) and ind.startswith("F9a") else (ESTR[c] if isinstance(c, int) else c)),
                           share=R if pub else None, se=s_ if pub else None, cv=ccv if pub else None,
                           ci95_low=(max(0, R - Z * s_) if pub else None), ci95_high=(min(1, R + Z * s_) if pub else None),
                           se_ratio_stratified_vs_main=(s_alt / s_ if (pub and s_) else None),
                           records_cell=ncell, records_group=nrec, unique_persons_group=nuni, status=st))
pd.DataFrame(F1).to_csv(os.path.join(OUT, "f1_enaho_diagnostic_pe.csv"), index=False)
pd.DataFrame(F9).to_csv(os.path.join(OUT, "f9_persona_socioeconomic_enaho_pe.csv"), index=False)
meta = dict(m500_sha256=hashlib.sha256(open(M500, "rb").read()).hexdigest(), employed_records=len(U), unmatched_to_sumaria=unmatched,
            employed_weighted=float(U.w.sum()), occ_valid_cno2015_share=valid_share, distinct_codes=int(U.occ.nunique()),
            psus=int(U.CONGLOME.nunique()), strata=int(U.stratum.nunique()), singleton_collapse=log)
json.dump(meta, open(os.path.join(OUT, "enaho_f9_meta_pe.json"), "w"), indent=1)
print(json.dumps(meta, indent=1))
