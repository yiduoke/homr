"""Write mine/scarce_stems.txt: the train-pool scores that supply the real bars of meters with fewer than 12 scores."""
import collections, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_windows as bw
runs, _ = bw.load_pools("train")
by = collections.defaultdict(set)
for m, lst in runs.items():
    for r in lst:
        if r["len"] >= 2:
            by[m].add(r["stem"])
scarce = set()
for m, st in by.items():
    if len(st) < 12:
        scarce |= st
        print(m, len(st))
open(f"{bw.ROOT}/mine/scarce_stems.txt", "w").write("\n".join(sorted(scarce)) + "\n")
print("scarce stems", len(scarce))
