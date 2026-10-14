"""Parse CNO 2015 (INEI) correspondence annexes with CIUO-08.

Annex 3 (pp. 425-447): CNO 2015 -> CIUO 2008. Columns: CNO code, CNO title, enlace, CIUO code, CIUO title, enlace.
Annex 4 (pp. 448-472): CIUO 2008 -> CNO 2015. Columns: CIUO code, CIUO title, enlace, CNO title, CNO code, enlace.

The PDF text layer contains residual (hidden) copies of neighbouring pages drawn before the
visible table; geometric extraction interleaves them. Reading characters in content-stream order
keeps each row contiguous, so rows are parsed from the stream string and de-duplicated across
pages. Each annex is parsed independently; the two directions are cross-checked.

Usage: python3 -I parse_cno2015_annex.py <CNO2015.pdf> <out_dir>
"""
import csv, os, re, sys, hashlib
import pdfplumber

PDF, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

# name: any run without digits (titles contain no digits)
A3 = re.compile(r"(\d{4})([^\d]+?)\s*([01])(\d{4})([^\d]+?)\s*([01])(?=\d{4}|\s*$)")
A4 = re.compile(r"(\d{4})([^\d]+?)\s*([01])([^\d]+?)\s*(\d{4})\s*([01])(?=\d{4}|\s*$)")


def stream_text(page):
    return "".join(c["text"] for c in page.chars)


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def strip_headers(t):
    for h in ["Instituto Nacional de Estadística e Informática", "CLASIFICADOR NACIONAL DE OCUPACIONES 2015",
              "Código C N O 2015", "Grupo Primario C N O 2015", "Código C I U O 2008", "Grupo Primario C I U O 2008",
              "Código CIUO 2008", "Grupo Primario CIUO 2008", "Código CNO 2015", "Grupo Primario CNO 2015",
              "Enlace", "Continúa...", "Continúa…", "Conclusión", "Anexo Nº 3", "Anexo Nº 4",
              "Tabla de Correspondencia del Clasificador Nacional de Ocupaciones (CNO) 2015 con el CIUO 2008",
              "Tabla de Correspondencia del CIUO 2008 con el Clasificador Nacional de Ocupaciones (CNO) 2015"]:
        t = t.replace(h, "|")
    t = re.sub(r"^\d{3}", "", t)  # leading page number
    return t


def parse(pages, rx, kind):
    rows, conflicts = {}, []
    with pdfplumber.open(PDF) as pdf:
        for pno in pages:
            t = strip_headers(stream_text(pdf.pages[pno - 1]))
            for seg in t.split("|"):
                for m in rx.finditer(seg):
                    g = [clean(x) for x in m.groups()]
                    if kind == "a3":
                        key = (g[0], g[3]); rec = dict(cno=g[0], cno_title=g[1], cno_enlace=g[2], ciuo=g[3], ciuo_title=g[4], ciuo_enlace=g[5])
                    else:
                        key = (g[4], g[0]); rec = dict(cno=g[4], cno_title=g[3], cno_enlace=g[5], ciuo=g[0], ciuo_title=g[1], ciuo_enlace=g[2])
                    rec["page_first_seen"] = pno
                    if key in rows:
                        a, b = rows[key], rec
                        if (a["cno_enlace"], a["ciuo_enlace"]) != (b["cno_enlace"], b["ciuo_enlace"]):
                            conflicts.append((kind, key, a, b))
                    else:
                        rows[key] = rec
    return rows, conflicts


def main():
    a3, c3 = parse(range(425, 448), A3, "a3")
    a4, c4 = parse(range(448, 473), A4, "a4")
    keys = sorted(set(a3) | set(a4))
    out = []
    for k in keys:
        r3, r4 = a3.get(k), a4.get(k)
        r = dict(r3 or r4)
        r["in_annex3"] = r3 is not None
        r["in_annex4"] = r4 is not None
        r["enlace_agree"] = (r3 is not None and r4 is not None and
                             (r3["cno_enlace"], r3["ciuo_enlace"]) == (r4["cno_enlace"], r4["ciuo_enlace"]))
        r.pop("page_first_seen", None)
        out.append(r)
    p = os.path.join(OUT, "cno2015_ciuo08_correspondence.csv")
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["cno", "cno_title", "cno_enlace", "ciuo", "ciuo_title", "ciuo_enlace", "in_annex3", "in_annex4", "enlace_agree"])
        w.writeheader(); w.writerows(out)
    h = hashlib.sha256(open(PDF, "rb").read()).hexdigest()
    print(f"pdf_sha256={h}")
    print(f"annex3_pairs={len(a3)} annex4_pairs={len(a4)} union={len(keys)} both={sum(r['in_annex3'] and r['in_annex4'] for r in out)}")
    print(f"enlace_disagree={sum((r['in_annex3'] and r['in_annex4']) and not r['enlace_agree'] for r in out)} dup_conflicts={len(c3)+len(c4)}")
    print(f"distinct_cno={len({r['cno'] for r in out})} distinct_ciuo={len({r['ciuo'] for r in out})}")


if __name__ == "__main__":
    main()
