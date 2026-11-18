"""table_d30.py: markdown tables of D30 from d30/eval_*.json (eval2.py) and eval_run1/merge_by_role/d30/results_<tag>.json (merge_score_d30.py).
usage (run/staff_rel_realbrace): python scripts/table_d30.py > d30/tables.md"""
import glob, json, re, os
R = "/Users/yiduoke/Documents/homr/run"
ev = {}
for f in sorted(glob.glob("d30/eval_*.json")):
    if "pairing" in f: continue
    ev.update(json.load(open(f)))
ORDER = ["shipped", "rb2", "rb3", "A_s0", "A_s1", "B_s0", "B_s1", "C_s0", "C_s1"]
names = [m for m in ORDER if m in ev]
cell = lambda c: f"{c['miss']} / {c['false_grand']} / {c['false_join']}"  # noqa
print("### Pairing decisions on held-out sets: missed grand / false grand / false join (n grand of n pairs)\n")
sets = [("mazeppa", "Mazeppa (reserved, same edition)"), ("schott_val", "Schott held-out pieces XI, XII, Waldesrauschen, Gnomenreigen + Concert-Etudes S.144"),
        ("curved_val", "held-out curved editions (22 editions)"), ("cappi1802", "Cappi 1802 (transfer)"), ("eder1800", "Eder 1800 (transfer, 2 pages)"), ("reichardt", "Reichardt 1819 (transfer)")]
print("| set (grand / pairs) | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
for k, t in sets:
    c0 = ev[names[0]][k]
    print(f"| {t} ({c0['grand']} / {c0['n']}) | " + " | ".join(cell(ev[m][k]) for m in names) + " |")
print("\n### Three Schott test scans, same edition, NOT transfer: grand-staff calls among the 169 within-system pairs (opening pages: 13 systems), separate pairs kept separate (of 136)\n")
print("| model | grand / 169 | opening pages / 13 | separate kept / 136 | Sonata | TE 5 | TE 10 |\n|---|---|---|---|---|---|---|")
for m in names:
    t = ev[m]["test_scans"]; tot = t["total"]; pp = t["per_piece"]
    print(f"| {m} | {tot['grand']} | {tot['opening_grand']} | {tot['between_sep']} | " + " | ".join(f"{pp[p]['grand']}/{pp[p]['inside']}" for p in ("liszt-sonata", "liszt-te-5", "liszt-te-10")) + " |")
print("\n### Per held-out curved edition (missed grand / false grand / false join)\n")
eds = sorted(ev[names[0]]["curved_val"]["per_group"])
print("| edition (grand) | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
for e in eds:
    print(f"| {e} ({ev[names[0]]['curved_val']['per_group'][e]['grand']}) | " + " | ".join(cell(ev[m]["curved_val"]["per_group"][e]) for m in names) + " |")
print("\n### Per held-out Schott piece (missed grand / false grand / false join)\n")
eds = sorted(ev[names[0]]["schott_val"]["per_group"])
print("| piece (grand) | " + " | ".join(names) + " |\n|---|" + "---|" * len(names))
for e in eds:
    print(f"| {e} ({ev[names[0]]['schott_val']['per_group'][e]['grand']}) | " + " | ".join(cell(ev[m]["schott_val"]["per_group"][e]) for m in names) + " |")
# pipeline
res = {}
for f in glob.glob(f"{R}/eval_run1/merge_by_role/d30/results_*.json"):
    res[os.path.basename(f)[8:-5]] = json.load(open(f))
if res:
    def f1(row, kind):
        j = row[kind]
        if not j: return "n/a"
        r0 = j["results"][0]; m = r0["metrics"]
        if kind == "pooled":
            sa = (r0.get("staff_agnostic") or {}).get("metrics")
            if not sa: return "n/a"
            m = sa
        k = m["pitch_inventory"]; k = k["combined"] if "combined" in k else k
        return f"{k['f1'] * 100:.1f}"
    def hs(row):
        m = re.search(r"'pct': ([\d.]+)", row["hand_sync"]); return f"{float(m.group(1)):.0f}%" if m else "?"
    def bars(row):
        r0 = row["staff"]["results"][0]; parts = re.findall(r"parts=(\d+)", row["parts_log"][0])[0]
        return f"{r0['predicted_measures']}/{r0['reference_measures']} ({parts}p)"
    tags = ["relbrace2_ctl_gpu"] + [f"relbrace2_{a}_s{s}_gpu" for a in "ABC" for s in (0, 1)]
    tags = [t for t in tags if t in res]
    print("\n### Full pipeline (box GPU, merger by staff role): staff-sensitive / pooled pitch F1; bars out / reference (parts after merge); hands in the same bar\n")
    print("| piece | " + " | ".join(t.replace("relbrace2_", "").replace("_gpu", "") for t in tags) + " |\n|---|" + "---|" * len(tags))
    for p in ["liszt-sonata", "liszt-te-5", "liszt-te-10", "liszt-te-4-schott"]:
        print(f"| {p} | " + " | ".join(f"{f1(res[t][p], 'staff')} / {f1(res[t][p], 'pooled')}; {bars(res[t][p])}; {hs(res[t][p])}" if p in res[t] else "-" for t in tags) + " |")
