"""Pitch-inventory F1 with the staff ignored (bar alignment from note-scores.json) vs the reported one."""
import sys
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/eval_run1")
from collections import Counter
import pitch_audit as PA, timing_audit_a as TA
for n in PA.PIECES:
    res, rb, pb, units, unal, pp = TA.build_units(n)
    pairs = {}
    for s, i, j in units:
        pairs.setdefault((i, j), []).append(s)
    nref = sum(len(rb[s][i].notes) for s in rb for i in range(len(rb[s])))
    npred = sum(len(pb[s][j].notes) for s in pb for j in range(len(pb[s])))
    m1 = m2 = 0
    for (i, j), ss in pairs.items():
        R = [x for s in ss for x in rb[s][i].notes]; P = [x for s in ss for x in pb[s][j].notes]
        m1 += sum((Counter((x.staff, x.pitch) for x in R) & Counter((x.staff, x.pitch) for x in P)).values())
        m2 += sum((Counter(x.pitch for x in R) & Counter(x.pitch for x in P)).values())
    f = lambda m: 100 * 2 * m / (nref + npred)
    print(f"{n}: reported {res['metrics']['pitch_inventory']['combined']['f1']*100:.1f} recomputed {f(m1):.1f} staff-agnostic {f(m2):.1f}")
