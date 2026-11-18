"""view.py piece bar_lo bar_hi out.png [tag]: crop of the scan for pred bars lo..hi (all systems that contain them, band with 100 px above for brackets); falls back to the full page.
Also prints the page, system positions and the shift events of the page XML in that range."""
import sys
from PIL import Image
from refs_lib import R, page_info
from locate import locate
piece, lo, hi, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
loc = [locate(piece, b) for b in range(lo, hi + 1)]
pages = sorted({l["page"] for l in loc})
tiles = []
for pg in pages:
    ls = [l for l in loc if l["page"] == pg]
    im = Image.open(f"{R}/eval_run1/pages/{piece}/page-{pg:02d}.png").convert("RGB")
    bands = sorted({l["band"] for l in ls if l["band"]})
    sysn = sorted({l["system"] for l in ls})
    print("page", pg, "systems", sysn, "bars in system", [(l["page_bar"], l["pos_in_system"], l["nsys_bars"]) for l in ls][:6], "bands" if bands else "no bands")
    if len(bands) == len(sysn):
        y0, y1 = int(min(b[0] for b in bands)) - 110, int(max(b[1] for b in bands)) + 40
        tiles.append(im.crop((0, max(0, y0), im.width, min(im.height, y1))))
    else:
        tiles.append(im.resize((im.width * 6 // 10, im.height * 6 // 10)))
W = max(t.width for t in tiles); H = sum(t.height for t in tiles)
canvas = Image.new("RGB", (W, H), "white"); y = 0
for t in tiles: canvas.paste(t, (0, y)); y += t.height
canvas.save(out)
for pg, off, n, parts, ev in page_info(piece):
    if pg in pages: print("page-xml events p%d (offset %d):" % (pg, off), [(e[1] + off, e[2]) for e in ev])
