"""Tables for pitch_audit.md from pitch_audit.json (run pitch_audit.py first)."""
import json
from collections import Counter
from pitch_audit import CATS, PIECES
d = json.load(open("/Users/yiduoke/Documents/homr/run/eval_run1/pitch_audit.json"))
print("| piece | pitch F1 | errors | " + " | ".join(c for c in CATS) + " |")
print("|" + "---|" * (len(CATS) + 3))
tot = Counter()
for n in PIECES:
    c = Counter(r["cat"] for r in d[n]["recs"]); tot += c
    print(f"| {n} | {d[n]['pitch_f1']} | {len(d[n]['recs'])} | " + " | ".join(str(c[k]) for k in CATS) + " |")
T = sum(tot.values())
print(f"| **all** | | {T} | " + " | ".join(f"{tot[k]} ({100*tot[k]/T:.0f}%)" for k in CATS) + " |")
print()
print("shares per focus piece (% of that piece's errors)")
for n in PIECES[:5]:
    c = Counter(r["cat"] for r in d[n]["recs"]); T = sum(c.values())
    print(n, ", ".join(f"{k.split()[0]}:{100*c[k]/T:.0f}%" for k in CATS if c[k]))
print()
print("octave errors: ref bracket / pred bracket / direction (pred-ref octave)")
for n in PIECES:
    r = [x for x in d[n]["recs"] if x["cat"] == "2 octave"]
    if not r: continue
    c = Counter(("ref8va" if x["ref"][0][3] else "no-ref-bracket", "pred-bracket" if x["pred"][0][3] else "no-pred-bracket") for x in r)
    sgn = Counter("pred lower" if int(x["label"]) < 0 else "pred higher" for x in r)
    print(n, len(r), dict(c), dict(sgn))
