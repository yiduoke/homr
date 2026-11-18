"""notes_dump.py piece bar_from bar_to [tag] [ref_file]: reference notes (staff, onset, pitch name) and prediction notes of aligned bars."""
import sys
from refs_lib import *
N = "C C# D D# E F F# G G# A A# B".split()
def nm(p): p = round(p); return f"{N[p % 12]}{p // 12 - 1}"
piece, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); tag = sys.argv[4] if len(sys.argv) > 4 else "layout1"
ref = parse(sys.argv[5] if len(sys.argv) > 5 else ref_path(piece)); pred = parse(pred_path(piece, tag))
pairs = dict(bar_pairs(ref, pred))
for i in range(a - 1, b):
    j = pairs.get(i)
    print(f"--- ref bar idx {i+1} (no. {ref.measures[i].number}) pred idx {None if j is None else j+1}")
    for lab, notes in (("REF ", ref.measures[i].notes), ("PRED", pred.measures[j].notes if j is not None else ())):
        for s in sorted({n.staff for n in notes}):
            ns = sorted((n for n in notes if n.staff == s), key=lambda n: (round(n.onset, 3), n.pitch))
            print(f"{lab} staff {s}: " + " ".join(f"{n.onset:.2f}:{nm(n.pitch)}" for n in ns))
