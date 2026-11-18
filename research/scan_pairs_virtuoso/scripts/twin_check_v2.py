"""v2: contact sheets for the by-eye check: scan crop above its rendered twin, caption with the name and a note, N per sheet.
usage: twin_check_v2.py OUT_PREFIX NAME[:note] ...   (names of pilot crops; images/<pid>/<name>.png and twins/<pid>/<name>.png)"""
import sys, os
import cv2, numpy as np
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, names = sys.argv[1], sys.argv[2:]
W = 1100
def fit(img):
    h, w = img.shape[:2]
    s = min(1.0, W / w)
    img = cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA) if s < 1 else img
    pad = np.full((img.shape[0], W), 255, np.uint8); pad[:, :img.shape[1]] = img
    return pad
rows = []
for n in names:
    name, _, note = n.partition(":")
    pid = name.split("_")[0]
    a = cv2.imread(f"{ROOT}/images/{pid}/{name}.png", 0); b = cv2.imread(f"{ROOT}/twins/{pid}/{name}.png", 0)
    cap = np.full((22, W), 235, np.uint8)
    cv2.putText(cap, f"{name}  {note}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.5, 0, 1)
    sep = np.full((4, W), 120, np.uint8)
    rows += [cap, fit(a), sep, fit(b), np.full((8, W), 255, np.uint8)]
per = int(os.environ.get("PER", 3)); k = 5
for i in range(0, len(names), per):
    cv2.imwrite(f"{out}_{i // per:02d}.png", np.vstack(rows[i * k:(i + per) * k]))
