"""Montages for the by-eye check: staff image, then meters/bars/key/clefs of its labels and the automatic bar check.
usage: verify_montage.py <outdir> <n per montage> <seed> <filter key=value ...> -- staffs.jsonl [...]    plan files via PLAN env (comma)
"""
import json, os, random, re, sys, textwrap
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import tokencheck as tc

outdir, per, seed = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
sep = sys.argv.index("--")
filt = dict(a.split("=") for a in sys.argv[4:sep])
files = sys.argv[sep + 1:]
plans = {}
for p in os.environ["PLAN"].split(","):
    for ln in open(p):
        s = json.loads(ln); plans[s["wid"]] = s
recs = [json.loads(l) for f in files for l in open(f)]
infos = tc.staff_infos(recs, plans)
def keep(d):
    for k, v in filt.items():
        if str(d.get(k)) != v:
            return False
    return True
infos = [d for d in infos if keep(d)]
rng = random.Random(seed)
rng.shuffle(infos)
N = int(os.environ.get("NSAMPLE", "80"))
sample = infos[:N]
os.makedirs(outdir, exist_ok=True)
json.dump(sample, open(f"{outdir}/sample.json", "w"))
font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
def head(d):
    t = open(d["tokens"]).read()
    keys = re.findall(r"keySignature_(-?\d+)", t)
    clefs = re.findall(r"clef_(\w+)", t)
    ms = d["start"] or "-"
    mids = " ".join(f"b{b+1}:{m}" for b, m in d["mids"])
    return (f"{os.path.basename(d['image'])} {d['renderer']}/{d['font']}/{d['tsclass']}{d['tsscale']} kind={d['kind']} | start={ms} mid=[{mids}] "
            f"bars={d['nbars']} key={','.join(keys)} | barcheck {d['checked']-d['bad']}/{d['checked']} off_ok={d['ok_offset']} bad={d['bad_list'][:3]}")
for i in range(0, len(sample), per):
    blocks = []
    for d in sample[i:i + per]:
        im = Image.open(d["image"]).convert("RGB")
        w = 1100
        im = im.resize((w, max(20, int(im.height * w / im.width))))
        lines = textwrap.wrap(head(d), 150)
        th = 17 * len(lines) + 4
        c = Image.new("RGB", (w, im.height + th), "white")
        dr = ImageDraw.Draw(c)
        for j, ln in enumerate(lines):
            dr.text((3, 2 + 17 * j), ln, fill=(150, 0, 0), font=font)
        c.paste(im, (0, th))
        blocks.append(c)
    H = sum(b.height for b in blocks) + 4 * len(blocks)
    m = Image.new("RGB", (1100, H), "white")
    y = 0
    for b in blocks:
        m.paste(b, (0, y)); y += b.height + 4
    m.save(f"{outdir}/m{i // per:02d}.png")
print("montages", (len(sample) + per - 1) // per, "staffs", len(sample))
