"""Detect the staff systems of scanned pages with homr's own detection (CPU, fp16 segnet on the CPU
provider, 2 threads) and cut one crop per system exactly like inference (homr.staff_parsing.prepare_staff_image:
margins, neighbour clipping, dewarping, scaling to the transformer canvas; stored without the white padding).

usage: PYTHONPATH=/workspace/homr566 python cut_pages.py <shard file: lines 'repo piece'>
pages: /workspace/kern_check/pages/<repo>/<piece>_p<k>.png (render of the scan PDF at 200 dpi, written by
kern_check/homr_count.py). Output /workspace/run4/scans/crops/<repo>/<piece>_p<k>_s<j>.png and
/workspace/run4/scans/crops/<repo>/<piece>.json (per page the systems in page order).
homr566 is used because /workspace/homr_acc has no segnet weights; detection and cropping code of the two trees is
identical (diff of staff_detection, staff_parsing, system_repair, staff_relations, staff_dewarping, resize,
autocrop, color_adjust, model is empty).
"""
import os, sys, json, glob, time, traceback
os.environ["CUDA_VISIBLE_DEVICES"] = ""
import onnxruntime as ort

_orig = ort.InferenceSession


def _patched(path, sess_options=None, providers=None, **kw):
    if not os.path.exists(path):
        path = path.replace(".onnx", "_fp16.onnx")
    so = sess_options or ort.SessionOptions()
    so.intra_op_num_threads = 2
    so.inter_op_num_threads = 1
    return _orig(path, sess_options=so, providers=["CPUExecutionProvider"], **kw)


ort.InferenceSession = _patched
ort.get_available_providers = lambda: ["CPUExecutionProvider"]

import cv2
from homr.main import ProcessingConfig, detect_staffs_in_image
from homr.system_repair import repair_systems
from homr.staff_parsing import _calculate_region, get_tr_omr_canvas_size, prepare_staff_image, _canvas_y_offset
from homr.staff_regions import StaffRegions

PAGES = "/workspace/kern_check/pages"
OUT = "/workspace/run4/scans/crops"
config = ProcessingConfig(enable_debug=False, enable_cache=False, write_staff_positions=False,
                          read_staff_positions=False, selected_staff=-1, transformer_use_gpu=False,
                          segnet_use_gpu=True, coreml_encoder=False, title_detection=False)


def do_page(png, outbase):
    multi, image, debug, _, _, _ = detect_staffs_in_image(png, config)
    multi = repair_systems(debug, multi)
    regions = StaffRegions(multi)
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
                rec["crops"].append(dict(error=repr(e)[:100]))
                idx += 1
                continue
            ch, cw = int(canvas[1]), int(canvas[0])
            y0 = _canvas_y_offset(ch)
            content = im[y0:y0 + ch, :cw]
            name = f"{outbase}_s{len(systems)}_{len(rec['crops'])}.png"
            cv2.imwrite(name, content)
            rec["crops"].append(dict(file=os.path.basename(name), shape=list(content.shape), unit=float(staff.average_unit_size),
                                     grandstaff=bool(staff.is_grandstaff),
                                     bbox=[float(staff.min_x), float(staff.min_y), float(staff.max_x), float(staff.max_y)],
                                     region=[int(v) for v in region]))
            idx += 1
        systems.append(rec)
    return systems, list(image.shape[:2])


def main():
    for line in open(sys.argv[1]):
        repo, piece = line.split()
        os.makedirs(f"{OUT}/{repo}", exist_ok=True)
        jf = f"{OUT}/{repo}/{piece}.json"
        if os.path.exists(jf):
            continue
        pages = sorted(glob.glob(f"{PAGES}/{repo}/{piece}_p*.png"), key=lambda p: int(p.rsplit("_p", 1)[1][:-4]))
        res = dict(repo=repo, piece=piece, pages=[])
        t = time.time()
        for png in pages:
            k = int(png.rsplit("_p", 1)[1][:-4])
            try:
                systems, shape = do_page(png, f"{OUT}/{repo}/{piece}_p{k}")
                res["pages"].append(dict(page=k, shape=shape, systems=systems))
            except Exception as e:  # noqa: BLE001
                res["pages"].append(dict(page=k, error=repr(e)[:200], systems=[]))
        json.dump(res, open(jf, "w"))
        print(repo, piece, len(pages), "pages", round(time.time() - t), "s", [len(p["systems"]) for p in res["pages"]], flush=True)


if __name__ == "__main__":
    main()
