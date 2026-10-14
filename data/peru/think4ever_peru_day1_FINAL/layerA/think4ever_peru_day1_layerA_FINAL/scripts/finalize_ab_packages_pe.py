"""Peru Day 1 - finalize Layer A and B packages: reproduction checks, value-identity checks, suppression checks,
data dictionaries, manifests and SHA256SUMS. Read-only with respect to results.

Usage: python3 -I finalize_ab_packages_pe.py <work_a> <work_b> <ig_repo> <so_results_csv> <scripts_dir> <ar_final_pkg> <out_root> <tmp_dir>
"""
import sys, os, csv, glob, hashlib, shutil, subprocess, filecmp
import pandas as pd

WA, WB, IG, SO, SC, ARP, OUT, TMP = sys.argv[1:9]
PA, PB = os.path.join(OUT, "think4ever_peru_day1_layerA_FINAL"), os.path.join(OUT, "think4ever_peru_day1_layerB_FINAL")
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
for f in ("layer_a_country.py", "build_layer_ab_packages_pe.py", "finalize_ab_packages_pe.py"):
    shutil.copy(os.path.join(SC, f), os.path.join(PA, "scripts", f))
for f in ("layer_b_engine.py", "build_layer_ab_packages_pe.py", "finalize_ab_packages_pe.py"):
    shutil.copy(os.path.join(SC, f), os.path.join(PB, "scripts", f))

# ---- 1. engine reproduction from raw sources
shutil.rmtree(TMP, ignore_errors=True); os.makedirs(os.path.join(TMP, "a")); os.makedirs(os.path.join(TMP, "b"))
subprocess.run([sys.executable, "-I", os.path.join(SC, "layer_a_country.py"), IG, os.path.join(TMP, "a"), "PE"], check=True, capture_output=True)
subprocess.run([sys.executable, "-I", os.path.join(SC, "layer_b_engine.py"), SO, "PE", os.path.join(TMP, "b")], check=True, capture_output=True)

def norm(v):
    v = "" if v is None else str(v)
    return {"True": "true", "False": "false"}.get(v, v)

def same_values(work_csv, pkg_csv, rename=None, extra_cols=()):
    w = pd.read_csv(work_csv, dtype=str, keep_default_na=False); p = pd.read_csv(pkg_csv, dtype=str, keep_default_na=False)
    if rename:
        w = w.rename(columns=rename)
    cols = [c for c in w.columns]
    if len(w) != len(p) or any(c not in p.columns for c in cols):
        return False, f"rows {len(w)} vs {len(p)}; missing cols {[c for c in cols if c not in p.columns]}"
    bad = 0
    for c in cols:
        for a, b in zip(w[c], p[c]):
            if norm(a) == norm(b):
                continue
            try:
                if abs(float(a) - float(b)) <= 1e-12 * max(1.0, abs(float(a))):
                    continue
            except ValueError:
                pass
            bad += 1
    added = [c for c in p.columns if c not in cols]
    return bad == 0, f"{len(w)} rows x {len(cols)} cols compared, {bad} differing cells; metadata columns added: {added}"

rowsA = []
for f in sorted(os.listdir(os.path.join(TMP, "a"))):
    if f.startswith("layer_a_pe") or f == "layer_a_source_hashes.json":
        ok = filecmp.cmp(os.path.join(TMP, "a", f), os.path.join(WA, f), shallow=False)
        rowsA.append(dict(check="engine_rerun_byte_identical", file=f, result="PASS" if ok else "FAIL", detail="layer_a_country.py re-run from the Innovation Graph clone vs existing output"))
for wf, pf in [("layer_a_pe_indicators.csv", "a_github_indicators_pe.csv"), ("layer_a_pe_languages.csv", "a_github_languages_pe.csv"), ("layer_a_pe_quarterly.csv", "a_github_country_quarterly_pe.csv")]:
    ok, det = same_values(os.path.join(WA, wf), os.path.join(PA, "data", pf))
    rowsA.append(dict(check="package_values_identical_to_existing_output", file=pf, result="PASS" if ok else "FAIL", detail=det))
pd.DataFrame(rowsA).to_csv(os.path.join(PA, "validation", "a_reproduction_check_pe.csv"), index=False)

