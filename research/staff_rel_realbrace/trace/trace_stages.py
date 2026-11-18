"""Stage 1-3 replay of the Schott pages: staff detection -> pair decisions -> group_staffs -> repair_systems.
usage: PYTHONPATH=run/rel_wt HOMR_FIXED_MARGIN=1 python trace_stages.py PIECE OUT.json
Runs the segmentation once per page (laptop, same code as the evaluation worktree rel_wt), then the pair
decisions of the four models and the grouping and the layout repair for each. No transformer."""
import glob, json, os, sys
import numpy as np
from homr.main import ProcessingConfig, detect_single_staffs
from homr import staff_relations as sr
from homr.system_repair import repair_systems
import homr.simple_logging as sl

R = "/Users/yiduoke/Documents/homr/run"
MODELS = {
    "shipped": sr.model_path if not os.environ.get("HOMR_STAFF_RELATION_MODEL") else None,
    "rb1": f"{R}/staff_rel_realbrace/staff_relations_realbrace-1.onnx",
    "rb2": f"{R}/staff_rel_realbrace/staff_relations_realbrace-2.onnx",
    "rb3": f"{R}/staff_rel_realbrace/staff_relations_realbrace-3.onnx",
}
piece, out = sys.argv[1], sys.argv[2]
cfg = ProcessingConfig(False, False, False, False, -1, False, True, False, False)
pages = sorted(glob.glob(f"{R}/eval_run1/pages/{piece}/page-*.png"))
res = {}
for path in pages:
    name = os.path.basename(path)[:-4]
    single = detect_single_staffs(path, cfg)
    staffs = single.staffs
    entry = {"staffs": len(staffs), "models": {}}
    for mk, mp in MODELS.items():
        model = sr.get_model(mp) if mp else sr.get_model()
        st = sr.join_pieces_with_model(single.predictions, staffs)
        pairs, crops = sr.page_inputs(single.predictions, st)
        probs = model.predict(crops)
        multi = sr.group_staffs(st, pairs, probs)
        grouped = [[len(m.staffs), [bool(s.is_grandstaff) for s in m.staffs], bool(m.certain)] for m in multi]
        calls = [sr.CLASSES[int(p.argmax())] for p in probs]
        repaired = repair_systems(single.debug, multi)
        rep = [[len(m.staffs), [bool(s.is_grandstaff) for s in m.staffs]] for m in repaired]
        entry["models"][mk] = {"pairs": [list(map(int, p)) for p in pairs], "probs": np.round(probs, 3).tolist(),
                               "calls": calls, "grouped": grouped, "repaired": rep}
    res[name] = entry
    print(name, entry["staffs"], {k: ([g[0] for g in v["grouped"]], [r[0] for r in v["repaired"]]) for k, v in entry["models"].items()}, flush=True)
    json.dump(res, open(out, "w"))
