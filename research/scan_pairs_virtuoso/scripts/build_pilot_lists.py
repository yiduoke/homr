"""Paired list files of the pilot: the same passages once as rendered twins, once as scanned crops (identical line order, identical token files).

usage: build_pilot_lists.py            (after twin_render.py wrote twins/ and twins_report.json)

Reads lists/train_strong.txt, lists/train_hard.txt (training) and lists/val_strong.txt (validation, kept separate) and twins_report.json.
A crop whose twin was dropped (reason in the report) is dropped from BOTH lists.
Writes (paths relative to run/, like the other lists):
  lists/pilot_twin_render.txt  lists/pilot_scan.txt  lists/val_twin_render.txt  lists/val_scan.txt  lists/pilot_dropped.txt  lists/pilot_clef_key_disagree.txt
  lists/box/<same names>      the same lines with the box paths (/workspace/pilot/{images,twins,tokens}/...), ready for upload
  pilot_pairs_summary.json    counts by piece, tier and drop reason
"""
import collections, csv, glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT + "/../integration_wt")
from unittest import mock
for _m in ("augraphy", "augraphy.base", "augraphy.base.augmentationpipeline", "augraphy.base.augmentation", "augraphy.utilities", "augraphy.utilities.overlaybuilder"):
    sys.modules.setdefault(_m, mock.MagicMock())
from training.transformer.training_vocabulary import max_ledger_lines, read_tokens, check_token_lines
from homr.transformer.configs import Config

REL = "scan_pairs_virtuoso/"; BOX = "/workspace/pilot/"
MAX_LEN = Config().max_seq_len - 2
report = {r["name"]: r for r in json.load(open(ROOT + "/twins_report.json"))}
bycrop = {r["crop"]: r for r in csv.DictReader(open(ROOT + "/manifest.csv"))}


def lines(name):
    return [l.strip() for l in open(f"{ROOT}/lists/{name}.txt") if l.strip()]


out = collections.defaultdict(list)
dropped = []
summary = collections.defaultdict(collections.Counter)
for split, lists in (("pilot", ["train_strong", "train_hard"]), ("val", ["val_strong"])):
    for lst in lists:
        for line in lines(lst):
            img, tok = line.split(",")
            img_r, tok_r = img.replace(REL, ""), tok.replace(REL, "")
            name = os.path.basename(img_r)[:-4]; pid = name.split("_")[0]
            rep = report[name]
            summary[split]["candidates"] += 1
            if rep["status"] != "ok":
                dropped.append(f"{split}\t{name}\t{rep['reason']}")
                summary[split]["dropped: " + re.sub(r"[(:].*", "", rep["reason"]).strip()] += 1
                continue
            twin_r = f"twins/{pid}/{name}.png"
            assert os.path.exists(f"{ROOT}/{twin_r}") and os.path.exists(f"{ROOT}/{img_r}") and os.path.exists(f"{ROOT}/{tok_r}"), name
            toks = read_tokens(f"{ROOT}/{tok_r}"); check_token_lines(toks)     # vocabulary
            assert len(toks) <= MAX_LEN and max_ledger_lines(toks) <= 5, name   # the trainer filters (prebuilt lists are not filtered by the trainer)
            kind = "twin_render"
            tw = {"pilot": "pilot_twin_render", "val": "val_twin_render"}[split]
            sc = {"pilot": "pilot_scan", "val": "val_scan"}[split]
            out[tw].append(f"{REL}{twin_r},{REL}{tok_r}"); out[sc].append(f"{REL}{img_r},{REL}{tok_r}")
            out["box/" + tw].append(f"{BOX}{twin_r},{BOX}{tok_r}"); out["box/" + sc].append(f"{BOX}{img_r},{BOX}{tok_r}")
            summary[split]["kept"] += 1; summary[split + " by piece: " + pid]["kept"] += 1
            summary[split]["tier " + bycrop[img_r]["tier"]] += 1
# crops whose first clefs or key signature in the label differ from the released model's read of the scan (model errors and label/print differences are mixed)
clef = list(json.load(open(sys.argv[1]))) if len(sys.argv) > 1 else []
out["pilot_clef_key_disagree"] = [l for l in out["pilot_scan"] + out["val_scan"] if os.path.basename(l.split(",")[0])[:-4] in set(clef)]
for k, v in out.items():
    if k.startswith("box/"):
        os.makedirs(f"{ROOT}/lists/box", exist_ok=True)
    open(f"{ROOT}/lists/{k}.txt", "w").write("\n".join(v) + "\n")
open(f"{ROOT}/lists/pilot_dropped.txt", "w").write("split\tcrop\treason\n" + "\n".join(dropped) + "\n")
json.dump({k: dict(v) for k, v in summary.items()}, open(f"{ROOT}/pilot_pairs_summary.json", "w"), indent=1)
for k in ("pilot", "val"):
    print(k, dict(summary[k]))
print({k: len(v) for k, v in out.items()})
