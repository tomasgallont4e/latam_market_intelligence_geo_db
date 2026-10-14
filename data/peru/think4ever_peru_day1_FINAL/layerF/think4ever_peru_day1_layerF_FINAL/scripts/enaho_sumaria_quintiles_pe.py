"""ENAHO 2025 (INEI) - Sumaria (8 grupos) -> real per-capita monthly household income (ipcr_0, official INEI
do-file '01_ConstrVarGastoIngreso2015-2025.do', ConstVarGasto-Metodologia actualizada_2025) and national
population quintiles/deciles. Controls: poverty rates (POBREZA) vs INEI 2025.

Usage: python3 -I enaho_sumaria_quintiles_pe.py <Sumaria-2025.csv> <deflactores_base2025_new.dta> <despacial_ldnew.dta> <out_dir>
"""
import sys, os, json, hashlib
import numpy as np, pandas as pd

SUM, DEF, LD, OUT = sys.argv[1:5]
os.makedirs(OUT, exist_ok=True)

def num(x):
    return pd.to_numeric(x.astype(str).str.replace(",", ".", regex=False).str.strip(), errors="coerce")

s = pd.read_csv(SUM, sep=";", encoding="latin-1", dtype=str, keep_default_na=False)
s.columns = [c.upper() for c in s.columns]
keys = ["CONGLOME", "VIVIENDA", "HOGAR", "UBIGEO", "DOMINIO", "ESTRATO", "MES"]
v = {c: (num(s[c]).fillna(0.0) if c in s.columns else pd.Series(0.0, index=s.index)) for c in
     "MIEPERHO FACTOR07 ESTRSOCIAL POBREZA INGHOG2D INGBRUHD INGINDHD INSEDTHD INGSEIHD INSEDTHD1 PAGESPHD PAESECHD INGAUTHD ISECAUHD PAESECHD1 INGEXTHD INGTRAHD INGTEXHD INGRENHD INGOEXHD GRU13HD3 GRU23HD3 GRU33HD3 GRU43HD3 GRU53HD3 GRU63HD3 GRU73HD3 GRU83HD3 GRU24HD GRU44HD GRU54HD GRU74HD GRU84HD GRU14HD5 IA01HD GRU34HD GA04HD GRU64HD GRU13HD1 SIG24 GRU23HD1 GRU33HD1 GRU43HD1 GRU53HD1 GRU63HD1 GRU73HD1 GRU83HD1 GRU14HD3 SIG26 SIG28 GRU13HD2 IG06HD GRU23HD2 GRU33HD2 GRU43HD2 GRU53HD2 GRU63HD2 IG08HD GRU73HD2 GRU83HD2 GRU14HD4 SG42D SG42D1 SG42D2 SG42D3".split()}
GASTO = "GRU11HD GRU12HD1 GRU12HD2 GRU13HD1 GRU13HD2 GRU13HD3 G05HD G05HD1 G05HD2 G05HD3 G05HD4 G05HD5 G05HD6 SG23 GRU14HD GRU14HD1 GRU14HD2 GRU14HD3 GRU14HD4 GRU14HD5 SG25 SG27 GRU21HD GRU22HD1 GRU22HD2 GRU23HD1 GRU23HD2 GRU23HD3 GRU24HD GRU31HD GRU32HD1 GRU32HD2 GRU33HD1 GRU33HD2 GRU33HD3 GRU41HD GRU42HD1 GRU42HD2 GRU43HD1 GRU43HD2 GRU43HD3 GRU44HD SG421 SG423 GRU51HD GRU52HD1 GRU52HD2 GRU53HD1 GRU53HD2 GRU53HD3 GRU61HD GRU62HD1 GRU62HD2 GRU63HD1 GRU63HD2 GRU63HD3 G07HD SG422 GRU71HD GRU72HD1 GRU72HD2 GRU73HD1 GRU73HD2 GRU73HD3 SG42 GRU81HD GRU82HD1 GRU82HD2 GRU83HD1 GRU83HD2 GRU83HD3 POBREZAV".split()
for c in GASTO:
    if c not in v:
        v[c] = num(s[c]).fillna(0.0) if c in s.columns else pd.Series(0.0, index=s.index)
