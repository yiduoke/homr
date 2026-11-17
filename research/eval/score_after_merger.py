"""Score the re-merged (padded) outputs of the three Schott Liszt scans, visible notes only, no inference.
Writes out/testset/<piece>/note-scores-<tag>_am.json (staff-sensitive) and out/pooled/<piece>/<tag>_am.json (--ignore-staff).
usage: python score_after_merger.py"""
import os, subprocess
R = "/Users/yiduoke/Documents/homr/run"; T = f"{R}/out/testset"; PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"; WT = f"{R}/integration_wt"
TAGS = ["layout1", "r3ctrl_s7", "r3ctrl_s11", "r3cand_s7", "r3cand_s11"]
for piece in ["liszt-sonata", "liszt-te-5", "liszt-te-10"]:
    ref = f"{T}/{piece}/{piece}-reference.musicxml"
    for t in TAGS:
        name = f"{t}_am"; pred = f"{T}/{piece}/{piece}-{name}.musicxml"
        if not os.path.exists(pred): continue
        for extra, out in (([], f"{T}/{piece}/note-scores-{name}.json"), (["--ignore-staff"], f"{R}/out/pooled/{piece}/{name}.json")):
            r = subprocess.run([PY, "-m", "validation.score_notes", ref, f"{name}={pred}", "--json", out, *extra], cwd=WT,
                               env={**os.environ, "PYTHONPATH": WT}, capture_output=True, text=True)
            if r.returncode: print("FAILED", piece, name, r.stderr[-200:])
print("done")
