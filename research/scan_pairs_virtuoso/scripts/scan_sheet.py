"""v2: contact sheets of scan crops only (pilot or batch 2) with a one-line caption, for by-eye checks.
usage: scan_sheet.py OUT_PREFIX NAME[:caption] ...   (PER=n crops per sheet, default 4; W=width)"""
import sys, os, glob
import cv2, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, names = sys.argv[1], sys.argv[2:]
W = int(os.environ.get("W", 1100)); per = int(os.environ.get("PER", 4))
def find(name):
    pid = name.split("_")[0]
    for p in (f"{ROOT}/images/{pid}/{name}.png", f"{ROOT}/batch2/images/{pid}/{name}.png"):
        if os.path.exists(p): return p
    raise FileNotFoundError(name)
rows = []
for n in names:
    name, _, note = n.partition(":")
    img = cv2.imread(find(name), 0)
    zl = float(os.environ.get("ZL", 0))                  # keep only the left fraction of the crop (time signature check), enlarged
    if zl: img = img[:, :int(img.shape[1] * zl)]; img = cv2.resize(img, None, fx=1.6, fy=1.6, interpolation=cv2.INTER_CUBIC)
    h, w = img.shape; s = min(1.0, W / w)
    if s < 1: img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)
    pad = np.full((img.shape[0], W), 255, np.uint8); pad[:, :img.shape[1]] = img
    cap = np.full((22, W), 235, np.uint8)
    cv2.putText(cap, f"{name}  {note}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 0, 1)
    rows += [cap, pad, np.full((6, W), 120, np.uint8)]
for i in range(0, len(names), per):
    cv2.imwrite(f"{out}_{i // per:02d}.png", np.vstack(rows[i * 3:(i + per) * 3]))
