"""Layer B engine - Stack Overflow Developer Survey 2025, parameterised by focus country.

Implements the approved Chile Day 1 Layer B framework (B1-B5, BX1-BX12) generically:
  - unweighted proportions; question-specific valid denominators (blanks excluded, no imputation)
  - Wilson 95% intervals; base flags: valid_n >= 50 ok, 30-49 indicative, < 30 suppressed (empty)
  - small_numerator_flag = numerator < 10
  - exploratory labels (focus country / all_respondents rows only): non-overlap of Wilson intervals
Usage: python3 -I layer_b_engine.py <results.csv> <focus_iso2> <out_dir>
"""
import csv, math, os, sys, json
from collections import Counter

csv.field_size_limit(10 ** 9)
Z = 1.959963984540054
LATAM19 = ["Argentina", "Bolivia", "Brazil", "Chile", "Colombia", "Costa Rica", "Cuba", "Dominican Republic", "Ecuador",
           "El Salvador", "Guatemala", "Honduras", "Mexico", "Nicaragua", "Panama", "Paraguay", "Peru", "Uruguay",
           "Venezuela, Bolivarian Republic of..."]
ISO = {"AR": "Argentina", "CL": "Chile", "BR": "Brazil", "MX": "Mexico", "CO": "Colombia", "PE": "Peru"}
PRO = "I am a developer by profession"
SRC = "SRC_SO_2025"
AI_NATIVE = ["Cursor", "Windsurf", "Claude Code", "Cline and/or Roo", "Aider", "Trae", "Bolt", "Lovable.dev", "Zed"]
TASK_COLS = {"current": ["AIToolCurrently partially AI", "AIToolCurrently mostly AI"],
             "planned": ["AIToolPlan to partially use AI", "AIToolPlan to mostly use AI"],
             "not_planned": ["AIToolDon't plan to use AI for this task"]}
STANCE_TXT = {"current": "currently uses AI (mostly or partially)", "planned": "plans to use AI (mostly or partially)",
              "not_planned": "does not plan to use AI"}
DIST = [("BX5", "AISent"), ("BX7", "AIComplex"), ("BX6", "AIAcc"), ("BX8", "AIAgentChange"), ("BX10", "PurchaseInfluence"),
        ("BX12", "LearnCodeAI"), ("BX11", "AIThreat")]
META = {"B1": ("adoption", "AISelect", "QID78"), "B2": ("adoption", "AISelect", "QID78"), "B3": ("adoption", "AIAgents", "QID85"),
        "B4a": ("tool_use", "DevEnvsHaveWorkedWith", "QID38"), "B4b": ("tool_use", "AIModelsHaveWorkedWith", "QID43"),
        "B4c": ("tool_use", "AIAgentExternal", "QID92"), "B5": ("sample", "Country", "QID20"),
        "BX1": ("intention", "AISelect", "QID78"), "BX2": ("intention", "AIAgents", "QID85"),
        "BX3": ("intention", "DevEnvsWantToWorkWith", "QID38"), "BX4": ("intention", "AITool* (5 matrix columns)", "QID82"),
        "BX5": ("sentiment", "AISent", "QID79"), "BX6": ("trust", "AIAcc", "QID80"), "BX7": ("trust", "AIComplex", "QID81"),
        "BX8": ("behaviour", "AIAgentChange", "QID83"), "BX9": ("behaviour", "AIFrustration", "QID99"),
        "BX10": ("behaviour", "PurchaseInfluence", "QID17"), "BX11": ("sentiment", "AIThreat", "QID28"),
        "BX12": ("behaviour", "LearnCodeAI", "QID12")}


def wilson(k, n):
    p = k / n
    d = 1 + Z * Z / n
    c = (p + Z * Z / (2 * n)) / d
    h = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def ms(v):
    return [x for x in v.split(";")] if v not in ("", "NA") else []


