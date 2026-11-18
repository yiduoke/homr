"""SCHOTT-GUIDED variant of vary_braces.py (D30): the brace style ranges are narrowed to what the real Schott pages show (measured on the
labelled pool: thin stroke about 0.2-0.4 unit, nearly straight spine with a short point, depth about 0.4-1 unit, 0.1-0.6 unit from the staff start, no
connecting line across the gap in most systems). Everything else (page-image drawing before segmentation, labels, output) as vary_braces.py.
Original docstring follows.

Brace and bracket variations drawn on the PAGE image, before segmentation (the segmentation net runs on the altered page).

usage: PYTHONPATH=<worktree> python vary_braces.py OUTDIR SEED MODE(piano|song) IMAGE... 
For each page the saved geometry (extract*/<volume>__<page>.npz: staff top/bottom/left/unit in the coordinates of the preprocessed
image) and the structure labels (label_pairs.py) tell which pairs are grand staffs (brace) and which belong to a system of separate parts
(bracket). In the margin left of the staffs the old brace/bracket (and the barline in the gaps, in some variants) is erased and a new one is
drawn:
  brace  : curvature (straight ... strongly bowed), centre point depth, thickness profile, distance from the staff, 
           connecting line (barline across the gap) kept / removed / added;
  bracket: thin or thick vertical line with serifs, distance, connecting line kept / removed / added (for systems of separate parts).
Separate pairs are not touched. The label of each pair stays the same. Writes OUTDIR/<volume>__<page>_v<seed>.npz like extract_pairs.py.
"""
import os, sys
import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import label_pairs as L
import extract_pairs as E
import homr.main as hm

SS = 3  # supersampling of the drawn shapes


def paper_ink(gray, y0, y1, x0, x1):
    roi = gray[max(y0, 0):y1, max(x0, 0):x1]
    if roi.size == 0:
        return 255, 40
    return float(np.percentile(roi, 85)), float(min(np.percentile(roi, 1.5), 70))


def blend(img, mask, x0, y0, ink):
    """img: gray (h,w) or BGR (h,w,3) uint8; mask float (h',w') in [0,1] placed at (x0,y0)."""
    h, w = mask.shape
    ys0, xs0 = max(y0, 0), max(x0, 0)
    ys1, xs1 = min(y0 + h, img.shape[0]), min(x0 + w, img.shape[1])
    if ys1 <= ys0 or xs1 <= xs0:
        return
    m = mask[ys0 - y0:ys1 - y0, xs0 - x0:xs1 - x0]
    if img.ndim == 3:
        m = m[..., None]
    region = img[ys0:ys1, xs0:xs1].astype(np.float32)
    img[ys0:ys1, xs0:xs1] = np.clip(region * (1 - m) + ink * m, 0, 255).astype(np.uint8)


def brace_mask(height, u, rng, style):
    """Mask of a brace of the given pixel height; width from style. Returns (mask, tip_x, width_px): the right edge of the mask is the staff side."""
    curv = style["curv"]          # 0 straight .. 1 strongly bowed (exponent of the spine)
    depth = style["depth"] * u    # horizontal extent of the brace
    tmax, tmin = style["thick"] * u, style["tip"] * u
    wpx = int(np.ceil(depth + tmax + 4 * u * 0.2)) + 2
    H, W = int(height * SS), int(wpx * SS)
    t = np.linspace(0, 1, 400)
    s = np.abs(2 * t - 1)                       # 0 at the centre, 1 at the ends
    e = 1.0 + 3.0 * (1 - curv)                  # larger exponent = straighter spine with a short point
    spine = (1 - s ** e)                        # 1 at the centre (point), 0 at the ends
    if style.get("point"):                      # Schott shape: nearly straight spine with a short point at the centre and hooks at the ends
        base, m = style["base"], style["m"]
        spine = base * (1 - s ** 8) + (1 - base) * (1 - s) ** m
    xr = W - 2 * SS                             # right edge (ends of the brace)
    xc = xr - depth * SS * spine
    yc = t * (H - 1)
    w = (tmin + (tmax - tmin) * np.sin(np.pi * t) ** style["p"]) * SS / 2
    # the point of the centre is thinner
    w = w * (1 - style["pointy"] * np.exp(-((t - 0.5) / 0.04) ** 2))
    left = np.stack([xc - w, yc], 1); right = np.stack([xc + w, yc], 1)
    poly = np.concatenate([left, right[::-1]]).astype(np.int32)
    m = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m, [poly], 255, lineType=cv2.LINE_AA)
    m = cv2.resize(m, (wpx, int(height)), interpolation=cv2.INTER_AREA).astype(np.float32) / 255
    return m, wpx


