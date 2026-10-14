"""Layer F - Peru - INEI EPEN 2025 (Departamentos, anual) - 13 Think4ever personas.

Inputs
  <epen_csv>   EPEN 2025 BD_Publicacion Dpto.csv (INEI microdatos, modulo 1001-Modulo76)
  <corr_csv>   cno2015_ciuo08_correspondence.csv (from parse_cno2015_annex.py)
  <out_dir>

Universe: employed persons (OCUP300 = 1) with a non-missing annual expansion factor FAC300_ANUAL
(persons aged 14+, habitual residents). FAC300_ANUAL sums to the annual-average population
(validated against INEI published totals: annual, quarterly, urban, rural).

Occupation: C308_COD = CNO 2015 grupo primario (4 digits; 3-character values are armed-forces codes
whose leading zero was dropped -> zero-padded). Personas are defined in CIUO-08 (template Annex 2)
and mapped to CNO 2015 with the official INEI correspondence (CNO 2015 Annexes 3 and 4).

Precision: design-based linearisation (Taylor) for totals and ratios, strata = CCDD x ESTRATO,
PSU = CONGLOMERADO (all monthly visits of a PSU pooled in the PSU total, so repeated panel
interviews of the same person are handled as within-PSU correlation). These are computed by
Think4ever from official design variables; INEI does not publish occupation-level CVs.

Usage: python3 -I layer_f_epen_peru.py <epen_csv> <corr_csv> <out_dir>
"""
import csv, os, sys, hashlib
import numpy as np
import pandas as pd

EPEN, CORR, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)
Z = 1.959964

# ---- personas: canonical names (think4ever-13-personas-definicion.xlsx), rings, template CIUO-08 codes
PERSONAS = [
    (1, "Core", "Software developers and analysts", "2511 2512 2513 2514 2519"),
    (2, "Core", "Database, systems and network professionals", "2521 2522 2523 2529"),
    (3, "Core", "ICT technicians and user support", "3511 3512 3513 3514 3521 3522"),
    (4, "Core", "ICT managers", "1330"),
    (5, "Adjacent", "Designers (graphic, multimedia, product)", "2163 2166"),
    (6, "Adjacent", "Business and management analysts", "2421 2422"),
    (7, "Adjacent", "Finance and investment analysts", "2412 2413"),
    (8, "Adjacent", "Data, statistics and research specialists", "2120 2631 2632 3314"),
    (9, "Adjacent", "Marketing and advertising professionals", "2431 2432"),
    (10, "Extended", "Accountants and auditors", "2411"),
    (11, "Extended", "Engineers (non-ICT)", "2141 2142 2143 2144 2145 2146 2149 2151 2152 2153"),
    (12, "Extended", "Business and operations managers", "1211 1212 1213 1219 1221 1222 1223 1321 1322 1323 1324 1341 1342 1343 1344 1345 1346 1349"),
    (13, "Extended", "Higher-education and IT educators", "2310 2356"),
]
TEMPLATE_ALIAS = {3: "IT technicians and support", 4: "IT managers", 5: "Designers", 7: "Finance analysts",
                  8: "Data and research specialists", 13: "University and IT educators"}

