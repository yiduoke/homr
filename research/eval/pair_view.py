"""D28: page image with the pair calls of the shipped model and rb2/rb3 drawn between the staves (staff numbers from the top).
usage: python pair_view.py PIECE PAGE   -> brace_models/eye/PIECE_PAGE.png (left margin: three columns of marks, shipped | rb2 | rb3;
green bar = grand staff, orange bar = same system, nothing = separate)"""
import json, sys, os
from PIL import Image, ImageDraw
piece, page = sys.argv[1:3]
E = "/Users/yiduoke/Documents/homr/run/eval_run1"
d = json.load(open(f"{E}/brace_models/replay_all.json"))[piece][page]
im = Image.open(f"{E}/pages/{piece}/{page}.png").convert("RGB")
s = im.width / 1920.0
dr = ImageDraw.Draw(im)
col = {"grand staff": (0, 170, 0), "same system": (255, 140, 0), "separate": None}
for k, name in enumerate(("shipped", "rb2", "rb3")):
    m = d["models"][name]
    x = 6 + 14 * k
    for (i, j), c in zip(m["pairs"], m["calls"]):
        if col[c] is None:
            continue
        y0 = d["boxes"][i][1] * s
        y1 = d["boxes"][j][3] * s
        dr.rectangle([x, y0, x + 9, y1], fill=col[c])
for i, b in enumerate(d["boxes"]):
    dr.text((52, b[1] * s - 10), str(i), fill=(255, 0, 0))
    dr.line([(52, b[1] * s), (im.width, b[1] * s)], fill=(255, 0, 0, 80), width=1) if False else None
os.makedirs(f"{E}/brace_models/eye", exist_ok=True)
im.save(f"{E}/brace_models/eye/{piece}_{page}.png")
print(f"{piece} {page}: shipped {d['models']['shipped']['calls']} rb2 {d['models']['rb2']['calls']} rb3 {d['models']['rb3']['calls']}")