def draw_brace(imgs, x_right, y_top, y_bottom, u, rng, ink, style):
    height = y_bottom - y_top
    m, wpx = brace_mask(height, u, rng, style)
    for img in imgs:
        blend(img, m, int(x_right - wpx), int(y_top), ink)


def draw_bracket(imgs, x_right, y_top, y_bottom, u, rng, ink, thick, serif):
    w = max(1, int(round(thick * u)))
    s = int(serif * u); h = max(1, int(round(0.25 * u)))
    for img in imgs:
        m = np.zeros((int(y_bottom - y_top) + 2, w + s + 1), np.float32)
        m[:, :w] = 1
        m[:h, :] = 1; m[-h:, :] = 1
        blend(img, m, int(x_right - w - s), int(y_top), ink)


def draw_line(imgs, x, y_top, y_bottom, u, ink, width=0.22):
    w = max(1, int(round(width * u)))
    for img in imgs:
        blend(img, np.ones((int(y_bottom - y_top), w), np.float32), int(x), int(y_top), ink)


def random_brace_style(rng):
    if rng.uniform() < 0.7:
        return dict(point=True, base=rng.uniform(0.3, 0.6), m=rng.uniform(3, 8), curv=0.0, depth=rng.uniform(0.7, 1.4), thick=rng.uniform(0.14, 0.4),
                    tip=rng.uniform(0.08, 0.2), p=rng.uniform(0.3, 1.0), pointy=rng.uniform(0, 0.4))
    return dict(curv=rng.uniform(0, 0.45), depth=rng.uniform(0.35, 1.1), thick=rng.uniform(0.14, 0.45), tip=rng.uniform(0.06, 0.16),
                p=rng.uniform(0.6, 1.6), pointy=rng.uniform(0, 0.5))


def vary_page(gray, bgr, geo, labels, rng):
    """Alters gray and bgr in place. geo: dict of arrays (top, bottom, left, unit) per staff; labels per pair in chain order."""
    order = list(np.argsort(geo["top"]))
    n = len(order)
    top, bottom, left, unit = (np.array(geo[k])[order] for k in ("top", "bottom", "left", "unit"))
    # systems: consecutive staffs joined by labels != separate
    systems, cur = [], [0]
    for k in range(n - 1):
        if labels[k] == L.SEPARATE:
            systems.append(cur); cur = [k + 1]
        else:
            cur.append(k + 1)
    systems.append(cur)
    imgs = [gray, bgr]
    for sysm in systems:
        if len(sysm) < 2:
            continue
        u = float(np.mean(unit[sysm]))
        x_left = float(np.min(left[sysm]))
        y_top, y_bot = float(top[sysm[0]]) - 0.2 * u, float(bottom[sysm[-1]]) + 0.2 * u
        paper, ink = paper_ink(gray, int(y_top), int(y_bot), int(x_left - 6 * u), int(x_left - 0.5 * u))
        # erase brace / bracket in the margin of the whole system
        x0, x1 = int(max(x_left - 7 * u, 0)), int(x_left - 0.35 * u)
        for img in imgs:
            img[int(y_top):int(y_bot), x0:x1] = paper if img.ndim == 2 else (paper, paper, paper)
        # connecting lines across the gaps
        mode = rng.choice(["keep", "remove", "add"], p=[0.25, 0.6, 0.15])
        for a, b in zip(sysm[:-1], sysm[1:]):
            ga0, ga1 = bottom[a] + 0.45 * u, top[b] - 0.45 * u
            if ga1 <= ga0:
                continue
            if mode == "remove":
                for img in imgs:
                    img[int(ga0):int(ga1), int(x_left - 0.6 * u):int(x_left + 0.5 * u)] = paper if img.ndim == 2 else (paper, paper, paper)
            elif mode == "add":
                draw_line(imgs, x_left - rng.uniform(0.0, 0.5) * u, ga0, ga1, u, ink, rng.uniform(0.12, 0.35))
        # grand staff pairs: brace; systems with separate parts: bracket round the whole system
        k0 = sysm[0]
        has_same = any(labels[k] == L.SAME_SYSTEM for k in range(k0, sysm[-1]))
        for k in range(k0, sysm[-1]):
            if labels[k] == L.GRAND_STAFF:
                dist = rng.uniform(0.1, 0.6) * u
                draw_brace(imgs, x_left - dist, top[k] - 0.1 * u, bottom[k + 1] + 0.1 * u, u, rng, ink, random_brace_style(rng))
        if has_same:
            dist = rng.uniform(0.3, 1.2) * u + (2.6 * u if any(labels[k] == L.GRAND_STAFF for k in range(k0, sysm[-1])) else 0)
            draw_bracket(imgs, x_left - dist, y_top, y_bot, u, rng, ink, rng.uniform(0.12, 0.45), rng.uniform(0.3, 0.9))