missing_vars = sorted(c for c in v if c not in s.columns)
h = s[keys].copy()
for c, x in v.items():
    h[c] = x
# --- official do-file steps
h["dpto"] = h.UBIGEO.str[:2].astype(int).replace({7: 15})
dom = h.DOMINIO.astype(int); est = h.ESTRATO.astype(int)
est = np.where(dom == 8, 1, est)
h["area"] = np.where(est < 6, 1, 2)
a = h.area
dA = np.select([(dom == 1) & (a == 1), (dom == 1) & (a == 2), (dom == 2) & (a == 1), (dom == 2) & (a == 2), (dom == 3) & (a == 1), (dom == 3) & (a == 2),
                (dom == 4) & (a == 1), (dom == 4) & (a == 2), (dom == 5) & (a == 1), (dom == 5) & (a == 2), (dom == 6) & (a == 1), (dom == 6) & (a == 2),
                (dom == 7) & (a == 1), (dom == 7) & (a == 2)], list(range(1, 15)), 0)
selva_baja = (dom == 7) & h.dpto.isin([16, 17, 25])
dA = np.where(selva_baja & (a == 1), 15, dA); dA = np.where(selva_baja & (a == 2), 16, dA); dA = np.where(dom == 8, 17, dA)
h["dominioA"] = dA
ld = pd.read_stata(LD); dfl = pd.read_stata(DEF)
h = h.merge(ld[["dominioA", "ld"]].astype({"dominioA": int}), on="dominioA", how="left")
d25 = dfl[dfl.aniorec == 2025][["dpto", "i00"]].astype({"dpto": int})
h = h.merge(d25, on="dpto", how="left")
assert h.ld.notna().all() and h.i00.notna().all()
p = 12
den = p * h.MIEPERHO * h.ld * h.i00
V = h
comp = dict(
    ipcr_2=(V.INGBRUHD + V.INGINDHD), ipcr_3=(V.INSEDTHD + V.INGSEIHD + V.INSEDTHD1),
    ipcr_4=(V.PAGESPHD + V.PAESECHD + V.INGAUTHD + V.ISECAUHD + V.PAESECHD1), ipcr_5=V.INGEXTHD,
    ipcr_7=V.INGTRAHD, ipcr_8=V.INGTEXHD, ipcr_16=V.INGRENHD,
    ipcr_17=(V.INGOEXHD + V.GRU13HD3 + V.GRU23HD3 + V.GRU33HD3 + V.GRU43HD3 + V.GRU53HD3 + V.GRU63HD3 + V.GRU73HD3 + V.GRU83HD3 + V.GRU24HD + V.GRU44HD + V.GRU54HD + V.GRU74HD + V.GRU84HD + V.GRU14HD5),
    ipcr_18=(V.IA01HD + V.GRU34HD - V.GA04HD + V.GRU64HD),
    ipcr_19=(V.GRU13HD1 + V.SIG24 + V.GRU23HD1 + V.GRU33HD1 + V.GRU43HD1 + V.GRU53HD1 + V.GRU63HD1 + V.GRU73HD1 + V.GRU83HD1 + V.GRU14HD3 + V.SIG26 + V.SIG28),
    ipcr_20=(V.GRU13HD2 + V.IG06HD + V.GRU23HD2 + V.GRU33HD2 + V.GRU43HD2 + V.GRU53HD2 + V.GRU63HD2 + V.IG08HD + V.GRU73HD2 + V.GRU83HD2 + V.GRU14HD4 + V.SG42D + V.SG42D1 + V.SG42D2 + V.SG42D3))