rowsB = []
for f in sorted(os.listdir(os.path.join(TMP, "b"))):
    ok = filecmp.cmp(os.path.join(TMP, "b", f), os.path.join(WB, f), shallow=False)
    rowsB.append(dict(check="engine_rerun_byte_identical", file=f, result="PASS" if ok else "FAIL", detail="layer_b_engine.py re-run on results.csv vs existing output"))
for wf, pf, ren in [("b_survey_indicators_pe.csv", "b_survey_indicators_pe.csv", {"vs_latam_ex_pe": "vs_regional_ex_focus"}),
                    ("b_survey_distributions_pe.csv", "b_survey_distributions_pe.csv", None), ("b_comparison_groups_pe.csv", "b_comparison_groups_pe.csv", None)]:
    ok, det = same_values(os.path.join(WB, wf), os.path.join(PB, "data", pf), ren)
    rowsB.append(dict(check="package_values_identical_to_existing_output", file=pf, result="PASS" if ok else "FAIL", detail=det + (" (column vs_latam_ex_pe renamed to vs_regional_ex_focus)" if ren else "")))
bi = pd.read_csv(os.path.join(PB, "data", "b_survey_indicators_pe.csv"))
w = pd.read_csv(os.path.join(WB, "b_survey_indicators_pe.csv"))
ren_ok = "vs_latam_ex_pe" not in bi.columns and (bi.vs_regional_ex_focus.fillna("") == w.vs_latam_ex_pe.fillna("")).all()
rowsB.append(dict(check="column_rename_values_unchanged", file="b_survey_indicators_pe.csv", result="PASS" if ren_ok else "FAIL",
                  detail=f"vs_regional_ex_focus == former vs_latam_ex_pe in all {len(bi)} rows"))
# suppression / base flags
def flag(n):
    return "ok" if n >= 50 else ("indicative" if n >= 30 else "suppressed")
x = bi[bi.base_flag != "not_applicable"]
flags_ok = (x.valid_n.apply(flag) == x.base_flag).all()
sup = bi[bi.base_flag == "suppressed"]
rowsB.append(dict(check="base_flag_rule", file="b_survey_indicators_pe.csv", result="PASS" if flags_ok else "FAIL",
                  detail=f"ok>=50, indicative 30-49, suppressed<30 on {len(x)} rows"))
rowsB.append(dict(check="suppressed_values_blank", file="b_survey_indicators_pe.csv", result="PASS" if sup[["numerator", "proportion", "ci_low", "ci_high"]].isna().all().all() else "FAIL",
                  detail=f"{len(sup)} suppressed rows (PE {int((sup.group_code=='PE').sum())}); numerator/proportion/CI blank"))
bd = pd.read_csv(os.path.join(PB, "data", "b_survey_distributions_pe.csv")); sd = bd[bd.base_flag == "suppressed"]
rowsB.append(dict(check="suppressed_values_blank_distributions", file="b_survey_distributions_pe.csv", result="PASS" if sd[["numerator", "proportion"]].isna().all().all() else "FAIL",
                  detail=f"{len(sd)} suppressed rows"))
g = pd.read_csv(os.path.join(PB, "data", "b_comparison_groups_pe.csv"))
pe = g[(g.group_code == "PE")].set_index("survey_segment").respondents.to_dict()
rowsB.append(dict(check="respondent_counts", file="b_comparison_groups_pe.csv", result="PASS" if pe == {"all_respondents": 64, "professional_developers": 46} else "FAIL",
                  detail=f"PE {pe}; LATAM_EX_PE {int(g[g.group_code=='LATAM_EX_PE'].respondents.iloc[0])}; GLOBAL {int(g[g.group_code=='GLOBAL'].respondents.iloc[0])}; PE + LATAM_EX_PE = {64 + int(g[g.group_code=='LATAM_EX_PE'].respondents.iloc[0])} (= AR 222 + LATAM_EX_AR 1,807 = 2,029)"))
rc = pd.read_csv(os.path.join(PB, "data", "b_reproduction_check_pe.csv"))
rowsB.append(dict(check="b_reproduction_check", file="b_reproduction_check_pe.csv", result="PASS" if not rc.result.str.startswith("MISMATCH").any() else "FAIL",
                  detail="; ".join(f"{a}:{b}:{c}" for a, b, c in rc[["check_type", "group_code", "result"]].itertuples(index=False))))
pd.DataFrame(rowsB).to_csv(os.path.join(PB, "validation", "b_validation_checks_pe.csv"), index=False)

