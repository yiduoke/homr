"""Tables after the page-merger fixes: out/testset/POOLED-table-2026-11-17-after-merger.md and CORRECTED-table-2026-11-17-after-merger.md.
Needs rescore_visible.py, rescore_pooled.py and (for the three Schott Liszt scans) remerge_after_merger.sh + score_after_merger.py first.
For liszt-sonata, liszt-te-5, liszt-te-10 the score of tag T is read from tag T_am (re-merged with simultaneous same-name parts kept
apart and lined up per page) where that exists; run B (r3B7) has no page outputs locally, so it is NOT re-merged. The older tables are kept."""
import json, os, statistics as st
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "testset"); P = os.path.join(T, "..", "pooled")
SCHOTT = {"liszt-sonata", "liszt-te-5", "liszt-te-10"}
DATE = "2026-11-17"
def metr(m):
    k = lambda x: m[x]["combined"] if "combined" in m[x] else m[x]
    return dict(f1=k("pitch_inventory")["f1"] * 100, p=k("pitch_inventory")["precision"] * 100, r=k("pitch_inventory")["recall"] * 100,
                po=k("pitch_onset")["f1"] * 100, full=k("pitch_onset_duration")["f1"] * 100)
def find(f, name):
    if not os.path.exists(f): return None
    for r in json.load(open(f))["results"]:
        if r["name"] == name: return r
def tagfor(piece, tag): return tag + "_am" if piece in SCHOTT and os.path.exists(f"{T}/{piece}/note-scores-{tag}_am.json") else tag
def sens(piece, tag):
    t = tagfor(piece, tag); r = find(f"{T}/{piece}/note-scores-{t}.json", t)
    return None if r is None else dict(metr(r["metrics"]), pred=r["predicted_measures"], ref=r["reference_measures"], mode=r["alignment_mode"])
def pooled(piece, tag):
    t = tagfor(piece, tag); r = find(f"{P}/{piece}/{t}.json", t)
    if r is None: return None
    sa = (r.get("staff_agnostic") or {}).get("metrics")
    return dict(metr(sa if sa else r["metrics"]), staff_agnostic=bool(sa))
def bars(x):
    v = x["pred"]; w = x["ref"]
    return (f"{v[0]}/{v[1]}" if isinstance(v, list) else str(v)), (str(w[0]) if isinstance(w, list) else str(w))
pieces = sorted(d for d in os.listdir(T) if os.path.isdir(f"{T}/{d}") and not d.endswith("-rendered") and os.path.exists(f"{T}/{d}/note-scores-layout1.json"))
tags = ["layout1", "r3B7", "r3ctrl_s7", "r3ctrl_s11", "r3cand_s7", "r3cand_s11"]
names = {"layout1": "released", "r3B7": "run B (not re-merged)", "r3ctrl_s7": "control s7 (unguarded loops)", "r3ctrl_s11": "control s11 (unguarded loops)",
         "r3cand_s7": "harder-data s7", "r3cand_s11": "harder-data s11"}
NOTE = ("Visible notes only (`print-object=\"no\"` and invisible noteheads are not counted). Scriabin is scored against its reference without the stray 47-note "
        "second part (original kept). **After-merger** = `merge_pages.py` keeps the simultaneous same-name parts of a page apart and gives the part with fewer bars on a page rests "
        "for the missing bars at the end of that page (the lost bars sit mid-page and cannot be located), so both hands have the same bars per page. This affects only liszt-sonata, liszt-te-5 and liszt-te-10 "
        "(tag `T_am`); the Schott staves are still not joined as grand staffs, that is handled separately. Run B has only its final files locally: not re-merged, its Schott rows keep the old "
        "doubled bars. **Petrushka is provisional**: it is scored staff-ignored with per-staff bar alignment in the staff-sensitive column (58.3), the pooled column uses one joint alignment (79.2) because "
        "the reference has three staves and ours two; the pooled figure is not verified. Rendered columns use the earlier outputs (not re-merged).")