h["ipcr_0"] = sum(comp.values()) / den
# real per-capita expenditure gpgru0 (do-file, 8 groups; 2025 deflators i01..i08 = 1)
dfl8 = dfl[dfl.aniorec == 2025][["dpto"] + [f"i0{k}" for k in range(1, 9)]].astype({"dpto": int})
h = h.merge(dfl8, on="dpto", how="left")
g = lambda cols, i: sum(V[c] for c in cols.split()) / (p * h.MIEPERHO * h.ld * h[i])
V = h
h["gpgru0"] = (g("GRU11HD GRU12HD1 GRU12HD2 GRU13HD1 GRU13HD2 GRU13HD3", "i01")
    + g("G05HD G05HD1 G05HD2 G05HD3 G05HD4 G05HD5 G05HD6 IG06HD", "i01") + g("SG23 SIG24", "i01")
    + g("GRU14HD GRU14HD1 GRU14HD2 GRU14HD3 GRU14HD4 GRU14HD5 SG25 SIG26 SG27 SIG28", "i01")
    + g("GRU21HD GRU22HD1 GRU22HD2 GRU23HD1 GRU23HD2 GRU23HD3 GRU24HD", "i02")
    + g("GRU31HD GRU32HD1 GRU32HD2 GRU33HD1 GRU33HD2 GRU33HD3 GRU34HD", "i03")
    + g("GRU41HD GRU42HD1 GRU42HD2 GRU43HD1 GRU43HD2 GRU43HD3 GRU44HD SG421 SG42D1 SG423 SG42D3", "i04")
    + g("GRU51HD GRU52HD1 GRU52HD2 GRU53HD1 GRU53HD2 GRU53HD3 GRU54HD", "i05")
    + g("GRU61HD GRU62HD1 GRU62HD2 GRU63HD1 GRU63HD2 GRU63HD3 GRU64HD G07HD IG08HD SG422 SG42D2", "i06")
    + g("GRU71HD GRU72HD1 GRU72HD2 GRU73HD1 GRU73HD2 GRU73HD3 GRU74HD SG42 SG42D", "i07")
    + g("GRU81HD GRU82HD1 GRU82HD2 GRU83HD1 GRU83HD2 GRU83HD3 GRU84HD", "i08"))
h["ipc_inghog2d_check"] = h.INGHOG2D / den   # simpler variant, for diagnostics only
h["factornd07"] = (h.FACTOR07 * h.MIEPERHO).round(0)

# --- national population quantiles of ipcr_0 (weights = persons)
def wq(x, w, qs):
    o = np.argsort(x.values, kind="mergesort"); xs, ws = x.values[o], w.values[o]
    c = np.cumsum(ws) / ws.sum()
    return [float(xs[np.searchsorted(c, q)]) for q in qs]
q5 = wq(h.ipcr_0, h.factornd07, [0.2, 0.4, 0.6, 0.8])
q10 = wq(h.ipcr_0, h.factornd07, [i / 10 for i in range(1, 10)])
h["quintil_ipcr"] = 1 + np.searchsorted(q5, h.ipcr_0.values, side="right")
h["decil_ipcr"] = 1 + np.searchsorted(q10, h.ipcr_0.values, side="right")
W = h.factornd07
qshare = (W.groupby(h.quintil_ipcr).sum() / W.sum()).round(4).to_dict()

# --- controls vs INEI 2025 (Informe tecnico pobreza monetaria 2025, as reported 05-05-2026)
pobre = h.POBREZA.isin([1, 2]); ext = h.POBREZA == 1
def r(m, sub=None):
    sub = np.ones(len(h), bool) if sub is None else sub
    return float(W[m & sub].sum() / W[sub].sum())
chk = [("poverty_total_2025", r(pobre), 0.257), ("poverty_urban_2025", r(pobre, h.area.values == 1), 0.234),
       ("poverty_rural_2025", r(pobre, h.area.values == 2), 0.355), ("extreme_poverty_2025", r(ext), 0.047)]
