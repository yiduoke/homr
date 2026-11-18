"""usage: python pair_montage.py OUT.png piece:page [piece:page ...]  -> left 42 % of the annotated pages (pair_view.py), side by side."""
import subprocess, sys
from PIL import Image
out, items = sys.argv[1], sys.argv[2:]
ims = []
for it in items:
    piece, page = it.split(":")
    subprocess.run([sys.executable, "pair_view.py", piece, page], capture_output=True, cwd="/Users/yiduoke/Documents/homr/run/eval_run1")
    im = Image.open(f"/Users/yiduoke/Documents/homr/run/eval_run1/brace_models/eye/{piece}_{page}.png")
    im = im.crop((0, 0, int(im.width * 0.42), im.height))
    im = im.resize((int(im.width * 0.62), int(im.height * 0.62)))
    ims.append(im)
W = sum(i.width for i in ims) + 10 * (len(ims) - 1)
H = max(i.height for i in ims)
m = Image.new("RGB", (W, H), "white")
x = 0
for i in ims:
    m.paste(i, (x, 0)); x += i.width + 10
m.save(out)
print(out, m.size)
