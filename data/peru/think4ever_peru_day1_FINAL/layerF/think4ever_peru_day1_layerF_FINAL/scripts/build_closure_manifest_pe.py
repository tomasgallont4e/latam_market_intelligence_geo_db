"""Closure packaging for Peru Day 1 Layer F (no new analysis): data_dictionary.csv and manifest.csv.

Usage: python3 -I build_closure_manifest_pe.py <package_dir>
"""
import sys, os, glob, hashlib, csv
import pandas as pd

PKG = sys.argv[1]
TABLES = {
    "f_persona_estimates_pe.csv": ("EPEN 2025", "F1/F2/F11: occupational population per persona, ring, combined/informational group and sensitivity (suppressed values blank)", "group_id"),
    "f_persona_profiles_pe.csv": ("EPEN 2025", "F3-F8 and F6: profile shares/medians per group (small cells and suppressed groups blank)", "group_id;indicator;category"),
    "f_persona_correspondence_pe.csv": ("CNO 2015 / EPEN 2025", "Deliverable B: 13 personas, CIUO-08 template codes, CNO 2015 codes, justification and warnings", "template_persona_number"),
    "f_occupation_mapping_pe.csv": ("CNO 2015 / EPEN 2025", "CNO 2015 code-level mapping to personas with INEI link flags (weighted value blank if <30 records)", "template_persona_number;cno2015_code"),
    "f_cno_code_counts_pe.csv": ("EPEN 2025", "Employed per CNO 2015 code (weighted value blank if <30 records)", "cno2015_code"),
    "cno2015_ciuo08_correspondence.csv": ("INEI CNO 2015 Anexos 3-4", "Official CNO 2015 <-> CIUO-08 correspondence extracted from the PDF", "cno;ciuo"),
    "f9_persona_socioeconomic_enaho_pe.csv": ("ENAHO 2025", "F9: share of each group by national income quintile (ipcr_0) and ESTRSOCIAL; separate from EPEN", "group_id;indicator;category"),
    "f1_enaho_diagnostic_pe.csv": ("ENAHO 2025", "ENAHO employed per group - diagnostic only, never replaces EPEN F1", "group_id"),
    "f_designers_informational_pe.csv": ("EPEN 2025 and ENAHO 2025 (rows by source)", "D-PE-09 designers informational group (CNO 2163+2166+3432), outside personas and rings", "group_id;source"),
    "enaho_quintile_cutpoints_pe.csv": ("ENAHO 2025", "National population quintile cut-points of real per-capita monthly income (S/, Lima prices)", "quantile"),
    "source_registry_layer_f_pe.csv": ("all", "Source registry: provenance, versions, hashes, roles, open requests", "source_id"),
    "decisions_log_pe.csv": ("all", "Methodological decisions and validation statuses (current / superseded_by)", "decision_id"),
}
DESC = {
    "group_id": "Group key (P01-P13 personas; RING_*; ALL13; COMB_*; INFO_* informational; S* sensitivities; REF_ALL_EMPLOYED)",
    "group_type": "persona | ring_total | combined_total | combined_group | informational_outside_rings | sensitivity | reference",
    "template_persona_number": "Persona number 1-13 (ordering only; key is the canonical name)", "label": "Group label", "persona": "Canonical persona name",
    "persona_canonical": "Canonical persona name (think4ever-13-personas-definicion.xlsx)", "template_alias": "Name used in the country template (alias)",
    "ring": "Core | Adjacent | Extended", "cno2015_codes": "CNO 2015 4-digit codes of the group (;-separated)", "cno2015_code": "CNO 2015 4-digit code (text)",
    "cno2015_title": "CNO 2015 title", "cno2015_codes_primary": "CNO 2015 codes used in the primary estimate", "cno2015_codes_excluded": "CNO 2015 codes excluded (D-PE-04)",
    "isco08_template_codes": "ISCO-08/CIUO-08 codes defining the persona (template Annex 2)", "ciuo08_codes_linked": "CIUO-08 codes linked by INEI to the CNO code",
    "ciuo08_codes_in_persona": "Linked CIUO-08 codes that belong to the persona", "enlace_cno_ciuo": "INEI link flags (0 absolute, 1 relative) per linked CIUO code",
    "annex_source": "CNO 2015 annex where the link appears (A3, A4)", "mapping_status": "exact_within_persona | relative_link_outside_persona | excluded_ambiguous | ciuo_without_reliable_cno_code",
    "mapping_class": "Persona-level mapping class", "in_primary": "Code used in the primary estimate (true/false)", "note": "Note", "justification": "Mapping justification",
    "warnings": "Interpretation warnings", "records": "Unweighted records (visits) in the sample", "sample_records": "Unweighted records in the sample",
    "unique_persons": "Unique persons (panel repeats counted once)", "psus": "Primary sampling units with records", "employed": "Weighted employed persons, annual average 2025",
    "employed_2025": "Weighted employed persons 2025 (blank if suppressed)", "weighted_employed": "Weighted employed persons (blank if <30 records)",
    "se": "Standard error (Taylor linearisation)", "cv": "Coefficient of variation (se / estimate)", "ci95_low": "95% CI lower bound", "ci95_high": "95% CI upper bound",
    "share_of_employed": "Share of all employed persons (0-1)", "share_se": "SE of the share", "template_confidence": "Template F2 confidence: high >=1000, medium 300-999, low <300 unique persons",
    "cv_flag": "cv_le_15 | cv_15_30 | cv_gt_30", "additive_to_ring": "True only for the 13 personas (sum to rings)",
    "publication_status": "publish | publish_low_precision (15%<CV<=30%) | suppressed_unreliable (CV>30% or <30 unique persons) (D-PE-03)",
    "scope_note": "Scope/interpretation note (e.g. persona 8 broad category, D-PE-05)", "measure": "Measure definition: occupational population, not users/TAM/SAM/SOM",
    "indicator": "Indicator id (F3..F9)", "category": "Indicator category", "value": "Indicator value (proportion 0-1, years or PEN/month per unit; blank if suppressed/small)",
    "unit": "proportion | years | PEN_month | ratio", "weighted_numerator": "Weighted numerator", "weighted_denominator": "Weighted denominator",
    "records_denominator": "Unweighted records in the group", "records_numerator": "Unweighted records in the cell", "small_cell": "Denominator <30 records (value blank)",
    "low_numerator": "Numerator <30 records (interpret with care)", "group_publication_status": "Publication status of the group (from estimates table)",
    "code_cell_status": "suppressed_lt30_records | publish_code_level_no_cv", "cno": "CNO 2015 code", "cno_title": "CNO 2015 title", "cno_enlace": "Link flag on CNO side",
    "ciuo": "CIUO-08 code", "ciuo_title": "CIUO-08 title", "ciuo_enlace": "Link flag on CIUO side", "in_annex3": "Pair present in Annex 3", "in_annex4": "Pair present in Annex 4",
    "enlace_agree": "Link flags agree between annexes", "source": "Survey source of the row (EPEN 2025 or ENAHO 2025; never combined)",
    "share": "Share within the group (0-1; blank if suppressed)", "se_ratio_stratified_vs_main": "AUDIT ONLY: SE under the superseded stratified spec / published SE (D-PE-12). Not a result",
    "records_cell": "Unweighted records in the cell", "records_group": "Unweighted records in the group", "unique_persons_group": "Unique persons in the group",
    "status": "Publication status (publish | publish_low_precision | suppressed_cell | suppressed_group | diagnostic... )",
    "enaho_employed": "ENAHO weighted employed (diagnostic; blank if suppressed)", "enaho_cv": "ENAHO CV (PSU-only spec, D-PE-12)", "enaho_ci95_low": "ENAHO 95% CI lower",
    "enaho_ci95_high": "ENAHO 95% CI upper", "epen_employed_2025": "EPEN published estimate for reference (blank if suppressed)",
    "enaho_vs_epen_ratio": "ENAHO / EPEN ratio (diagnostic; not an adjustment factor)", "use": "Permitted use", "in_rings": "Whether the group belongs to a ring",
    "quantile": "Quantile boundary", "cutpoint_soles_month_lima_prices": "Cut-point, soles per month at Lima prices (2025)",
    "source_id": "Source key", "source_name": "Source name", "publisher": "Publisher", "dataset_version": "Version", "reference_period": "Reference period",
    "url": "URL", "access": "How the file was obtained", "sha256": "SHA-256 of the file(s)", "zip_sha256": "SHA-256 of the archive", "role": "Role in the research",
    "license_status": "Licence / redistribution status", "decision_id": "Decision or validation id", "date": "Date", "decision": "Decision", "current": "Decision currently in force",
    "superseded_by": "Decision that supersedes it",
}
dd, man = [], []
for fn, (src, desc, pk) in TABLES.items():
    p = os.path.join(PKG, "data", fn)
    t = pd.read_csv(p, dtype=str)
    for c in t.columns:
        dd.append(dict(table=fn, column=c, description=DESC.get(c, ""), non_empty=int(t[c].notna().sum()), rows=len(t)))
