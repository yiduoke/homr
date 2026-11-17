"""Height of the printed time signature in staff spaces, measured on staff images (heuristic).
usage: measure_ts.py <list.txt of "image,tokens"> <n sample> <label>
Single-staff images only, key signature of C major (no accidentals), a signature at the start: after removing the staff lines,
the first ink columns are the clef, the second group of ink columns is the time signature; its vertical extent divided by
the staff space is printed (default engravings: 4 staff spaces for stacked digits, about 2 for C).
"""
import json, random, re, sys
import cv2
import numpy as np

lst, n, label = sys.argv[1], int(sys.argv[2]), sys.argv[3]
rows = [l.strip().split(",") for l in open(lst) if l.strip()]
random.Random(5).shuffle(rows)
out = []
for img, tok in rows:
    t = open(tok).read()
    lines = t.split("\n")
    if lines[0].count("clef_") != 1 or "keySignature_0" not in lines[1] or not lines[2].startswith("timeSignature_"):
        continue
    sig = lines[2].split(" ")[0][len("timeSignature_"):]
    if sig in ("common", "cut"):
        continue
    try:
        info = json.load(open(img[:-4] + ".json"))
    except Exception:
        continue
    im = cv2.imread(img, cv2.IMREAD_GRAYSCALE)
    if im is None:
        continue
    ss = info["staff_space"]
    top, bot = info["lines"]
    b = (im < 140).astype(np.uint8)
    # remove horizontal lines
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, int(3 * ss)), 1))
    lines_mask = cv2.morphologyEx(b, cv2.MORPH_OPEN, k)
    b = b & (1 - cv2.dilate(lines_mask, np.ones((3, 1), np.uint8)))
    y0, y1 = int(top - 3 * ss), int(bot + 3 * ss)
    band = b[max(0, y0):y1, :]
    cols = band.sum(axis=0) > 0
    # ink segments
    segs = []
    x = 0
    W = len(cols)
    while x < W:
        if cols[x]:
            s = x
            while x < W and cols[x]:
                x += 1
            segs.append((s, x))
        x += 1
    # merge segments closer than 0.25 staff spaces
    merged = []
    for s in segs:
        if merged and s[0] - merged[-1][1] < 0.25 * ss:
            merged[-1] = (merged[-1][0], s[1])
        else:
            merged.append(s)
    if len(merged) < 3:
        continue
    # skip the left barline/brace: first segment narrower than 0.5 ss
    merged = [m for m in merged if m[1] - m[0] > 0.3 * ss] if merged and merged[0][1] - merged[0][0] < 0.3 * ss else merged
    if len(merged) < 2:
        continue
    s, e = merged[1]
    seg = band[:, s:e]
    ys = np.where(seg.sum(axis=1) > 0)[0]
    if len(ys) == 0:
        continue
    h = (ys.max() - ys.min() + 1) / ss
    out.append((sig, h))
    if len(out) >= n:
        break
hs = sorted(h for _s, h in out)
if hs:
    print(label, "n", len(hs), "height/ss median %.2f p10 %.2f p90 %.2f" % (hs[len(hs) // 2], hs[len(hs) // 10], hs[9 * len(hs) // 10]))
else:
    print(label, "no samples")