# CNO 2015 codes excluded from the primary mapping (documented decisions) and sensitivities
EXCLUDED = {
    "1499": (12, "Annexes disagree: Annex 4 links CIUO 1349 -> CNO 1499; Annex 3 links CNO 1499 -> CIUO 1439 (not a persona code)"),
    "2312": (13, "CNO 'Profesores de educacion tecnico productiva' (CETPRO, not higher education); relative link to CIUO 2310 and 2353"),
    "3313": (8, "CNO 'Tecnicos en contabilidad': primary link CIUO 3313 (not a persona code); only a relative link to 3314"),
}
SENS = [  # (id, persona, description, add, remove)
    ("S12_add_1499", 12, "Persona 12 + CNO 1499 (otros gerentes de servicios)", ["1499"], []),
    ("S13_only_2353", 13, "Persona 13 = CNO 2353 only (IT instructors), without university professors 2311", [], ["2311"]),
    ("S13_add_2312", 13, "Persona 13 + CNO 2312 (CETPRO teachers)", ["2312"], []),
    ("S8_add_3313", 8, "Persona 8 + CNO 3313 (accounting technicians)", ["3313"], []),
    ("S8_excl_3317", 8, "Persona 8 without CNO 3317 (tecnicos en economia: comercio, exportacion, marketing; official link to CIUO 3314)", [], ["3317"]),
    ("S8_excl_3315_3317", 8, "Persona 8 professionals only (CNO 2120, 2631, 2632; no technician codes)", [], ["3315", "3317"]),
    ("S3_ict_only", 3, "Persona 3 ICT-only subset: without CNO 3521-3522 (broadcasting/audiovisual and telecom engineering technicians)", [], ["3521", "3522"]),
    ("S3_excl_3126", 3, "Persona 3 without CNO 3126 (IT service supervisors)", [], ["3126"]),
    ("S1_excl_2521", 1, "Persona 1 without CNO 2521 (soporte de sistemas -> CIUO 2511 per INEI)", [], ["2521"]),
    ("S2_add_2521", 2, "Persona 2 + CNO 2521 (alternative reading: support specialists as persona 2)", ["2521"], []),
]

SECTION = {}
for a, b, s in [(1, 3, "A"), (5, 9, "B"), (10, 33, "C"), (35, 35, "D"), (36, 39, "E"), (41, 43, "F"), (45, 47, "G"), (49, 53, "H"),
                (55, 56, "I"), (58, 63, "J"), (64, 66, "K"), (68, 68, "L"), (69, 75, "M"), (77, 82, "N"), (84, 84, "O"), (85, 85, "P"),
                (86, 88, "Q"), (90, 93, "R"), (94, 96, "S"), (97, 98, "T"), (99, 99, "U")]:
    for k in range(a, b + 1):
        SECTION[f"{k:02d}"] = s