missing = [r for r in dd if not r["description"]]
pd.DataFrame(dd).to_csv(os.path.join(PKG, "data_dictionary.csv"), index=False)
for f in sorted(glob.glob(os.path.join(PKG, "**", "*"), recursive=True)):
    if not os.path.isfile(f) or os.path.basename(f) in ("manifest.csv", "SHA256SUMS.txt"):
        continue
    rel = os.path.relpath(f, PKG); fn = os.path.basename(f)
    role = ("data_publishable" if rel.startswith("data/") else "internal_audit_not_publishable" if "internal_not_publishable" in rel
            else "validation" if rel.startswith("validation/") else "script" if rel.startswith("scripts/") else "documentation")
    rows = cols = ""
    if f.endswith(".csv"):
        t = pd.read_csv(f, dtype=str); rows, cols = len(t), len(t.columns)
    man.append(dict(path=rel, role=role, source=TABLES.get(fn, ("", "", ""))[0], description=TABLES.get(fn, ("", "", ""))[1],
                    primary_key=TABLES.get(fn, ("", "", ""))[2], rows=rows, columns=cols, bytes=os.path.getsize(f),
                    sha256=hashlib.sha256(open(f, "rb").read()).hexdigest()))
pd.DataFrame(man).to_csv(os.path.join(PKG, "manifest.csv"), index=False)
print("dictionary rows", len(dd), "undocumented", [(r["table"], r["column"]) for r in missing]); print("manifest files", len(man))