checks = [dict(check_id=c, estimate=round(e, 4), official=o, abs_diff=round(e - o, 4), tolerance=0.0005,
               status="PASS" if abs(e - o) <= 0.0005 else "FAIL",
               note="INEI pobreza monetaria 2025 (El Peruano 05-05-2026); weight FACTOR07*MIEPERHO") for c, e, o in chk]
mg = float(np.average(h.gpgru0, weights=W))
checks.append(dict(check_id="mean_real_pc_expenditure_month_2025", estimate=round(mg, 1), official=920, abs_diff=round(mg - 920, 1), tolerance=1.0,
                   status="PASS" if abs(mg - 920) <= 1.0 else "FAIL", note="gpgru0 (INEI do-file); INEI 2025: S/ 920 (Infobae/Energiminas 05-05-2026)"))
vul = r(h.POBREZAV == 3)
checks.append(dict(check_id="vulnerable_non_poor_2025", estimate=round(vul, 4), official=0.328, abs_diff=round(vul - 0.328, 4), tolerance=0.0005,
                   status="PASS" if abs(vul - 0.328) <= 0.0005 else "FAIL", note="POBREZAV = 3; INEI 2025: 32,8%"))
ne = float(W[ext].sum())
checks.append(dict(check_id="extreme_poor_persons_2025", estimate=round(ne, 0), official=1614000, abs_diff=round(ne - 1614000, 0), tolerance=None,
                   status="PASS" if abs(ne / 1614000 - 1) <= 0.005 else "FAIL", note="INEI 2025: 1 614 mil (rel. tolerance 0.5%)"))
checks.append(dict(check_id="population_2025_persons", estimate=round(float(W.sum()), 0), official=None, abs_diff=None, tolerance=None,
                   status="INFO", note="Sum of FACTOR07*MIEPERHO (household members)"))
mean_ipcr = float(np.average(h.ipcr_0, weights=W))
checks.append(dict(check_id="mean_real_pc_income_month_2025", estimate=round(mean_ipcr, 1), official=None, abs_diff=None, tolerance=None,
                   status="INFO", note="Weighted mean of ipcr_0 (soles/month, Lima prices); INEI official 2025 value not yet sourced"))
pd.DataFrame(checks).to_csv(os.path.join(OUT, "enaho_sumaria_checks_pe.csv"), index=False)
cut = pd.DataFrame(dict(quantile=["Q1|Q2", "Q2|Q3", "Q3|Q4", "Q4|Q5"], cutpoint_soles_month_lima_prices=[round(x, 2) for x in q5]))
cut.to_csv(os.path.join(OUT, "enaho_quintile_cutpoints_pe.csv"), index=False)
h[["CONGLOME", "VIVIENDA", "HOGAR", "UBIGEO", "DOMINIO", "ESTRATO", "area", "dominioA", "ld", "MIEPERHO", "FACTOR07", "factornd07",
   "ipcr_0", "ipc_inghog2d_check", "quintil_ipcr", "decil_ipcr", "ESTRSOCIAL", "POBREZA"]].to_pickle(os.path.join(OUT, "hh_quintiles_LOCAL_ONLY.pkl"))
meta = dict(vars_absent_set_to_zero=missing_vars, sumaria_sha256=hashlib.sha256(open(SUM, "rb").read()).hexdigest(), households=len(h), quintile_cutpoints=q5,
            decile_cutpoints=q10, population_share_by_quintile=qshare, mean_ipcr_0=mean_ipcr,
            corr_ipcr0_vs_inghog2d_variant=float(np.corrcoef(h.ipcr_0, h.ipc_inghog2d_check)[0, 1]))
json.dump(meta, open(os.path.join(OUT, "enaho_sumaria_meta_pe.json"), "w"), indent=1)
print(json.dumps(meta, indent=1)); print(pd.DataFrame(checks).to_string())
