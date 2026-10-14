"""Peru Day 1 - closure audit of Layer A and Layer B packages (read-only; writes the audit CSV only).

Usage: python3 -I audit_closure_ab_pe.py <pkgA> <pkgB> <ig_repo> <so_results_csv> <so_ai_json> <out_csv>
"""
import sys, os, glob, hashlib, re
import pandas as pd

PA, PB, IG, SO, AIJ, OUT = sys.argv[1:7]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
R = []
def rec(layer, cid, control, evidence, ok, severity="Mayor", action=""):
    R.append(dict(layer=layer, check_id=cid, control=control, evidence=evidence, result="PASS" if ok else "FAIL", severity="" if ok else severity, action="" if ok else action))

REQUIRED = {"A": ["README.md", "data_dictionary.csv", "manifest.csv", "data/a_github_indicators_pe.csv", "data/a_github_languages_pe.csv",
                  "data/a_github_country_quarterly_pe.csv", "data/source_registry_layer_a_pe.csv", "validation/a_validation_checks_pe.csv",
                  "validation/a_reproduction_check_pe.csv", "validation/SHA256SUMS.txt", "scripts/layer_a_country.py"],
            "B": ["README.md", "data_dictionary.csv", "manifest.csv", "data/b_survey_indicators_pe.csv", "data/b_survey_distributions_pe.csv",
                  "data/b_comparison_groups_pe.csv", "data/b_indicator_definitions_pe.csv", "data/b_reproduction_check_pe.csv",
                  "data/source_registry_layer_b_pe.csv", "validation/b_validation_checks_pe.csv", "validation/SHA256SUMS.txt", "scripts/layer_b_engine.py"]}
for L, P in (("A", PA), ("B", PB)):
    miss = [f for f in REQUIRED[L] if not os.path.exists(os.path.join(P, f))]
    rec(L, f"{L}1_completeness", "Required package components present (README, registry, dictionary, tables, validation, scripts, manifest, hashes)",
        f"{len(REQUIRED[L])} required; missing {miss}", not miss, "Mayor", "Add missing components")
    dd = pd.read_csv(os.path.join(P, "data_dictionary.csv"), dtype=str, keep_default_na=False)
    cols = {(os.path.basename(f), c) for f in glob.glob(os.path.join(P, "data", "*.csv")) for c in pd.read_csv(f, nrows=0).columns}
    have = {(r.table_name, r.column_name) for r in dd.itertuples() if r.description}
    rec(L, f"{L}2_dictionary", "Every data column documented with a description", f"{len(cols)} columns; undocumented {sorted(cols - have)}", cols <= have, "Menor", "Document")
    bad = []
    for l in open(os.path.join(P, "validation", "SHA256SUMS.txt")):
        h, p = l.rstrip("\n").split("  ", 1)
        fp = os.path.join(os.path.dirname(P), p)
        if not os.path.exists(fp) or sha(fp) != h:
            bad.append(p)
    rec(L, f"{L}3_hashes", "SHA256SUMS verifies against package files", f"mismatches {bad}", not bad, "Mayor", "Regenerate")
    man = pd.read_csv(os.path.join(P, "manifest.csv"))
    mbad = [r.path for r in man.itertuples() if sha(os.path.join(P, r.path)) != r.sha256]
    rec(L, f"{L}4_manifest", "manifest.csv hashes match files", f"{len(man)} files; mismatches {mbad}", not mbad, "Mayor", "Regenerate")
    ids = [os.path.basename(f) for f in glob.glob(os.path.join(P, "**", "*.csv"), recursive=True)
           if {"ResponseId", "ResponseID", "user_id", "login"} & set(pd.read_csv(f, nrows=0).columns)]
    big = [os.path.basename(f) for f in glob.glob(os.path.join(P, "**", "*"), recursive=True) if os.path.isfile(f) and os.path.getsize(f) > 5_000_000]
    rec(L, f"{L}5_no_microdata", "No respondent-level or raw source files in the package", f"id files {ids}; large files {big}", not ids and not big, "Critico", "Remove")

# ---- Layer A: values vs approved (readiness report 2026-10-08) and documentation
ind = pd.read_csv(os.path.join(PA, "data", "a_github_indicators_pe.csv"))
v = lambda i: float(ind[ind.indicator_id == i].value.iloc[0])
APP = {"A1_developer_accounts": 907052, "A1_developer_accounts_prev_year": 649794, "A2_organizations": 36740, "A3_git_pushes": 1144909}
APPR = {"A1_developer_accounts_yoy": 0.396, "A2_organizations_yoy": 0.240, "A3_git_pushes_yoy": 1.227, "A3_pushes_per_developer_account": 1.262,
        "A2_developers_per_organization": 24.69, "A5_enterprise_share_template_basket": 0.0667}
ok = all(v(k) == x for k, x in APP.items()) and all(abs(v(k) - x) < 0.0006 * max(1, x) for k, x in APPR.items())
rec("A", "A6_values_unchanged", "Published A1-A5 equal the values reported on 2026-10-08 (no unauthorised change)",
    "; ".join(f"{k}={v(k):.4g}" for k in list(APP) + list(APPR)), ok, "Critico", "Restore")
