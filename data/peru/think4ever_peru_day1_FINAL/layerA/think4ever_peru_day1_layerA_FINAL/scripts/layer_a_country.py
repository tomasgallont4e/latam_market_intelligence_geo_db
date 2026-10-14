"""Layer A - GitHub Innovation Graph - Argentina (AR).

Reproduces the Chile Day 1 conventions exactly (release 1.0.10, commit 078fb62):
  A1-A3 direct reads, YoY on same quarter, ratios on latest quarter.
  A4 growth threshold = 5000 x focus total memberships(prev-year Q) / CO total memberships(prev-year Q)
     (Chile precedent, PENDING D-04); alternative >=1000 shown.
  A5 two variants: template basket incl. PLSQL, and earlier T4E method excl. PLSQL (PENDING D-03).
Also re-computes the Chile values as a reproduction check of the method.
Usage: python3 -I layer_a_argentina.py <innovationgraph_repo_dir> <out_dir>
"""
import csv, json, sys, hashlib, os

REPO, OUT = sys.argv[1], sys.argv[2]
D = os.path.join(REPO, "data")
LATEST, PREV = (2026, 1), (2025, 1)
BASKET = ["Java", "C#", "Visual Basic .NET", "COBOL", "PLSQL", "TSQL", "ABAP", "Apex", "Groovy", "Scala", "Kotlin"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def series(fname, metric):
    out = {}
    with open(os.path.join(D, fname), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            out.setdefault(r["iso2_code"], {})[(int(r["year"]), int(r["quarter"]))] = int(r[metric])
    return out


def langs():
    out = {}
    with open(os.path.join(D, "languages.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            k = (int(r["year"]), int(r["quarter"]))
            out.setdefault(r["iso2_code"], {}).setdefault(k, {})[r["language"]] = (int(r["num_pushers"]), r["language_type"])
    return out


def lab(k):
    return f"{k[0]}Q{k[1]}"


def compute(cc, S, L):
    dev, org, push, repo = (S[m].get(cc, {}) for m in ("developers", "organizations", "git_pushes", "repositories"))
    rows = []
    def add(i, name, val, unit, num=None, den=None, method="", per=LATEST, cmp=None, variant=None, canon="canonical", vstat="verified"):
        rows.append(dict(indicator_id=i, indicator_name=name, country_code=cc, period_label=lab(per),
                         comparison_period_label=lab(cmp) if cmp else None, value=val, unit=unit,
                         numerator=num, denominator=den, method=method, method_variant=variant,
                         canonical_status=canon, validation_status=vstat))
    add("A1_developer_accounts", "Developer accounts (latest quarter)", dev[LATEST], "count", method=f"direct read, developers.csv iso2_code={cc}")
    add("A1_developer_accounts_prev_year", "Developer accounts (same quarter previous year)", dev[PREV], "count", method="direct read", per=PREV)
    add("A1_developer_accounts_2024q1", "Developer accounts 2024Q1 (history check)", dev[(2024, 1)], "count", method="direct read", per=(2024, 1))
    add("A1_developer_accounts_yoy", "Developer accounts year-on-year growth", dev[LATEST] / dev[PREV] - 1, "growth_rate", dev[LATEST], dev[PREV], "latest / previous - 1 (same quarter)", cmp=PREV)
    add("A2_organizations", "Organization accounts (latest quarter)", org[LATEST], "count", method="direct read, organizations.csv")
    add("A2_organizations_yoy", "Organization accounts year-on-year growth", org[LATEST] / org[PREV] - 1, "growth_rate", org[LATEST], org[PREV], "latest / previous - 1 (same quarter)", cmp=PREV)
    add("A2_developers_per_organization", "Developer accounts per organization", dev[LATEST] / org[LATEST], "ratio", dev[LATEST], org[LATEST], "developers / organizations")
    add("A3_git_pushes", "Git pushes in the quarter", push[LATEST], "count", method="direct read, git_pushes.csv")
    add("A3_git_pushes_yoy", "Git pushes year-on-year growth", push[LATEST] / push[PREV] - 1, "growth_rate", push[LATEST], push[PREV], "latest / previous - 1 (same quarter)", cmp=PREV)
    add("A3_pushes_per_developer_account", "Git pushes per developer account", push[LATEST] / dev[LATEST], "ratio", push[LATEST], dev[LATEST], "git_pushes / developers (flow / stock incl. inactive)")
    # A4
    lat, prv = L[cc][LATEST], L[cc][PREV]
    tot_prev = sum(v[0] for v in prv.values())
    co_prev = sum(v[0] for v in L["CO"][PREV].values())
    thr = 5000 * tot_prev / co_prev
    add("A4_growth_threshold", f"Fastest-growing list: minimum prior-year pushers (scaled from Colombia 5,000 rule)", thr, "count", 5000 * tot_prev, co_prev,
        f"5000 x {cc} total memberships 2025Q1 / CO total memberships 2025Q1", canon="undetermined", vstat="pending_methodological_validation")
    def growth(minbase):
        g = [(lang, n / prv[lang][0] - 1, n, prv[lang][0]) for lang, (n, t) in lat.items()
             if t == "programming" and lang in prv and prv[lang][0] >= minbase]
        return sorted(g, key=lambda x: -x[1])
    g_main = growth(thr)
    for i, (lang, gr, n, p) in enumerate(g_main[:6], 1):
        add(f"A4_fastest_growing_{i:02d}", f"Fastest-growing language #{i}: {lang} (pushers YoY)", gr, "growth_rate", n, p,
            "num_pushers 2026Q1 / 2025Q1 - 1; programming languages above threshold", cmp=PREV, canon="undetermined", vstat="pending_methodological_validation")
    g_alt = growth(1000)
    for i, (lang, gr, n, p) in enumerate(g_alt[:6], 1):
        add(f"A4_alt1000_fastest_growing_{i:02d}", f"Fastest-growing language #{i} (alternative base >=1,000): {lang}", gr, "growth_rate", n, p,
            "same, programming languages with prior-year base >= 1,000 (alternative shown in Chile G7)", cmp=PREV, variant="alt_min_base_1000",
            canon="undetermined", vstat="pending_methodological_validation")
    # A5
    tot = sum(v[0] for v in lat.values())
    b1 = sum(lat[l][0] for l in BASKET if l in lat)
    b2 = sum(lat[l][0] for l in BASKET if l in lat and l != "PLSQL")
    add("A5_enterprise_share_template_basket", "Enterprise-language share (template basket incl. PLSQL)", b1 / tot, "proportion", b1, tot,
        "sum(basket pushers) / sum(all language pushers)", variant="template_basket_incl_plsql", canon="undetermined", vstat="pending_methodological_validation")
    add("A5_enterprise_share_earlier_method", "Enterprise-language share (earlier Think4Ever method, PLSQL omitted)", b2 / tot, "proportion", b2, tot,
        "same, excluding PLSQL", variant="earlier_t4e_method_excl_plsql", canon="undetermined", vstat="pending_methodological_validation")
    # languages table
    lrows = []
    for per in (LATEST, PREV):
        d = L[cc][per]
        ranked = sorted(d.items(), key=lambda kv: -kv[1][0])
        for rank, (lang, (n, t)) in enumerate(ranked, 1):
            ge = None
            if per == LATEST:
                ge = (t == "programming" and lang in prv and prv[lang][0] >= thr)
            lrows.append(dict(country_code=cc, period_label=lab(per), language=lang, language_type=t, num_pushers=n, rank_in_period=rank,
                              in_a5_template_basket=lang in BASKET, growth_eligible=ge,
                              growth_rule_status="pending_methodological_validation" if per == LATEST else None))
    # quarterly table
    qrows = []
    defs = {"developers": "developer accounts located in economy (mode daily IP), incl. inactive",
            "organizations": "organization accounts located in economy",
            "git_pushes": "git pushes in the quarter (flow)",
            "repositories": "repositories with activity, located in economy"}
    for m in ("developers", "organizations", "git_pushes", "repositories"):
        for k, v in sorted(S[m].get(cc, {}).items()):
            qrows.append(dict(country_code=cc, metric=m, metric_definition=defs[m], year=k[0], quarter=k[1], period_label=lab(k), value=v))
    return rows, lrows, qrows, dict(basket_present=[l for l in BASKET if l in lat], basket_absent=[l for l in BASKET if l not in lat], total_memberships_latest=tot,
                                    total_memberships_prev=tot_prev, co_total_memberships_prev=co_prev, latest_quarter_available=lab(max(dev)))


def main():
    S = {m: series(f"{m}.csv", m) for m in ("developers", "organizations", "git_pushes", "repositories")}
    L = langs()
    os.makedirs(OUT, exist_ok=True)
    res = {}
    for cc in (sys.argv[3] if len(sys.argv)>3 else "PE", "AR", "CL"):
        res[cc] = compute(cc, S, L)
    for cc, (rows, lrows, qrows, meta) in res.items():
        for name, data in (("indicators", rows), ("languages", lrows), ("quarterly", qrows)):
            p = os.path.join(OUT, f"layer_a_{cc.lower()}_{name}.csv")
            with open(p, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
                w.writeheader(); w.writerows(data)
        with open(os.path.join(OUT, f"layer_a_{cc.lower()}_meta.json"), "w") as f:
            json.dump(meta, f, indent=1)
    hashes = {fn: sha(os.path.join(D, fn)) for fn in sorted(os.listdir(D)) if fn.endswith(".csv")}
    with open(os.path.join(OUT, "layer_a_source_hashes.json"), "w") as f:
        json.dump(hashes, f, indent=1)


if __name__ == "__main__":
    main()
