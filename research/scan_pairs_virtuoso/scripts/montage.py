import sys, glob, os
from PIL import Image, ImageDraw
# usage: montage.py piece out.png first last [cols] [mode: top|full]
piece, out, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
mode = sys.argv[6] if len(sys.argv) > 6 else "top"
files = sorted(glob.glob(f"work/pages/{piece}/p-*.png"))
W = 520
tiles = []
for f in files:
    n = int(os.path.basename(f)[2:-4])
    if not (a <= n <= b): continue
    im = Image.open(f).convert("L")
    h = int(im.height * W / im.width); im = im.resize((W, h))
    if mode == "top": im = im.crop((0, 0, W, int(h * 0.30)))
    d = ImageDraw.Draw(im); d.rectangle((0, 0, 60, 18), fill=0); d.text((3, 3), f"p{n}", fill=255)
    tiles.append(im)
H = max(t.height for t in tiles)
rows = (len(tiles) + cols - 1) // cols
M = Image.new("L", (cols * W, rows * H), 255)
for i, t in enumerate(tiles): M.paste(t, ((i % cols) * W, (i // cols) * H))
M.save(out)
print(M.size)
