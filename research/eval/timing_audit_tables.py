"""Print the Part A tables used in timing_audit.md (reads timing_audit_a.json)."""
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
d = json.load(open(HERE / "timing_audit_a.json"))
C = ["1 tuplet", "2 voice confusion", "3 rest shift", "4 grace/cue", "5 bar length/meter",
     "6 duration only", "7 alignment artefact", "8 other"]
print("| piece | F1 pitch / +onset / +duration | ref notes | pitch-matched, not fully matched | "
      + " | ".join(c.split(" ", 1)[0] for c in C) + " | ref notes in unmatched bars |")
print("|" + "---|" * (len(C) + 5))
tot, T, U, R = Counter(), 0, 0, 0
for n, a in d.items():
    c = Counter(r["cat"] for r in a["recs"])
    tot += c
    T += a["targets"]
    U += a["ref_notes_in_unmatched_bars"]
    R += a["ref_notes"]
    print(f"| {n} | {' / '.join(str(x) for x in a['f1'])} | {a['ref_notes']} | {a['targets']} | "
          + " | ".join(str(c[x]) for x in C) + f" | {a['ref_notes_in_unmatched_bars']} |")
print(f"| **all** | | {R} | {T} | " + " | ".join(f"{tot[x]} ({100 * tot[x] / T:.0f}%)" for x in C) + f" | {U} |")

# sub-causes
sub = Counter()
for a in d.values():
    for r in a["recs"]:
        de = r["detail"]
        if r["cat"] == "1 tuplet":
            if de.startswith("ref "):
                sub["1a ref tuplet, prediction plain notes"
                    if de.endswith("plain") else "1b ref tuplet, prediction has tuplet of other ratio/position"] += 1
            elif "spurious" in de:
                sub["1c spurious tuplet in prediction (plain ref)"] += 1
            elif "cascade" in de:
                sub["1d later notes of the voice shifted by a tuplet error"] += 1
            else:
                sub["1e bar overlong because tuplets written plain (ref note itself plain)"] += 1
        if r["cat"] == "5 bar length/meter":
            sub["5a cadenza-like bar (ref or pred bar much longer than the time signature)" if "cadenza" in de else
                "5b time signature differs from reference" if "time sig" in de else "5c other over/under length"] += 1
print()
for k, v in sorted(sub.items()):
    print(f"| {k} | {v} |")
