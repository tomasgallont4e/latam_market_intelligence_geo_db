"""Peru Day 1 FINAL - regenerate manifests and SHA256SUMS (no change to results).

Usage: python3 -I rehash_peru_day1_final.py <final_integral_dir> {layers|integral}
  layers   : manifest.csv (A, B) and validation/SHA256SUMS.txt (A, B, F). F manifest is built by build_closure_manifest_pe.py.
  integral : manifest_peru_day1.csv and SHA256SUMS.txt at the integral root.
"""
import sys, os, glob, hashlib
import pandas as pd

ROOT, MODE = sys.argv[1], sys.argv[2]
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
files = lambda d: sorted(f for f in glob.glob(os.path.join(d, "**", "*"), recursive=True) if os.path.isfile(f))

def sums(pkg):
    with open(os.path.join(pkg, "validation", "SHA256SUMS.txt"), "w") as fh:
        for f in files(pkg):
            if os.path.basename(f) != "SHA256SUMS.txt":
                fh.write(f"{sha(f)}  {os.path.relpath(f, os.path.dirname(pkg))}\n")

if MODE == "layers":
    for L in "AB":
        pkg = os.path.join(ROOT, f"layer{L}", f"think4ever_peru_day1_layer{L}_FINAL")
        rows = []
        for f in files(pkg):
            if os.path.basename(f) in ("manifest.csv", "SHA256SUMS.txt"):
                continue
            rel = os.path.relpath(f, pkg); r = c = ""
            if f.endswith(".csv"):
                t = pd.read_csv(f, dtype=str); r, c = len(t), len(t.columns)
            rows.append(dict(path=rel, role=("data" if rel.startswith("data/") else "validation" if rel.startswith("validation/") else "script" if rel.startswith("scripts/") else "documentation"),
                             rows=r, columns=c, bytes=os.path.getsize(f), sha256=sha(f)))
        pd.DataFrame(rows).to_csv(os.path.join(pkg, "manifest.csv"), index=False)
        sums(pkg); print(L, "manifest", len(rows))
    sums(os.path.join(ROOT, "layerF", "think4ever_peru_day1_layerF_FINAL")); print("F SHA256SUMS written")
else:
    rows = []
    for f in files(ROOT):
        rel = os.path.relpath(f, ROOT)
        if rel in ("manifest_peru_day1.csv", "SHA256SUMS.txt"):
            continue
        layer = rel.split("/")[0] if "/" in rel else "root"
        role = ("internal_audit_not_publishable" if "/internal_not_publishable/" in rel else "data" if "/data/" in rel else
                "validation" if ("/validation/" in rel or (layer == "audit" and rel.endswith(".csv"))) else "script" if rel.endswith(".py") else "documentation")
        rows.append(dict(layer=layer, path=rel, role=role, bytes=os.path.getsize(f), sha256=sha(f)))
    pd.DataFrame(rows).to_csv(os.path.join(ROOT, "manifest_peru_day1.csv"), index=False)
    with open(os.path.join(ROOT, "SHA256SUMS.txt"), "w") as fh:
        for f in files(ROOT):
            if os.path.basename(f) != "SHA256SUMS.txt" or os.path.dirname(f) != ROOT.rstrip("/"):
                fh.write(f"{sha(f)}  {os.path.relpath(f, os.path.dirname(ROOT.rstrip('/')))}\n")
    print("integral manifest", len(rows))
