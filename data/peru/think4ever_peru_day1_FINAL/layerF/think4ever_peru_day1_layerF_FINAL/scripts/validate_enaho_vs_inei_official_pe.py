"""Validate ENAHO 2025 household-level reproduction against INEI's official statistical annex
('Peru: Evolucion de la Pobreza Monetaria 2016-2025', Anexo Estadistico en Excel).

Compares: I.17 real per-capita income (mean, SE, CI) by 13 geographic domains; III.1 poverty; III.4 extreme poverty;
I.1 real per-capita expenditure (national/urban/rural). SE compared under the Think4ever specification
(PSU = CONGLOME, strata = department x ESTRATO) and the INEI do-file specification (PSU only).

Usage: python3 -I validate_enaho_vs_inei_official_pe.py <anexo_dir> <hh_quintiles_LOCAL_ONLY.pkl> <Sumaria-2025.csv> <out_csv>
"""
import sys, os, warnings
import numpy as np, pandas as pd, openpyxl
from openpyxl.utils import column_index_from_string as ci
warnings.filterwarnings("ignore")
AX, HH, SUM, OUT = sys.argv[1:5]

h = pd.read_pickle(HH)
s = pd.read_csv(SUM, sep=";", encoding="latin-1", dtype=str, keep_default_na=False, usecols=lambda c: c.upper() in
                {"CONGLOME", "VIVIENDA", "HOGAR", "GRU11HD"})
h["dep"] = h.UBIGEO.str[:2].replace({"07": "15"})
dom = h.DOMINIO.astype(int).values; a = h.area.values
W = h.factornd07.values
ST_T4E = (h.dep + "_" + h.ESTRATO.astype(str)).values
ST_NONE = np.zeros(len(h))
PSU = h.CONGLOME.values

def mean_se(y, mask, st):
    m = mask.astype(float); X = (W * m).sum(); R = (W * m * y).sum() / X; u = W * m * (y - R)
    t = pd.DataFrame({"s": st, "p": PSU, "u": u}).groupby(["s", "p"]).u.sum().reset_index(); v = 0.0
    for _, g in t.groupby("s"):
        k = len(g)
        if k > 1:
            z = g.u.values; v += k / (k - 1) * ((z - z.mean()) ** 2).sum()
    return R, v ** 0.5 / X

# gasto real per capita (from the quintile script output is not stored) -> recompute share via POBREZA only; expenditure mean
# is validated in enaho_sumaria_checks_pe.csv; here we read it back for the official comparison
checks_prev = pd.read_csv(os.path.join(os.path.dirname(HH), "enaho_sumaria_checks_pe.csv"))
g_mean = float(checks_prev.loc[checks_prev.check_id == "mean_real_pc_expenditure_month_2025", "estimate"].iloc[0])

MASK = {
    "Nacional": np.ones(len(h), bool), "Urbana": a == 1, "Rural": a == 2,
    "Costa": (dom <= 3) | (dom == 8), "Sierra": (dom >= 4) & (dom <= 6), "Selva": dom == 7,
    "Costa urbana": (dom <= 3) & (a == 1), "Costa rural": (dom <= 3) & (a == 2),
    "Sierra urbana": (dom >= 4) & (dom <= 6) & (a == 1), "Sierra rural": (dom >= 4) & (dom <= 6) & (a == 2),
    "Selva urbana": (dom == 7) & (a == 1), "Selva rural": (dom == 7) & (a == 2), "Lima Metropolitana": dom == 8}

rows = []
ws = openpyxl.load_workbook(os.path.join(AX, "01_Ingresos Reales_nominales_ 2016-2025_informe.xlsx"), data_only=True)["I.17"]
for r in range(9, 24):
    lab = ws[f"AW{r}"].value
    if not lab:
        continue
    lab = str(lab).strip(); key = "Lima Metropolitana" if lab.startswith("Lima") else lab
    if key not in MASK:
        continue
    off = [ws[f"{c}{r}"].value for c in ("AX", "AY", "AZ", "BA")]
    R, se = mean_se(h.ipcr_0.values, MASK[key], ST_T4E)
    _, se0 = mean_se(h.ipcr_0.values, MASK[key], ST_NONE)
    rows.append(dict(table="I.17 ingreso real per capita mensual 2025", domain=key, official=off[0], estimate=R, abs_diff=R - off[0],
                     official_se=off[1], se_t4e_spec=se, se_psu_only=se0, se_ratio_t4e_vs_official=se / off[1],
                     official_ci_low=off[2], official_ci_high=off[3], ci_low_t4e=R - 1.959964 * se, ci_high_t4e=R + 1.959964 * se,
                     status="PASS" if abs(R - off[0]) < 0.01 else "FAIL"))

def col2025(ws):
    for row in ws.iter_rows(min_row=1, max_row=12):
        for c in row:
            if c.value is not None and str(c.value).strip() in ("2025", "2025.0"):
                return c.column
fgt = openpyxl.load_workbook(os.path.join(AX, "03_FGT de Pobreza 2016-2025_informe.xlsx"), data_only=True)
gas = openpyxl.load_workbook(os.path.join(AX, "01_Gastos reales_nominales_2016_2025_informe.xlsx"), data_only=True)
pob = h.POBREZA.isin([1, 2]).astype(float).values; ext = (h.POBREZA == 1).astype(float).values
for wb, sh, nm, y, scale in [(fgt, "3.1", "III.1 incidencia pobreza 2025 (%)", pob, 100), (fgt, "3.4", "III.4 incidencia pobreza extrema 2025 (%)", ext, 100),
                             (gas, "I.1", "I.1 gasto real per capita mensual 2025", None, 1)]:
    ws = wb[sh]; c = col2025(ws); seen = set()
    for row in ws.iter_rows():
        lab = row[0].value
        if lab and str(lab).strip() in ("Nacional", "Urbana", "Rural") and str(lab).strip() not in seen:
            lab = str(lab).strip(); seen.add(lab); off = row[c - 1].value
            if y is None:
                est = g_mean if lab == "Nacional" else None
            else:
                est = mean_se(y, MASK[lab], ST_T4E)[0] * scale
            rows.append(dict(table=nm, domain=lab, official=off, estimate=est, abs_diff=(est - off) if est is not None else None,
                             status=("PASS" if est is not None and abs(est - off) < (0.01 if scale == 100 else 0.5) else ("NOT_COMPUTED" if est is None else "FAIL"))))
pd.DataFrame(rows).to_csv(OUT, index=False)
df = pd.DataFrame(rows)
print(df[["table", "domain", "official", "estimate", "abs_diff", "status"]].to_string())
x = df.dropna(subset=["se_ratio_t4e_vs_official"])
print("SE ratio T4E/official: min %.3f median %.3f max %.3f" % (x.se_ratio_t4e_vs_official.min(), x.se_ratio_t4e_vs_official.median(), x.se_ratio_t4e_vs_official.max()))
print("SE ratio PSU-only/official: min %.3f median %.3f max %.3f" % ((x.se_psu_only / x.official_se).min(), (x.se_psu_only / x.official_se).median(), (x.se_psu_only / x.official_se).max()))
