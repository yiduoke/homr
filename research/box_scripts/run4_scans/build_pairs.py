"""Pair the system crops of every matched piece with the token labels of its .krn systems, run the automatic checks
and write the lists.

usage: PYTHONPATH=/workspace/homr_acc python build_pairs.py [--model-check-file '/workspace/run4/scans/model_check_*.jsonl']
Inputs : /workspace/run4/scans/kern/<repo>/<piece>.json   (kern_systems.py)
         /workspace/run4/scans/crops/<repo>/<piece>.json  (cut_pages.py)
         /workspace/run4/scans/piece_status.json          (piece-level match of system counts, test exclusions)
         model_check_*.jsonl                              (model_check.py)
Output : /workspace/run4/scans/tokens/<repo>/<piece>_s<i>.tokens, pairs.jsonl (every pair with all check results),
         pieces.json, scan_train.txt scan_val.txt scan_quarantine.txt scan_val_pieces.json

Checks per pair (all must pass for the training/validation lists):
  kern     conversion of the .krn system succeeded (no octave shift, no repeat sign at the system start, vocabulary ...)
  crop     homr found exactly one grand staff for the system and the crop was cut
  trainer  the training-time filters (vocabulary, sequence length <= max_seq_len-2, <= 5 ledger lines)
  verify   two independent measures on the image: (1) barlines counted in the crop (crop_bars.py) = barline tokens of the
           label (+1 for the line joining the staves at the left edge, which may be missed); (2) the released model's
           reading of the crop (model_check.py): "strong" = pitch F1 >= 0.8 against the label's notes, same number of
           barlines, note count within 10%; "medium" = F1 >= 0.6 and note count within 25%. Accepted: bars ok and model
           strong or medium, or bars not ok (fail / not judged) but model strong. Everything else is quarantined.
           scan_*_strong.txt = the same lists without the "medium" pairs.
  piece    quarantine the whole piece if fewer than 40% of its judged systems pass the bar count, or fewer than 50% of its
           systems are read strongly by the model (a shifted system assignment gives only chance agreement).
Validation: whole pieces, about 8% per source, seeded (SEED_VAL), only from pieces that pass the piece check.
"""
import collections
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cv2

import crop_bars

BASE = "/workspace/run4/scans"
SEED_VAL = 20261118
VAL_FRAC = 0.08
PIECE_MIN_BAR_MATCH = 0.4
PIECE_MIN_MODEL_STRONG = 0.5
MODEL_STRONG = 0.8
MODEL_MEDIUM = 0.6


def trainer_filter(tok_path):
    from homr.transformer.configs import Config
    from training.transformer.data_loader import MAX_ALLOWED_LEDGER_LINES
    from training.transformer.training_vocabulary import check_token_lines, max_ledger_lines, read_tokens

    try:
        t = read_tokens(tok_path)
        check_token_lines(t)
    except Exception:  # noqa: BLE001
        return "vocab"
    if len(t) > Config().max_seq_len - 2:
        return "long"
    if max_ledger_lines(t) > MAX_ALLOWED_LEDGER_LINES:
        return "ledger"
    return "ok"


def bar_check(img_path, n_bars):
    im = cv2.imread(img_path, 0)
    groups, u, ok = crop_bars.count_bars(im)
    if not ok:
        return "undetermined", None
    d = len(groups) - (n_bars + 1)
    if d == 0:
        return "ok", d
    if d == -1 and groups[0][0] > 4 * u:
        return "ok", d  # the line joining the staves at the left edge was not seen
    return "fail", d


