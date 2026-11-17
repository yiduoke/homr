"""Montages for the by-eye check: crop on top, compact label below (clef/key/time, then per staff the notes of every
measure). usage (laptop or box): python eye_montage.py <sample.json> <outdir> [per_image=3]
sample.json: list of {"id", "image", "tokens"}  (paths readable on the machine that runs this)."""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont


def summary(tokens_text):
    head, rh, lh = [], [], []
    cur = {"upper": [], "lower": []}
    out = {"upper": [], "lower": []}
    meas = 1
    for line in tokens_text.split("\n"):
        parts = [p.strip().split(" ") for p in line.split("&") if p.strip()]
        for f in parts:
            if len(f) != 6:
                continue
            r, pitch, lift, art, slur, pos = f
            p0 = pos.rstrip("2")
            if r.startswith(("clef", "keySignature", "timeSignature")):
                head.append(r.replace("clef_", "").replace("keySignature_", "k").replace("timeSignature_", "t") + ("/" + p0[0] if r.startswith("clef") else ""))
            elif r.startswith("note"):
                cur[p0].append(r.split("_")[1] + ":" + pitch + (lift if lift not in ("_",) else ""))
            elif r.startswith("rest"):
                cur[p0].append("r" + r.split("_")[1])
            elif "barline" in r or r.startswith("repeat"):
                for k in cur:
                    out[k].append(" ".join(cur[k]))
                    cur[k] = []
    for k in cur:
        if cur[k]:
            out[k].append(" ".join(cur[k]))
    return " ".join(head), out


def main():
    sample = json.load(open(sys.argv[1]))
    outdir = sys.argv[2]
    per = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    os.makedirs(outdir, exist_ok=True)
    font = ImageFont.load_default(size=13)
    W = 1300
    for gi in range(0, len(sample), per):
        group = sample[gi:gi + per]
        tiles = []
        for s in group:
            im = Image.open(s["image"]).convert("L")
            head, out = summary(open(s["tokens"]).read())
            lines = [f"{s['id']}   [{head}]"]
            for k, name in (("upper", "RH"), ("lower", "LH")):
                lines.append(f"{name}: " + " | ".join(out[k]))
            # wrap long lines
            wrapped = []
            for l in lines:
                while len(l) > 190:
                    wrapped.append(l[:190]); l = "      " + l[190:]
                wrapped.append(l)
            h = im.height + 16 * len(wrapped) + 14
            t = Image.new("RGB", (W, h), "white")
            t.paste(im, (0, 0))
            d = ImageDraw.Draw(t)
            for i, l in enumerate(wrapped):
                d.text((4, im.height + 4 + 16 * i), l, fill=(160, 0, 0) if i == 0 else (0, 0, 0), font=font)
            tiles.append(t)
        H = sum(t.height for t in tiles) + 6 * len(tiles)
        m = Image.new("RGB", (W, H), (200, 200, 255))
        y = 0
        for t in tiles:
            m.paste(t, (0, y)); y += t.height + 6
        m.save(f"{outdir}/m{gi // per:03d}.png")


if __name__ == "__main__":
    main()