def valid(v):
    return v not in ("", "NA")


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def groups(rows, focus):
    fname = ISO[focus]
    latam = [c for c in LATAM19 if c != fname]
    G = [("country", focus, "all_respondents", f'Respondents with Country = "{fname}"', fname, "", lambda r: r["Country"] == fname),
         ("country", focus, "professional_developers", f'Respondents with Country = "{fname}" and MainBranch = "{PRO}"',
          f"{fname} - professional developers", "", lambda r: r["Country"] == fname and r["MainBranch"] == PRO),
         ("region", f"LATAM_EX_{focus}", "all_respondents", f"Respondents in 18 Latin American countries, {fname} EXCLUDED",
          f"LATAM excl. {fname} (18 countries)", ";".join(latam), lambda r: r["Country"] in latam),
         ("global", "GLOBAL", "all_respondents", "All 49,191 respondents in the public CSV, including 13,754 with no country",
          "Global", "", lambda r: True)]
    for cc in ("BR", "MX", "AR", "CO", "CL", "PE"):
        if cc == focus:
            continue
        if cc == "PE":
            continue  # not in the Chile reference set; kept out for comparability
        G.append(("country", cc, "all_respondents", f'Country = "{ISO[cc]}"', ISO[cc], "", (lambda n: lambda r: r["Country"] == n)(ISO[cc])))
    return G


def universe(rows):
    U = {}
    for var in ("DevEnvsHaveWorkedWith", "AIModelsHaveWorkedWith", "AIAgentExternal", "DevEnvsWantToWorkWith", "AIFrustration"):
        c = Counter()
        for r in rows:
            c.update(ms(r[var]))
        U[var] = [k for k, _ in c.most_common()]
    tasks = Counter()
    for cols in TASK_COLS.values():
        for col in cols:
            for r in rows:
                tasks.update(ms(r[col]))
    U["tasks"] = sorted(t for t in tasks if t != "Other (write in):")  # write-in column excluded (Chile framework: 14 tasks)
    for _, var in DIST:
        U["dist_" + var] = sorted({r[var] for r in rows if valid(r[var])})
    return U


