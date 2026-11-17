"""Count systems on the KernScores scans with homr's own staff detection.

Renders every page of each repo's reference-edition PDF, runs homr's segmentation, staff
detection, grouping and system repair (no transformer), and stores per page the systems
found and the staves per system. Staff positions are saved next to each PNG (homr's
.txt format) so systems can be cut later. Then compares systems per piece with the .krn
line breaks taken from step1_results.csv.

    PYTHONPATH=/workspace/homr566 python homr_count.py
"""

import csv
import glob
import json
import os
import sys
import traceback

import pypdfium2 as pdfium

ROOT = "/workspace/extra_scores/kern"
OUT = "/workspace/kern_check"
PAGES = f"{OUT}/pages"
REPOS = ["mozart-piano-sonatas", "beethoven-piano-sonatas", "chopin-mazurkas"]
DPI = 200


def ensure_weights() -> None:
    from homr import download_utils, staff_relations
    from homr.segmentation.config import segnet_path_onnx_fp16

    base_url = "https://github.com/liebharc/homr/releases/download/onnx_checkpoints/"
    for model in [segnet_path_onnx_fp16, staff_relations.model_path, staff_relations.horizontal_model_path]:
        if os.path.exists(model):
            continue
        name = os.path.basename(model).split(".")[0]
        os.makedirs(os.path.dirname(model), exist_ok=True)
        zip_path = os.path.join(os.path.dirname(model), name + ".zip")
        download_utils.download_file(base_url + name + ".zip", zip_path)
        download_utils.unzip_file(zip_path, os.path.dirname(model))
        os.remove(zip_path)


def main() -> None:
    ensure_weights()
    from homr.main import ProcessingConfig, detect_staffs_in_image
    from homr.staff_position_save_load import save_staff_positions
    from homr.system_repair import repair_systems

    config = ProcessingConfig(
        enable_debug=False, enable_cache=False, write_staff_positions=False,
        read_staff_positions=False, selected_staff=-1, transformer_use_gpu=True,
        segnet_use_gpu=True, coreml_encoder=False, title_detection=False,
    )
    krn = {(r["repo"], r["piece"]): r for r in csv.DictReader(open(f"{OUT}/step1_results.csv"))}
    out_json = f"{OUT}/homr_count.json"
    results = json.load(open(out_json)) if os.path.exists(out_json) else {}
    for repo in REPOS:
        for pdf in sorted(glob.glob(f"{ROOT}/{repo}/reference-edition/*.pdf")):
            piece = os.path.basename(pdf)[:-4]
            key = f"{repo}/{piece}"
            if key in results:
                continue
            folder = f"{PAGES}/{repo}"
            os.makedirs(folder, exist_ok=True)
            pages = []
            doc = pdfium.PdfDocument(pdf)
            for i in range(len(doc)):
                png = f"{folder}/{piece}_p{i}.png"
                if not os.path.exists(png):
                    doc[i].render(scale=DPI / 72).to_pil().convert("L").save(png)
                try:
                    staffs, image, debug, _, _, _ = detect_staffs_in_image(png, config)
                    staffs = repair_systems(debug, staffs)
                    save_staff_positions(staffs, image.shape, png[:-4] + ".txt")
                    pages.append([len(s.staffs) for s in staffs])
                except Exception as e:  # noqa: BLE001
                    print("ERROR", png, repr(e), file=sys.stderr)
                    traceback.print_exc()
                    pages.append(None)
            k = krn.get((repo, piece), {})
            homr_sys = sum(len(p) for p in pages if p)
            krn_sys = int(k["krn_sys"]) if k.get("krn_sys") not in (None, "", "0") and k.get("hasLB") == "True" else None
            results[key] = {
                "pages": pages,
                "homr_sys": homr_sys,
                "krn_sys": krn_sys,
                "match": krn_sys is not None and homr_sys == krn_sys,
                "step1_status": k.get("status"),
            }
            print(key, "homr", homr_sys, "krn", krn_sys, [len(p) if p else None for p in pages], flush=True)
            json.dump(results, open(out_json, "w"))
    summary = {}
    for key, r in results.items():
        repo = key.split("/")[0]
        s = summary.setdefault(repo, {"pieces": 0, "match": 0, "mismatch": 0, "no_markers": 0})
        s["pieces"] += 1
        if r["krn_sys"] is None:
            s["no_markers"] += 1
        elif r["match"]:
            s["match"] += 1
        else:
            s["mismatch"] += 1
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