def main():
    out, seed, mode, images = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
    os.makedirs(out, exist_ok=True)
    src_dir = {"piano": "extract", "song": "extract_songs"}[mode]
    base = "/Users/yiduoke/Documents/homr/run/staff_rel_realbrace"
    current = {}
    orig = hm.get_predictions

    def patched(original, preprocessed, img_path, enable_cache, segnet_use_gpu):
        if "geo" in current:
            preprocessed = preprocessed.copy(); original = original.copy()
            rng = np.random.default_rng(current["seed"])
            vary_page(preprocessed, original, current["geo"], current["labels"], rng)
            current["last"] = preprocessed
        return orig(original, preprocessed, img_path, False, segnet_use_gpu)

    hm.get_predictions = patched
    for image in images:
        name = os.path.basename(os.path.dirname(image)) + "__" + os.path.splitext(os.path.basename(image))[0]
        target = f"{out}/{name}_v{seed}.npz"
        if os.path.exists(target):
            continue
        z = np.load(f"{base}/{src_dir}/{name}.npz")
        lab, why = L.label_page(z, mode)
        if lab is None:
            continue
        order = list(np.argsort(z["top"])); by = {tuple(p): k for k, p in enumerate(z["pairs"])}
        chain_labels = [int(lab[by[(order[k], order[k + 1])]]) for k in range(len(order) - 1)]
        geo = {k: z[k] for k in ("top", "bottom", "left", "unit")}
        current.update(geo=geo, labels=chain_labels, seed=hash((name, seed)) % (2 ** 31))
        # a copy of the page, so that no cache is written next to the original
        tmp = f"{out}/tmp_{name}_v{seed}.png"
        cv2.imwrite(tmp, cv2.imread(image))
        try:
            single = hm.detect_single_staffs(tmp, E.CONFIG)
            from homr import staff_relations as sr
            staffs = sr.join_pieces_with_model(single.predictions, single.staffs)
            pairs, crops = sr.page_inputs(single.predictions, staffs)
            gray = single.predictions.preprocessed
            conn = [E.connectors(gray, staffs[i], staffs[j]) for i, j in pairs]
            ys = lambda s, line: float(np.mean([p.y[line] for p in s.grid]))  # noqa
            np.savez_compressed(target, crops=(crops * 255).round().astype(np.uint8), pairs=np.array(pairs, dtype=np.int64).reshape(-1, 2),
                                top=[ys(s, 0) for s in staffs], bottom=[ys(s, -1) for s in staffs], left=[s.min_x for s in staffs],
                                right=[s.max_x for s in staffs], unit=[s.average_unit_size for s in staffs],
                                connectors=[c[0] for c in conn], gap=[c[1] for c in conn], shape=gray.shape, image=image)
            if os.environ.get("SAVE_PAGES"):
                cv2.imwrite(f"{out}/{name}_v{seed}_pre.png", current["last"])
            print("ok", name, len(staffs), "staffs", len(pairs), "pairs", flush=True)
        except Exception as e:  # noqa
            print("FAIL", name, repr(e)[:100], flush=True)
        finally:
            for f in (tmp, tmp[:-4] + ".npy"):
                if os.path.exists(f): os.remove(f)


if __name__ == "__main__":
    main()