def indicators(sub, U):
    out = []  # (iid, item, task, stance, k, n, derived)
    def single(var, cats):
        v = [r[var] for r in sub if valid(r[var])]
        return sum(x in cats for x in v), len(v)
    def multi(var, opts):
        v = [set(ms(r[var])) for r in sub if valid(r[var])]
        return v
    k, n = single("AISelect", {"Yes, I use AI tools daily", "Yes, I use AI tools weekly", "Yes, I use AI tools monthly or infrequently"})
    out.append(("B1", "Uses AI tools (daily, weekly or monthly/infrequently)", "", "", k, n, False))
    k, n = single("AISelect", {"Yes, I use AI tools daily"})
    out.append(("B2", "Uses AI tools daily", "", "", k, n, False))
    k, n = single("AIAgents", {"Yes, I use AI agents at work daily", "Yes, I use AI agents at work weekly", "Yes, I use AI agents at work monthly or infrequently"})
    out.append(("B3", "Uses AI agents at work (daily, weekly or monthly/infrequently)", "", "", k, n, False))
    for iid, var in (("B4a", "DevEnvsHaveWorkedWith"), ("B4b", "AIModelsHaveWorkedWith"), ("B4c", "AIAgentExternal")):
        v = multi(var, None)
        for o in U[var]:
            out.append((iid, o, "", "", sum(o in s for s in v), len(v), False))
    out.append(("B5", "Respondents (rows with group definition)", "", "", len(sub), len(sub), False))
    v = multi("DevEnvsHaveWorkedWith", None)
    out.append(("B4a", "ANY AI-native editor (" + ", ".join(AI_NATIVE) + ")", "", "", sum(bool(s & set(AI_NATIVE)) for s in v), len(v), True))
    k, n = single("AISelect", {"No, but I plan to soon"})
    out.append(("BX1", "Does not use AI tools but plans to soon", "", "", k, n, False))
    k2, n2 = single("AISelect", {"No, but I plan to soon", "No, and I don't plan to"})
    out.append(("BX1", "Plans to soon, as share of NON-users", "", "", k, k2, False))
    for item, cat in (("Does not use AI agents but plans to", "No, but I plan to"),
                      ("Uses AI only in copilot/autocomplete mode (not agents)", "No, I use AI exclusively in copilot/autocomplete mode"),
                      ("Does not use AI agents and does not plan to", "No, and I don't plan to")):
        k, n = single("AIAgents", {cat})
        out.append(("BX2", item, "", "", k, n, False))
    v = multi("DevEnvsWantToWorkWith", None)
    for o in U["DevEnvsWantToWorkWith"]:
        out.append(("BX3", o, "", "", sum(o in s for s in v), len(v), False))
    for t in U["tasks"]:
        placed = [r for r in sub if any(t in ms(r[c]) for cols in TASK_COLS.values() for c in cols)]
        for st, cols in TASK_COLS.items():
            k = sum(any(t in ms(r[c]) for c in cols) for r in placed)
            out.append(("BX4", f"{t} | {STANCE_TXT[st]}", t, st, k, len(placed), False))
    k, n = single("AISent", {"Very favorable", "Favorable"})
    out.append(("BX5", "Favorable or very favorable towards AI tools", "", "", k, n, False))
    k, n = single("AIAcc", {"Highly trust", "Somewhat trust"})
    out.append(("BX6", "Trusts accuracy of AI output (highly or somewhat)", "", "", k, n, False))
    k, n = single("AIAcc", {"Highly distrust", "Somewhat distrust"})
    out.append(("BX6", "Distrusts accuracy of AI output (highly or somewhat)", "", "", k, n, False))
    k, n = single("AIComplex", {"Very well at handling complex tasks", "Good, but not great at handling complex tasks"})
    out.append(("BX7", "AI handles complex tasks very well or good", "", "", k, n, False))
    k, n = single("AIComplex", {"I don't use AI tools for complex tasks / I don't know"})
    out.append(("BX7", "Does not use AI for complex tasks / doesn't know", "", "", k, n, False))
    k, n = single("AIAgentChange", {"Yes, to a great extent", "Yes, somewhat"})
    out.append(("BX8", "AI tools or agents changed how development work is done", "", "", k, n, False))
    v = multi("AIFrustration", None)
    for o in U["AIFrustration"]:
        out.append(("BX9", o, "", "", sum(o in s for s in v), len(v), False))
    pi = ["Yes, I influenced the purchase of a substantial addition to the tech stack",
          "Yes, I influenced the purchase of a tool that more than five colleagues use but it is not a substantial addition to the tech stack",
          "Yes, I endorsed a tool that was open-source and is currently used by more than just myself but no purchase was made",
          "Yes, I endorsed a tool that was ultimately not purchased or used at my organization"]
    k, n = single("PurchaseInfluence", set(pi))
    out.append(("BX10", "Influenced or endorsed a technology purchase/tool in the past year", "", "", k, n, False))
    k, n = single("PurchaseInfluence", set(pi[:2]))
    out.append(("BX10", "Influenced a paid purchase (substantial addition or tool used by >5 colleagues)", "", "", k, n, False))
    k, n = single("AIThreat", {"Yes"})
    out.append(("BX11", "Believes AI is a threat to current job", "", "", k, n, False))
    lc = ["Yes, I learned how to use AI-enabled tools required for my job or to benefit my career",
          "Yes, I learned how to use AI-enabled tools for my personal curiosity and/or hobbies"]
    k, n = single("LearnCodeAI", set(lc))
    out.append(("BX12", "Learned AI-enabled tools in the past year", "", "", k, n, False))
    k, n = single("LearnCodeAI", {lc[0]})
    out.append(("BX12", "Learned AI-enabled tools for job or career", "", "", k, n, False))
    return out


def flag(n):
    return "ok" if n >= 50 else "indicative" if n >= 30 else "suppressed"


