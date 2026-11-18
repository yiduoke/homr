"""labelcheck.py OUT.png N SEED LABELS.npz [LABELS.npz ...] : N random crops (channel 0, 96 x 96 enlarged x2) with the structure label (G grand, S same system, - separate) and the shipped decision (cap)"""
import sys, numpy as np, cv2, os
out, n, seed, files = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
items = []
for f in files:
    d = np.load(f)
    for i in range(len(d["labels"])): items.append((f, i))
rng = np.random.default_rng(seed); pick = rng.choice(len(items), min(n, len(items)), replace=False)
cache = {}; tiles = []
for j in pick:
    f, i = items[j]
    d = cache.setdefault(f, np.load(f)); c = 255 - d["crops"][i][0]
    t = cv2.cvtColor(cv2.resize(c, (c.shape[1] * 2, c.shape[0] * 2), interpolation=cv2.INTER_AREA), cv2.COLOR_GRAY2BGR)
    lab = "G S"[0:0] + "-SG"[d["labels"][i]]; sh = "-SG"[d["shipped"][i]]
    col = (0, 140, 0) if lab == "G" else (200, 0, 0) if lab == "S" else (0, 0, 200)
    cv2.putText(t, f"label {lab}  shipped {sh}", (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, col, 1)
    cv2.putText(t, os.path.basename(f)[:14] + " " + str(d["page"][i])[-8:], (2, t.shape[0] - 4), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (90, 90, 90), 1)
    tiles.append(t)
cols = 8; h, w = tiles[0].shape[:2]; rows = (len(tiles) + cols - 1) // cols
canvas = np.full((rows * h, cols * w, 3), 255, np.uint8)
for k, t in enumerate(tiles): canvas[(k // cols) * h:(k // cols + 1) * h, (k % cols) * w:(k % cols + 1) * w] = t
cv2.imwrite(out, canvas); print(canvas.shape)
