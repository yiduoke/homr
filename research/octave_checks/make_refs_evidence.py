"""Side-by-side evidence for the octave-bracket reference check (D33): scan crop, reference engraving (Verovio, reference as stored), released-model engraving (layout1).
Writes refs/<id>.png. Reference bars and model bars are given by position (1-based index in the file), the scan boxes are page pixel boxes (page, x0, y0, x1, y1) or 'auto' (system band from locate.py)."""
import sys, os
from PIL import Image, ImageDraw, ImageFont
from refs_lib import *
from locate import locate
from crop_render2 import render
import warnings
OUT = f"{R}/octave_checks/refs"; os.makedirs(OUT, exist_ok=True)
W = 1500

D = [  # id, piece, ref bars, pred bars, scan boxes, verdict text
 ("H1_hammerklavier_b246-249", "beethoven-hammerklavier-4", (246, 249), (246, 249), [(41, 60, 90, 1227, 600)],
  "(c) model error: the print's 8va covers bar 246 and only the first note of 247 (hook after it); the model puts the whole of 247 under an 8va. The reference has the sounding pitches (A#6 then the run at staff pitch) but no direction."),
 ("H2_hammerklavier_b365-368", "beethoven-hammerklavier-4", (365, 368), (365, 368), [(45, 60, 580, 1227, 960)],
  "(c) model error: the print's 8va runs from 365 over the system break to the end of 368; the model ends it in 367. Reference pitches in 367-368 are the sounding ones."),
 ("H3_hammerklavier_b402-406", "beethoven-hammerklavier-4", (402, 406), (402, 406), [(46, 60, 1320, 1227, 1660)],
  "(c) model error: the print's last 8va covers bar 403 and the first chord of 404 (hook after it); the model never closes it, so bars 405-406 are an octave too high. Reference has no direction, pitches fine."),
 ("W1_wanderer_b114-118", "schubert-wanderer-3-4", (114, 118), (114, 118), [(21, 40, 1370, 1246, 1620)],
  "(c) model error: the print's 8va covers the chords of 115-116 and the first beat of 117 (hook); the model keeps it open through 118. The reference has the sounding pitches of 115-117 but no start (orphan stop elsewhere)."),
 ("W2_wanderer_b439-444", "schubert-wanderer-3-4", (438, 443), (439, 444), [(31, 0, 370, 1246, 1090)],
  "(c) model error: the print's 8va 'start 440' runs over three systems to the hook in 444; the model stops it in 441. Reference pitches are the sounding ones (stop 439 and 446 have no start in the reference)."),
 ("W3_wanderer_b471-476", "schubert-wanderer-3-4", (471, 475), (472, 476), [(33, 0, 1350, 1274, 1610)],
  "(c) model error: print has two short 8va brackets (bars 1-2 of the last system and the chord in bar 4); the model leaves the first open through the figure bar. The reference holds the sounding pitches, with orphan stops only."),
 ("HR1_liszt_hr6_b35-42", "liszt-hr-6", (35, 42), (35, 42), "auto:2",
  "(c) model error: the print's 8va over bars 36-40 and the chord before the double bar is in the reference (start and stop); the model reads no bracket there."),
 ("D1_debussy_b44-52", "debussy-pour-le-piano-1", (44, 52), (44, 52), "auto:6",
  "(c) model error: the glissando 8va ends at the hook over the first note of bar 51 (E6 printed, E7 sounding, as in the reference); the model misreads bar 51. The reference has stops in 50/51 without start."),
 ("K1_kreisleriana_b1-4", "schumann-kreisleriana-1", (2, 5), (1, 4), "auto:2",
  "(c) model error: the model invents an 8vb under the left hand of bars 1-3 (low ledger-line notes); the print has none, the reference matches the print."),
 ("S1_scriabin_b297-306", "scriabin-sonata-5", (297, 306), (297, 306), "auto:12",
  "(c) model error: the model writes an 8vb over the right-hand chords of bars 299-304; the print has no bracket there (reference has none)."),
 ("S2_scriabin_b305-314", "scriabin-sonata-5", (305, 314), (305, 314), [(13, 0, 40, 1371, 560)],
  "(c) model error: the print's 8va ends at the barline before 308 (and again before 312); the model ends its bracket one or more bars late. Reference pitches follow the print."),
 ("S3_scriabin_b322-333", "scriabin-sonata-5", (322, 333), (322, 333), [(13, 0, 1130, 1371, 1786), (14, 0, 0, 1371, 520)],
  "(c) model error: 322-324 invented 8va (no bracket in the print), and 329-332 raised because the stop at the end of 328 is lost. Reference: start 325, stop 328 as in the print."),
]

