"""contact sheets of rendered pages: contact.py <pdf stem> <first> <last> <out.png> [cols]"""
import sys, glob, os
from PIL import Image, ImageDraw
stem, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 6
base = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2/work/pages/" + stem
tw = 330
ims = []
for p in range(a, b + 1):
    f = f"{base}/p-{p:02d}.png"
    if not os.path.exists(f): continue
    im = Image.open(f).convert("L"); im = im.resize((tw, int(im.height * tw / im.width)))
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 44, 22), fill=255); d.text((4, 4), f"p{p}", fill=0)
    ims.append(im)
rows = (len(ims) + cols - 1) // cols; th = max(i.height for i in ims)
sheet = Image.new("L", (cols * tw, rows * th), 255)
for k, im in enumerate(ims): sheet.paste(im, ((k % cols) * tw, (k // cols) * th))
sheet.save(out)