def main():
    path, focus, out_dir = sys.argv[1], sys.argv[2], sys.argv[3]
    rows = load(path)
    U = universe(rows)
    G = groups(rows, focus)
    ind, dist, grp = [], [], []
    for gtype, code, seg, gdef, glabel, incl, fn in G:
        sub = [r for r in rows if fn(r)]
        grp.append(dict(focus_country_code=focus, group_type=gtype, group_code=code, survey_segment=seg, group_definition=gdef,
                        group_label=glabel, countries_included=incl, respondents=len(sub),
                        template_confidence="LOW (<300)" if len(sub) < 300 else ">=300", source_id=SRC))
        for iid, item, task, st, k, n, der in indicators(sub, U):
            base = dict(survey="stack_overflow_developer_survey", survey_year=2025, indicator_id=iid, indicator_block=META[iid][0],
                        variable=META[iid][1], qid=META[iid][2], item=item, task=task, task_stance=st, focus_country_code=focus,
                        group_type=gtype, group_code=code, survey_segment=seg, group_definition=gdef)
            if iid == "B5":
                base.update(numerator=k, valid_n=n, proportion=None, ci_low=None, ci_high=None, base_flag="not_applicable",
                            small_numerator_flag=False)
            else:
                bf = flag(n)
                if bf == "suppressed" or n == 0:
                    base.update(numerator=None, valid_n=n, proportion=None, ci_low=None, ci_high=None, base_flag="suppressed",
                                small_numerator_flag=False)
                else:
                    lo, hi = wilson(k, n)
                    base.update(numerator=k, valid_n=n, proportion=k / n, ci_low=lo, ci_high=hi, base_flag=bf, small_numerator_flag=(k < 10 and gtype == "country"))  # country groups only
            base.update(is_derived=der, source_id=SRC)
            ind.append(base)
        for iid, var in DIST:
            v = [r[var] for r in sub if valid(r[var])]
            c = Counter(v)
            for cat in U["dist_" + var]:
                n = len(v); bf = flag(n)
                k = c.get(cat, 0)
                sup = bf == "suppressed"
                dist.append(dict(focus_country_code=focus, group_type=gtype, group_code=code, survey_segment=seg, group_definition=gdef,
                                 survey_year=2025, indicator_id=iid, variable=var, category=cat, numerator=None if sup else k, valid_n=n,
                                 proportion=None if sup else k / n, base_flag=bf, small_numerator_flag=False if sup else (k < 10 and gtype == "country"), source_id=SRC))
    # exploratory comparison labels (focus all_respondents rows only)
    key = lambda r: (r["indicator_id"], r["item"], r["task"], r["task_stance"])
    by = {(r["group_code"], r["survey_segment"], key(r)): r for r in ind}
    lat = f"LATAM_EX_{focus}"
    def lab(a, b):
        if a is None or b is None or a["ci_low"] is None or b["ci_low"] is None:
            return "not_assessed"
        if a["ci_low"] > b["ci_high"]:
            return "higher_exploratory"
        if a["ci_high"] < b["ci_low"]:
            return "lower_exploratory"
        return "no_clear_difference_exploratory"
    vs_l, vs_g = f"vs_latam_ex_{focus.lower()}", "vs_global"
    for r in ind:
        if r["group_code"] == focus and r["survey_segment"] == "all_respondents":
            r[vs_l] = lab(r, by.get((lat, "all_respondents", key(r))))
            r[vs_g] = lab(r, by.get(("GLOBAL", "all_respondents", key(r))))
        else:
            r[vs_l] = None; r[vs_g] = None
    cols = ["survey", "survey_year", "indicator_id", "indicator_block", "variable", "qid", "item", "task", "task_stance", "focus_country_code",
            "group_type", "group_code", "survey_segment", "group_definition", "numerator", "valid_n", "proportion", "ci_low", "ci_high",
            "base_flag", "small_numerator_flag", vs_l, vs_g, "is_derived", "source_id"]
    os.makedirs(out_dir, exist_ok=True)
    def w(name, data, fields):
        with open(os.path.join(out_dir, name), "w", newline="", encoding="utf-8") as f:
            wr = csv.DictWriter(f, fieldnames=fields); wr.writeheader()
            for d in data:
                wr.writerow({k: ("" if d.get(k) is None else d[k]) for k in fields})
    w(f"b_survey_indicators_{focus.lower()}.csv", ind, cols)
    w(f"b_survey_distributions_{focus.lower()}.csv", dist, list(dist[0].keys()))
    w(f"b_comparison_groups_{focus.lower()}.csv", grp, list(grp[0].keys()))
    print(json.dumps({"rows": len(rows), "groups": [(g["group_code"], g["survey_segment"], g["respondents"]) for g in grp],
                      "indicator_rows": len(ind), "distribution_rows": len(dist)}))


if __name__ == "__main__":
    main()
