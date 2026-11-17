import sys, os, multiprocessing
from pathlib import Path
# usage: render.py <name> <dir with .mxl>   -> datasets/<name>/{rendered_scores,flat,index.txt}
from training.omr_datasets import convert_lieder as cl
from training.omr_datasets.convert_lieder import convert_xml_and_svg_file, create_musicxml_and_svg_files_from_mxl, write_index
name, src = sys.argv[1], Path(sys.argv[2])
root = Path(cl.dataset_root) / name
flat = root / "flat"; rendered = root / "rendered_scores"
def tok(p): return convert_xml_and_svg_file(p, False, str(flat))
if __name__ == "__main__":
    multiprocessing.set_start_method("spawn")
    flat.mkdir(parents=True, exist_ok=True); rendered.mkdir(parents=True, exist_ok=True)
    create_musicxml_and_svg_files_from_mxl(sorted(src.glob("*.mxl")), str(rendered))
    files = sorted(rendered.rglob("*.musicxml"))
    print("musicxml rendered:", len(files), flush=True)
    write_index(str(root / "index.txt"), files, tok)
    print("done")
