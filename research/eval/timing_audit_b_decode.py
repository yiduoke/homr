"""Part B step 1 (runs on the GPU box, /workspace/audit_val/): decode 300 random lines of
run2_val.txt with the released run2s7 checkpoint and save labels + predictions as token text.

Run: cd /workspace/homr_acc && PYTHONPATH=. /venv/main/bin/python /workspace/audit_val/timing_audit_b_decode.py
"""
import json
import random
import sys
import time

import torch

sys.path.insert(0, "/workspace/homr_acc")
from homr.transformer.configs import Config  # noqa: E402
from training.architecture.transformer.staff2score import Staff2Score  # noqa: E402
from training.transformer.data_loader import DataLoader  # noqa: E402
from training.transformer.image_utils import ndarray_to_tensor, pad_to_3_dims  # noqa: E402
from training.transformer.training_vocabulary import read_tokens, token_lines_to_str  # noqa: E402

CKPT = ("/workspace/homr_acc/training/architecture/transformer/"
        "pytorch_model_acc_run2s7_658-afae0e3dbdf84b2f9a53bc0e57fa7db788f64f10.pth")
VAL = "/workspace/run2/run2_val.txt"
OUT = "/workspace/audit_val/val_preds.jsonl"

lines = [l for l in open(VAL).read().splitlines() if l.strip()]
random.Random(20261116).shuffle(lines)
lines = lines[:300]

config = Config()
config.filepaths.checkpoint = CKPT
model = Staff2Score(config)
loader = DataLoader(lines, config, is_validation=True)  # same preparation as validation in training
t0 = time.time()
with open(OUT, "w") as f:
    for i, entry in enumerate(lines):
        png, tok = entry.strip().split(",")
        img = loader._prepare_image(i)
        if img is None:
            continue
        tensor = pad_to_3_dims(ndarray_to_tensor(img)).float().unsqueeze(0).to(model.device)
        with torch.no_grad():
            pred = model._generate(tensor)
        f.write(json.dumps({"i": i, "png": png, "tokens": tok,
                            "label": token_lines_to_str(read_tokens(tok)),
                            "pred": token_lines_to_str(pred)}) + "\n")
        if i % 25 == 0:
            print(i, round(time.time() - t0), "s", flush=True)
print("done", OUT)
