"""Per page and per stage counts for one saved page set: detection -> grouping -> repair (from trace_stages.py replay),
page MusicXML parts (music21 ids and bars), the key the merger gives each part, parts after merge_pages.py, parts after drop_minor_parts.py.
usage: python trace_pipeline.py TAG PIECE MODELKEY  > table.md   (TAG: relctl|relbrace|relB0|relC0, MODELKEY: shipped|rb1|rb2|rb3)"""
import glob, json, os, re, sys, warnings
warnings.filterwarnings("ignore")
from music21 import converter
R = "/Users/yiduoke/Documents/homr/run"
tag, piece, mk = sys.argv[1:4]
D = f"{R}/eval_run1/testset/{tag}/{piece}"
stages = json.load(open(f"{R}/staff_rel_realbrace/trace/stages_{piece}.json"))
pages = sorted((f for f in glob.glob(f"{D}/page-xml/page-*.musicxml") if "_teaser" not in f),
               key=lambda p: int(re.search(r"page-(\d+)", p).group(1)))
totals, rows = {}, []
seen_keys = []
for path in pages:
    name = os.path.basename(path)[:-9]
    st = stages.get(name)
    sc = converter.parse(path, forceSource=True)
    seen, keys = {}, []
    for p in sc.parts:
        seen[p.id] = seen.get(p.id, 0) + 1
        k = p.id if seen[p.id] == 1 else f"{p.id}#{seen[p.id]}"
        n = len(p.getElementsByClass("Measure"))
        notes = len(p.flatten().notes)
        keys.append((k, n, notes))
        t = totals.setdefault(k, [0, 0]); t[0] += n; t[1] += notes
        if k not in seen_keys: seen_keys.append(k)
    if st:
        m = st["models"][mk]
        grouped = "".join(str(g[0]) for g in m["grouped"]); rep = "".join(str(r[0]) + ("g" if r[1][0] else "s") for r in m["repaired"])
        calls = "".join({"separate": "-", "same system": "s", "grand staff": "G"}[c] for c in m["calls"])
        info = (st["staffs"], calls, grouped, rep)
    else:
        info = ("?", "?", "?", "?")
    rows.append((name, info, keys))
print(f"### {tag} {piece} (replay model {mk})\n")
print("| page | staffs | pair calls (- separate, s same system, G grand) | systems after grouping (staffs each) | after repair (g grand, s single) | page XML parts: key bars/notes |")
print("|---|---|---|---|---|---|")
for name, info, keys in rows:
    print(f"| {name[5:]} | {info[0]} | {info[1]} | {info[2]} | {info[3]} | " + "; ".join(f"{k} {n}/{c}" for k, n, c in keys) + " |")
print("\nsum of bars per merger key (old rule):", {k: v[0] for k, v in totals.items()})
for label, f in (("after merge_pages", f"{D}/joined.musicxml"), ("final (after drop_minor_parts)", f"{R}/out/testset/{piece}/{piece}-{tag}.musicxml")):
    if os.path.exists(f):
        s = converter.parse(f, forceSource=True)
        print(f"{label}:", [(p.id, len(p.getElementsByClass('Measure')), len(p.flatten().notes)) for p in s.parts])
