"""Re-export MuseScore MusicXML for the ASAP and Scriabin source .mxl files (the original rendered_scores
were deleted). Same MuseScore, same per-piece font style as the image rendering, only musicxml, written to
/workspace/run3/ms_export/<set>/ (datasets/ is not touched).
usage: export_ms.py <set: asap|kern_scriabin> [limit]
"""
import os, re, shutil, sys
from pathlib import Path
sys.path.insert(0, "/workspace/homr566")
from training.omr_datasets import convert_lieder as cl

name = sys.argv[1]
limit = int(sys.argv[2]) if len(sys.argv) > 2 else 0
SRC = {"asap": "/workspace/r6_extra/asap_mxl", "kern_scriabin": "/workspace/r6_extra/kern_mxl"}[name]
dest = Path(f"/workspace/run3/ms_export/{name}")
dest.mkdir(parents=True, exist_ok=True)
stems = set()
for ln in open(f"/workspace/homr566/datasets_meter/{name}/index_excl_v2.txt"):
    t = ln.strip().split(",")[1]
    m = re.match(r"^(.*)-vrv-(\d+)-(\d+)\.tokens$", os.path.basename(t)) or re.match(
        r"^(.*)-(\d+)-(\d+)\.tokens$", os.path.basename(t))
    stems.add(m[1])
stems = sorted(stems)
if limit:
    stems = stems[:limit]
print(name, "stems", len(stems), flush=True)
for s in stems:
    shutil.copyfile(f"{SRC}/{s}.mxl", dest / f"{s}.mxl")
cl._ensure_music_font_style_files()
jobs = []
for s in stems:
    f = str(dest / f"{s}.mxl")
    style = cl._music_font_style_file(cl._music_font_for_file(f))
    jobs.extend(cl.create_formats(f, ["musicxml"], style, ".mxl"))
print("jobs", len(jobs), flush=True)
cl._run_musescore_jobs(os.path.join(cl.dataset_root, "MuseScore"), jobs)
print("done", len(list(dest.glob("*.musicxml"))), flush=True)
