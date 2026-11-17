"""Run homr.main once on all page images of a piece, keeping the per-page MusicXML.

homr.main joins several images with relieur and deletes the per-page files. This wrapper
copies them to PAGE_XML_DIR just before the join (nothing else is changed); the page
joiner of the evaluation (run/merge_pages.py) then works on those files.

    PYTHONPATH=<worktree> HOMR_FIXED_MARGIN=1 python run_homr.py PAGE_XML_DIR img1.png img2.png ...
"""
import os
import shutil
import sys

import homr.main as hm

out_dir = sys.argv[1]
orig = hm.process_concat


def keep_pages_then_concat(xml_paths, *a, **k):
    os.makedirs(out_dir, exist_ok=True)
    for p in xml_paths:
        shutil.copy(p, os.path.join(out_dir, os.path.basename(p)))
    return orig(xml_paths, *a, **k)


hm.process_concat = keep_pages_then_concat
sys.argv = ["homr"] + sys.argv[2:]
hm.main()
