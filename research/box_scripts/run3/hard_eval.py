# ruff: noqa: T201
"""Free-generation evaluation of a trained .pth on a list of staffs: pitch precision/recall, missing/extra notes, printed accidentals,
rhythm values, exact meter recognition and invented signatures. usage: hard_eval.py MODEL.pth LIST.txt OUT.json [N] [SEED]"""
import json, random, re, sys
from collections import Counter, defaultdict
import torch
from homr.transformer.configs import Config
from training.architecture.transformer.tromr_arch import TrOMR
from training.transformer.data_loader import DataLoader
from training.transformer.training_vocabulary import read_token_lines

def src(path):
    for k in ("kern_scriabin", "/asap/", "/pdmx/hard/", "/pdmx/", "Lieder-main", "grandstaff", "musescore_octave", "lilypond", "run4"):
        if k in path: return k.strip("/")
    return "other"

def symbols(lines):
    return [s for s in read_token_lines([l for l in lines if l.strip()])]

def notes(syms):
    return [s for s in syms if s.rhythm.startswith("note_") and s.pitch not in ("_", ".")]

def inter(a: Counter, b: Counter) -> int:
    return sum(min(a[k], b[k]) for k in a)

def main():
    pth, lst, out = sys.argv[1:4]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 500
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    entries = [l.strip() for l in open(lst) if l.strip()]
    random.Random(seed).shuffle(entries); entries = entries[:n]
    config = Config()
    model = TrOMR(config); model.load_state_dict(torch.load(pth, map_location="cpu"), strict=True); model.cuda().eval_mode()
    loader = DataLoader(entries, config, is_validation=True)
    agg = defaultdict(Counter)
    for i, e in enumerate(entries):
        tok = e.split(",")[1]
        truth = symbols(open(tok).read().splitlines())
        with torch.no_grad():
            pred = model.generate(loader[i]["inputs"].unsqueeze(0).cuda())
        tn, pn = notes(truth), notes(pred)
        for name, key in (("pitch", lambda s: s.pitch), ("pitch_lift", lambda s: (s.pitch, s.lift)), ("pitch_rhythm", lambda s: (s.pitch, s.rhythm))):
            t, p = Counter(map(key, tn)), Counter(map(key, pn))
            for g in ("all", src(e)):
                agg[g][name + "_tp"] += inter(t, p); agg[g][name + "_truth"] += sum(t.values()); agg[g][name + "_pred"] += sum(p.values())
        tts = [s.rhythm for s in truth if s.rhythm.startswith("timeSignature")]
        pts = [s.rhythm for s in pred if s.rhythm.startswith("timeSignature")]
        for g in ("all", src(e)):
            agg[g]["staffs"] += 1
            if tts:
                agg[g]["ts_staffs"] += 1; agg[g]["ts_exact"] += tts == pts
                agg[g]["ts_first_right"] += bool(pts) and pts[0] == tts[0]
                agg[g]["ts_truth"] += len(tts); agg[g]["ts_tp"] += inter(Counter(tts), Counter(pts)); agg[g]["ts_pred"] += len(pts)
            else:
                agg[g]["no_ts_staffs"] += 1; agg[g]["invented"] += bool(pts)
        if i % 100 == 0: print(i, "of", len(entries), flush=True)
    res = {}
    for g, c in agg.items():
        r = {"staffs": c["staffs"]}
        for name in ("pitch", "pitch_lift", "pitch_rhythm"):
            tp, t, p = c[name + "_tp"], c[name + "_truth"], c[name + "_pred"]
            r[name] = {"precision": tp / p if p else None, "recall": tp / t if t else None, "f1": 2 * tp / (t + p) if t + p else None, "missing": t - tp, "extra": p - tp, "truth": t}
        r["meter"] = {"staffs_with_ts": c["ts_staffs"], "exact_sequence": c["ts_exact"] / c["ts_staffs"] if c["ts_staffs"] else None,
                      "first_right": c["ts_first_right"] / c["ts_staffs"] if c["ts_staffs"] else None,
                      "ts_recall": c["ts_tp"] / c["ts_truth"] if c["ts_truth"] else None, "ts_precision": c["ts_tp"] / c["ts_pred"] if c["ts_pred"] else None,
                      "staffs_without_ts": c["no_ts_staffs"], "invented_rate": c["invented"] / c["no_ts_staffs"] if c["no_ts_staffs"] else None}
        res[g] = r
    json.dump({"model": pth, "list": lst, "n": len(entries), "seed": seed, "results": res}, open(out, "w"), indent=1)
    a = res["all"]; print(pth.split("/")[-1][:40], "n", len(entries), "pitch P %.3f R %.3f F1 %.3f | meter exact %s invented %s" % (a["pitch"]["precision"], a["pitch"]["recall"], a["pitch"]["f1"], a["meter"]["exact_sequence"], a["meter"]["invented_rate"]))

if __name__ == "__main__":
    main()
