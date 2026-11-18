"""D28: where do the pair decisions (the 'Staffs i and j' lines) and the layout after repair_systems of realbrace-2/-3 differ from the shipped model?
usage: python pair_diff.py replay_all.json [OUT.md]   (replay_all.json = merged output of pair_replay.py shards)
Code per pair, from the top: G grand staff, S same system, - separate. Layout = systems after the repair, G = grand staff (two staves joined), s = single staff, + = staves of one system."""
import json
import sys
from collections import Counter, defaultdict

d = json.load(open(sys.argv[1]))
out_path = sys.argv[2] if len(sys.argv) > 2 else None
CODE = {"grand staff": "G", "same system": "S", "separate": "-"}


def calls(m):
    return "".join(CODE[c] for c in m["calls"])


def layout(m):
    return " ".join("+".join("G" if g else "s" for g in flags) for n, flags in m["repaired"])


rows = []
stat = defaultdict(Counter)
for piece in sorted(d):
    for page in sorted(d[piece]):
        e = d[piece][page]
        if "error" in e:
            continue
        m = e["models"]
        stat[piece]["pages"] += 1
        stat[piece]["pairs"] += len(m["shipped"]["calls"])
        for k in ("rb2", "rb3"):
            cd = [i for i, (a, b) in enumerate(zip(m["shipped"]["calls"], m[k]["calls"])) if a != b]
            ld = layout(m["shipped"]) != layout(m[k])
            if cd:
                stat[piece][k + "_pairs"] += len(cd)
                stat[piece][k + "_pages_calls"] += 1
            if ld:
                stat[piece][k + "_pages_layout"] += 1
        if any(m["shipped"]["calls"][i] != m[k]["calls"][i] for k in ("rb2", "rb3") for i in range(len(m["shipped"]["calls"]))) or any(
                layout(m["shipped"]) != layout(m[k]) for k in ("rb2", "rb3")):
            rows.append((piece, page, e["staffs"], calls(m["shipped"]), calls(m["rb2"]), calls(m["rb3"]), layout(m["shipped"]), layout(m["rb2"]), layout(m["rb3"])))
lines = ["| piece | page | staves | shipped | rb2 | rb3 | layout shipped | layout rb2 | layout rb3 |", "|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    lines.append("| " + " | ".join(map(str, r)) + " |")
lines += ["", "| piece | pages | pairs | rb2: pairs changed | pages with changed calls | pages with changed layout | rb3: pairs changed | pages calls | pages layout |", "|---|---|---|---|---|---|---|---|---|"]
tot = Counter()
for p, c in sorted(stat.items()):
    tot.update(c)
    lines.append(f"| {p} | {c['pages']} | {c['pairs']} | {c['rb2_pairs']} | {c['rb2_pages_calls']} | {c['rb2_pages_layout']} | {c['rb3_pairs']} | {c['rb3_pages_calls']} | {c['rb3_pages_layout']} |")
lines.append(f"| **all** | {tot['pages']} | {tot['pairs']} | {tot['rb2_pairs']} | {tot['rb2_pages_calls']} | {tot['rb2_pages_layout']} | {tot['rb3_pairs']} | {tot['rb3_pages_calls']} | {tot['rb3_pages_layout']} |")
txt = "\n".join(lines)
print(txt)
if out_path:
    open(out_path, "w").write(txt + "\n")
