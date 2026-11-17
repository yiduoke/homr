"""Image statistics for the crop audit. usage: image_stats3.py <out.jsonl> <list 'image,token'>
Per image: size, staff lines found (rows with > 50% dark pixels, merged), staffs seen in the image (groups of
lines), ink in the 3 top and 3 bottom pixel rows (a cut-off neighbour system or staff), and the number of staffs
the label describes (clef symbols in the first token line).
"""
import json, multiprocessing as mp, os, sys
import numpy as np
from PIL import Image


def staffs_from_lines(lines):
    if not lines:
        return 0
    gaps = np.diff(lines)
    if len(gaps) == 0:
        return 1
    sp = np.median(gaps[gaps < np.percentile(gaps, 60) + 1]) if len(gaps) > 3 else np.min(gaps)
    n = 1
    for g in gaps:
        if g > 2.2 * sp:
            n += 1
    return n


def work(item):
    png, tok = item
    try:
        im = np.asarray(Image.open(png).convert("L"))
    except Exception:
        return None
    H, W = im.shape
    dark = im < 128
    rowfrac = dark.mean(axis=1)
    rows = np.where(rowfrac > 0.5)[0]
    lines = []
    for r in rows:
        if not lines or r - lines[-1][-1] > 1:
            lines.append([r])
        else:
            lines[-1].append(r)
    centers = [float(np.mean(l)) for l in lines]
    top = int(dark[:3].sum()); bot = int(dark[-3:].sum())
    try:
        first = open(tok).readline()
        lab = sum(1 for s in first.split("&") if s.startswith("clef_"))
    except Exception:
        lab = -1
    return dict(key=png, W=W, H=H, nlines=len(centers), nstaffs=staffs_from_lines(centers), top=top, bot=bot, lab=lab)


if __name__ == "__main__":
    items = [tuple(l.strip().split(",")[:2]) for l in open(sys.argv[2]) if l.strip()]
    with mp.Pool(int(os.environ.get("NP", "50"))) as pool, open(sys.argv[1], "w") as fo:
        for r in pool.imap(work, items, chunksize=100):
            if r:
                fo.write(json.dumps(r) + "\n")
