"""Map an aligned prediction bar to its page and crop it from the page image (read-only helper).

usage: timing_audit_crops.py piece pred_bar_index(1-based) out.png [margin]
Uses the '<!-- imgpos: x, y -->' comments homr writes into the per-page MusicXML.
"""
import difflib
import glob
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

HOME = Path("/Users/yiduoke/Documents/homr/run/eval_run1")
SEM = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midis(measure):
    out = []
    for n in measure.iter("note"):
        p = n.find("pitch")
        if p is not None:
            out.append(12 * (int(p.findtext("octave")) + 1) + SEM[p.findtext("step")] + int(float(p.findtext("alter") or 0)))
    return tuple(sorted(out))


def page_measures(piece):
    """list of (page_png_stem, measure_no, midis, bbox) for main part of every page."""
    res = []
    for f in sorted(glob.glob(str(HOME / f"run2s7/{piece}/page-xml/page-*.musicxml"))):
        text = Path(f).read_text()
        root = ET.fromstring(text)
        part = root.find("part")
        # imgpos comments: parse measure by measure with regex on raw text
        raw_parts = re.split(r'<measure ', text.split('<part id="', 2)[1])[1:]
        for k, m in enumerate(part.findall("measure")):
            raw = raw_parts[k] if k < len(raw_parts) else ""
            pts = [(int(a), int(b)) for a, b in re.findall(r"imgpos: (\d+), (\d+)", raw.split("</measure>")[0])]
            res.append((Path(f).stem, m.get("number"), midis(m), pts))
    return res


def joined_bars(piece):
    p = HOME / f"run2s7/{piece}/{piece}-run2s7.musicxml"
    if not p.exists():
        p = HOME / f"out/compare/{piece}/{piece}-run2s7.musicxml"
        p = Path("/Users/yiduoke/Documents/homr/run/out/compare") / piece / f"{piece}-run2s7.musicxml"
    root = ET.parse(p).getroot()
    parts = root.findall("part")
    if len({len(p.findall("measure")) for p in parts}) > 1:
        parts = parts[:1]  # staves with different bar counts: map through the first part only
    n = len(parts[0].findall("measure"))
    out = []
    for i in range(n):
        allm = []
        for part in parts:
            ms = part.findall("measure")
            if i < len(ms):
                allm += list(midis(ms[i]))
        out.append(tuple(sorted(allm)))
    return out


def locate(piece):
    pm = page_measures(piece)
    jb = joined_bars(piece)
    # page measures cover only the main part, joined may include more parts; compare by subset
    sm = difflib.SequenceMatcher(None, [m[2] for m in pm], jb, autojunk=False)
    mapping = {}
    for a, b, size in sm.get_matching_blocks():
        for k in range(size):
            mapping[b + k] = pm[a + k]
    return mapping, pm, jb


if __name__ == "__main__":
    piece, bar, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    margin = int(sys.argv[4]) if len(sys.argv) > 4 else 90
    mapping, pm, jb = locate(piece)
    hit = mapping.get(bar - 1)
    if hit is None:
        # nearest mapped neighbour
        near = min(mapping, key=lambda k: abs(k - (bar - 1)))
        print("bar not matched by content; nearest mapped bar", near + 1, mapping[near][:2])
        sys.exit(1)
    stem, num, _, pts = hit
    img = Image.open(HOME / f"pages/{piece}/{stem}.png")
    print(piece, "pred bar", bar, "->", stem, "measure", num, "points", len(pts), "img", img.size,
          "ptsmax", max(pts) if pts else None)
    if pts:
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        box = (max(0, min(xs) - margin), max(0, min(ys) - margin), min(img.width, max(xs) + margin),
               min(img.height, max(ys) + margin))
        img.crop(box).save(out)
        print("crop", box)
