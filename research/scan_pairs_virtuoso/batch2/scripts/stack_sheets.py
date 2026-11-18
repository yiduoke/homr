"""stack_sheets.py <outdir> <per image> <names...>: eye-review sheets (sheet2.make) stacked N per image"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sheet2
from PIL import Image
out, per = sys.argv[1], int(sys.argv[2]); names = open(sys.argv[3][1:]).read().split() if sys.argv[3].startswith('@') else sys.argv[3:]
os.makedirs(out, exist_ok=True)
W = int(os.environ.get('SHEET_W', 1200))
for k in range(0, len(names), per):
    ims = []
    for n in names[k:k + per]:
        tmp = f"{out}/_t.png"; sheet2.make(n, tmp, W=W); ims.append(Image.open(tmp).convert('L'))
    H = sum(i.height for i in ims) + 8 * len(ims)
    s = Image.new('L', (W, H), 128); y = 0
    for i in ims: s.paste(i, (0, y)); y += i.height + 8
    s.save(f"{out}/{k//per:02d}_{names[k]}.png")
os.path.exists(f"{out}/_t.png") and os.remove(f"{out}/_t.png")
