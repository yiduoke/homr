#!/usr/bin/env python3
"""Markdown tables of the D27 audit from data/summary.json and the detail TSVs (laptop)."""
import json, collections, sys
d = json.load(open("data/summary.json"))
order = ["pdmx", "pdmx_hard", "asap", "scriabin", "lieder", "grandstaff", "lilypond", "musescore_octave", "kern_scans", "meter_arm"]
names = {"pdmx": "PDMX", "pdmx_hard": "hard PDMX", "asap": "ASAP (4.6.5 re-export)", "scriabin": "Scriabin (4.6.5 re-export)",
         "lieder": "Lieder", "grandstaff": "GrandStaff (kern)", "lilypond": "LilyPond", "musescore_octave": "MuseScore octave sets",
         "kern_scans": "KernScores scan pairs (kern)", "meter_arm": "meter arm"}
for sp in ("train", "val"):
    print(f"\n#### {sp}\n")
    T = collections.Counter()
    print("| source | staves | staves flagged | % | suspicious bars | bars | % of bars | rest_8 alone | all-rest short | rest_8, bar unknown | XML scores scanned | typeless rests in XML |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for s in order:
        v = d[sp]["detector"].get(s)
        if not v:
            continue
        x = d[sp]["xml"].get(s)
        xs = f"{x['scanned']:,}" if x else "n/a (kern)"
        xt = f"{x['typeless']}" if x else "n/a"
        print(f"| {names[s]} | {v['staves']:,} | {v['flagged']} | {100*v['flagged']/v['staves']:.2f} | {v['susp_bars']} | {v['bars']:,} | {100*v['susp_bars']/v['bars']:.2f} | {v['bug_rest8']} | {v['allrest_short']} | {v['unknown_rest8']} | {xs} | {xt} |")
        for k in ("staves", "flagged", "susp_bars", "bars", "bug_rest8", "allrest_short", "unknown_rest8"):
            T[k] += v[k]
    print(f"| **total** | {T['staves']:,} | {T['flagged']} | {100*T['flagged']/T['staves']:.2f} | {T['susp_bars']} | {T['bars']:,} | {100*T['susp_bars']/T['bars']:.2f} | {T['bug_rest8']} | {T['allrest_short']} | {T['unknown_rest8']} | | |")
for fn in ("data/det_train.tsv", "data/det_val.tsv"):
    c = collections.Counter()
    for l in open(fn):
        f = l.rstrip("\n").split("\t")
        if f[0] == "source":
            continue
        pos = "first bar" if f[2] == "0" else ("last bar" if int(f[2]) == int(f[3]) - 1 else "middle")
        c[pos] += 1
    print(fn, dict(c), sum(c.values()))