def main():
    status = {(r[0], r[1]): r for r in json.load(open(f"{BASE}/piece_status.json"))}
    model_res = {}
    if "--model-check-file" in sys.argv:
        for mf in glob.glob(sys.argv[sys.argv.index("--model-check-file") + 1]):
            for line in open(mf):
                r = json.loads(line)
                model_res[r["id"]] = r
    pairs, pieces = [], []
    for (repo, piece), st in sorted(status.items()):
        if st[2] != "match":
            continue
        kj = json.load(open(f"{BASE}/kern/{repo}/{piece}.json"))
        cj = f"{BASE}/crops/{repo}/{piece}.json"
        if not os.path.exists(cj):
            continue
        cr = json.load(open(cj))
        flat = [(p["page"], s) for p in cr["pages"] for s in p["systems"]]
        ks = kj["systems"]
        if len(flat) != len(ks):
            pieces.append(dict(repo=repo, piece=piece, status="count_mismatch_after_cut", n_kern=len(ks), n_crops=len(flat)))
            continue
        recs = []
        os.makedirs(f"{BASE}/tokens/{repo}", exist_ok=True)
        for i, ((page, s), k) in enumerate(zip(flat, ks)):
            pid = f"{repo}/{piece}/s{i:03d}"
            rec = dict(id=pid, repo=repo, piece=piece, index=i, page=page, reasons=[], checks={})
            tok_path = f"{BASE}/tokens/{repo}/{piece}_s{i:03d}.tokens"
            crop = s["crops"][0] if s["crops"] else None
            if k["status"] != "ok":
                rec["reasons"] += ["kern:" + r.split(":")[0][:40] for r in k["reasons"]]
            else:
                open(tok_path, "w").write(k["tokens"])
                rec["tokens"] = tok_path
                rec["n_notes"], rec["n_bars"] = k["n_notes"], k["n_bars"]
                rec["lift_rule_vs_mei_lines"] = k.get("lift_rule_vs_mei_lines", 0)
                rec["with_meter"] = k["with_meter"]
            if crop is None or "error" in crop or s["n_staffs"] != 1 or not crop.get("grandstaff", False):
                rec["reasons"].append("crop:not_one_grand_staff")
            else:
                rec["image"] = f"{BASE}/crops/{repo}/{crop['file']}"
                rec["shape"] = crop["shape"]
            if "tokens" in rec and "image" in rec:
                rec["checks"]["trainer"] = trainer_filter(tok_path)
                if rec["checks"]["trainer"] != "ok":
                    rec["reasons"].append("trainer:" + rec["checks"]["trainer"])
                b, d = bar_check(rec["image"], rec["n_bars"])
                rec["checks"]["bars"], rec["bars_delta"] = b, d
                if pid in model_res:
                    m = model_res[pid]
                    rec["model"] = m
                    nd = abs(m["label_notes"] - m["pred_notes"]) / max(1, m["label_notes"])
                    strong = m["pitch_f1"] >= MODEL_STRONG and m["pred_bars"] == m["label_bars"] and nd <= 0.1
                    medium = m["pitch_f1"] >= MODEL_MEDIUM and nd <= 0.25
                    rec["checks"]["model"] = "strong" if strong else ("medium" if medium else "weak")
                else:
                    rec["checks"]["model"] = "missing"
                mm = rec["checks"]["model"]
                if b == "ok" and mm in ("strong", "medium"):
                    rec["checks"]["verified_by"] = "bars+model_" + mm
                elif b != "ok" and mm == "strong":
                    rec["checks"]["verified_by"] = "model_only"
                elif rec["checks"]["trainer"] == "ok":
                    rec["reasons"].append(f"verify:bars_{b}_model_{mm}")
            recs.append(rec)
        judged = [r for r in recs if r["checks"].get("bars") in ("ok", "fail")]
        frac_ok = sum(1 for r in judged if r["checks"]["bars"] == "ok") / max(1, len(judged))
        msamp = [r for r in recs if "model" in r]
        mstrong = sum(1 for r in msamp if r["checks"]["model"] == "strong")
        piece_bad = frac_ok < PIECE_MIN_BAR_MATCH or (len(msamp) >= 3 and mstrong / len(msamp) < PIECE_MIN_MODEL_STRONG)
        if piece_bad:
            for r in recs:
                r["reasons"].append("piece:suspect_alignment")
        pieces.append(dict(repo=repo, piece=piece, status="suspect" if piece_bad else "ok", n_systems=len(recs),
                           bar_match_frac=round(frac_ok, 3), model_pairs=len(msamp), model_strong=mstrong))
        pairs += recs
    json.dump(pieces, open(f"{BASE}/pieces.json", "w"), indent=1)
    with open(f"{BASE}/pairs.jsonl", "w") as f:
        for r in pairs:
            f.write(json.dumps(r) + "\n")

    rng = random.Random(SEED_VAL)
    val_pieces = set()
    by_repo = collections.defaultdict(list)
    for p in pieces:
        if p["status"] == "ok":
            by_repo[p["repo"]].append(p["piece"])
    for repo, lst in sorted(by_repo.items()):
        lst = sorted(lst)
        n = max(1, round(VAL_FRAC * len(lst)))
        val_pieces |= {(repo, x) for x in rng.sample(lst, n)}
    train, val, quar, train_s, val_s = [], [], [], [], []
    for r in pairs:
        if r["reasons"]:
            if "image" in r and "tokens" in r:
                quar.append(f"{r['image']},{r['tokens']},{';'.join(r['reasons'])}")
            else:
                quar.append(f",,{r['id']};{';'.join(r['reasons'])}")
            continue
        line = f"{r['image']},{r['tokens']}"
        (val if (r["repo"], r["piece"]) in val_pieces else train).append(line)
        if r["checks"].get("verified_by") != "bars+model_medium":
            (val_s if (r["repo"], r["piece"]) in val_pieces else train_s).append(line)
    open(f"{BASE}/scan_train.txt", "w").write("\n".join(train) + "\n")
    open(f"{BASE}/scan_val.txt", "w").write("\n".join(val) + "\n")
    open(f"{BASE}/scan_train_strong.txt", "w").write("\n".join(train_s) + "\n")
    open(f"{BASE}/scan_val_strong.txt", "w").write("\n".join(val_s) + "\n")
    open(f"{BASE}/scan_quarantine.txt", "w").write("\n".join(quar) + "\n")
    json.dump(sorted(map(list, val_pieces)), open(f"{BASE}/scan_val_pieces.json", "w"))
    print("pairs", len(pairs), "train", len(train), "val", len(val), "quarantine", len(quar))


if __name__ == "__main__":
    main()
