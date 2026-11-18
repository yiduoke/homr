"""D25 driver: figures + numbers for the Schott opening pages, working scans and the Reichardt volume. usage: PYTHONPATH=run/rel_wt python run_all.py"""
import json, os, sys
import numpy as np, cv2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inspect_input as I
from homr.main import detect_single_staffs
from homr import staff_relations as sr

R = I.R; D = f"{R}/staff_rel_realbrace/input_inspection"
RB = f"{R}/staff_rel_realbrace"
SCH = {"shipped": None, "rb1": I.MODELS["rb1"], "rb2": I.MODELS["rb2"], "rb3": I.MODELS["rb3"]}
HELD = {"shipped": None, "A0_s0": f"{RB}/models/A0_s0.onnx", "B_s0": f"{RB}/models/B_s0.onnx", "rb3 (trained on it)": I.MODELS["rb3"]}
PAGES = f"{R}/eval_run1/pages"
JOBS = [  # name, image, pairs (None = all), models, label function
    ("schott_te5_p029", f"{PAGES}/liszt-te-5/page-029.png", [0, 2, 4, 6, 8], SCH),
    ("schott_te10_p076", f"{PAGES}/liszt-te-10/page-076.png", [0, 2, 4, 6], SCH),
    ("schott_sonata_p02", f"{PAGES}/liszt-sonata/page-02.png", [0, 2, 4, 6], SCH),
    ("working_waldstein_p02", f"{PAGES}/beethoven-waldstein-1/page-02.png", [0, 2, 4], SCH),
    ("working_paganini_p11", f"{PAGES}/liszt-paganini-6/page-11.png", [0, 2], SCH),
] + [(f"reichardt_p{n:02d}", f"{RB}/pages/lieder-IMSLP511856_/page-{n:02d}.png", None, HELD) for n in (3, 4, 6, 7, 8, 9, 10)]

def crop_at(pred, staffs_pair, p, scale_chan):
    upper, lower = staffs_pair
    unit = (upper.average_unit_size + lower.average_unit_size) / 2
    left = min(upper.min_x, lower.min_x)
    width = int(24 * p)
    x = left + (np.arange(width) / p - 10) * unit
    outer, staff, gap = int(3 * p), int(4 * p), int(10 * p)
    anchors = np.cumsum([0, outer, staff, gap, staff, outer])
    ut, ub, lt, lb = (sr._line_at(upper, 0, x), sr._line_at(upper, -1, x), sr._line_at(lower, 0, x), sr._line_at(lower, -1, x))
    ys = [ut - 3 * unit, ut, ub, lt, lb, lb + 3 * unit]
    rows = np.empty((anchors[-1], width))
    for i in range(5):
        a, b = anchors[i], anchors[i + 1]
        rows[a:b] = ys[i] + ((np.arange(a, b) - a) / (b - a))[:, None] * (ys[i + 1] - ys[i])
    page, scale = scale_chan
    crop = sr._remap(page, np.broadcast_to(x, rows.shape) * scale, rows * scale)
    return crop.transpose(2, 0, 1), anchors

def peak(crop, k, p, anchors):
    gap = crop[k][anchors[3] - int(10 * p) : anchors[3], :] if False else crop[k][anchors[2]:anchors[3]]
    zone = gap[:, int(7 * p): int(11 * p)]            # 3 units left to 1 unit right of the staff start (column 40 at 4 px/unit)
    return float(zone.mean(axis=0).max())

summary = {}
for name, image, sel, models in JOBS:
    if os.path.exists(f"{D}/{name}.json") and os.environ.get("KEEP"):
        continue
    try:
        single = detect_single_staffs(image, I.CFG)
    except Exception as e:
        print(name, "FAILED", e, flush=True); continue
    staffs = sr.join_pieces_with_model(single.predictions, single.staffs)
    pairs, crops = sr.page_inputs(single.predictions, staffs)
    probs = {k: (sr.get_model(p) if p else sr.get_model()).predict(crops) for k, p in models.items()}
    unit = float(np.median([s.average_unit_size for s in staffs]))
    chans = {p: sr.page_channels(single.predictions, unit) if p == 4 else None for p in (4,)}
    # page channels at other resolutions
    def page_at(p):
        sc = min(1.0, p / unit)
        g = single.predictions.preprocessed
        if g.ndim == 3: g = cv2.cvtColor(g, cv2.COLOR_BGR2GRAY)
        layers = [255 - g, single.predictions.staff * 255, single.predictions.symbols * 255, single.predictions.stems_rest * 255, single.predictions.clefs_keys * 255]
        size = (max(1, round(g.shape[1] * sc)), max(1, round(g.shape[0] * sc)))
        sc_l = [cv2.resize(np.clip(l, 0, 255).astype(np.uint8), size, interpolation=cv2.INTER_AREA) for l in layers]
        return np.stack(sc_l, -1).astype(np.float32) / 255, sc
    pages_at = {p: page_at(p) for p in (4, 8, 12)}
    if sel is None:   # Reichardt: staff count a multiple of 3, pair n%3 == 1 is the grand staff, 0 same system, 2 separate
        if len(staffs) % 3: print(name, "staffs not a multiple of 3:", len(staffs)); continue
        sel = [n for n in range(len(pairs)) if n % 3 in (0, 1)]
    rows = []
    for n in sel:
        i, j = pairs[n]
        nat, u = I.native_margin(single.predictions, staffs[i], staffs[j])
        row = dict(n=n, pair=(i, j), native=nat, unit=u, crop=crops[n], probs={k: probs[k][n] for k in probs}, brace=I.brace_measure(crops[n]))
        row["peaks"] = {}
        for p in (4, 8, 12):
            c, anc = crop_at(single.predictions, (staffs[i], staffs[j]), p, pages_at[p])
            row["peaks"][p] = {"gray": round(peak(c, 0, p, anc), 2), "symbols": round(peak(c, 2, p, anc), 2)}
        rows.append(row)
    kind = {"schott": "grand (printed brace, no connecting line)", "working": "grand", "reichardt": ""}
    # figure in chunks of 5 rows
    for c0 in range(0, len(rows), 5):
        I.figure(rows[c0:c0 + 5], f"{D}/{name}" + (f"_{c0 // 5}" if len(rows) > 5 else "") + ".png", f"{name}  (unit {unit:.1f} px)", models)
    summary[name] = [dict(n=r["n"], pair=r["pair"], label=("grand" if (name.startswith("reichardt") and r["n"] % 3 == 1) else "same" if name.startswith("reichardt") else "grand" if name.startswith(("working",)) else "printed system"),
                          calls={k: sr.CLASSES[int(v.argmax())] for k, v in r["probs"].items()}, probs={k: np.round(v, 2).tolist() for k, v in r["probs"].items()},
                          tallest=r["brace"], peaks=r["peaks"]) for r in rows]
    json.dump(summary, open(f"{D}/summary_{os.getpid()}.json", "w"), indent=1)
    np.savez_compressed(f"{D}/{name}_crops.npz", crops=np.stack([r["crop"] for r in rows]), pairs=np.array([r["pair"] for r in rows]))
    print(name, "done", len(rows), flush=True)
json.dump(summary, open(f"{D}/summary.json", "w"), indent=1)
