"""Count the barlines of a grand-staff crop: columns whose pixels between the first line of the upper staff and the
last line of the lower staff are dark in (almost) every row that is not a staff line. Neighbouring columns (and groups
closer than 2 staff spaces, e.g. double bars) form one group. Returns (groups, unit, ok). The first group is normally
the line which joins the two staves at the left edge of the system, so a system with k measures shows k+1 groups.
"""
import cv2
import numpy as np


def staff_lines(bw):
    H, W = bw.shape
    k = cv2.getStructuringElement(cv2.MORPH_RECT, (max(15, W // 12), 1))
    hl = cv2.morphologyEx(bw, cv2.MORPH_OPEN, k)
    rows = hl.sum(1) > 0.2 * W
    centers = []
    y = 0
    while y < H:
        if rows[y]:
            y0 = y
            while y < H and rows[y]:
                y += 1
            centers.append((y0 + y - 1) / 2)
        else:
            y += 1
    return centers


def best_ten(centers):
    best = None
    for i in range(len(centers) - 9):
        w = centers[i:i + 10]
        d = np.diff(w)
        within = np.r_[d[:4], d[5:]]
        u = np.median(within)
        err = np.abs(within - u).max() / u
        gap = d[4] / u
        if err < 0.35 and 1.8 < gap < 9:
            if best is None or err < best[0]:
                best = (err, w, u)
    return best


def count_bars(gray):
    g = cv2.GaussianBlur(gray, (3, 3), 0)
    bw = (g < 180).astype(np.uint8)
    centers = staff_lines(bw)
    b = best_ten(centers)
    if b is None:
        return None, None, False
    _, w, u = b
    top, bot = int(round(w[0])), int(round(w[-1]))
    mask = np.ones(bw.shape[0], bool)
    for c in w:
        mask[max(0, int(c) - 1):int(c) + 2] = False
    rows = np.zeros(bw.shape[0], bool)
    rows[top:bot + 1] = True
    rows &= mask
    seg = bw[rows]
    frac = seg.mean(0)
    cols = np.where(frac >= 0.93)[0]
    groups = []
    for c in cols:
        if groups and c - groups[-1][-1] <= max(2, 0.25 * u):
            groups[-1].append(c)
        else:
            groups.append([c])
    # merge groups closer than 2 staff spaces (double bars, repeat signs)
    merged = []
    for g_ in groups:
        if merged and g_[0] - merged[-1][-1] < 1.6 * u:
            merged[-1].extend(g_)
        else:
            merged.append(list(g_))
    return [(int(g_[0]), int(g_[-1])) for g_ in merged], float(u), True
