"""Peru Day 1 - build Layer A (GitHub) and Layer B (Stack Overflow) packages from the EXISTING outputs.
No indicator is recomputed for publication: tables are copied from the work outputs (byte-reproduced separately),
with metadata columns added (source_id, dataset_version, reconciliation, period_end_date), booleans in lower case,
and the Layer B column vs_latam_ex_pe renamed to vs_regional_ex_focus (values unchanged).

Usage: python3 -I build_layer_ab_packages_pe.py <work_a> <work_b> <ig_repo> <so_results_csv> <so_ai_json> <ar_final_pkg> <cl_final_pkg> <out_root>
"""
import sys, os, csv, json, hashlib, shutil, subprocess
import pandas as pd

WA, WB, IG, SO, AIJ, ARP, CLP, OUT = sys.argv[1:9]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
PA, PB = os.path.join(OUT, "think4ever_peru_day1_layerA_FINAL"), os.path.join(OUT, "think4ever_peru_day1_layerB_FINAL")
for P in (PA, PB):   # README.md (hand-written documentation) is preserved; generated sub-folders are rebuilt
    for s in ("data", "validation", "scripts"):
        shutil.rmtree(os.path.join(P, s), ignore_errors=True)
        os.makedirs(os.path.join(P, s), exist_ok=True)

def lowbool(df):
    for c in df.columns:
        if df[c].dtype == object and set(df[c].dropna().unique()) <= {"True", "False"} and df[c].notna().any():
            df[c] = df[c].str.lower()
    return df

def write(df, path):
    df.to_csv(path, index=False, quoting=csv.QUOTE_NONNUMERIC, lineterminator="\n")

# ================= LAYER A
ind = pd.read_csv(os.path.join(WA, "layer_a_pe_indicators.csv"), dtype=str, keep_default_na=False).replace("", None)
ind["previous_t4e_value"] = None
ind["reconciliation"] = "NO BENCHMARK (latam-country-breakdown-2026Q1.csv not supplied)"
ind["source_id"] = "SRC_GH_IG"
ind = ind[["indicator_id", "indicator_name", "country_code", "period_label", "comparison_period_label", "value", "unit", "numerator", "denominator",
           "method", "method_variant", "previous_t4e_value", "reconciliation", "source_id", "canonical_status", "validation_status"]]
lang = lowbool(pd.read_csv(os.path.join(WA, "layer_a_pe_languages.csv"), dtype=str, keep_default_na=False).replace("", None))
lang["source_id"] = "SRC_GH_IG"
lang = lang[["country_code", "period_label", "language", "language_type", "num_pushers", "rank_in_period", "in_a5_template_basket", "growth_eligible", "source_id", "growth_rule_status"]]
q = pd.read_csv(os.path.join(WA, "layer_a_pe_quarterly.csv"), dtype=str, keep_default_na=False)
q["period_end_date"] = q.apply(lambda r: {"1": "03-31", "2": "06-30", "3": "09-30", "4": "12-31"}[r.quarter].join([r.year + "-", ""]), axis=1)
q["dataset_version"] = "1.0.10"; q["source_id"] = "SRC_GH_IG"
q = q[["country_code", "metric", "metric_definition", "year", "quarter", "period_label", "period_end_date", "value", "dataset_version", "source_id"]]
for c in ("value", "numerator", "denominator"):
    ind[c] = pd.to_numeric(ind[c])
lang["num_pushers"] = pd.to_numeric(lang.num_pushers); lang["rank_in_period"] = pd.to_numeric(lang.rank_in_period)
for c in ("year", "quarter", "value"):
    q[c] = pd.to_numeric(q[c])
write(ind, os.path.join(PA, "data", "a_github_indicators_pe.csv"))
write(lang, os.path.join(PA, "data", "a_github_languages_pe.csv"))
write(q, os.path.join(PA, "data", "a_github_country_quarterly_pe.csv"))

