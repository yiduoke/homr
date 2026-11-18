import sys, glob, os
from PIL import Image, ImageDraw
# usage: montage2.py piece out.png "17,18,19" cols [frac]
piece, out, pl, cols = sys.argv[1], sys.argv[2], [int(x) for x in sys.argv[3].split(",")], int(sys.argv[4])
frac = float(sys.argv[5]) if len(sys.argv) > 5 else 0.3
W = 700; tiles = []
for n in pl:
    f = [x for x in glob.glob(f"work/pages/{piece}/p-*.png") if int(os.path.basename(x)[2:-4]) == n][0]
    im = Image.open(f).convert("L"); h = int(im.height * W / im.width); im = im.resize((W, h)).crop((0, 0, W, int(h * frac)))
    ImageDraw.Draw(im).rectangle((0, 0, 70, 20), fill=0); ImageDraw.Draw(im).text((4, 4), f"p{n}", fill=255); tiles.append(im)
H = max(t.height for t in tiles); rows = (len(tiles) + cols - 1) // cols
M = Image.new("L", (cols * W, rows * H), 255)
for i, t in enumerate(tiles): M.paste(t, ((i % cols) * W, (i // cols) * H))
M.save(out)
