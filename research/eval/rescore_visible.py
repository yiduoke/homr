"""Rescore every existing output with the visible-note scorer, no inference.
Originals are copied once to out/scores_before_hidden_fix/<piece>/ and never overwritten.
usage: python rescore_visible.py [--only PIECE ...]   (run from anywhere)"""
import glob, json, os, shutil, subprocess, sys
R = "/Users/yiduoke/Documents/homr/run"; T = f"{R}/out/testset"; PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"
WT = f"{R}/integration_wt"; OLD = f"{R}/out/scores_before_hidden_fix"
only = sys.argv[sys.argv.index("--only") + 1:] if "--only" in sys.argv else None
bad = ("ignorestaff", "before", "hidden")
done = failed = 0
for f in sorted(glob.glob(f"{T}/*/note-scores-*.json")):
    d = os.path.dirname(f); piece = os.path.basename(d); tag = os.path.basename(f)[len("note-scores-"):-5]
    if any(b in tag for b in bad) or (only and piece not in only): continue
    os.makedirs(f"{OLD}/{piece}", exist_ok=True)
    keep = f"{OLD}/{piece}/{os.path.basename(f)}"
    if not os.path.exists(keep): shutil.copy(f, keep)
    names = [r["name"] for r in json.load(open(keep))["results"]]
    base = piece[:-9] if piece.endswith("-rendered") else piece
    pre = f"{piece}-"
    ref = f"{d}/{pre}reference.musicxml"
    models = []
    for n in names:
        p = f"{d}/{pre}{n}.musicxml"
        if os.path.exists(p): models.append(f"{n}={p}")
    if not os.path.exists(ref) or not models: print("skip", piece, tag, "(missing files)"); failed += 1; continue
    extra = ["--ignore-staff"] if base == "stravinsky-petrushka" else []
    r = subprocess.run([PY, "-m", "validation.score_notes", ref, *models, "--json", f + ".new", *extra], cwd=WT,
                       env={**os.environ, "PYTHONPATH": WT}, capture_output=True, text=True)
    if r.returncode == 0 and os.path.exists(f + ".new"): os.replace(f + ".new", f); done += 1
    else: print("FAILED", piece, tag, r.stderr[-200:]); failed += 1
print("rescored", done, "failed/skipped", failed)
