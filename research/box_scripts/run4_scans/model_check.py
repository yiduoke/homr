"""Independent check of image <-> label pairs with the released model (CPU ONNX, no GPU).
usage: PYTHONPATH=/workspace/export_acc_run2s7 python model_check.py <pairs.jsonl> <out.jsonl>
pairs.jsonl lines: {"id":..., "image":..., "tokens":...}. Writes per pair: model note count, label note count,
pitch-multiset F1, bar counts, first/last 3 pitches equal. Used only to catch misaligned pairs (it is NOT a quality
filter: only gross disagreement quarantines), so the decision thresholds live in build_pairs.py.
"""
import os, sys, json, time, collections
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import onnxruntime as ort
_orig = ort.InferenceSession


def _patched(path, sess_options=None, providers=None, **kw):
    so = sess_options or ort.SessionOptions()
    so.intra_op_num_threads = 2
    so.inter_op_num_threads = 1
    return _orig(path, sess_options=so, providers=["CPUExecutionProvider"], **kw)


ort.InferenceSession = _patched
ort.get_available_providers = lambda: ["CPUExecutionProvider"]
import cv2
from homr.staff_parsing import add_image_into_tr_omr_canvas
from homr.transformer.configs import Config
from homr.transformer.staff2score import Staff2Score


def label_notes(path):
    notes, bars = [], 0
    for line in open(path).read().split("\n"):
        for p in line.split("&"):
            f = p.strip().split(" ")
            if len(f) != 6:
                continue
            if f[0].startswith("note"):
                notes.append(f[1])
            elif "barline" in f[0] or f[0].startswith("repeat"):
                bars += 1
    return notes, bars


def f1(a, b):
    ca, cb = collections.Counter(a), collections.Counter(b)
    tp = sum((ca & cb).values())
    if not a and not b:
        return 1.0
    p = tp / max(1, len(b))
    r = tp / max(1, len(a))
    return 0.0 if tp == 0 else 2 * p * r / (p + r)


def main():
    cfg = Config()
    cfg.use_gpu_inference = False
    model = Staff2Score(cfg)
    done = set()
    if os.path.exists(sys.argv[2]):
        done = {json.loads(l)["id"] for l in open(sys.argv[2])}
    out = open(sys.argv[2], "a")
    for line in open(sys.argv[1]):
        r = json.loads(line)
        if r["id"] in done:
            continue
        im = cv2.imread(r["image"], 0)
        canvas = add_image_into_tr_omr_canvas(im)
        t = time.time()
        syms = model.predict(canvas)
        lab, lb = label_notes(r["tokens"])
        pr = [s.pitch for s in syms if s.rhythm.startswith("note")]
        pb = sum(1 for s in syms if "barline" in s.rhythm or s.rhythm.startswith("repeat"))
        res = dict(id=r["id"], label_notes=len(lab), pred_notes=len(pr), label_bars=lb, pred_bars=pb,
                   pitch_f1=f1(lab, pr), first3=sorted(lab[:3]) == sorted(pr[:3]), last3=sorted(lab[-3:]) == sorted(pr[-3:]),
                   secs=round(time.time() - t, 1))
        out.write(json.dumps(res) + "\n")
        out.flush()


if __name__ == "__main__":
    main()
