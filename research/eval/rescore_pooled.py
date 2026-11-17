"""Pooled-staff scores (pitches counted on either staff, same bar alignment) for every saved output, no inference.
Writes out/pooled/<piece>/<tag>.json (score_notes --ignore-staff, visible notes only). usage: python rescore_pooled.py"""
import glob, json, os, subprocess
R = "/Users/yiduoke/Documents/homr/run"; T = f"{R}/out/testset"; PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"; WT = f"{R}/integration_wt"
TAGS = ["layout1", "r3B7", "r3ctrl_s7", "r3ctrl_s11", "r3cand_s7", "r3cand_s11"]
ONLY = os.environ.get("ONLY", "").split()
n = 0
for d in sorted(glob.glob(f"{T}/*/")):
    piece = os.path.basename(d.rstrip("/"))
    if ONLY and piece not in ONLY: continue
    ref = f"{d}{piece}-reference.musicxml"
    if not os.path.exists(ref): continue
    for tag in (TAGS if not piece.endswith("-rendered") else ["layout1"]):
        pred = f"{d}{piece}-{tag}.musicxml"
        if not os.path.exists(pred): continue
        out = f"{R}/out/pooled/{piece}/{tag}.json"; os.makedirs(os.path.dirname(out), exist_ok=True)
        r = subprocess.run([PY, "-m", "validation.score_notes", ref, f"{tag}={pred}", "--json", out, "--ignore-staff"], cwd=WT,
                           env={**os.environ, "PYTHONPATH": WT}, capture_output=True, text=True)
        if r.returncode: print("FAILED", piece, tag, r.stderr[-120:])
        n += 1
print("pooled scores written:", n)
