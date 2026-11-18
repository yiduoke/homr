"""D28: the staff-pairing decisions of the shipped model and the realbrace models on every page of the 28 real scans, from one
segmentation and staff detection per page (no transformer). Same stages as staff_rel_realbrace/trace/trace_stages.py (staff
detection -> join_pieces_with_model -> page_inputs -> model -> group_staffs -> repair_systems), on the box GPU segmentation.
usage: PYTHONPATH=run/rel_wt HOMR_FIXED_MARGIN=1 python pair_replay.py OUT.json SHARD NSHARDS [PIECE ...]
Output: {piece: {page: {staffs, models: {name: {pairs, probs, calls, grouped, repaired}}}}}; resumes from OUT.json."""
import glob
import json
import os
import sys

import numpy as np

from homr import staff_relations as sr
from homr.main import ProcessingConfig, detect_single_staffs
from homr.system_repair import repair_systems

R = "/Users/yiduoke/Documents/homr/run"
sys.path.insert(0, f"{R}/eval_run1")
import res_lib as L  # noqa: E402

MODELS = {
    "shipped": None,
    "rb2": f"{R}/staff_rel_realbrace/staff_relations_realbrace-2.onnx",
    "rb3": f"{R}/staff_rel_realbrace/staff_relations_realbrace-3.onnx",
}
out, shard, nshard = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
pieces = sys.argv[4:] or L.pieces28()
cfg = ProcessingConfig(False, False, False, False, -1, False, True, False, False)
res = json.load(open(out)) if os.path.exists(out) else {}
jobs = [(p, pg) for p in pieces for pg in sorted(glob.glob(f"{L.E}/pages/{p}/page-*.png")) if os.path.basename(pg)[:-4].replace("page-", "").isdigit()]
for k, (piece, path) in enumerate(jobs):
    if k % nshard != shard:
        continue
    name = os.path.basename(path)[:-4]
    if name in res.get(piece, {}):
        continue
    try:
        single = detect_single_staffs(path, cfg)
    except Exception as e:  # a page without staffs
        res.setdefault(piece, {})[name] = {"error": str(e)[:200]}
        continue
    staffs = single.staffs
    entry = {"staffs": len(staffs), "shape": list(single.predictions.preprocessed.shape[:2]),
             "boxes": [[round(float(s.min_x)), round(float(s.min_y)), round(float(s.max_x)), round(float(s.max_y))] for s in staffs], "models": {}}
    for mk, mp in MODELS.items():
        model = sr.get_model(mp) if mp else sr.get_model(sr.model_path)
        st = sr.join_pieces_with_model(single.predictions, staffs)
        pairs, crops = sr.page_inputs(single.predictions, st)
        probs = model.predict(crops)
        multi = sr.group_staffs(st, pairs, probs)
        grouped = [[len(m.staffs), [bool(s.is_grandstaff) for s in m.staffs]] for m in multi]
        calls = [sr.CLASSES[int(p.argmax())] for p in probs]
        repaired = repair_systems(single.debug, multi)
        rep = [[len(m.staffs), [bool(s.is_grandstaff) for s in m.staffs]] for m in repaired]
        entry["models"][mk] = {"pairs": [list(map(int, p)) for p in pairs], "probs": np.round(probs, 3).tolist(), "calls": calls,
                               "grouped": grouped, "repaired": rep}
    res.setdefault(piece, {})[name] = entry
    print(piece, name, entry["staffs"], {k2: [r[0] for r in v["repaired"]] for k2, v in entry["models"].items()}, flush=True)
    json.dump(res, open(out, "w"))
json.dump(res, open(out, "w"))