hashes = json.load(open(os.path.join(WA, "layer_a_source_hashes.json")))
commit = subprocess.run(["git", "-C", IG, "log", "-1", "--format=%H|%ci"], capture_output=True, text=True).stdout.strip()
regA = [dict(source_id="SRC_GH_IG", source_name="GitHub Innovation Graph", publisher="GitHub", dataset_version="1.0.10 (docs/datasheet.md)",
             repo_commit=commit, reference_period="2020Q1-2026Q1 (indicators: 2026Q1 vs 2025Q1)", url="https://github.com/github/innovationgraph",
             access_date="2026-10-08", access_method="git clone (read-only)", files="; ".join(sorted(hashes)),
             sha256="; ".join(f"{k}: {v}" for k, v in sorted(hashes.items())), license="CC0-1.0 (repository LICENSE.md)",
             role="Layer A primary data (iso2_code = PE)", status="verified"),
        dict(source_id="REQ_T4E_LATAM_BREAKDOWN", source_name="latam-country-breakdown-2026Q1.csv (earlier Think4ever Layer A values)", publisher="Think4ever",
             dataset_version="", repo_commit="", reference_period="2026Q1", url="", access_date="", access_method="requested, not supplied", files="", sha256="",
             license="internal", role="Reconciliation benchmark (previous_t4e_value)", status="open request"),
        dict(source_id="INT_T4E_TEMPLATE", source_name="Think4ever country research template (EN), Layer A definitions", publisher="Think4ever", dataset_version="October 2026",
             repo_commit="", reference_period="", url="", access_date="2026-10-08", access_method="supplied",
             files="think4ever-plantilla-investigacion-paises-EN.pdf", sha256="", license="internal", role="Indicator definitions A1-A5", status="provided"),
        dict(source_id="INT_T4E_AR_CL_FINAL", source_name="Argentina and Chile Day 1 FINAL packages (method reference only; no values reused)", publisher="Think4ever",
             dataset_version="FINAL 2026-10-08", repo_commit="", reference_period="", url="", access_date="2026-10-08", access_method="supplied",
             files="think4ever_argentina_day1_FINAL.zip; think4ever_chile_day1_FINAL.zip", sha256="", license="internal",
             role="Method validation: the same script reproduces AR and CL published Layer A values", status="provided")]
write(pd.DataFrame(regA), os.path.join(PA, "data", "source_registry_layer_a_pe.csv"))

# method validation: script's AR/CL rows vs AR/CL FINAL packages
chk = []
for cc, pkg in (("ar", ARP), ("cl", CLP)):
    mine = pd.read_csv(os.path.join(WA, f"layer_a_{cc}_indicators.csv"))
    ref = pd.read_csv(os.path.join(pkg, "data", "a_github_indicators.csv"))
    m = ref.merge(mine, on=["indicator_id", "period_label"], suffixes=("_ref", "_new"))
    ok = (abs(m.value_ref - m.value_new) <= 1e-9 * m.value_ref.abs().clip(lower=1)).sum()
    chk.append(dict(check="method_reproduces_" + cc.upper() + "_FINAL_indicators", reference_rows=len(ref), compared=len(m), matches=int(ok),
                    result="PASS" if ok == len(m) and len(m) > 0 else "FAIL"))
latest = q[q.metric == "developers"].period_label.max()
chk.append(dict(check="latest_quarter_present", reference_rows="", compared="", matches="", result="PASS" if latest == "2026Q1" else "FAIL", detail=latest))
yoy = ind[ind.indicator_id == "A1_developer_accounts_yoy"].iloc[0]
chk.append(dict(check="growth_same_quarter_previous_year", reference_rows="", compared="", matches="",
                result="PASS" if (yoy.period_label, yoy.comparison_period_label) == ("2026Q1", "2025Q1") else "FAIL", detail=f"{yoy.period_label} vs {yoy.comparison_period_label}"))
devq = q[(q.metric == "developers") & (q.period_label == "2026Q1")].value.iloc[0]
a1 = ind[ind.indicator_id == "A1_developer_accounts"].value.iloc[0]
chk.append(dict(check="A1_equals_quarterly_series", reference_rows="", compared="", matches="", result="PASS" if devq == a1 else "FAIL", detail=f"{a1} vs {devq}"))
chk.append(dict(check="country_total_vs_innovation_graph_website", reference_rows="", compared="", matches="", result="NOT_VERIFIABLE",
                detail="Website not reachable from this environment; the repository data/ files are the published source of the website figures"))
