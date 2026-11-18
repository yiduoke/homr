"""By-eye sheets: scan crop above the Verovio engraving of the label measures. usage: eye.py <out dir> <seed> <n> [tier=hard] [pids comma]"""
import sys, os, json, random, glob, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import render_label
from pieces import BY
BASE = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/work"
out, seed, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
tier = sys.argv[4] if len(sys.argv) > 4 else "hard"
recs = []
for f in sorted(glob.glob(f"{BASE}/export/*.json")):
    d = json.load(open(f))
    for r in d["records"]:
        if tier == "octave":
            if any(x.startswith("octave") for x in r["reasons"]): recs.append(r)
        elif tier == "q":
            if r.get("tier") is None and r.get("tokens") and any(x.startswith(("bar mismatch", "alignment ambiguous")) for x in r["reasons"]): recs.append(r)
        elif r.get("tier") == tier: recs.append(r)
random.Random(seed).shuffle(recs); recs = recs[:n]
os.makedirs(out, exist_ok=True)
W = int(os.environ.get('EYE_W', 1700)); PER = int(os.environ.get('EYE_PER', 2))
cases = []
for i, r in enumerate(recs):
    cfg = BY[r["pid"]]
    a, b = r["measures"]
    lab = f"{out}/_lab.png"
    render_label.render(cfg["asap"], a, b, lab, width=W)
    L = Image.open(lab).convert("L")
    C = Image.open(r["crop"]).convert("L"); C = C.resize((W, int(C.height * W / C.width)))
    H = C.height + L.height + 30
    im = Image.new("L", (W, H), 255); im.paste(C, (0, 0)); im.paste(L, (0, C.height + 30))
    d = ImageDraw.Draw(im); d.rectangle((0, C.height, W, C.height + 26), fill=0)
    d.text((6, C.height + 6), f"#{i} {r['name']}  {cfg['title']}  measures idx {a}-{b-1} (L={b-a})  f1={r['f1']:.2f}  groups={r['groups']}", fill=255)
    cases.append((r, im))
# two cases per sheet
for k in range(0, len(cases), PER):
    ims = [c[1] for c in cases[k:k + PER]]
    sheet = Image.new("L", (W, sum(m.height for m in ims) + 10 * len(ims)), 128)
    y = 0
    for m in ims: sheet.paste(m, (0, y)); y += m.height + 10
    sheet.save(f"{out}/sheet_{k//PER:02d}.png")
json.dump([dict(i=i, name=r["name"], pid=r["pid"]) for i, (r, _) in enumerate(cases)], open(f"{out}/cases.json", "w"), indent=1)
print(len(cases), "cases")
