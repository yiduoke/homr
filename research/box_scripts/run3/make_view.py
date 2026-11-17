"""Sample staffs of a set, write montages (3 staffs per picture: image, then key/time/accidentals of the new tokens).
usage: make_view.py <set> [n_sample=150] [n_view=45] [seed]
Sample: random staffs among those relabeled (status ok), seed fixed; list in lists/verify_sample_<set>.txt.
"""
import os, random, sys, textwrap
from PIL import Image, ImageDraw, ImageFont

S = "/workspace/run3/"
name = sys.argv[1]
n_sample = int(sys.argv[2]) if len(sys.argv) > 2 else 150
n_view = int(sys.argv[3]) if len(sys.argv) > 3 else 45
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 11
rows = [l.strip().split(",") for l in open(f"{S}lists/selected_{name}.txt")]
rows = [(p, t) for p, t in rows if os.path.exists(S + "tokens/" + t[len("/workspace/"):])]
rng = random.Random(seed)
sample = rng.sample(rows, n_sample)
open(f"{S}lists/verify_sample_{name}.txt", "w").write("".join(f"{p},{S}tokens/{t[len('/workspace/'):]}\n" for p, t in sample))
os.makedirs(f"{S}view/{name}", exist_ok=True)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 15)
except Exception:
    font = ImageFont.load_default()


def summary(tok):
    lines = open(tok).read().strip().split("\n")
    meas = 1
    out, head, notes = [], [], 0
    for ln in lines:
        for part in ln.split("&"):
            f = part.strip().split(" ")
            if f[0].startswith(("keySignature", "timeSignature", "clef")) or f[0].startswith("octaveShift"):
                head.append(f"m{meas}:{f[0]}")
            elif f[0].startswith("note") and len(f) == 6:
                notes += 1
                if f[2] != "_":
                    out.append(f"m{meas}:{f[1]}{f[2]}")
            elif f[0] == "barline" or f[0].startswith("repeat"):
                meas += 1
    return " ".join(head), " ".join(out), notes, meas


for v in range(n_view // 3):
    group = sample[v * 3:(v + 1) * 3]
    blocks = []
    for p, t in group:
        im = Image.open(p).convert("RGB")
        head, signs, notes, meas = summary(S + "tokens/" + t[len("/workspace/"):])
        txt = f"{os.path.basename(p)} | notes {notes} bars {meas}\n{head}\nPRINTED SIGNS: {signs or '(none)'}"
        wrapped = []
        for ln in txt.split("\n"):
            wrapped += textwrap.wrap(ln, 140) or [""]
        th = 20 * len(wrapped) + 8
        canvas = Image.new("RGB", (max(im.width, 1290), im.height + th), "white")
        canvas.paste(im, (0, 0))
        d = ImageDraw.Draw(canvas)
        for i, ln in enumerate(wrapped):
            d.text((6, im.height + 4 + 20 * i), ln, fill=(160, 0, 0) if ln.startswith("PRINTED") else (0, 0, 0), font=font)
        blocks.append(canvas)
    H = sum(b.height for b in blocks) + 6 * len(blocks)
    W = max(b.width for b in blocks)
    m = Image.new("RGB", (W, H), (200, 200, 200))
    y = 0
    for b in blocks:
        m.paste(b, (0, y)); y += b.height + 6
    m.save(f"{S}view/{name}/m{v:02d}.png")
print(name, "sample", len(sample), "montages", n_view // 3)