DEPT = {"01": "Amazonas", "02": "Ancash", "03": "Apurimac", "04": "Arequipa", "05": "Ayacucho", "06": "Cajamarca", "08": "Cusco",
        "09": "Huancavelica", "10": "Huanuco", "11": "Ica", "12": "Junin", "13": "La Libertad", "14": "Lambayeque", "15": "Lima (incl. Callao)",
        "16": "Loreto", "17": "Madre de Dios", "18": "Moquegua", "19": "Pasco", "20": "Piura", "21": "Puno", "22": "San Martin",
        "23": "Tacna", "24": "Tumbes", "25": "Ucayali"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load():
    d = pd.read_csv(EPEN, dtype=str, keep_default_na=False)
    d["w"] = pd.to_numeric(d["FAC300_ANUAL"].str.replace(",", "."), errors="coerce")
    d["Q"] = (d["MES"].astype(int) - 1) // 3 + 1
    d["stratum"] = d["CCDD"] + "_" + d["ESTRATO"]
    # person key across panel visits (household-member order + sex guards against order-number reuse)
    d["pkey"] = d["CONGLOMERADO"] + "|" + d["SELVIV"] + "|" + d["HOGAR"] + "|" + d["C201"] + "|" + d["C207"]
    return d


def collapse_singletons(f):
    """Merge strata with a single PSU into the adjacent ESTRATO of the same department (documented)."""
    log = []
    while True:
        n = f.groupby("stratum")["CONGLOMERADO"].nunique()
        single = n[n < 2]
        if single.empty:
            return f, log
        s = single.index[0]
        dep, est = s.split("_")
        cands = sorted(x for x in n.index if x.startswith(dep + "_") and x != s)
        tgt = min(cands, key=lambda x: abs(int(x.split("_")[1]) - int(est)))
        f.loc[f["stratum"] == s, "stratum"] = tgt
        log.append(f"{s}->{tgt}")


class Design:
    """Linearised variance for totals/ratios over a fixed respondent frame."""

    def __init__(self, frame):
        self.f = frame.reset_index(drop=True)
        self.psu = self.f["CONGLOMERADO"].values
        self.st = self.f["stratum"].values
        self.w = self.f["w"].values
        g = self.f.groupby(["stratum", "CONGLOMERADO"]).size().reset_index()[["stratum", "CONGLOMERADO"]]
        self.n_h = g.groupby("stratum").size()
        self.n_psu, self.n_str = len(g), len(self.n_h)
        self.singletons = int((self.n_h == 1).sum())

    def _var(self, u):
        t = pd.DataFrame({"s": self.st, "p": self.psu, "u": u}).groupby(["s", "p"])["u"].sum().reset_index()
        v = 0.0
        for s, grp in t.groupby("s"):
            n = len(grp)
            if n < 2:
                continue  # singleton strata contribute 0 (counted in self.singletons; none expected)
            z = grp["u"].values
            v += n / (n - 1) * ((z - z.mean()) ** 2).sum()
        return v

    def total(self, y):
        Y = float((self.w * y).sum())
        se = self._var(self.w * y) ** 0.5
        return Y, se

    def ratio(self, y, x):
        Y, X = float((self.w * y).sum()), float((self.w * x).sum())
        R = Y / X
        se = self._var(self.w * (y - R * x)) ** 0.5 / X
        return R, se


def wmedian(v, w):
    o = np.argsort(v)
    v, w = v[o], w[o]
    c = np.cumsum(w)
    return float(v[np.searchsorted(c, 0.5 * c[-1])])


def tconf(n):
    return "high" if n >= 1000 else ("medium" if n >= 300 else "low")


def main():
    d = load()
    corr = list(csv.DictReader(open(CORR, encoding="utf-8")))
    cno_valid = {r["cno"] for r in corr}

    # ---------- universe & checks
    emp_all = d[d["OCUP300"] == "1"]
    U = emp_all[emp_all["w"].notna()].copy()
    U["occ"] = U["C308_COD"].str.zfill(4)
    U["ind"] = U["C309_COD"].str.zfill(4)
    U, collapse_log = collapse_singletons(U)
    pea = d[d["OCUP300"].isin(["1", "2"]) & d["w"].notna()]
    checks = []
    def chk(name, est, off, tol, note=""):
        diff = est / off - 1 if off else None
        checks.append(dict(check_id=name, estimate=round(est, 1), official=off, rel_diff=diff, tolerance=tol,
                           status="PASS" if (diff is not None and abs(diff) <= tol) else "FAIL", note=note))
    chk("employed_annual_2025", U["w"].sum(), 17575200, 0.005, "INEI EPEN informe tecnico anual 2025 (Andina 15-02-2026): 17 575,2 mil")
    for q, off in [(1, 17374000), (4, 17834800)]:
        chk(f"employed_Q{q}_2025", U.loc[U.Q == q, "w"].sum() * 4, off, 0.005,
            "Q1: INEI informe tecnico I trim 2025 (17 374,0 mil); Q4: INEI anual/IV trim 2025 (17 834,8 mil). Quarter = 4 x sum of FAC300_ANUAL")
    chk("employed_urban_2025", U.loc[U.AREA == "1", "w"].sum(), 14019200 + 267800, 0.005, "INEI 2024 urbano 14 019,2 mil + variacion 2025 267,8 mil")
    chk("employed_rural_2025", U.loc[U.AREA == "2", "w"].sum(), 3303700 - 15600, 0.005, "INEI 2024 rural 3 303,7 mil + variacion 2025 -15,6 mil")
    for sx, off in [("1", 0.042), ("2", 0.057)]:
        pp = pea[pea.C207 == sx]
        r_ = pp.loc[pp.OCUP300 == "2", "w"].sum() / pp["w"].sum()
        checks.append(dict(check_id=f"open_unemployment_rate_sex{sx}_2025", estimate=round(r_, 4), official=off, rel_diff=r_ - off, tolerance=0.0005,
                           status="PASS" if abs(r_ - off) <= 0.0005 else "FAIL", note="INEI 2025: hombres 4,2%, mujeres 5,7%"))
    lm = U[(U.DIVISION_LIMA == "1")]
    iw = pd.to_numeric(lm["ingtrabw"], errors="coerce")
    li = float(np.average(iw[iw > 0], weights=lm["w"][iw > 0]))
    chk("lima_mean_labour_income_2025", li, 2486.0, 0.005, "INEI 2025 Lima Metropolitana y Callao S/ 2 486,0 = weighted mean of ingtrabw > 0")
    # INEI informe tecnico anual 2025 (Feb 2026), read directly at inei.gob.pe (SRC_INEI_EPEN_IT_ANUAL_2025)
    IT = "INEI 'Peru: Comportamiento de los indicadores del mercado laboral a nivel nacional y en 27 ciudades', ene-dic 2025 (feb 2026)"
    chk("employed_men_2025", U.loc[U.C207 == "1", "w"].sum(), 9751500, 0.005, IT)
    chk("employed_women_2025", U.loc[U.C207 == "2", "w"].sum(), 7823700, 0.005, IT)
    szn = pd.to_numeric(U["C317A"], errors="coerce")
    chk("employed_size_1_10_2025", U.loc[szn <= 10, "w"].sum(), 12601300, 0.005, IT + "; bands from C317A")
    chk("employed_size_11_50_2025", U.loc[(szn > 10) & (szn <= 50), "w"].sum(), 1381400, 0.005, IT + "; bands from C317A")
    chk("employed_size_51plus_2025", U.loc[szn > 50, "w"].sum(), 3592400, 0.005, IT + "; bands from C317A")
    dv = U["ind"].str[:2].astype(int)
    for nm, msk, off in [("agri_fish_mining", dv <= 9, 4219700), ("manufacturing", (dv >= 10) & (dv <= 33), 1518400),
                         ("construction", (dv >= 41) & (dv <= 43), 1169700), ("commerce", (dv >= 45) & (dv <= 47), 3335200),
                         ("services", ~((dv <= 33) | ((dv >= 41) & (dv <= 47))), 7332200)]:
        chk(f"employed_branch_{nm}_2025", U.loc[msk, "w"].sum(), off, 0.005, IT + "; CIIU Rev.4 divisions of C309_COD (01-09, 10-33, 41-43, 45-47, rest)")
    chk("unemployed_2025", d.loc[(d.OCUP300 == "2") & d.w.notna(), "w"].sum(), 902100, 0.005, IT)
    inf = U.loc[U.Informal_P == "1", "w"].sum() / U["w"].sum()
    checks.append(dict(check_id="informality_rate_2025", estimate=round(inf, 4), official=0.702, rel_diff=inf - 0.702, tolerance=0.0005,
                       status="PASS" if abs(inf - 0.702) <= 0.0005 else "FAIL", note=IT + "; Informal_P = 1"))
    for ar, off in [("1", 0.057), ("2", 0.014)]:
        pp = pea[pea.AREA == ar]
        r_ = pp.loc[pp.OCUP300 == "2", "w"].sum() / pp["w"].sum()
        checks.append(dict(check_id=f"open_unemployment_rate_area{ar}_2025", estimate=round(r_, 4), official=off, rel_diff=r_ - off, tolerance=0.0005,
                           status="PASS" if abs(r_ - off) <= 0.0005 else "FAIL", note=IT))
    ur = d.loc[(d.OCUP300 == "2") & d.w.notna(), "w"].sum() / pea["w"].sum()
    checks.append(dict(check_id="open_unemployment_rate_2025", estimate=round(ur, 4), official=0.049, rel_diff=ur - 0.049, tolerance=0.0005,
                       status="PASS" if abs(ur - 0.049) <= 0.0005 else "FAIL", note="OCUP300=2 / (OCUP300 in 1,2); INEI 4,9%"))
    chk("occ_code_valid_cno2015_share", float(U["w"][U.occ.isin(cno_valid)].sum() / U.w.sum()), 1.0, 0.0,
        "After zero-padding 3-char armed-forces codes")

    # ---------- mapping table
    by_ciuo = {}
    for r in corr:
        by_ciuo.setdefault(r["ciuo"], []).append(r)
    by_cno = {}
    for r in corr:
        by_cno.setdefault(r["cno"], []).append(r)
    ciuo2p = {c: p for p, _, _, s in PERSONAS for c in s.split()}
    pcodes = {p: set() for p, *_ in PERSONAS}
    maprows = []
    for c in sorted({r["cno"] for r in corr if r["ciuo"] in ciuo2p}):
        targets = by_cno[c]
        tp = {ciuo2p.get(t["ciuo"]) for t in targets}
        in_p = sorted({t["ciuo"] for t in targets if t["ciuo"] in ciuo2p})
        out_p = sorted({t["ciuo"] for t in targets if t["ciuo"] not in ciuo2p})
        persona = ciuo2p[in_p[0]]
        if c in EXCLUDED:
            status, note, prim = "excluded_ambiguous", EXCLUDED[c][1], False
        elif len(tp - {None}) > 1:
            status, note, prim = "cross_persona", "links to several personas", False
        elif out_p:
            status, note, prim = "relative_link_outside_persona", "CNO title is specific to the persona; INEI relative links also to " + ";".join(out_p), True
        else:
            status, note, prim = "exact_within_persona", "", True
        if prim:
            pcodes[persona].add(c)
        enl = ";".join(f"{t['ciuo']}:{t['cno_enlace']}{t['ciuo_enlace']}" for t in targets)
        src = ";".join(sorted({("A3" if t["in_annex3"] == "True" else "") + ("A4" if t["in_annex4"] == "True" else "") for t in targets}))
        maprows.append(dict(template_persona_number=persona, persona=PERSONAS[persona - 1][2], ring=PERSONAS[persona - 1][1],
                            cno2015_code=c, cno2015_title=targets[0]["cno_title"], ciuo08_codes_linked=";".join(t["ciuo"] for t in targets),
                            ciuo08_codes_in_persona=";".join(in_p), enlace_cno_ciuo=enl, annex_source=src,
                            mapping_status=status, in_primary=prim, note=note,
                            sample_records=int((U.occ == c).sum()), weighted_employed=round(float(U.w[U.occ == c].sum()), 1)))
    # CIUO persona codes with no reliable CNO code
    for p, ring, name, s in PERSONAS:
        for ci in s.split():
            linked = [r["cno"] for r in by_ciuo.get(ci, [])]
            if not any(x in pcodes[p] for x in linked):
                maprows.append(dict(template_persona_number=p, persona=name, ring=ring, cno2015_code="", cno2015_title="",
                                    ciuo08_codes_linked=ci, ciuo08_codes_in_persona=ci, enlace_cno_ciuo="",
                                    annex_source="", mapping_status="ciuo_without_reliable_cno_code", in_primary=False,
                                    note="CIUO code only reachable through: " + (";".join(linked) or "none"), sample_records=0, weighted_employed=0))
    assert sum(len(v) for v in pcodes.values()) == len(set().union(*pcodes.values())), "double counting"

    # ---------- estimates
    D = Design(U)
    x1 = np.ones(len(D.f))
    occ = D.f["occ"].values
    est = []
    def add(gid, gtype, label, ring, codes, persona=None, additive=False):
        y = np.isin(occ, sorted(codes)).astype(float)
        sub = D.f[y == 1]
        Y, se = D.total(y)
        R, se_r = D.ratio(y, x1)
        n = int(y.sum())
        cv = se / Y if Y else None
        est.append(dict(group_id=gid, group_type=gtype, template_persona_number=persona, label=label, ring=ring,
                        cno2015_codes=";".join(sorted(codes)), records=n, unique_persons=int(sub["pkey"].nunique()),
                        psus=int(sub["CONGLOMERADO"].nunique()), employed=round(Y, 1), se=round(se, 1), cv=cv,
                        ci95_low=round(Y - Z * se, 1), ci95_high=round(Y + Z * se, 1), share_of_employed=R, share_se=se_r,
                        template_confidence=tconf(int(sub["pkey"].nunique())), cv_flag=("cv_le_15" if cv is not None and cv <= 0.15 else ("cv_15_30" if cv is not None and cv <= 0.30 else "cv_gt_30")),
                        additive_to_ring=additive,
                        publication_status=("suppressed_unreliable" if (cv is None or cv > 0.30 or sub["pkey"].nunique() < 30)
                                            else ("publish_low_precision" if cv > 0.15 else "publish"))))
    for p, ring, name, _ in PERSONAS:
        add(f"P{p:02d}", "persona", name, ring, pcodes[p], p, True)
    for ring in ["Core", "Adjacent", "Extended"]:
        codes = set().union(*[pcodes[p] for p, r, *_ in PERSONAS if r == ring])
        add(f"RING_{ring.upper()}", "ring_total", f"{ring} ring (sum of its personas)", ring, codes)
    add("ALL13", "combined_total", "13 personas combined", None, set().union(*pcodes.values()))
    add("COMB_P01_P02", "combined_group", "Personas 1+2 combined (CNO 251x + 252x): robust reading of the ICT-professional block", "Core", pcodes[1] | pcodes[2])
    add("INFO_3432", "informational_outside_rings", "CNO 3432 Disenadores y decoradores (CIUO 3432, technician level; NOT persona 5; not in any ring)", None, {"3432"})
    # D-PE-09 (approved option B): designers informational group, outside the 13 personas and the rings
    add("INFO_2163", "informational_outside_rings", "CNO 2163 Disenadores de productos y de prendas (code-level, informational)", None, {"2163"})
    add("INFO_2166", "informational_outside_rings", "CNO 2166 Disenadores graficos y multimedia (code-level, informational)", None, {"2166"})
    add("INFO_DESIGN_2163_2166_3432", "informational_outside_rings", "Designers informational group CNO 2163+2166+3432 (D-PE-09; not persona 5; not in any ring)", None, {"2163", "2166", "3432"})
    add("INFO_1150", "informational_outside_rings", "CNO 1150 Directores generales del sector privado de servicios TIC (national opening; INEI link to CIUO 1120, not persona 4; not in any ring)", None, {"1150"})
    for sid, p, desc, plus, minus in SENS:
        add(sid, "sensitivity", desc, PERSONAS[p - 1][1], (pcodes[p] | set(plus)) - set(minus), p)
    allc = set(U.occ.unique())
    add("REF_ALL_EMPLOYED", "reference", "All employed persons (universe)", None, allc)

    # ---------- profiles F3-F8 (+F6) for personas, rings, all employed
    f = D.f
    pos = np.select([f.C310 == "1", f.C310 == "2", f.C310.isin(["3", "7"]) & f.C311.isin(["1", "2", "3"]),
                     f.C310.isin(["3", "7"]) & f.C311.isin(["4", "5", "6"])],
                    ["employer", "self_employed", "government_employee", "private_employee"], "other_family_domestic_unpaid")
    size = pd.to_numeric(f.C317A, errors="coerce")
    sizeb = np.select([size == 1, size <= 10, size <= 50, size <= 200], ["1_alone", "2_10", "11_50", "51_200"], "201_plus")
    sect = f.ind.str[:2].map(SECTION).fillna("unknown")
    geo = np.where(f.DIVISION_LIMA == "1", "Lima Metropolitana y Callao", f.CCDD.map(DEPT))
    inc = pd.to_numeric(f.INGTOTP, errors="coerce").values
    incw = pd.to_numeric(f.ingtrabw, errors="coerce").values
    age = pd.to_numeric(f.C208, errors="coerce").values
    univ = f.C366.isin(["11", "12"]).values
    women = (f.C207 == "2").values
    groups = [(r["group_id"], set(r["cno2015_codes"].split(";"))) for r in est if r["group_type"] in ("persona", "ring_total", "combined_total", "combined_group", "informational_outside_rings", "reference")]
    allinc_med = wmedian(inc[inc > 0], f.w.values[inc > 0])
    prof = []
    def pr(gid, ind, cat, num_w, den_w, n_den, n_num, value=None, unit="proportion"):
        small = n_den < 30
        val = value if value is not None else (num_w / den_w if den_w else None)
        prof.append(dict(group_id=gid, indicator=ind, category=cat, value=None if small else val, unit=unit,
                         weighted_numerator=None if unit != "proportion" else round(num_w, 1), weighted_denominator=round(den_w, 1),
                         records_denominator=n_den, records_numerator=n_num, small_cell=small,
                         low_numerator=(n_num is not None and n_num < 30 and not small)))
    for gid, codes in groups:
        m = np.isin(occ, sorted(codes))
        w = f.w.values * m
        W, n = w.sum(), int(m.sum())
        for ind, var, cats in [("F3_position", pos, ["private_employee", "government_employee", "self_employed", "employer", "other_family_domestic_unpaid"]),
                               ("F4_company_size", sizeb, ["1_alone", "2_10", "11_50", "51_200", "201_plus"])]:
            for c in cats:
                k = m & (var == c)
                pr(gid, ind, c, f.w.values[k].sum(), W, n, int(k.sum()))
        kJ = m & (sect.values == "J")
        pr(gid, "F5_section_J_info_comm", "J", f.w.values[kJ].sum(), W, n, int(kJ.sum()))
        pr(gid, "F5_outside_tech", "not_J", W - f.w.values[kJ].sum(), W, n, n - int(kJ.sum()))
        for s in sorted(set(sect.values[m])):
            k = m & (sect.values == s)
            pr(gid, "F5_section", s, f.w.values[k].sum(), W, n, int(k.sum()))
        for g in sorted(set(geo[m])):
            k = m & (geo == g)
            pr(gid, "F6_geography", g, f.w.values[k].sum(), W, n, int(k.sum()))
        k = m & women; pr(gid, "F7_women", "women", f.w.values[k].sum(), W, n, int(k.sum()))
        k = m & univ; pr(gid, "F7_university_degree", "C366 in 11,12", f.w.values[k].sum(), W, n, int(k.sum()))
        pr(gid, "F7_median_age", "years", None, W, n, None, value=wmedian(age[m], f.w.values[m]) if n else None, unit="years")
        mi = m & (inc > 0)
        med = wmedian(inc[mi], f.w.values[mi]) if mi.sum() else None
        pr(gid, "F8_median_labour_income", "PEN_per_month", None, f.w.values[mi].sum(), int(mi.sum()), None, value=med, unit="PEN_month")
        pr(gid, "F8_income_vs_all_employed", "ratio", None, f.w.values[mi].sum(), int(mi.sum()), None,
           value=(med / allinc_med if med else None), unit="ratio")
        mt = m & (incw > 0)
        pr(gid, "F8b_median_total_labour_income_ingtrabw", "PEN_per_month", None, f.w.values[mt].sum(), int(mt.sum()), None,
           value=(wmedian(incw[mt], f.w.values[mt]) if mt.sum() else None), unit="PEN_month")
        k = m & (f.AREA == "2").values
        pr(gid, "F6_rural_share", "rural", f.w.values[k].sum(), W, n, int(k.sum()))

    # ---------- write
    def wcsv(name, rows):
        p = os.path.join(OUT, name)
        with open(p, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
    wcsv("f_employed_totals_check_pe.csv", checks)
    wcsv("f_occupation_mapping_pe.csv", maprows)
    wcsv("f_persona_estimates_pe.csv", est)
    wcsv("f_persona_profiles_pe.csv", prof)
    code_rows = (U.groupby("occ").agg(records=("w", "size"), employed=("w", "sum")).reset_index())
    wcsv("f_cno_code_counts_pe.csv", code_rows.rename(columns={"occ": "cno2015_code"}).round(1).to_dict("records"))
    meta = dict(epen_sha256=sha(EPEN), corr_sha256=sha(CORR), records_file=len(d), employed_records=len(U),
                employed_records_without_weight=int(emp_all["w"].isna().sum()), psus=D.n_psu, strata=D.n_str,
                singleton_strata=D.singletons, singleton_collapse=";".join(collapse_log), income_median_all=allinc_med,
                employed_unique_persons=int(U["pkey"].nunique()))
    pd.Series(meta).to_json(os.path.join(OUT, "f_run_meta_pe.json"), indent=1)
    print(meta)


if __name__ == "__main__":
    main()
