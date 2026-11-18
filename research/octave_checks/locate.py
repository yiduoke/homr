"""locate.py: map a global (prediction) bar index to page / system / bar-in-system, and find system bands (y ranges) on the scan by staff-line projection.
usage: locate.py piece bar [bar2]  -> page, system number, bars of that system, y band (original pixels)."""
import sys, re, glob
import numpy as np
from PIL import Image
from refs_lib import R, page_info

def systems_of_page(piece, page, tag="layout1"):
    s = open(f"{R}/eval_run1/testset/{tag}/{piece}/page-xml/page-{page:02d}.musicxml", encoding="utf-8").read()
    ms = re.findall(r'<measure number="(\d+)"(.*?)</measure>', s, flags=re.S)
    starts = [int(n) for n, b in ms if "new-system" in b]
    if not starts or starts[0] != 1: starts = [1] + starts
    return starts, len(ms)

def staff_bands(piece, page, tag="layout1"):
    """Staves from the staff-line projection of the scan (rows dark over a good part of the middle width); band is only returned if 2 staves per system are found."""
    im = np.array(Image.open(f"{R}/eval_run1/pages/{piece}/page-{page:02d}.png").convert("L")) < 128
    h, w = im.shape
    dark = im[:, w // 8: w - w // 8].mean(axis=1)
    lines = []
    for r in np.where(dark > 0.30)[0]:
        if lines and r - lines[-1][-1] <= 2: lines[-1].append(r)
        else: lines.append([r])
    ys = [np.mean(l) for l in lines]
    staves, cur = [], []
    for y in ys:
        if cur and y - cur[-1] > 40: staves.append(cur); cur = []
        cur.append(y)
    if cur: staves.append(cur)
    return [(s_[0], s_[-1]) for s_ in staves if len(s_) >= 4], h, w

def locate(piece, bar):
    for pg, off, n, parts, ev in page_info(piece):
        if off < bar <= off + n:
            b = bar - off
            starts, nb = systems_of_page(piece, pg)
            k = max(i for i, s in enumerate(starts) if s <= b)
            last = (starts[k + 1] - 1) if k + 1 < len(starts) else nb
            staves, h, w = staff_bands(piece, pg)
            band = None
            if len(staves) == 2 * len(starts):
                band = (staves[2 * k][0], staves[2 * k + 1][1])
            return dict(page=pg, page_bar=b, system=k + 1, nsystems=len(starts), sys_bars=(starts[k], last), pos_in_system=b - starts[k] + 1,
                        nsys_bars=last - starts[k] + 1, band=band, n_staves=len(staves), size=(w, h))
    return None

if __name__ == "__main__":
    for b in map(int, sys.argv[2:]):
        print(b, locate(sys.argv[1], b))
