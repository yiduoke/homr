"""crop.py piece page x0 y0 x1 y1 out [scale] : crop a region of a scan page (pixel coordinates of eval_run1/pages/<piece>/page-NN.png) and upscale."""
import sys
from PIL import Image
piece, page, x0, y0, x1, y1, out = sys.argv[1], int(sys.argv[2]), *map(int, sys.argv[3:7]), sys.argv[7]
sc = float(sys.argv[8]) if len(sys.argv) > 8 else 1.5
im = Image.open(f"/Users/yiduoke/Documents/homr/run/eval_run1/pages/{piece}/page-{page:02d}.png").convert("RGB").crop((x0, y0, x1, y1))
im = im.resize((int(im.width * sc), int(im.height * sc)), Image.LANCZOS); im.save(out)
