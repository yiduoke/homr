"""Free-generation read of crops by the released model (integration_wt ONNX weights, CPU).
usage: HOMR_FIXED_MARGIN=1 PYTHONPATH=integration_wt python model_read.py <in.jsonl {"id","image"}> <out.jsonl>
Writes per crop: tokens text of the read, notes [[bar_index, pitch],...], n_bars (barline/repeat tokens)."""
import os, sys, json, time
os.environ.setdefault("HOMR_ORT_THREADS", "2"); os.environ.setdefault("HOMR_DECODER_THREADS", "1")
import cv2
from homr.staff_parsing import add_image_into_tr_omr_canvas
from homr.transformer.configs import Config
from homr.transformer.staff2score import Staff2Score
from training.transformer.training_vocabulary import token_lines_to_str

def main():
    cfg = Config(); cfg.use_gpu_inference = False
    model = Staff2Score(cfg, decoder_threads=1)
    done = set()
    if os.path.exists(sys.argv[2]):
        done = {json.loads(l)["id"] for l in open(sys.argv[2])}
    out = open(sys.argv[2], "a")
    for line in open(sys.argv[1]):
        r = json.loads(line)
        if r["id"] in done: continue
        im = cv2.imread(r["image"], 0)
        t = time.time()
        try:
            syms = model.predict(add_image_into_tr_omr_canvas(im))
        except Exception as e:  # noqa: BLE001
            out.write(json.dumps(dict(id=r["id"], error=repr(e)[:200])) + "\n"); out.flush(); continue
        notes, bar = [], 0
        for s in syms:
            if "barline" in s.rhythm or s.rhythm.startswith("repeat"):
                bar += 1
            elif s.rhythm.startswith("note") and s.pitch not in ("_", "."):
                notes.append([bar, s.pitch])
        try:
            txt = token_lines_to_str(syms)
        except Exception:  # noqa: BLE001
            txt = ""
        out.write(json.dumps(dict(id=r["id"], notes=notes, n_bars=bar, tokens=txt, secs=round(time.time() - t, 1))) + "\n"); out.flush()

if __name__ == "__main__":
    main()
