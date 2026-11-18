"""D32: tables for OCTAVE_CAUSES.md from octave_causes_notes.json (octave_causes_crops.py) and eye_verdicts.csv (by-eye check).
Prints markdown tables to stdout and writes octave_causes_tables.json."""
import csv
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/octave_checks")
import octave_causes_crops as O  # noqa: E402

D = O.OUT
res = json.load(open(D + "octave_causes_notes.json"))
by = {r["name"]: r for r in res}
verd = {r["name"]: r for r in csv.DictReader(open(D + "eye_verdicts.csv"))}
CL = ["a", "b", "c", "d", "e", "x"]
CLN = {"a": "(a) start", "b": "(b) stop", "c": "(c) continuation", "d": "(d) wrong register", "e": "(e) edition/reference", "x": "mixed (register + bracket)"}
GROUPS = ["pilot-train", "pilot-train(rendered)", "pilot-val", "b2-train", "b2-train(Demets)", "b2-val"]
VAL = {"pilot-val", "b2-val"}

usable = [r for r in res if r["usable"] == "yes"]
analysed = [r for r in usable if r["pc_f1"] >= 0.8]
flag = [r for r in analysed if r["flagged"]]
out = {}


def pct(a, b):
    return f"{100 * a / b:.0f} %" if b else "-"


print("### T1 population\n")
print("| group | manifest crops | with label tokens + read, label reliable | analysed (letter F1 >= 0.8) | flagged (octave or bracket difference) | share | notes with an octave/bracket difference |")
print("|---|---|---|---|---|---|---|")
tot = Counter()
for g in GROUPS + ["all"]:
    sel = [r for r in res if g == "all" or r["group"] == g]
    us = [r for r in sel if r["usable"] == "yes"]
    an = [r for r in us if r["pc_f1"] >= 0.8]
    fl = [r for r in an if r["flagged"]]
    nn = sum(r["n_events"] for r in fl)
    print(f"| {g} | {len(sel)} | {len(us)} | {len(an)} | {len(fl)} | {pct(len(fl), len(an))} | {nn} |")
    out.setdefault("T1", {})[g] = [len(sel), len(us), len(an), len(fl), nn]

print("\nexcluded: ", Counter(r["usable"][:70] for r in res if r["usable"] != "yes").most_common())
print("low letter F1 (< 0.8, read differs by more than octaves, not analysed):", sum(1 for r in usable if r["pc_f1"] < 0.8), Counter(r["tier"] for r in usable if r["pc_f1"] < 0.8))

# strict: pitch classes agree, octaves differ
strict = [r for r in analysed if r["pc_f1"] == 1.0 and r["n_label_notes"] == r["n_read_notes"] and r["n_written_diff_notes"] > 0]
print("\ncrops where all pitch letters agree and written octaves differ for at least one note:", len(strict), "notes:", sum(r["n_written_diff_notes"] for r in strict))
brk = [r for r in analysed if (r["label_starts"] != r["read_starts"] or r["label_stops"] != r["read_stops"])]
print("crops where the number of start/stop tokens differs:", len(brk))

print("\n### T2 causes (automatic class; crop = primary class = class with most affected notes; notes = all affected notes of that class)\n")
print("| cause | crops (train/pilot+b2) | crops (validation) | crops total | notes, all | notes, sounding pitch differs | share of flagged crops |")
print("|---|---|---|---|---|---|---|")
T2 = {}
for c in CL:
    cr = [r for r in flag if r["auto_primary"] == c]
    tr = sum(1 for r in cr if r["group"] not in VAL)
    va = sum(1 for r in cr if r["group"] in VAL)
    nall = sum(r["n_events_by_cls"].get(c, 0) for r in flag)
    nsd = sum(1 for r in flag for e in r["events"] if e["cls"] == c and e["sd"] != 0)
    T2[c] = [tr, va, len(cr), nall, nsd]
    print(f"| {CLN[c]} | {tr} | {va} | {len(cr)} | {nall} | {nsd} | {pct(len(cr), len(flag))} |")
print(f"| total | {sum(v[0] for v in T2.values())} | {sum(v[1] for v in T2.values())} | {len(flag)} | {sum(v[3] for v in T2.values())} | {sum(v[4] for v in T2.values())} | |")
out["T2"] = T2
anyc = Counter()
for r in flag:
    for ch in r["auto_classes_present"]:
        anyc[ch] += 1