write(pd.DataFrame(chk), os.path.join(PA, "validation", "a_validation_checks_pe.csv"))

# ================= LAYER B
bi = lowbool(pd.read_csv(os.path.join(WB, "b_survey_indicators_pe.csv"), dtype=str, keep_default_na=False).replace("", None))
assert "vs_latam_ex_pe" in bi.columns
bi = bi.rename(columns={"vs_latam_ex_pe": "vs_regional_ex_focus"})
bd = lowbool(pd.read_csv(os.path.join(WB, "b_survey_distributions_pe.csv"), dtype=str, keep_default_na=False).replace("", None))
bg = pd.read_csv(os.path.join(WB, "b_comparison_groups_pe.csv"), dtype=str, keep_default_na=False).replace("", None)
for df, cols in ((bi, ("survey_year", "numerator", "valid_n", "proportion", "ci_low", "ci_high")), (bd, ("survey_year", "numerator", "valid_n", "proportion")), (bg, ("respondents",))):
    for c in cols:
        df[c] = pd.to_numeric(df[c])
write(bi, os.path.join(PB, "data", "b_survey_indicators_pe.csv"))
write(bd, os.path.join(PB, "data", "b_survey_distributions_pe.csv"))
write(bg, os.path.join(PB, "data", "b_comparison_groups_pe.csv"))
defs = pd.read_csv(os.path.join(ARP, "data", "b_indicator_definitions.csv"), dtype=str, keep_default_na=False).replace("", None)
defs.loc[defs.indicator_id == "B5", "numerator_categories"] = 'rows with Country == "Peru"'
write(defs, os.path.join(PB, "data", "b_indicator_definitions_pe.csv"))

# reproduction check 1: official aggregate (ai.json) vs GLOBAL rows recomputed from the public CSV
aj = json.load(open(AIJ))
def off(q_, ds, yes):
    d = aj[q_]["datasets"][ds]; n = d["total_respondents"]; f = sum(x["frequency"] for x in d["data"] if x["response"] in yes)
    return n, f, f / n
G = bi[(bi.group_code == "GLOBAL") & (bi.survey_segment == "all_respondents")]
rows = []
for iid, q_, ds, yes in [("B1", "AISelect", "AISelect", {"Yes, I use AI tools daily", "Yes, I use AI tools weekly", "Yes, I use AI tools monthly or infrequently"}),
                         ("B2", "AISelect", "AISelect", {"Yes, I use AI tools daily"}),
                         ("B3", "AIAgents", "AIAgents", {"Yes, I use AI agents at work daily", "Yes, I use AI agents at work weekly", "Yes, I use AI agents at work monthly or infrequently"})]:
    n, f, p = off(q_, ds, yes); r = G[G.indicator_id == iid].iloc[0]
    rows.append(dict(check_type="official_aggregate_ai_json", focus_country_code="PE", group_code="GLOBAL", survey_segment="all_respondents", indicator_id=iid,
                     item=r["item"], official_valid_n=n, official_numerator=f, official_proportion=round(p, 6),
                     recomputed_valid_n=int(r.valid_n), recomputed_numerator=int(r.numerator), recomputed_proportion=float(r.proportion),
                     abs_diff_proportion=round(float(r.proportion) - p, 6),
                     result="MATCH" if abs(float(r.proportion) - p) <= 0.001 else "MISMATCH",
                     note="Public CSV has more rows than the published total (49,191 vs 49,019); tolerance 0.1 pp"))
