"""How the scan crops differ from the rendered training crops, measured on what the model sees (the 256x1280 canvas).
usage: PYTHONPATH=/workspace/homr_acc python image_stats.py <list scans> <list rendered> <out.json> [n=300] [seed=11]
Per image: staff space in canvas pixels (median spacing of the 10 staff lines), staff line thickness, canvas content
width fraction, margin above/below the staff in staff spaces, skew of the staff lines (degrees, left third vs right
third), background (paper) level and noise (std of the paper pixels), ink level (5th percentile), share of non-white
pixels, text/marks outside the staff (ink share above the first and below the last line)."""
import json, random, sys
import cv2
import numpy as np
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import crop_bars as cb
from homr.staff_parsing import add_image_into_tr_omr_canvas


def measure(path):
    im = cv2.imread(path, 0)
    if im is None:
        return None
    h0, w0 = im.shape
    canvas = add_image_into_tr_omr_canvas(im)
    g = cv2.GaussianBlur(canvas, (3, 3), 0)
    bw = (g < 180).astype(np.uint8)
    cs = cb.staff_lines(bw)
    b = cb.best_ten(cs)
    if b is None:
        return None
    _, w, u = b
    H, W = canvas.shape
    content_w = w0 * (min(H, 256) / h0) if False else None
    ink_cols = np.where((canvas < 200).any(0))[0]
    out = dict(unit=float(u), content_w=float((ink_cols.max() + 1) / W) if len(ink_cols) else 0.0,
               margin_top=float(w[0] / u), margin_bottom=float((np.where((canvas < 200).any(1))[0].max() if (canvas < 200).any() else H) / u),
               )
    rows_ink = np.where((canvas < 200).any(1))[0]
    out["content_h_units"] = float((rows_ink.max() - rows_ink.min() + 1) / u)
    out["margin_top"] = float((w[0] - rows_ink.min()) / u)
    out["margin_bottom"] = float((rows_ink.max() - w[-1]) / u)
    # skew: y of the first staff line in left and right thirds
    def line_y(x0, x1):
        prof = (255 - canvas[:, x0:x1].astype(np.float32)).mean(1)
        lo, hi = int(w[0]) - 4, int(w[0]) + 5
        return lo + int(np.argmax(prof[lo:hi]))
    third = int(0.3 * W * 0 + 1)
    ink_w = int(ink_cols.max()) if len(ink_cols) else W
    xl, xr = int(0.1 * ink_w), int(0.9 * ink_w)
    try:
        yl = line_y(xl, xl + int(0.2 * ink_w)); yr = line_y(xr - int(0.2 * ink_w), xr)
        out["skew_deg"] = float(np.degrees(np.arctan2(yr - yl, xr - xl)))
    except Exception:  # noqa: BLE001
        out["skew_deg"] = None
    # staff line thickness: dark run length across the first line
    col = canvas[int(w[0]) - 4:int(w[0]) + 5, ink_w // 2]
    out["line_thick"] = float((col < 170).sum())
    paper = canvas[canvas > 150]
    out["paper_mean"] = float(paper.mean()) if paper.size else None
    out["paper_std"] = float(paper.std()) if paper.size else None
    out["ink_p1"] = float(np.percentile(canvas, 1))
    out["nonwhite"] = float((canvas < 200).mean())
    above = (canvas[:max(0, int(w[0] - 1.5 * u))] < 160).mean() if w[0] > 1.5 * u else 0.0
    below = (canvas[int(w[-1] + 1.5 * u):] < 160).mean()
    out["ink_above"], out["ink_below"] = float(above), float(below)
    out["orig_h"], out["orig_w"] = h0, w0
    return out


def main():
    la, lb, outp = sys.argv[1:4]
    n = int(sys.argv[4]) if len(sys.argv) > 4 else 300
    seed = int(sys.argv[5]) if len(sys.argv) > 5 else 11
    rng = random.Random(seed)
    res = {}
    for name, lst in (("scan", la), ("rendered", lb)):
        paths = [l.split(",")[0] for l in open(lst) if l.strip()]
        rng.shuffle(paths)
        rows, fails = [], 0
        for p in paths[:n]:
            m = measure(p)
            if m is None:
                fails += 1
            else:
                rows.append(m)
        summ = {}
        for k in rows[0]:
            v = np.array([r[k] for r in rows if r[k] is not None], dtype=float)
            summ[k] = dict(mean=float(v.mean()), p10=float(np.percentile(v, 10)), median=float(np.median(v)), p90=float(np.percentile(v, 90)))
        res[name] = dict(n=len(rows), measure_failed=fails, stats=summ)
    json.dump(res, open(outp, "w"), indent=1)
    for k in res["scan"]["stats"]:
        a, b = res["scan"]["stats"][k], res["rendered"]["stats"][k]
        print(f"{k:16s} scan med {a['median']:9.3f} [{a['p10']:9.3f},{a['p90']:9.3f}]   rendered med {b['median']:9.3f} [{b['p10']:9.3f},{b['p90']:9.3f}]")


if __name__ == "__main__":
    main()
