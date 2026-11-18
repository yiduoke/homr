"""D25: what the staff-relation classifier gets. For the vertical pairs of a page image: the original page margin at full resolution (straight
rectangle of predictions.original), the 5 channels of the 96 x 96 crop exactly as homr.staff_relations.page_inputs builds them (shown x3,
nearest), and the probabilities (separate / same system / grand staff) of several models. Also a numeric 'brace survival' measure per channel.
usage: PYTHONPATH=run/rel_wt python inspect_input.py OUT_PREFIX IMAGE [--pairs 0,2,4] [--models label=path,...] [--save-npz]"""
import argparse, json, os, sys
import cv2, numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from homr.main import ProcessingConfig, detect_single_staffs
from homr import staff_relations as sr

R = "/Users/yiduoke/Documents/homr/run"
MODELS = {"shipped": None, "rb1": f"{R}/staff_rel_realbrace/staff_relations_realbrace-1.onnx", "rb2": f"{R}/staff_rel_realbrace/staff_relations_realbrace-2.onnx",
          "rb3": f"{R}/staff_rel_realbrace/staff_relations_realbrace-3.onnx"}
CH = ["gray ink (255-gray)", "staff", "symbols", "stems/rests", "clefs/keys"]
CFG = ProcessingConfig(False, False, False, False, -1, False, True, False, False)


def native_margin(pred, upper, lower, before=12, after=4):
    unit = (upper.average_unit_size + lower.average_unit_size) / 2
    left = min(upper.min_x, lower.min_x)
    x0, x1 = int(left - before * unit), int(left + after * unit)
    y0 = int(min(np.interp(left, [p.x for p in upper.grid], [p.y[0] for p in upper.grid]) - 3 * unit, 1e9))
    y1 = int(np.interp(left, [p.x for p in lower.grid], [p.y[-1] for p in lower.grid]) + 3 * unit)
    img = pred.original
    if img.ndim == 3:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return img[max(0, y0):y1, max(0, x0):x1], unit


def brace_measure(crop, threshold=0.25):
    """The tallest connected ink structure left of the staff start in each channel, as a share of the crop height (crop (5,96,96) in [0,1]).
    Zone: columns 28-43 (the staff starts at column 40, the brace is within 3 units left of it). A brace, or a brace with its
    connecting line, gives 0.8 or more; a barline of each staff alone gives about 0.3."""
    out = {}
    for k, name in enumerate(CH):
        zone = (crop[k][:, 28:44] > threshold).astype(np.uint8)
        n, _, stats, _ = cv2.connectedComponentsWithStats(zone, connectivity=8)
        out[name] = round(float(stats[1:, cv2.CC_STAT_HEIGHT].max() / 96), 2) if n > 1 else 0.0
    return out


def run(image, pairs_sel, models):
    single = detect_single_staffs(image, CFG)
    staffs = sr.join_pieces_with_model(single.predictions, single.staffs)
    pairs, crops = sr.page_inputs(single.predictions, staffs)
    probs = {}
    for k, p in models.items():
        probs[k] = (sr.get_model(p) if p else sr.get_model()).predict(crops)
    rows = []
    for n, (i, j) in enumerate(pairs):
        if pairs_sel is not None and n not in pairs_sel:
            continue
        nat, unit = native_margin(single.predictions, staffs[i], staffs[j])
        rows.append(dict(n=n, pair=(i, j), native=nat, unit=unit, crop=crops[n], probs={k: probs[k][n] for k in probs},
                         brace=brace_measure(crops[n])))
    return rows, crops, pairs


def figure(rows, out, title, models):
    nrow = len(rows)
    fig, axes = plt.subplots(nrow, 7, figsize=(17, 2.6 * nrow), gridspec_kw={"width_ratios": [2.4, 1, 1, 1, 1, 1, 1.6]}, squeeze=False)
    for r, row in zip(axes, rows):
        r[0].imshow(row["native"], cmap="gray", vmin=0, vmax=255, aspect="equal")
        r[0].set_title(f"pair {row['pair'][0]}-{row['pair'][1]}: page margin, native (unit {row['unit']:.1f} px)", fontsize=8)
        for k in range(5):
            r[1 + k].imshow(row["crop"][k], cmap="gray_r" if k else "gray_r", vmin=0, vmax=1, aspect="equal")
            r[1 + k].set_title(f"{CH[k]}\ntallest {row['brace'][CH[k]]}", fontsize=7)
        r[6].axis("off")
        txt = "\n".join(f"{m}: sep {p[0]:.2f}  same {p[1]:.2f}  grand {p[2]:.2f}" for m, p in row["probs"].items())
        r[6].text(0, 0.5, txt, fontsize=8, va="center", family="monospace")
        for a in r[:6]:
            a.set_xticks([]); a.set_yticks([])
    fig.suptitle(title, fontsize=10)
    fig.tight_layout()
    fig.savefig(out, dpi=80)
    plt.close(fig)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("out"); ap.add_argument("image"); ap.add_argument("--pairs", default=None); ap.add_argument("--models", default="shipped,rb1,rb2,rb3")
    ap.add_argument("--title", default=None); ap.add_argument("--save", action="store_true")
    a = ap.parse_args()
    models = {}
    for m in a.models.split(","):
        if "=" in m:
            k, p = m.split("=", 1); models[k] = p
        else:
            models[m] = MODELS[m]
    sel = None if a.pairs is None else {int(x) for x in a.pairs.split(",")}
    rows, crops, pairs = run(a.image, sel, models)
    figure(rows, a.out + ".png", a.title or os.path.basename(a.image), models)
    json.dump([dict(n=r["n"], pair=r["pair"], brace=r["brace"], probs={k: np.round(v, 3).tolist() for k, v in r["probs"].items()}) for r in rows], open(a.out + ".json", "w"), indent=1)
    if a.save:
        np.savez_compressed(a.out + ".npz", crops=crops, pairs=np.array(pairs), sel=[r["n"] for r in rows])
    print("done", a.out, len(rows))