S = {t: {p: sens(p, t) for p in pieces} for t in tags}; Q = {t: {p: pooled(p, t) for p in pieces} for t in tags}
ok = [t for t in tags if all(S[t][p] and Q[t][p] for p in pieces)]
mean = lambda xs: st.mean(xs)
# ---- POOLED table
L = [f"# Pooled-staff pitch table after the merger fixes (visible notes only), {DATE}", "", NOTE, "",
     "Pooled = a pitch counts if it appears on either staff of the aligned bar. Staff-sensitive = the pitch must be on the reference staff. Pitch inventory F1 in %; P, R, +onset and full are pooled. "
     "Bars = our bars per part / reference bars (a pair of numbers when the two hands have different counts).", "",
     "## Released model, per scan", "", "| piece | bars ours / ref | staff-sens pitch | staff-sens +onset | staff-sens full | pooled P | pooled R | pooled pitch | pooled +onset | pooled full |", "|---|---|---|---|---|---|---|---|---|---|"]
for p in pieces:
    s, q = S["layout1"][p], Q["layout1"][p]; a, b = bars(s)
    mark = " *" if p in SCHOTT else (" (provisional)" if p == "stravinsky-petrushka" else "")
    L.append(f"| {p}{mark} | {a} / {b} | {s['f1']:.1f} | {s['po']:.1f} | {s['full']:.1f} | {q['p']:.1f} | {q['r']:.1f} | {q['f1']:.1f} | {q['po']:.1f} | {q['full']:.1f} |")
