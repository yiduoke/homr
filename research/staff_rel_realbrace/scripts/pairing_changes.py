"""pairing_changes.py (D30, task e): pairing decisions (the 'Staffs i and j (from the top): ...' lines of homr.log) of a new relation model against the shipped
model on the saved crops of every page of the test-set scans (extract_eval/<piece>__<page>.npz, made by extract_pairs.py from eval_run1/pages; the shipped model
reproduces the class counts of the released-model homr.log). Lists every page whose decision changes. Only the relation model is run (no transcription).
usage (from run/staff_rel_realbrace): python pairing_changes.py NAME=MODEL.onnx [NAME=MODEL.onnx ...] > out.md"""
import glob, os, sys, collections, json
import numpy as np
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/rel_wt")
from homr import staff_relations as sr
N = ["separate", "same system", "grand staff"]
shipped = sr.StaffRelationModel()
models = {a.split("=", 1)[0]: sr.StaffRelationModel(a.split("=", 1)[1]) for a in sys.argv[1:]}
SCHOTT = {"liszt-te-5", "liszt-te-10", "liszt-sonata"}
rows = {m: [] for m in models}; per_piece = {m: collections.defaultdict(lambda: [0, 0, 0]) for m in models}; stats = {m: collections.Counter() for m in models}
for f in sorted(glob.glob("extract_eval/*.npz")):
    piece, page = os.path.basename(f)[:-4].split("__")
    z = np.load(f)
    if "crops" not in z or len(z["crops"]) == 0:
        continue
    x = z["crops"].astype(np.float32) / 255
    old = shipped.predict(x).argmax(1)
    order = np.argsort(z["top"]); rank = {int(s): r for r, s in enumerate(order)}
    for m, mod in models.items():
        new = mod.predict(x).argmax(1)
        per_piece[m][piece][0] += len(x)
        for k in np.nonzero(old != new)[0]:
            i, j = (int(v) for v in z["pairs"][k])
            rows[m].append((piece, page, rank[i], rank[j], N[old[k]], N[new[k]], piece in SCHOTT))
            per_piece[m][piece][1] += 1
        per_piece[m][piece][2] += int((old != new).any())
for m in models:
    other = [r for r in rows[m] if not r[6]]
    print(f"### {m}: pairs changed on the 26 non-Schott scan sets (relation model only, argmax)\n")
    tot = sum(v[0] for p, v in per_piece[m].items() if p not in SCHOTT)
    print(f"{len(other)} changed pairs of {tot} on {len({(r[0], r[1]) for r in other})} pages; Schott test scans (same edition, expected to change): {sum(v[1] for p, v in per_piece[m].items() if p in SCHOTT)} pairs\n")
    print("| piece | page | staffs i and j (from the top, 0-based as in homr.log) | shipped | new |\n|---|---|---|---|---|")
    for r in other:
        print(f"| {r[0]} | {r[1]} | {r[2]} and {r[3]} | {r[4]} | {r[5]} |")
    print()