print("\ncrops containing at least one event of the class:", dict(anyc))

print("\n### T3 sub-classes (events = affected notes; crops = crops with at least one)\n")
sub = defaultdict(lambda: [0, set(), 0])
for r in flag:
    for e in r["events"]:
        k = (e["cls"], e["sub"])
        sub[k][0] += 1
        sub[k][1].add(r["name"])
        sub[k][2] += e["sd"] != 0
    for t in r["tok_diffs"]:
        k = (t[0], "token only: " + t[2:])
        sub[k][0] += 0
        sub[k][1].add(r["name"])
print("| class | sub-class | crops | notes | notes with sounding difference |")
print("|---|---|---|---|---|")
for k in sorted(sub):
    print(f"| {k[0]} | {k[1]} | {len(sub[k][1])} | {sub[k][0]} | {sub[k][2]} |")
out["T3"] = {f"{k[0]}|{k[1]}": [len(v[1]), v[0], v[2]] for k, v in sub.items()}

print("\n### T4 by-eye check of the automatic class\n")
conf = Counter()
rows = []
for n, v in verd.items():
    r = by[n]
    a = r.get("auto_primary") or "excl"
    conf[(a, v["eye"] if a != "excl" else "n/a")] += 1
ok = [(a, e) for (a, e), c in conf.items() for _ in range(c) if e != "n/a"]
agree = sum(1 for a, e in ok if a == e)
print(f"sample {sum(conf.values())} crops (stratified random, seed 20261132; {sum(c for (a, e), c in conf.items() if e == 'n/a')} not assessable), agreement {agree}/{len(ok)} = {100 * agree / len(ok):.0f} %\n")
eyes = ["a", "b", "c", "d", "e"]
print("| auto \\ eye | " + " | ".join(eyes) + " | n/a | n |")
print("|---|" + "---|" * (len(eyes) + 2))
for a in CL:
    n = sum(c for (x, e), c in conf.items() if x == a)
    if not n:
        continue
    print(f"| {a} | " + " | ".join(str(conf.get((a, e), 0)) for e in eyes) + f" | {conf.get((a, 'n/a'), 0)} | {n} |")
out["T4"] = {f"{a}|{e}": c for (a, e), c in conf.items()}
out["T4_agree"] = [agree, len(ok)]

# calibrated estimate: redistribute auto class counts by the eye confusion rates (crops)
print("\ncalibrated crop counts (auto primary counts redistributed with the eye confusion of the sample; rough, small sample):")
est = Counter()
for a in CL:
    n_auto = len([r for r in flag if r["auto_primary"] == a])
    row = {e: conf.get((a, e), 0) for e in eyes}
    s = sum(row.values())
    if s == 0:
        continue
    for e, c in row.items():
        est[e] += n_auto * c / s
print({k: round(v) for k, v in est.items()})
out["calibrated"] = {k: round(v) for k, v in est.items()}

# earlier by-eye reviews as a second reference
print("\n### T5 earlier by-eye reviews (octave_review.md; 110 crops) against the automatic class\n")
rev = {}
for r in csv.DictReader(open(O.R + "octave_review.csv")):
    rev[os.path.basename(r["crop"])[:-4]] = (r["decision"], r["direction"])
for r in csv.DictReader(open(O.R + "batch2/octave_review.csv")):
    rev[r["crop"]] = ({"admit": "1 label right", "corrected": "edition/printed bracket", "quarantine": "quarantine"}[r["decision"]], r["direction"])
t5 = Counter()
for n, (d, di) in rev.items():
    r = by.get(n)
    if not r or r["usable"] != "yes" or not r.get("flagged"):
        t5[(d, "not analysed" if not r or r["usable"] != "yes" else "not flagged")] += 1
        continue
    d2 = "edition/reference" if ("edition" in d or "corrected" in d) else ("label right" if d.startswith("1") else d)
    t5[(d2, r["auto_primary"])] += 1
print("| earlier eye decision | auto class | crops |")
print("|---|---|---|")
for (d, a), c in sorted(t5.items()):
    print(f"| {d} | {a} | {c} |")
out["T5"] = {f"{d}|{a}": c for (d, a), c in t5.items()}

json.dump(out, open(D + "octave_causes_tables.json", "w"), indent=1)