# ---- 2. data dictionaries (descriptions from the AR FINAL dictionary for identical column names; country text adapted)
ard = pd.read_csv(os.path.join(ARP, "data_dictionary.csv"), dtype=str, keep_default_na=False)
EXTRA = {"previous_t4e_value": "Earlier Think4ever value (empty: latam-country-breakdown-2026Q1.csv not supplied)",
         "reconciliation": "Reconciliation status against earlier Think4ever value",
         "check_type": "official_aggregate_ai_json | cross_check_ar_final_package | previous_t4e_values",
         "official_valid_n": "Valid respondents in the official aggregate (ai.json)", "official_numerator": "Respondents in the numerator categories (ai.json)",
         "official_proportion": "Official proportion (ai.json)", "recomputed_valid_n": "Valid answers recomputed from results.csv",
         "recomputed_numerator": "Numerator recomputed from results.csv", "recomputed_proportion": "Proportion recomputed from results.csv",
         "abs_diff_proportion": "recomputed - official", "result": "MATCH | MISMATCH | NOT_AVAILABLE", "note": "Note", "item": "Item or comparison scope",
         "dataset_version": "Innovation Graph dataset version", "period_end_date": "Last day of the quarter",
         "source_id": "Source key (source registry)", "source_name": "Source name", "publisher": "Publisher", "repo_commit": "Repository commit and date",
         "reference_period": "Reference period", "url": "URL", "access_date": "Access date", "access_method": "Access method", "files": "Files", "file_name": "File",
         "sha256": "SHA-256", "license": "Licence", "role": "Role", "status": "Status"}
def dictionary(pkg, mapping):
    out = []
    for f in sorted(glob.glob(os.path.join(pkg, "data", "*.csv"))):
        t = pd.read_csv(f, dtype=str, keep_default_na=False); base = os.path.basename(f).replace("_pe.csv", "")
        for c in t.columns:
            m = ard[(ard.table_name == mapping.get(base, base)) & (ard.column_name == c)]
            d = m.description.iloc[0] if len(m) else EXTRA.get(c, "")
            d = d.replace("(always AR); never implies the row is about Argentina", "(always PE); never implies the row is about Peru").replace("(AR)", "(PE)").replace("Argentina", "Peru")
            ex = next((v for v in t[c] if v != ""), "")
            out.append(dict(table_name=os.path.basename(f), column_name=c, type=(m.type.iloc[0] if len(m) else "text"), description=d, example=ex[:80]))
    df = pd.DataFrame(out); df.to_csv(os.path.join(pkg, "data_dictionary.csv"), index=False, quoting=csv.QUOTE_NONNUMERIC)
    return int((df.description == "").sum()), len(df)
ua = dictionary(PA, {}); ub = dictionary(PB, {})

# ---- 3. manifests and hashes
def manifest(pkg):
    rows = []
    for f in sorted(glob.glob(os.path.join(pkg, "**", "*"), recursive=True)):
        if os.path.isfile(f) and os.path.basename(f) not in ("manifest.csv", "SHA256SUMS.txt"):
            rel = os.path.relpath(f, pkg); r = c = ""
            if f.endswith(".csv"):
                t = pd.read_csv(f, dtype=str); r, c = len(t), len(t.columns)
            rows.append(dict(path=rel, role=("data" if rel.startswith("data/") else "validation" if rel.startswith("validation/") else "script" if rel.startswith("scripts/") else "documentation"),
                             rows=r, columns=c, bytes=os.path.getsize(f), sha256=sha(f)))
    pd.DataFrame(rows).to_csv(os.path.join(pkg, "manifest.csv"), index=False)
    with open(os.path.join(pkg, "validation", "SHA256SUMS.txt"), "w") as fh:
        for f in sorted(glob.glob(os.path.join(pkg, "**", "*"), recursive=True)):
            if os.path.isfile(f) and os.path.basename(f) != "SHA256SUMS.txt":
                fh.write(f"{sha(f)}  {os.path.relpath(f, os.path.dirname(pkg))}\n")
    return len(rows)
print("A checks", pd.DataFrame(rowsA).result.value_counts().to_dict(), "dict undocumented/rows", ua, "manifest", manifest(PA))
print("B checks", pd.DataFrame(rowsB).result.value_counts().to_dict(), "dict undocumented/rows", ub, "manifest", manifest(PB))
