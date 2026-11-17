"""Engrave each test piece's reference MusicXML with Verovio (square pages) into eval_run1/pages/<piece>-rendered/page-NN.png and
copy the reference to out/testset/<piece>-rendered/ so the same evaluation pipeline can score a RENDERED version of the same music."""
import glob, os, shutil, subprocess, sys, tempfile
import verovio
verovio.enableLog(verovio.LOG_WARNING)
from PIL import Image
R = "/Users/yiduoke/Documents/homr/run/"
pieces = [os.path.basename(os.path.dirname(f)) for f in sorted(glob.glob(R + "out/testset/*/*-reference.musicxml")) if not os.path.dirname(f).endswith("-rendered")]
skip = set(); ONLY = os.environ.get("ONLY")   # ONLY=<piece> renders just that piece (Petrushka has three staves per system)
import re
LOGRE = re.compile(r"ratio smaller than 0\.8: ([0-9.]+)")
PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"
def render(ref, scale):
    tmp = tempfile.mkdtemp()
    r = subprocess.run([PY, R + "render_one_svg.py", ref, str(scale), tmp], capture_output=True, text=True)
    ratios = [float(x) for x in LOGRE.findall(r.stderr + r.stdout)]
    return sorted(glob.glob(tmp + "/p*.svg")), ratios
report = {}
for p in pieces:
    if p in skip or (ONLY and p != ONLY): continue
    ref = f"{R}out/testset/{p}/{p}-reference.musicxml"; out = f"{R}eval_run1/pages/{p}-rendered"
    if os.path.isdir(out): shutil.rmtree(out)
    os.makedirs(out)
    scale = 30
    while True:
        files, ratios = render(ref, scale)
        if not ratios or scale <= 22: break
        scale -= 2
    subprocess.run(["qlmanage", "-t", "-s", "1754", "-o", os.path.dirname(files[0]), *files], check=True, capture_output=True)
    for i, f in enumerate(files, 1):
        Image.open(f + ".png").convert("L").save(f"{out}/page-{i:02d}.png")
    d = f"{R}out/testset/{p}-rendered"; os.makedirs(d, exist_ok=True)
    shutil.copy(ref, f"{d}/{p}-rendered-reference.musicxml")
    report[p] = (scale, len(files), len(ratios), min(ratios) if ratios else None)
    print(p, "scale", scale, "pages", len(files), "compressed systems", len(ratios), "worst", min(ratios) if ratios else "-", flush=True)
import json
_rp = R + "eval_run1/render_testset_report.json"
_old = json.load(open(_rp)) if os.path.exists(_rp) else {}
_old.update(report); json.dump(_old, open(_rp, "w"), indent=1)
