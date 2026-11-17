"""Montages of staffs flagged by verify_run3.py (sounding alteration from the new printed signs differs from the
run-1 lift). usage: view_flagged.py <set> <n=6> <seed=3>"""
import json, os, random, sys, textwrap
from PIL import Image, ImageDraw, ImageFont
S = "/workspace/run3/"
name = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 6; seed = int(sys.argv[3]) if len(sys.argv) > 3 else 3
flag = json.load(open(f"{S}status/verify_{name}_first.json"))
random.Random(seed).shuffle(flag)
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
os.makedirs(f"{S}view/flag_{name}", exist_ok=True)
for v in range(n // 2):
    blocks = []
    for t, i, k in flag[v * 2:(v + 1) * 2]:
        newp = S + "tokens/" + t[len("/workspace/"):]
        png = t.replace("/datasets_meter/", "/datasets/")[:-7] + ".png"
        new = open(newp).read().split("\n"); old = open(t).read().split("\n")
        meas = 1 + sum(1 for l in new[:i] if l.startswith("barline") or l.startswith("repeat"))
        keysig = [l.split(" ")[0] for l in new[:i + 1] if l.startswith("keySignature")]
        im = Image.open(png).convert("RGB")
        txt = [f"{os.path.basename(png)} | FLAG in bar {meas}: {k} | key {keysig[-1] if keysig else '?'}",
               "old: " + old[i][:140], "new: " + new[i][:140]]
        if i > 0: txt += ["old prev: " + old[i - 1][:132], "new prev: " + new[i - 1][:132]]
        th = 20 * len(txt) + 8
        c = Image.new("RGB", (max(im.width, 1290), im.height + th), "white")
        c.paste(im, (0, 0)); d = ImageDraw.Draw(c)
        for j, l in enumerate(txt):
            d.text((6, im.height + 4 + 20 * j), l, fill=(160, 0, 0) if j == 0 else (0, 0, 0), font=font)
        blocks.append(c)
    W = max(b.width for b in blocks); H = sum(b.height for b in blocks) + 6 * len(blocks)
    m = Image.new("RGB", (W, H), (200, 200, 200)); y = 0
    for b in blocks:
        m.paste(b, (0, y)); y += b.height + 6
    m.save(f"{S}view/flag_{name}/f{v:02d}.png")
