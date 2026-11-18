"""For each aligned bar (pooled alignment) of piece: pitch matches of the prediction against the reference, and the matches if the prediction's
staff-1 notes are moved by +-12 / +-24 (the best one). A positive gain with shift -12 means the prediction is an octave higher than the reference in the upper staff
(Schubert pattern: the reference lacks the printed 8va); +12 means the prediction is an octave lower (missed bracket in the output, or an 8vb the reference lacks).
usage: bar_octave_diff.py piece [tag] [min_gain]"""
import sys
from refs_lib import *

def flagged(piece, tag="layout1", gain=3, ref_file=None):
    ref = parse(ref_file or ref_path(piece)); pred = parse(pred_path(piece, tag))
    rows = []
    for i, j in bar_pairs(ref, pred):
        rn, pn = ref.measures[i].notes, pred.measures[j].notes
        m0 = match_pooled(rn, pn)[0]
        a = Counter(round(n.pitch) for n in rn)
        best = (m0, 0)
        for s in (-12, 12, -24, 24):
            b = Counter(round(n.pitch) + (s if n.staff == 1 else 0) for n in pn)
            m = sum((a & b).values())
            if m > best[0]:
                best = (m, s)
        if best[0] - m0 >= gain:
            rows.append((i + 1, ref.measures[i].number, j + 1, m0, best[0], best[1], len(rn), len(pn)))
    return rows

if __name__ == "__main__":
    piece = sys.argv[1]; tag = sys.argv[2] if len(sys.argv) > 2 else "layout1"; gain = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    rows = flagged(piece, tag, gain)
    for r in rows:
        print("ref bar %d (no. %s) pred bar %d: matches %d -> %d with upper staff %+d; ref notes %d pred notes %d" % r)
    print(len(rows), "bars flagged")