L += ["", "\\* re-merged (after-merger). Bar counts equal to the reference: " + str(sum(bars(S['layout1'][p])[0] == bars(S['layout1'][p])[1] for p in pieces)) + f" of {len(pieces)} scans.", "",
      "## All checkpoints, mean over 28 scans", "",
      "| model | staff-sens pitch | staff-sens +onset | staff-sens full | pooled pitch | pooled +onset | pooled full | at 97+ staff-sens | at 97+ pooled | worst piece staff-sens | worst piece pooled (without Petrushka) |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for t in ok:
    a = [S[t][p] for p in pieces]; b = [Q[t][p] for p in pieces]; w = min((p for p in pieces if p != "stravinsky-petrushka"), key=lambda p: Q[t][p]["f1"]); v = min(pieces, key=lambda p: S[t][p]["f1"])
    L.append(f"| {names[t]} | {mean(x['f1'] for x in a):.1f} | {mean(x['po'] for x in a):.1f} | {mean(x['full'] for x in a):.1f} | {mean(x['f1'] for x in b):.1f} | {mean(x['po'] for x in b):.1f} | {mean(x['full'] for x in b):.1f} | "
             f"{sum(x['f1'] >= 97 for x in a)} | {sum(x['f1'] >= 97 for x in b)} | {v} {S[t][v]['f1']:.1f} | {w} {Q[t][w]['f1']:.1f} |")
L += ["", "Same means without Petrushka (provisional) and without the three Schott scans:", "", "| model | staff-sens pitch (27) | pooled pitch (27) | staff-sens pitch (25) | pooled pitch (25) |", "|---|---|---|---|---|"]
for t in ok:
    p27 = [p for p in pieces if p != "stravinsky-petrushka"]; p25 = [p for p in p27 if p not in SCHOTT]
    L.append(f"| {names[t]} | {mean(S[t][p]['f1'] for p in p27):.1f} | {mean(Q[t][p]['f1'] for p in p27):.1f} | {mean(S[t][p]['f1'] for p in p25):.1f} | {mean(Q[t][p]['f1'] for p in p25):.1f} |")
rend = [(sens(p + "-rendered", "layout1"), pooled(p + "-rendered", "layout1"), p) for p in pieces]; rend = [x for x in rend if x[0] and x[1]]
L += ["", f"Rendered (released, {len(rend)} pieces): staff-sensitive {mean(x[0]['f1'] for x in rend):.1f}, pooled {mean(x[1]['f1'] for x in rend):.1f}; at 97+ pooled: {sum(x[1]['f1'] >= 97 for x in rend)}."]
# the three Schott scans before and after
L += ["", "## The three Schott Liszt scans, released model, step by step", "",
      "Original = hands poured into one part (about twice the bars). Merge fix = parts kept apart, per-staff bar alignment (unequal bars, no pooled score possible). After-merger = parts lined up per page, joint bar alignment.", "",
      "| piece | stage | bars ours / ref | staff-sens pitch | staff-sens +onset | pooled pitch | pooled +onset |", "|---|---|---|---|---|---|---|"]
for p in sorted(SCHOTT):
    for label, t in (("original", "layout1"), ("merge fix, hands not lined up", "mergefix"), ("after-merger", "layout1_am")):
        s = find(f"{T}/{p}/note-scores-{t}.json", t)
        if s is None: continue
        m = dict(metr(s["metrics"]), pred=s["predicted_measures"], ref=s["reference_measures"]); a, b = bars(m)
        q = find(f"{P}/{p}/{t}.json", t); qq = None
        if q: sa = (q.get("staff_agnostic") or {}).get("metrics"); qq = metr(sa if sa else q["metrics"])
        L.append(f"| {p} | {label} | {a} / {b} | {m['f1']:.1f} | {m['po']:.1f} | " + (f"{qq['f1']:.1f} | {qq['po']:.1f} |" if qq else "n/a | n/a |"))
open(f"{T}/POOLED-table-{DATE}-after-merger.md", "w").write("\n".join(L) + "\n")
# ---- CORRECTED table (staff-sensitive pitch, +onset in brackets)
C = [f"# Corrected test-set table after the merger fixes, {DATE}", "", NOTE, "",
     "Staff-sensitive pitch F1 % (pitch inventory, timing ignored), with pitch+onset in brackets. Pooled-staff scores and bar counts: `POOLED-table-2026-11-17-after-merger.md`.", "",
     "| piece | rendered (released) | scan released | scan run B | scan control s7 | scan control s11 | scan harder-data s7 | scan harder-data s11 |", "|---|---|---|---|---|---|---|---|"]
cell = lambda x: f"{x['f1']:.1f} ({x['po']:.1f})"
for p in pieces:
    r = sens(p + "-rendered", "layout1")
    mark = " *" if p in SCHOTT else (" (provisional)" if p == "stravinsky-petrushka" else "")
    C.append(f"| {p}{mark} | " + (cell(r) if r else "n/a") + " | " + " | ".join(cell(S[t][p]) for t in tags) + " |")
C.append("| **mean** | " + f"{mean(x[0]['f1'] for x in rend):.1f} ({mean(x[0]['po'] for x in rend):.1f}) | " + " | ".join(f"{mean(S[t][p]['f1'] for p in pieces):.1f} ({mean(S[t][p]['po'] for p in pieces):.1f})" for t in tags) + " |")
C.append("| **mean without Petrushka** | " + " | ".join(
    f"{mean(x[0]['f1'] for x in rend if x[2] != 'stravinsky-petrushka'):.1f} ({mean(x[0]['po'] for x in rend if x[2] != 'stravinsky-petrushka'):.1f})" for _ in [0]) + " | " + " | ".join(
    f"{mean(S[t][p]['f1'] for p in pieces if p != 'stravinsky-petrushka'):.1f} ({mean(S[t][p]['po'] for p in pieces if p != 'stravinsky-petrushka'):.1f})" for t in tags) + " |")
open(f"{T}/CORRECTED-table-{DATE}-after-merger.md", "w").write("\n".join(C) + "\n")
print("\n".join(L[L.index("## All checkpoints, mean over 28 scans"):]))
