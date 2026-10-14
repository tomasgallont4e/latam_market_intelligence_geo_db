"""Peru Day 1 FINAL - second documentation pass after close_peru_day1_final.py (status wording only; no results touched).

Usage: python3 -I close_peru_day1_final_polish.py <final_integral_dir>
"""
import sys, os, glob

R = sys.argv[1]
F = os.path.join(R, "layerF", "think4ever_peru_day1_layerF_FINAL")

def edit(path, old, new, count=1):
    s = open(path, encoding="utf-8").read()
    n = s.count(old)
    if n != count:
        raise SystemExit(f"{path}: expected {count} match(es) of {old[:60]!r}, found {n}")
    open(path, "w", encoding="utf-8").write(s.replace(old, new))

# 1. nested parentheses introduced by the closure timestamp
for p in glob.glob(os.path.join(R, "**", "*.md"), recursive=True):
    s = open(p, encoding="utf-8").read()
    t = s.replace("19:06 (hora de Bogotá))", "19:06, hora de Bogotá)").replace("19:06 (hora de Bogotá) (sección 6)", "19:06, hora de Bogotá (sección 6)")
    if t != s:
        open(p, "w", encoding="utf-8").write(t)

# 2. sentences that still read as pending authorisation
for p in (os.path.join(R, "Peru_Day1_Auditoria_Final_Cierre.md"), os.path.join(F, "Peru_Day1_Auditoria_Final_Cierre.md")):
    edit(p, "**El paso a FINAL queda a la espera de tu autorización expresa.**",
         "**En la v2, el paso a FINAL quedaba a la espera de autorización expresa. Think4ever la concedió el 9 de octubre de 2026, 19:06, hora de Bogotá (sección 6).**")
edit(os.path.join(F, "README.md"), "C1–C3 resueltas; pendiente de autorización)",
     "C1–C3 resueltas; FINAL autorizado el 9 de octubre de 2026, 19:06, hora de Bogotá)")
print("polish applied")
