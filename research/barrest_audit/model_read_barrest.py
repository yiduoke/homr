#!/usr/bin/env python3
"""
What does the released model read where the pilot label has the typeless bar rest (rest_8)?
Uses the stored free-generation reads of the pilot (scan_pairs_virtuoso/work/reads/*.jsonl, released
weights meteracc-r2s7) and the label bars the detector flags in the frozen token files.
usage: python3 model_read_barrest.py   (laptop, run/ as cwd)
"""
import collections
import json
import os
import sys

sys.path.insert(0, "scan_pairs_virtuoso/scripts")
sys.path.insert(0, "barrest_audit")
import detect_barrest as D  # noqa: E402
from pieces import BY  # noqa: E402

ROOT = "scan_pairs_virtuoso"
pos = {}
for lst in ("train_strong_typeless_rest_fixed.txt", "val_strong_typeless_rest_fixed.txt"):
    for l in open(f"{ROOT}/lists/{lst}"):
        name = l.strip().split(",")[1].split("/")[-1][: -len(".tokens")]
        pos[name] = 1
tok = collections.Counter()
stats = collections.Counter()
examples = []
for pid, cfg in BY.items():
    ex = f"{ROOT}/work/export/{pid}.json"
    rf = f"{ROOT}/work/reads/{cfg['pdf']}.jsonl"
    if not (os.path.exists(ex) and os.path.exists(rf)):
        continue
    reads = {json.loads(l)["id"]: json.loads(l) for l in open(rf)}
    for r in json.load(open(ex))["records"]:
        name = r.get("name")
        if name not in pos:
            continue
        stats["crops"] += 1
        rd = reads.get(r["id"])
        if rd is None:
            stats["no_read"] += 1
            continue
        label = D.analyse(open(f"{ROOT}/tokens/{name}.tokens").read())
        lm = D.parse_staff(open(f"{ROOT}/tokens/{name}.tokens").read())
        rm = D.parse_staff(rd["tokens"])
        if len(lm) != len(rm):
            stats["bar_count_differs"] += 1
            continue
        stats["compared_crops"] += 1
        for bar, nbars, kind, tracks, barlen, basis in label["details"]:
            if kind != "bug_rest8":
                continue
            for part in tracks.split("|"):
                tag, _, toks = part.partition("=")
                if toks != "rest_8" or tag not in D.PRIMARY:
                    continue
                stats["label_bars"] += 1
                rt_ = rm[bar]["tracks"].get(tag)
                if not rt_:
                    tok["(track absent in the read)"] += 1
                    continue
                s = "+".join(x[2] for x in rt_)
                if not all(x[0] for x in rt_):
                    tok["(notes in the read)"] += 1
                elif len(rt_) == 1:
                    tok[s] += 1
                else:
                    tok["(several rests)"] += 1
                if len(examples) < 5 and len(rt_) == 1 and rt_[0][0]:
                    examples.append(f"{name} bar {bar} {tag}: label rest_8, read {s}")
print(dict(stats))
for k, v in tok.most_common():
    print(f"  {k}: {v}")
print(examples)