def font(sz):
    for f in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(f): return ImageFont.truetype(f, sz)
    return ImageFont.load_default()

def scan_tiles(piece, boxes, pred):
    tiles = []
    if isinstance(boxes, str):
        pg = int(boxes.split(":")[1])
        locs = [locate(piece, b) for b in range(pred[0], pred[1] + 1)]
        for page in sorted({l["page"] for l in locs}):
            ls = [l for l in locs if l["page"] == page]
            bands = sorted({l["band"] for l in ls if l["band"]})
            im = Image.open(f"{R}/eval_run1/pages/{piece}/page-{page:02d}.png").convert("RGB")
            if bands and len(bands) == len({l["system"] for l in ls}):
                tiles.append(im.crop((0, max(0, int(min(b[0] for b in bands)) - 110), im.width, min(im.height, int(max(b[1] for b in bands)) + 40))))
            else:
                tiles.append(im.resize((im.width * 6 // 10, im.height * 6 // 10)))
    else:
        for page, x0, y0, x1, y1 in boxes:
            tiles.append(Image.open(f"{R}/eval_run1/pages/{piece}/page-{page:02d}.png").convert("RGB").crop((x0, y0, x1, y1)))
    return tiles

def wrap(draw, text, fnt, width):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=fnt) > width: lines.append(cur); cur = w
        else: cur = t
    lines.append(cur); return lines

def build(d, only=None):
    id_, piece, rr, pr, boxes, text = d
    if only and not any(o in id_ for o in only): return
    sc = scan_tiles(piece, boxes, pr)
    ref = render(ref_path(piece), rr[0], rr[1], f"{OUT}/_r.png")
    mod = render(pred_path(piece), pr[0], pr[1], f"{OUT}/_m.png")
    parts = [("scan (print)", t) for t in sc] + [(f"reference engraving (ref bars {rr[0]}-{rr[1]}, as stored: no octave-shift unless stated)", Image.open(ref).convert("RGB")),
                                              (f"released model (layout1) engraving (output bars {pr[0]}-{pr[1]})", Image.open(mod).convert("RGB"))]
    f1, f2 = font(22), font(20)
    tmp = Image.new("RGB", (W, 10)); dr = ImageDraw.Draw(tmp)
    head = wrap(dr, f"{piece}: {text}", f1, W - 20)
    canvas_h = 16 + len(head) * 28 + 10
    ims = []
    for lab, im in parts:
        s = W / im.width; im = im.resize((W, max(1, int(im.height * s))), Image.LANCZOS)
        if im.height > 760 and lab == "scan (print)": im = im.crop((0, 0, W, 760))
        ims.append((lab, im)); canvas_h += im.height + 30
    c = Image.new("RGB", (W, canvas_h), "white"); dc = ImageDraw.Draw(c)
    y = 8
    for l in head: dc.text((10, y), l, fill="black", font=f1); y += 28
    y += 10
    for lab, im in ims:
        dc.text((10, y), lab, fill=(150, 0, 0), font=f2); y += 28
        c.paste(im, (0, y)); y += im.height + 2
    c.save(f"{OUT}/{id_}.png"); print(id_, c.size)
    for f in (f"{OUT}/_r.png", f"{OUT}/_m.png"):
        if os.path.exists(f): os.remove(f)

if __name__ == "__main__":
    for d in D: build(d, sys.argv[1:] or None)
