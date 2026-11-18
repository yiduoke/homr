"""Detect the systems of rendered scan pages with homr (integration_wt code, released weights) and cut one crop per system
like inference (prepare_staff_image). Pairing fallback in THIS script only (no change to homr): if the staff relation model
leaves staffs of a page unmerged (missing braces) the detected single staffs are paired top-down into grand staffs.
usage: HOMR_FIXED_MARGIN=1 PYTHONPATH=integration_wt python detect_pages.py <piece dir name> [page numbers or all]
output: work/crops/<piece>/<pagefile>.json, <pagefile>_s<k>.png
"""
import os, sys, json, glob, time, traceback
import cv2, numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import crop_bars
from homr.main import ProcessingConfig, detect_single_staffs, group_staffs
from homr.system_repair import repair_systems
from homr.staff_parsing import _calculate_region, get_tr_omr_canvas_size, prepare_staff_image, _canvas_y_offset
from homr.staff_regions import StaffRegions
from homr.staff_relations import _merge_grand_staff
from homr.model import MultiStaff

BASE = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/work"
config = ProcessingConfig(enable_debug=False, enable_cache=False, write_staff_positions=False, read_staff_positions=False,
                          selected_staff=-1, transformer_use_gpu=False, segnet_use_gpu=True, coreml_encoder=False, title_detection=False)


def do_page(png, outbase):
    single = detect_single_staffs(png, config)
    debug, staffs = single.debug, single.staffs
    multi = group_staffs(single.predictions, staffs)
    multi = repair_systems(debug, multi)
    image = single.predictions.preprocessed
    mode = "model"
    n_gs = sum(1 for m in multi for s in m.staffs if s.is_grandstaff)
    flat = [s for m in multi for s in m.staffs]
    if n_gs == 0 and len(flat) >= 2 and len(flat) % 2 == 0:
        # staff model found no grand staff (missing braces): pair detected staffs top-down
        ss = sorted(flat, key=lambda s: s.min_y)
        merged = []
        for a, b in zip(ss[0::2], ss[1::2]):
            merged.append(MultiStaff([_merge_grand_staff(a, b)], [], certain=False))
        multi = merged
        mode = "paired"
    regions = StaffRegions(multi)
    to_page = single.to_input_image
    systems = []
    idx = 0
    for j, ms in enumerate(multi):
        rec = dict(system=j, n_staffs=len(ms.staffs), crops=[])
        for staff in ms.staffs:
            region = _calculate_region(staff, regions, image)
            canvas = get_tr_omr_canvas_size((int(region[3] - region[1]), int(region[2] - region[0])))
            try:
                im, st, _ = prepare_staff_image(debug, idx, staff, image, regions)
            except Exception as e:  # noqa: BLE001
                rec["crops"].append(dict(error=repr(e)[:100])); idx += 1; continue
            ch, cw = int(canvas[1]), int(canvas[0])
            y0 = _canvas_y_offset(ch)
            content = im[y0:y0 + ch, :cw]
            if content.ndim == 3:
                content = cv2.cvtColor(content, cv2.COLOR_BGR2GRAY)
            name = f"{outbase}_s{len(systems)}_{len(rec['crops'])}.png"
            cv2.imwrite(name, content)
            groups, u, ok = crop_bars.count_bars(content)
            x0, y0p = to_page((float(region[0]), float(region[1]))); x1, y1p = to_page((float(region[2]), float(region[3])))
            rec["crops"].append(dict(file=os.path.basename(name), shape=list(content.shape), unit=float(staff.average_unit_size),
                                     grandstaff=bool(staff.is_grandstaff), n_bar_groups=(len(groups) if ok else None),
                                     bar_first_x=(groups[0][0] if ok and groups else None), bar_unit=u,
                                     page_bbox=[round(x0), round(y0p), round(x1), round(y1p)]))
            idx += 1
        systems.append(rec)
    return systems, mode, n_gs


def main():
    piece = sys.argv[1]
    files = sorted(glob.glob(f"{BASE}/pages/{piece}/p-*.png"))
    sel = sys.argv[2:] 
    if sel and sel != ["all"]:
        want = {int(x) for x in sel}
        files = [f for f in files if int(os.path.basename(f)[2:-4]) in want]
    out = f"{BASE}/crops/{piece}"; os.makedirs(out, exist_ok=True)
    for png in files:
        pf = os.path.basename(png)[:-4]
        jf = f"{out}/{pf}.json"
        if os.path.exists(jf):
            continue
        t = time.time()
        try:
            systems, mode, n_gs = do_page(png, f"{out}/{pf}")
            res = dict(page=pf, page_shape=list(cv2.imread(png, 0).shape), mode=mode, n_grandstaffs=n_gs, systems=systems)
        except Exception as e:  # noqa: BLE001
            res = dict(page=pf, error=repr(e)[:300], systems=[])
        res["secs"] = round(time.time() - t, 1)
        json.dump(res, open(jf, "w"))
        print(piece, pf, res.get("mode"), [s["n_staffs"] for s in res["systems"]], res.get("error", ""), res["secs"], flush=True)


if __name__ == "__main__":
    main()
