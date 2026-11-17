"""Pooled vs staff-sensitive table for every checkpoint -> out/testset/POOLED-table-<date>.md (needs rescore_visible.py and rescore_pooled.py first)."""
import json, os, statistics as st, sys
T = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "testset"); P = os.path.join(T, "..", "pooled")
def metr(m):
    k = lambda x: m[x]["combined"] if "combined" in m[x] else m[x]
    return dict(f1=k("pitch_inventory")["f1"] * 100, p=k("pitch_inventory")["precision"] * 100, r=k("pitch_inventory")["recall"] * 100,
                po=k("pitch_onset")["f1"] * 100, full=k("pitch_onset_duration")["f1"] * 100)
def load(f, name, pooled=False):
    if not os.path.exists(f): return None
    for r in json.load(open(f))["results"]:
        if r["name"] == name:
            sa = (r.get("staff_agnostic") or {}).get("metrics")
            return metr(sa if (pooled and sa) else r["metrics"])
pieces = sorted(d for d in os.listdir(T) if os.path.isdir(f"{T}/{d}") and not d.endswith("-rendered") and os.path.exists(f"{T}/{d}/note-scores-layout1.json"))
tags = ["layout1", "r3B7", "r3ctrl_s7", "r3ctrl_s11", "r3cand_s7", "r3cand_s11"]
names = {"layout1": "released", "r3B7": "run B", "r3ctrl_s7": "control s7 (unguarded loops)", "r3ctrl_s11": "control s11 (unguarded loops)",
         "r3cand_s7": "harder-data s7", "r3cand_s11": "harder-data s11"}
L = ["# Pooled-staff pitch table (visible notes only), 2026-11-17", "",
     "Pooled = a pitch counts if it appears on either staff of the bar (bars are aligned again with staves ignored, so totals can differ by a few notes). Staff-sensitive = the pitch must be on the reference staff. Pitch inventory F1 in %; P and R are pooled precision and recall; +onset and full are pooled as well. Scriabin is scored against its reference without the stray 47-note second part (original kept). Petrushka is scored staff-ignored in both columns.", "",
     "## Released model, per scan", "", "| piece | staff-sensitive F1 | pooled P | pooled R | pooled F1 | pooled +onset | pooled full |", "|---|---|---|---|---|---|---|"]
rel = {}
for p in pieces:
    s = load(f"{T}/{p}/note-scores-layout1.json", "layout1"); q = load(f"{P}/{p}/layout1.json", "layout1", True); rel[p] = (s, q)
    L.append(f"| {p} | {s['f1']:.1f} | {q['p']:.1f} | {q['r']:.1f} | {q['f1']:.1f} | {q['po']:.1f} | {q['full']:.1f} |")
L += ["", "## All checkpoints, mean over 28 scans", "", "| model | staff-sensitive F1 | pooled F1 | pooled +onset | pooled full | scans at 97+ (staff-sensitive) | scans at 97+ (pooled) |", "|---|---|---|---|---|---|---|"]
for t in tags:
    a = [load(f"{T}/{p}/note-scores-{t}.json", t) for p in pieces]; b = [load(f"{P}/{p}/{t}.json", t, True) for p in pieces]
    if None in a or None in b: continue
    L.append(f"| {names[t]} | {st.mean(x['f1'] for x in a):.1f} | {st.mean(x['f1'] for x in b):.1f} | {st.mean(x['po'] for x in b):.1f} | {st.mean(x['full'] for x in b):.1f} | {sum(x['f1'] >= 97 for x in a)} | {sum(x['f1'] >= 97 for x in b)} |")
rend = [(load(f"{T}/{p}-rendered/note-scores-layout1.json", "layout1"), load(f"{P}/{p}-rendered/layout1.json", "layout1", True)) for p in pieces]
rend = [x for x in rend if x[0] and x[1]]
L += ["", f"Rendered (released, {len(rend)} pieces): staff-sensitive {st.mean(x[0]['f1'] for x in rend):.1f}, pooled {st.mean(x[1]['f1'] for x in rend):.1f}; at 97+ pooled: {sum(x[1]['f1'] >= 97 for x in rend)}."]
open(f"{T}/POOLED-table-2026-11-17.md", "w").write("\n".join(L) + "\n")
print("\n".join(L[-11:])); print("scans at 97+ pooled (released):", [p for p in pieces if rel[p][1]["f1"] >= 97])
print("biggest pooled gains:", sorted(((round(rel[p][1]["f1"] - rel[p][0]["f1"], 1), p) for p in pieces), reverse=True)[:6])
print("Petrushka:", {k: round(v, 1) for k, v in rel["stravinsky-petrushka"][0].items()}, {k: round(v, 1) for k, v in rel["stravinsky-petrushka"][1].items()})
