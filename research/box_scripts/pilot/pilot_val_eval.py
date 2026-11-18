"""Free-generation read of the held-out pilot crops (validation group C: three pieces never trained on) with one model; staff-level metrics.

usage:  [HOMR_INPUT_SCALE=1.5] HOMR_MODEL_NAME=<model> PYTHONPATH=<res_wt or integration_wt> HOMR_FORCE_CPU=1 \
        python pilot_val_eval.py LIST.txt OUT.json [--limit N]
LIST.txt: lines "image,tokens" (lists/val_scan.txt or lists/val_twin_render.txt, paths as in the list; run from run/ or pass --root).
Per crop: pitch-multiset F1 (read vs label), (pitch, rhythm) multiset F1, bar count agreement, whether the read is token-for-token identical
(pitch/rhythm/lift columns). Summary: mean/median per piece and overall, plus the paired difference when two result files are compared
(see PILOT_SPEC.md, `--compare A.json B.json`). Crops are cut like the training crops (no page layout is involved), so this isolates the transformer.
"""
import argparse, collections, json, os, sys


def label_notes(path):
    notes, bars = [], 0
    for line in open(path).read().split("\n"):
        for el in line.split("&"):
            f = el.split()
            if not f:
                continue
            if f[0] == "barline" or f[0].startswith("repeat") or f[0] == "doublebarline":
                bars += 1
            elif f[0].startswith("note_"):
                notes.append((f[1], f[0]))
    return notes, bars


def f1(a, b):
    ca, cb = collections.Counter(a), collections.Counter(b)
    tp = sum((ca & cb).values())
    if not a and not b:
        return 1.0
    p, r = tp / max(1, sum(cb.values())), tp / max(1, sum(ca.values()))
    return 2 * p * r / (p + r) if p + r else 0.0


def compare(fa, fb):
    a, b = json.load(open(fa)), json.load(open(fb))
    common = sorted(set(a["crops"]) & set(b["crops"]))
    d = [b["crops"][k]["pitch_f1"] - a["crops"][k]["pitch_f1"] for k in common]
    wins = sum(x > 0.005 for x in d); loss = sum(x < -0.005 for x in d)
    print(f"{len(common)} crops: mean pitch F1 {sum(a['crops'][k]['pitch_f1'] for k in common) / len(common):.4f} -> "
          f"{sum(b['crops'][k]['pitch_f1'] for k in common) / len(common):.4f}; mean diff {sum(d) / len(d):+.4f}; better {wins}, worse {loss}, equal {len(d) - wins - loss}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("list", nargs="?"); ap.add_argument("out", nargs="?")
    ap.add_argument("--limit", type=int, default=0); ap.add_argument("--root", default=".")
    ap.add_argument("--compare", nargs=2)
    args = ap.parse_args()
    if args.compare:
        return compare(*args.compare)
    os.environ.setdefault("HOMR_ORT_THREADS", "2"); os.environ.setdefault("HOMR_DECODER_THREADS", "1")
    import cv2
    from homr.staff_parsing import add_image_into_tr_omr_canvas
    from homr.transformer.configs import Config
    from homr.transformer.staff2score import Staff2Score
    cfg = Config(); cfg.use_gpu_inference = os.environ.get("HOMR_FORCE_CPU") != "1"
    model = Staff2Score(cfg, decoder_threads=1)
    rows = [l.strip().split(",") for l in open(args.list) if l.strip()]
    if args.limit:
        rows = rows[:args.limit]
    res = {}
    for img, tok in rows:
        name = os.path.basename(img)[:-4]
        im = cv2.imread(os.path.join(args.root, img), 0)
        try:
            syms = model.predict(add_image_into_tr_omr_canvas(im))
        except Exception as e:  # noqa: BLE001
            res[name] = dict(error=repr(e)[:200], pitch_f1=0.0, pitch_rhythm_f1=0.0, bars_ok=False, exact=False); continue
        read, rbars = [], 0
        for s in syms:
            if "barline" in s.rhythm or s.rhythm.startswith("repeat"):
                rbars += 1
            elif s.rhythm.startswith("note") and s.pitch not in ("_", "."):
                read.append((s.pitch, s.rhythm))
        lab, lbars = label_notes(os.path.join(args.root, tok))
        res[name] = dict(pitch_f1=f1([p for p, _ in lab], [p for p, _ in read]), pitch_rhythm_f1=f1(lab, read), bars_ok=rbars == lbars,
                         exact=sorted(lab) == sorted(read), n_label=len(lab), n_read=len(read))
    by_piece = collections.defaultdict(list)
    for k, v in res.items():
        by_piece[k.split("_")[0]].append(v["pitch_f1"])
    mean = lambda x: sum(x) / len(x) if x else float("nan")
    summary = dict(n=len(res), pitch_f1=mean([v["pitch_f1"] for v in res.values()]), pitch_rhythm_f1=mean([v["pitch_rhythm_f1"] for v in res.values()]),
                   bars_ok=mean([float(v["bars_ok"]) for v in res.values()]), exact=mean([float(v["exact"]) for v in res.values()]),
                   by_piece={p: mean(v) for p, v in sorted(by_piece.items())}, model=os.environ.get("HOMR_MODEL_NAME", "released"),
                   scale=os.environ.get("HOMR_INPUT_SCALE", "1"))
    json.dump(dict(summary=summary, crops=res), open(args.out, "w"), indent=1)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
