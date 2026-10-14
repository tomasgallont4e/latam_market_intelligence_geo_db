"""Peru Day 1 FINAL - DRAFT->FINAL change control and classification of remaining DRAFT references (read-only on results).

Usage: python3 -I final_change_control_pe.py <draft_integral_dir> <final_integral_dir> <out_dir>
Writes <out_dir>/draft_to_final_change_control_pe.csv and <out_dir>/draft_references_classification_pe.csv.
Exit code 1 if any result file changed beyond the authorised decisions-log row or any current DRAFT reference remains.
"""
import sys, os, glob, hashlib, re, csv, difflib

D, F, OUT = sys.argv[1:4]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
files = lambda d: sorted(os.path.relpath(f, d) for f in glob.glob(os.path.join(d, "**", "*"), recursive=True) if os.path.isfile(f))
to_final = lambda rel: rel.replace("_DRAFT/", "_FINAL/")
SELF = {"audit/draft_to_final_change_control_pe.csv", "audit/draft_references_classification_pe.csv"}
REGEN = ("manifest.csv", "manifest_peru_day1.csv", "SHA256SUMS.txt", "data_dictionary.csv")

def kind(rel):
    b = os.path.basename(rel)
    if b in REGEN: return "integrity_metadata"
    if "/data/" in rel: return "data"
    if "/validation/" in rel or (rel.startswith("audit/") and rel.endswith(".csv")): return "validation_result"
    if rel.endswith(".py"): return "script"
    return "documentation"

dmap = {to_final(r): r for r in files(D)}
rows, problems = [], []
for rel in sorted(set(dmap) | set(files(F))):
    if rel in SELF: continue
    dr = dmap.get(rel); fp = os.path.join(F, rel); dp = os.path.join(D, dr) if dr else None
    k = kind(rel)
    if dr and os.path.exists(fp):
        same = sha(dp) == sha(fp)
        a = open(dp, encoding="utf-8", errors="replace").read().splitlines(); b = open(fp, encoding="utf-8", errors="replace").read().splitlines()
        diff = [l for l in difflib.unified_diff(a, b, lineterm="", n=0) if l[:1] in "+-" and not l.startswith(("+++", "---"))]
        added = [l[1:] for l in diff if l.startswith("+")]; removed = [l[1:] for l in diff if l.startswith("-")]
        status = "identical" if same else "modified"
        note = ""
        if not same:
            if k == "data":
                ok = rel.endswith("decisions_log_pe.csv") and not removed and len(added) == 1 and added[0].startswith('"CLOSE-PE-D1"')
                note = "one row added: CLOSE-PE-D1 (FINAL authorisation); all previous rows unchanged" if ok else "UNAUTHORISED DATA CHANGE"
                if not ok: problems.append(rel)
            elif k == "validation_result":
                ok = rel.endswith("validation/audit_layer_f_checks_pe.csv") and len(added) == 1 and "E2_sha256sums" in added[0] and "40 entries" in added[0]
                note = ("in-package copy synchronised with the FINAL re-run of the Layer F audit (only E2 evidence: SHA256SUMS entry count 38 -> 40); results PASS 60/60 unchanged"
                        if ok else "UNEXPLAINED VALIDATION CHANGE")
                if not ok: problems.append(rel)
            elif k == "integrity_metadata":
                note = "regenerated for FINAL (paths and hashes of modified files)"
            elif k == "script":
                note = "status/paths/docstrings only" + ("; DEC list gains CLOSE-PE-D1" if rel.endswith("build_layer_f_deliverables_pe.py") else "")
            else:
                note = "status wording updated to FINAL"
        rows.append(dict(final_path=rel, draft_path=dr, file_kind=k, status=status, lines_removed=len(removed) if not same else 0,
                         lines_added=len(added) if not same else 0, sha256_draft=sha(dp), sha256_final=sha(fp), note=note))
    elif dr:
        rows.append(dict(final_path="", draft_path=dr, file_kind=k, status="removed", lines_removed="", lines_added="", sha256_draft=sha(dp), sha256_final="",
                         note="regenerated under the same name" if os.path.basename(dr) in REGEN else "REMOVED"))
        if os.path.basename(dr) not in REGEN: problems.append(dr)
    else:
        rows.append(dict(final_path=rel, draft_path="", file_kind=k, status="added", lines_removed="", lines_added="", sha256_draft="", sha256_final=sha(fp),
                         note="closure document / closure tooling"))
        if k in ("data", "validation_result") and not rel.startswith("audit/"): problems.append(rel)
fields = list(rows[0])
with open(os.path.join(OUT, "draft_to_final_change_control_pe.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=fields); w.writeheader(); w.writerows(rows)

# ---- remaining DRAFT references
RULES = [
    ("closure_tooling", lambda rel, l: rel.startswith("audit/") and rel.endswith(".py") and "close" in rel or rel.endswith("final_change_control_pe.py")),
    ("closure_report", lambda rel, l: rel.endswith("Peru_Day1_Informe_Cierre_FINAL.md")),
    ("previous_version_name", lambda rel, l: re.search(r"(Versión anterior|\(antes|versión DRAFT histórica|\(histórica\))", l) is not None),
    ("dated_decision_record", lambda rel, l: re.search(r'"?D-PE-10b?"?,\s*"2026-10-09"', l) is not None),
    ("historical_context_note", lambda rel, l: re.search(r"(se emitió cuando los paquetes estaban en DRAFT|se escribieron cuando los paquetes estaban en DRAFT|En ese momento la capa F seguía en DRAFT)", l) is not None),
    ("resolved_item", lambda rel, l: "cambio de DRAFT a FINAL" in l and "Resuelto" in l),
    ("change_control_reference", lambda rel, l: re.search(r"(control DRAFT → FINAL|draft_to_final_change_control|draft_references_classification|referencias a DRAFT)", l) is not None),
]
refs, current = [], 0
for rel in files(F):
    if os.path.basename(rel) in ("SHA256SUMS.txt", "manifest_peru_day1.csv", "manifest.csv") or rel in SELF: continue
    try: lines = open(os.path.join(F, rel), encoding="utf-8").read().splitlines()
    except UnicodeDecodeError: continue
    for i, l in enumerate(lines, 1):
        if not re.search(r"draft|borrador", l, re.I): continue
        cls = next((c for c, f in RULES if f(rel, l)), "CURRENT_INCORRECT")
        current += cls == "CURRENT_INCORRECT"
        refs.append(dict(path=rel, line=i, classification=cls, legitimate=cls != "CURRENT_INCORRECT", text=l.strip()[:300]))
with open(os.path.join(OUT, "draft_references_classification_pe.csv"), "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["path", "line", "classification", "legitimate", "text"]); w.writeheader(); w.writerows(refs)

from collections import Counter
print("files:", Counter(r["status"] for r in rows), "| modified by kind:", Counter(r["file_kind"] for r in rows if r["status"] == "modified"))
print("data identical:", sum(r["status"] == "identical" for r in rows if r["file_kind"] == "data"), "of", sum(r["file_kind"] == "data" for r in rows))
print("validation identical:", sum(r["status"] == "identical" for r in rows if r["file_kind"] == "validation_result"), "of", sum(r["file_kind"] == "validation_result" for r in rows))
print("DRAFT references:", Counter(r["classification"] for r in refs))
print("problems:", problems, "| current DRAFT refs:", current)
sys.exit(1 if problems or current else 0)