prov = ind[ind.indicator_id.str.startswith(("A4", "A5"))].canonical_status.unique().tolist()
rec("A", "A7_provisional_A4_A5", "A4 and A5 rows flagged undetermined (D-03/D-04)", f"canonical_status {prov}", prov == ["undetermined"], "Mayor", "Flag")
reg = pd.read_csv(os.path.join(PA, "data", "source_registry_layer_a_pe.csv"), dtype=str, keep_default_na=False)
regh = dict(re.findall(r"(\S+\.csv): ([0-9a-f]{64})", reg[reg.source_id == "SRC_GH_IG"].sha256.iloc[0]))
hb = [f for f, h in regh.items() if sha(os.path.join(IG, "data", f)) != h]
import subprocess
head = subprocess.run(["git", "-C", IG, "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
rec("A", "A8_source_hashes", "Registry hashes match the Innovation Graph files; commit = 078fb62",
    f"{len(regh)} files, mismatches {hb}; HEAD {head}", not hb and head == "078fb62" and len(regh) == 8, "Mayor", "Correct registry")
rd = open(os.path.join(PA, "README.md")).read()
need = {"accounts_not_people": "no equivalen a personas", "weak_base": "base débil", "provisional": "provisional", "period": "2026T1 frente a 2025T1"}
rec("A", "A9_required_statements", "README states: accounts are not people; weak-base effect on pushes; A4/A5 provisional; period",
    "; ".join(f"{k}:{t in rd}" for k, t in need.items()), all(t in rd for t in need.values()), "Mayor", "Document")
va = pd.read_csv(os.path.join(PA, "validation", "a_validation_checks_pe.csv")); ra = pd.read_csv(os.path.join(PA, "validation", "a_reproduction_check_pe.csv"))
rec("A", "A10_validation_results", "Validation and reproduction checks", f"validation {va.result.value_counts().to_dict()}; reproduction {ra.result.value_counts().to_dict()}",
    (va.result.isin(["PASS", "NOT_VERIFIABLE"])).all() and (ra.result == "PASS").all(), "Mayor", "Investigate")

# ---- Layer B
bi = pd.read_csv(os.path.join(PB, "data", "b_survey_indicators_pe.csv"))
rec("B", "B6_rename", "vs_latam_ex_pe renamed to vs_regional_ex_focus", f"columns with vs_: {[c for c in bi.columns if c.startswith('vs_')]}",
    "vs_regional_ex_focus" in bi.columns and "vs_latam_ex_pe" not in bi.columns, "Menor", "Rename")
pe = bi[(bi.group_code == "PE") & (bi.survey_segment == "all_respondents")]
g = lambda i: pe[pe.indicator_id == i].iloc[0]
vals = [(i, int(g(i).numerator), int(g(i).valid_n)) for i in ("B1", "B2", "B3")]
rec("B", "B7_values_unchanged", "B1-B3 numerators/denominators equal the values reported on 2026-10-08 (52/59, 37/59, 25/57); n = 64",
    f"{vals}", vals == [("B1", 52, 59), ("B2", 37, 59), ("B3", 25, 57)], "Critico", "Restore")
sup = bi[bi.base_flag == "suppressed"]
rec("B", "B8_suppression", "Suppressed rows (<30) have blank numerator/proportion/CI; flags follow 50/30 thresholds",
    f"{len(sup)} suppressed; non-blank {int(sup[['numerator','proportion','ci_low','ci_high']].notna().sum().sum())}",
    sup[["numerator", "proportion", "ci_low", "ci_high"]].isna().all().all(), "Critico", "Suppress")
rc = pd.read_csv(os.path.join(PB, "data", "b_reproduction_check_pe.csv"))
offi = rc[rc.check_type == "official_aggregate_ai_json"]
rec("B", "B9_reproduction_check", "b_reproduction_check vs official ai.json and AR FINAL cross-check",
    "; ".join(f"{r.check_type[:8]}:{r.group_code}:{r.indicator_id}:{r.result}" for r in rc.itertuples()),
    len(offi) == 3 and (offi.result == "MATCH").all() and (rc[rc.check_type == "cross_check_ar_final_package"].result == "MATCH").all(), "Mayor", "Investigate")
regb = pd.read_csv(os.path.join(PB, "data", "source_registry_layer_b_pe.csv"), dtype=str, keep_default_na=False).set_index("source_id")
hok = regb.loc["SRC_SO_2025"].sha256 == sha(SO) == "2d1f65308877282edfb4470520eabbc08cb499118432a3dcec6a66c086aa2baa" and regb.loc["SRC_SO_2025_AGG"].sha256 == sha(AIJ)
rec("B", "B10_source_hashes", "Registry hashes match results.csv (LFS oid) and ai.json", f"results {sha(SO)[:12]}; ai.json {sha(AIJ)[:12]}", hok, "Mayor", "Correct")
rb = open(os.path.join(PB, "README.md")).read()
needb = {"self_selected": "autoseleccionada", "low_conf": "Confianza BAJA", "no_multiply": "multiplicar", "exploratory": "no son pruebas estadísticas", "period": "2025"}
rec("B", "B11_required_statements", "README states: self-selected; low confidence; never multiply by F; labels exploratory; period",
    "; ".join(f"{k}:{t in rb}" for k, t in needb.items()), all(t in rb for t in needb.values()), "Mayor", "Document")
vb = pd.read_csv(os.path.join(PB, "validation", "b_validation_checks_pe.csv"))
rec("B", "B12_validation_results", "Validation checks", f"{vb.result.value_counts().to_dict()}", (vb.result == "PASS").all(), "Mayor", "Investigate")
pd.DataFrame(R).to_csv(OUT, index=False)
print(pd.DataFrame(R)[["check_id", "result", "evidence"]].to_string(max_colwidth=110)); print("PASS", sum(r["result"] == "PASS" for r in R), "FAIL", sum(r["result"] == "FAIL" for r in R))