# reproduction check 2: same engine + same file -> GLOBAL and LATAM country rows must equal the Argentina FINAL package rows
ar = pd.read_csv(os.path.join(ARP, "data", "b_survey_indicators.csv"), dtype=str, keep_default_na=False)
K = ["group_code", "survey_segment", "indicator_id", "item", "task", "task_stance"]
mine = pd.read_csv(os.path.join(WB, "b_survey_indicators_pe.csv"), dtype=str, keep_default_na=False)  # engine output, empty = ""
for g in ["GLOBAL", "BR", "MX", "CO", "CL", "AR"]:
    a = ar[ar.group_code == g]; m = mine[mine.group_code == g]
    if g == "AR":
        a = a[a.survey_segment == "all_respondents"]; m = m[m.survey_segment == "all_respondents"]
    mm = a.merge(m, on=K, suffixes=("_ar", "_pe"))
    eqn = sum(1 for _, x in mm.iterrows() if all(
        (x[c + "_ar"] == x[c + "_pe"]) or (x[c + "_ar"] and x[c + "_pe"] and abs(float(x[c + "_ar"]) - float(x[c + "_pe"])) <= 1e-12)
        for c in ("numerator", "valid_n", "proportion")))
    rows.append(dict(check_type="cross_check_ar_final_package", focus_country_code="PE", group_code=g, survey_segment="all_respondents" if g == "AR" else "all",
                     indicator_id="all", item=f"{len(a)} rows in AR FINAL package; {len(mm)} matched keys", official_valid_n="", official_numerator="", official_proportion="",
                     recomputed_valid_n="", recomputed_numerator="", recomputed_proportion="", abs_diff_proportion="",
                     result="MATCH" if eqn == len(mm) and len(mm) > 0 else f"MISMATCH ({len(mm)-eqn})",
                     note="Same results.csv and engine; numerator, valid_n and proportion compared"))
rows.append(dict(check_type="previous_t4e_values", focus_country_code="PE", group_code="PE", survey_segment="all_respondents", indicator_id="",
                 item="Earlier Think4ever Peru Layer B values", official_valid_n="", official_numerator="", official_proportion="", recomputed_valid_n="",
                 recomputed_numerator="", recomputed_proportion="", abs_diff_proportion="", result="NOT_AVAILABLE",
                 note="No earlier Peru values were supplied (not present in the Chile or Argentina packages)"))
write(pd.DataFrame(rows), os.path.join(PB, "data", "b_reproduction_check_pe.csv"))

regB = [dict(source_id="SRC_SO_2025", source_name="Stack Overflow Developer Survey 2025, results.csv", publisher="Stack Overflow",
             dataset_version="2025 public data (49,191 rows; published total 49,019); archive repo commit c9c23dc", reference_period="2025",
             url="https://survey.stackoverflow.co/ ; https://github.com/StackExchange/Survey/tree/main/packages/archive/2025",
             access_date="2026-10-08", access_method="Git LFS object from media.githubusercontent.com; sha256 equals the LFS pointer oid",
             file_name="results.csv", sha256=sha(SO), license="ODbL 1.0 (database) / DbCL 1.0 (contents)", role="Layer B primary data (Country = Peru)", status="verified"),
        dict(source_id="SRC_SO_2025_AGG", source_name="Stack Overflow Developer Survey 2025 official aggregate (ai.json)", publisher="Stack Overflow",
             dataset_version="archive repo commit c9c23dc", reference_period="2025", url="https://github.com/StackExchange/Survey/tree/main/packages/archive/2025/json",
             access_date="2026-10-08", access_method="git sparse checkout", file_name="ai.json", sha256=sha(AIJ), license="ODbL 1.0",
             role="b_reproduction_check: official global AISelect and AIAgents", status="verified"),
        dict(source_id="INT_T4E_AR_FINAL", source_name="Argentina Day 1 FINAL package (engine, indicator definitions and cross-check reference; no AR values reused as Peru values)",
             publisher="Think4ever", dataset_version="FINAL 2026-10-08", reference_period="2025", url="", access_date="2026-10-08", access_method="supplied",
             file_name="think4ever_argentina_day1_FINAL.zip", sha256="", license="internal", role="layer_b_engine.py; b_indicator_definitions (B5 text adapted to Peru)", status="provided"),
        dict(source_id="REQ_T4E_PE_PREVIOUS_B", source_name="Earlier Think4ever Peru Layer B values", publisher="Think4ever", dataset_version="", reference_period="",
             url="", access_date="", access_method="not supplied", file_name="", sha256="", license="internal", role="Optional reconciliation", status="not available")]
write(pd.DataFrame(regB), os.path.join(PB, "data", "source_registry_layer_b_pe.csv"))
print("A and B packages written")
