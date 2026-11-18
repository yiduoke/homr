"""Side-by-side sheets: scan crop (top) and its rendered twin (bottom), both at stored size (the twin as written by twin_render.py).
usage: twin_compare.py OUT_DIR TWIN_DIR NAME [NAME ...]   (or --random N --seed S)"""
import sys, os, glob, random, csv
from PIL import Image, ImageDraw
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
out, twdir = sys.argv[1], sys.argv[2]; rest = sys.argv[3:]
os.makedirs(out, exist_ok=True)
if rest and rest[0] == "--random":
    n, seed = int(rest[1]), int(rest[3])
    names = sorted(os.path.basename(p)[:-4] for p in glob.glob(f"{twdir}/*/*.png"))
    random.Random(seed).shuffle(names); names = names[:n]
else:
    names = rest
per = 3; W = 1300
for k in range(0, len(names), per):
    ims = []
    for nm in names[k:k + per]:
        pid = nm.split("_")[0]
        a = Image.open(f"{ROOT}/images/{pid}/{nm}.png").convert("L"); b = Image.open(f"{twdir}/{pid}/{nm}.png").convert("L")
        h = a.height + b.height + 36
        im = Image.new("L", (W, h), 255); im.paste(a, (0, 14)); im.paste(b, (0, a.height + 30))
        d = ImageDraw.Draw(im); d.text((2, 0), f"{nm}  SCAN {a.size}", fill=0); d.text((2, a.height + 16), f"TWIN {b.size}", fill=0)
        d.line((0, a.height + 14, W, a.height + 14), fill=128)
        ims.append(im)
    sheet = Image.new("L", (W, sum(i.height for i in ims) + 8 * len(ims)), 160)
    y = 0
    for i in ims: sheet.paste(i, (0, y)); y += i.height + 8
    sheet.save(f"{out}/sheet_{k // per:02d}.png")
print(len(names), "crops,", (len(names) + per - 1) // per, "sheets")
