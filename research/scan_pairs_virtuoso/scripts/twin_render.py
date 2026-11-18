"""Rendered twins of the scanned crops: the same ASAP measures, engraved by Verovio and cut like a homr staff crop.

usage:  twin_render.py [--only NAME ...] [--workers N] [--out DIR]       (all crops of the train and validation lists)

For every crop of lists/train_strong.txt, train_hard.txt and val_strong.txt (names and measure ranges from manifest.csv) the measures
[a, b) (0-based index in the part, manifest range a+1 .. b) of the ASAP MusicXML are engraved as ONE system:
  * Verovio's `select` keeps the clef, key and (octave) brackets that begin before the range; time signatures that begin before the range are
    set to print-object=no, because the token files carry a time signature only where the first measure of the range declares one;
    the part name ("Pno.") is removed, the scans do not have it.
  * Font: one of the five Verovio fonts per piece (hash of the piece id), like training/omr_datasets/verovio_staffs.py.
  * Spacing: the tightest rung of a ladder (spacingLinear, spacingNonLinear) at which no two notes of different onset touch
    (`readable()` below, a bounding-box test on notehead + accidental + dots). A crop whose loosest rung still fails is dropped (reason in the report).
  * Cut: like homr's prepare_staff_image for a grand staff: 4 staff spaces above the top line and below the bottom line of the system, extended
    to hold stems, beams, ledger notes, brackets and dynamics (+1 staff space), 1 space left of the brace and 2 right of the staff lines; the
    region is rasterised at the scale at which it fits homr's 256 x 1280 canvas (same rule as get_tr_omr_canvas_size), stored WITHOUT the white
    canvas padding and without a crop JSON, i.e. exactly as the scan crops are stored. The canvas size of the model (256x1280 or 384x1920)
    is applied later by the data loader, so the twin is resolution-agnostic in the same way the scan crops are.
  * Check against the token file: number of note heads, presence of octave brackets; a mismatch drops the crop.
"""
import argparse, csv, copy, hashlib, io, json, multiprocessing, os, re, subprocess, sys, tempfile, zipfile
import xml.etree.ElementTree as ET
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # run/scan_pairs_virtuoso
RUN = os.path.dirname(ROOT)                                    # run
ASAP = RUN + "/box_scripts/r6_extra/asap_mxl/"
sys.path.insert(0, HERE)
sys.path.insert(0, RUN + "/integration_wt")
from unittest import mock
for _m in ("augraphy", "augraphy.base", "augraphy.base.augmentationpipeline", "augraphy.base.augmentation", "augraphy.utilities", "augraphy.utilities.overlaybuilder"):
    sys.modules.setdefault(_m, mock.MagicMock())
import verovio
verovio.enableLog(verovio.LOG_OFF)
from pieces import BY
import training.omr_datasets.verovio_staffs as vs     # fill_voices, clef_changes_within_measures, parse_page, _random_for (code of integration_wt, unchanged)

FONTS = ["Leipzig", "Bravura", "Gootville", "Leland", "Petaluma"]
SCALE = 40
# (spacingLinear, spacingNonLinear) from tight to loose; Verovio's defaults are (0.25, 0.6)
LADDER = [(0.18, 0.42), (0.21, 0.5), (0.25, 0.6), (0.29, 0.66), (0.33, 0.72), (0.38, 0.78), (0.44, 0.85), (0.52, 0.92)]
# canvas of homr (Config.max_height / max_width at scale 1); scans and twins are stored at this size
CANVAS_H, CANVAS_W = 256, 1280
MARGIN_LINES = 4.0          # staff spaces above / below the outer staff lines (homr's _calculate_region)
CONTENT_SLACK = 1.0         # staff spaces beyond stems, ledger notes, brackets and dynamics
MIN_GAP = 0.25              # staff spaces between heads/accidentals in different columns that are less than 0.5 staff spaces apart vertically
SVG = "{http://www.w3.org/2000/svg}"
IGNORED = {"verse", "syl", "label", "labelAbbr", "mNum", "dir", "tempo", "harm", "reh", "pgHead"}


def cls(e):
    c = (e.get("class") or "").split(" ")
    return "" if "bounding-box" in c else c[0]


def is_bbox(e):
    return "bounding-box" in (e.get("class") or "")


def font_for(pid):
    return FONTS[int(hashlib.sha256(("twin-" + pid).encode()).hexdigest()[:8], 16) % len(FONTS)]


_XML_CACHE = {}
_NOTE_TO_REST_DROP = ("pitch", "unpitched", "accidental", "stem", "beam", "tie", "notations", "notehead", "notehead-text", "lyric", "dot_")


def hide_invisible_notes(root):
    """ASAP/MuseScore XML writes trills and tremolos out as notes with print-object="no" (the print shows a trill sign). The token converter does not
    count them and the print does not show them, but Verovio still draws their beams: they become invisible rests of the same duration
    (hidden chord members and hidden grace notes are removed)."""
    n_conv = 0
    for part in root.findall("part"):
        for measure in part.findall("measure"):
            for note in list(measure.findall("note")):
                if note.get("print-object") != "no":
                    continue
                if note.find("chord") is not None or note.find("grace") is not None:
                    measure.remove(note); continue
                pitch = note.find("pitch")
                if pitch is None:
                    continue                                   # already a rest
                idx = list(note).index(pitch)
                for tag in ("pitch", "accidental", "stem", "beam", "tie", "notations", "notehead", "lyric", "cue"):
                    for el in note.findall(tag):
                        note.remove(el)
                note.insert(idx, ET.Element("rest"))
                n_conv += 1
    return n_conv




def asap_root(asap):
    if asap not in _XML_CACHE:
        root = ET.fromstring(zipfile.ZipFile(ASAP + asap + ".mxl").read("score.xml").decode("utf-8"))
        # a stray minor part would be engraved as an extra staff (same rule as render_one_svg.py)
        sizes = {p.get("id"): sum(1 for n in p.iter("note") if n.find("rest") is None) for p in root.findall("part")}
        big = max(sizes.values())
        for p in list(root.findall("part")):
            if sizes[p.get("id")] < 0.05 * big:
                root.remove(p)
                for sp in list(root.iter("score-part")):
                    if sp.get("id") == p.get("id"):
                        root.find("part-list").remove(sp)
        for sp in root.iter("score-part"):                 # no "Pno." in front of the first system
            for tag in ("part-name", "part-abbreviation", "part-name-display", "part-abbreviation-display"):
                for el in sp.findall(tag):
                    sp.remove(el)
            ET.SubElement(sp, "part-name").set("print-object", "no")
        for el in root.iter("part-name"):
            el.text = ""
        for pr in root.iter("print"):                        # no measure numbers at the system starts
            for el in pr.findall("measure-numbering"):
                pr.remove(el)
        hide_invisible_notes(root)
        vs.fill_voices(root)
        _XML_CACHE[asap] = root
    return _XML_CACHE[asap]


def xml_for(asap, a):
    """Whole piece, with every time signature before measure index a hidden."""
    root = copy.deepcopy(asap_root(asap))
    part = root.find("part")
    for i, m in enumerate(part.findall("measure")):
        if i >= a:
            break
        for t in m.iter("time"):
            t.set("print-object", "no")
    return ET.tostring(root, encoding="unicode")


def token_stats(path):
    txt = open(path).read()
    elems = [e for line in txt.split("\n") for e in line.split("&")]
    heads = sum(1 for e in elems if e.startswith("note_"))
    octave = len(re.findall(r"octaveShift_8v[ab]", txt)) > 0
    time_sig = "timeSignature" in txt.split("barline")[0]
    return dict(heads=heads, octave=octave, time_first=time_sig, bars=txt.count("barline"))


def rect(g):
    for r in g.iter(SVG + "rect"):
        return [float(r.get("x")), float(r.get("y")), float(r.get("width")), float(r.get("height"))]
    return None


def boxes_of(g):
    """All bounding boxes (x, y, w, h) below g (a group), skipping ignored classes."""
    out = []
    if cls(g) in IGNORED:
        return out
    for ch in g:
        if ch.tag != SVG + "g":
            continue
        if is_bbox(ch):
            r = rect(ch)
            if r and r[2] > 0 and r[3] > 0 and cls(ch).split(" ")[0] not in IGNORED:
                out.append(r)
        else:
            out.extend(boxes_of(ch))
    return out


def analyse(svg, timemap, ss_hint=None):
    """Geometry (svg units) and readability of the one system of an SVG page."""
    root = ET.fromstring(svg)
    m = re.search(r'class="page-margin" transform="translate\(([\d.-]+), ([\d.-]+)\)', svg)
    mx, my = float(m.group(1)), float(m.group(2))
    view = re.search(r'class="definition-scale"[^>]*viewBox="0 0 ([\d.]+) ([\d.]+)', svg)
    vw, vh = float(view.group(1)), float(view.group(2))
    system = next(g for g in root.iter(SVG + "g") if cls(g) == "system")
    staves = []                                                     # per measure, per staff: lines
    lines_by_staff = {}
    for meas in (g for g in system if cls(g) == "measure"):
        for n, st in enumerate(g for g in meas if cls(g) == "staff"):
            ls = []
            for p in st:
                if p.tag == SVG + "path":
                    v = [float(t) for t in re.findall(r"[\d.-]+", p.get("d", ""))]
                    ls.append((v[0], v[1], v[2], v[3]))
            ls = ls[:5]
            if len(ls) == 5:
                d = lines_by_staff.setdefault(n, dict(top=1e9, bottom=-1e9, left=1e9, right=-1e9))
                d["top"] = min(d["top"], min(l[1] for l in ls)); d["bottom"] = max(d["bottom"], max(l[1] for l in ls))
                d["left"] = min(d["left"], min(l[0] for l in ls)); d["right"] = max(d["right"], max(l[2] for l in ls))
    ns = sorted(lines_by_staff)
    top, bottom = lines_by_staff[ns[0]]["top"], lines_by_staff[ns[-1]]["bottom"]
    left, right = min(lines_by_staff[n]["left"] for n in ns), max(lines_by_staff[n]["right"] for n in ns)
    ss = (lines_by_staff[ns[0]]["bottom"] - lines_by_staff[ns[0]]["top"]) / 4
    # content extent (stems, beams, ledger lines, brackets, dynamics, slurs ...), left of the brace
    allb = boxes_of(system)
    ctop = min(b[1] for b in allb); cbottom = max(b[1] + b[3] for b in allb); cleft = min(b[0] for b in allb)
    # note heads: boxes of notes (own bounding box is the head), their accidentals and dots, grouped by onset
    notes = []
    for g in system.iter(SVG + "g"):
        if cls(g) != "note":
            continue
        nid = g.get("id")
        if g.find(SVG + "g[@class='notehead']") is None:
            continue
        boxes = []; hx = None
        for ch in g:
            if ch.tag != SVG + "g":
                continue
            if is_bbox(ch) and (ch.get("class") or "").startswith("note"):
                r = rect(ch)
                if r: boxes.append(r); hx = r[0] + r[2] / 2
            elif cls(ch) in ("accid", "dots") :
                for sub in ch:
                    if sub.tag == SVG + "g" and is_bbox(sub):
                        r = rect(sub)
                        if r: boxes.append(r)
        if not boxes or hx is None:
            continue
        x0 = min(b[0] for b in boxes); x1 = max(b[0] + b[2] for b in boxes)
        y0 = min(b[1] for b in boxes); y1 = max(b[1] + b[3] for b in boxes)
        notes.append((nid, x0, x1, y0, y1, hx))
    onset = {}
    for ev in timemap:
        for nid in ev.get("on", []):
            onset[nid] = ev["qstamp"]
    return dict(mx=mx, my=my, vw=vw, vh=vh, top=top, bottom=bottom, left=left, right=right, ss=ss, ctop=ctop, cbottom=cbottom, cleft=cleft,
                notes=notes, onset=onset, n_staff=len(ns), n_heads=len(notes))


def readable(a):
    """(ok, worst gap in staff spaces): heads and accidentals of notes in different columns must not touch.
    Same column = note heads at the same x (within 0.3 staff spaces; chords, voices at one onset); notes of exactly equal onset are never compared
    (second intervals are drawn side by side)."""
    ss = a["ss"]
    ns = sorted(a["notes"], key=lambda n: n[5])
    worst = 1e9
    for i, n1 in enumerate(ns):
        for n2 in ns[i + 1:i + 60]:
            if n2[5] - n1[5] > 8 * ss:
                break
            if abs(n2[5] - n1[5]) < 0.3 * ss:
                continue
            o1, o2 = a["onset"].get(n1[0]), a["onset"].get(n2[0])
            if o1 is not None and o2 is not None and abs(o1 - o2) < 1e-4:
                continue
            gap_x = max(n2[1] - n1[2], n1[1] - n2[2]) / ss
            gap_y = max(n2[3] - n1[4], n1[3] - n2[4], 0) / ss
            if gap_y < 0.5:
                worst = min(worst, gap_x - MIN_GAP)
    return worst >= 0, worst


def strip_measure_numbers(svg):
    """Verovio writes an automatic measure number at the start of a selected range; the scans have none."""
    ET.register_namespace("", "http://www.w3.org/2000/svg"); ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
    root = ET.fromstring(svg)
    for parent in root.iter():
        for ch in list(parent):
            if ch.tag == SVG + "g" and "mNum" in (ch.get("class") or "").split(" "):
                parent.remove(ch)
    return ET.tostring(root, encoding="unicode")


def region_px(a, k):
    """Crop region in raster pixels for an svg-unit -> pixel factor k."""
    ss = a["ss"]
    y0 = min(a["top"] - MARGIN_LINES * ss, a["ctop"] - CONTENT_SLACK * ss)
    y1 = max(a["bottom"] + MARGIN_LINES * ss, a["cbottom"] + CONTENT_SLACK * ss)
    x0 = min(a["left"], a["cleft"]) - 1.0 * ss
    x1 = a["right"] + 2.0 * ss
    extended = (y0 < a["top"] - MARGIN_LINES * ss - 1e-6) or (y1 > a["bottom"] + MARGIN_LINES * ss + 1e-6)
    return (x0 + a["mx"]) * k, (y0 + a["my"]) * k, (x1 + a["mx"]) * k, (y1 + a["my"]) * k, extended


def canvas_size(h, w):
    """homr.staff_parsing.get_tr_omr_canvas_size: (width, height) of the region inside the 256 x 1280 canvas."""
    if h / w > CANVAS_H / CANVAS_W:
        return int(w / h * CANVAS_H), CANVAS_H
    return CANVAS_W, int(h / w * CANVAS_W)


def render_crop(name, pid, a, b, token_file, out_png, svg_dir=None):
    import cv2
    cfg = BY[pid]
    res = dict(name=name, pid=pid, a=a, b=b, status="ok", reason="")
    tk = verovio.toolkit()
    tk.setOptions({"pageWidth": 60000, "pageHeight": 6000, "scale": SCALE, "adjustPageHeight": True, "adjustPageWidth": True, "breaks": "none",
                   "header": "none", "footer": "none", "svgBoundingBoxes": True, "font": font_for(pid), "mnumInterval": 0,
                   "pageMarginLeft": 50, "pageMarginRight": 50, "pageMarginTop": 50, "pageMarginBottom": 50})
    if not tk.loadData(xml_for(cfg["asap"], a)):
        res.update(status="drop", reason="verovio load failed"); return res
    chosen = None
    forced = os.environ.get("TWIN_LEVEL")
    for lvl, (lin, nonlin) in enumerate(LADDER):
        if forced is not None and lvl != int(forced):
            continue
        tk.setOptions({"spacingLinear": lin, "spacingNonLinear": nonlin})
        tk.select({}); tk.select({"measureRange": f"{a + 1}-{b}"}); tk.redoLayout()
        svg = tk.renderToSVG(1)
        an = analyse(svg, tk.renderToTimemap())
        ok, worst = readable(an)
        if chosen is None or ok:
            chosen = (lvl, svg, an, worst, ok)
        if ok and forced is None:
            break
    lvl, svg, an, worst, ok = chosen
    res.update(level=lvl, worst_gap=round(worst, 2), font=font_for(pid), heads_svg=an["n_heads"], staves=an["n_staff"])
    if tk.getPageCount() != 1:
        res.update(status="drop", reason=f"{tk.getPageCount()} pages"); return res
    if not ok:
        res.update(status="drop", reason=f"notes touch at the loosest spacing (gap {worst:.2f} ss)")
    ts = token_stats(token_file)
    res.update(heads_tok=ts["heads"], octave_tok=ts["octave"])
    octave_svg = bool(re.search(r'class="octave[ "]', svg))
    res["octave_svg"] = octave_svg
    if an["n_heads"] != ts["heads"]:
        res.update(status="drop", reason=f"note heads: tokens {ts['heads']}, rendering {an['n_heads']}")
    elif octave_svg != ts["octave"]:
        res.update(status="drop", reason=f"octave bracket: tokens {ts['octave']}, rendering {octave_svg}")
    elif an["n_staff"] != 2:
        res.update(status="drop", reason=f"{an['n_staff']} staves")
    # raster at the canvas scale
    k0 = 1.0
    x0, y0, x1, y1, ext = region_px(an, k0)
    w_new, h_new = canvas_size(y1 - y0, x1 - x0)
    k = h_new / (y1 - y0)
    x0, y0, x1, y1, ext = region_px(an, k)
    page_w = int(round(an["vw"] * k))
    with tempfile.TemporaryDirectory() as td:
        sp = td + "/p.svg"; pp = td + "/p.png"
        svg = strip_measure_numbers(svg)
        open(sp, "w").write(svg)
        subprocess.run(["rsvg-convert", "-b", "white", "-w", str(page_w), "-o", pp, sp], check=True)
        img = cv2.imread(pp, cv2.IMREAD_GRAYSCALE)
    H, W = img.shape
    xi0, yi0 = max(0, int(round(x0))), max(0, int(round(y0)))
    crop = img[yi0:min(H, yi0 + h_new), xi0:min(W, xi0 + w_new)]
    if crop.shape != (h_new, w_new):                       # padding of the page was too small: pad white
        pad = np.full((h_new, w_new), 255, np.uint8); pad[:crop.shape[0], :crop.shape[1]] = crop; crop = pad
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    cv2.imwrite(out_png, crop)
    res.update(w=w_new, h=h_new, ss_px=round(an["ss"] * k, 2), ss_wide=round((an["right"] - an["left"]) / an["ss"], 1), extended=bool(ext),
               width_limited=h_new < CANVAS_H)
    if svg_dir:
        os.makedirs(svg_dir, exist_ok=True); open(f"{svg_dir}/{name}.svg", "w").write(svg)
    return res


def _job(args):
    try:
        return render_crop(*args)
    except Exception as e:                                 # noqa: BLE001
        return dict(name=args[0], pid=args[1], status="drop", reason="error " + repr(e)[:120])


def read_manifest():
    rows = {}
    for r in csv.DictReader(open(ROOT + "/manifest.csv")):
        rows[r["crop"]] = r
    return rows


def groups():
    """(list name, relative crop path, token path) of the frozen training and validation lists."""
    out = []
    for lst in ("train_strong", "train_hard", "val_strong"):
        for line in open(f"{ROOT}/lists/{lst}.txt"):
            line = line.strip()
            if not line:
                continue
            img, tok = line.split(",")
            out.append((lst, img.replace("scan_pairs_virtuoso/", ""), tok.replace("scan_pairs_virtuoso/", "")))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", default=ROOT + "/twins")
    ap.add_argument("--report", default=ROOT + "/twins_report.json")
    ap.add_argument("--svg", default=None)
    args = ap.parse_args()
    man = read_manifest()
    jobs = []
    for lst, img, tok in groups():
        r = man[img]
        name = os.path.basename(img)[:-4]
        if args.only and name not in args.only:
            continue
        a, b = (int(x) for x in r["asap_measure_range"].split("-"))
        jobs.append((name, r["pid"], a - 1, b, f"{ROOT}/{tok}", f"{args.out}/{r['pid']}/{name}.png", args.svg))
    print(len(jobs), "crops", flush=True)
    with multiprocessing.Pool(args.workers) as pool:
        res = []
        for i, x in enumerate(pool.imap_unordered(_job, jobs, chunksize=2)):
            res.append(x)
            if i % 50 == 0:
                print(i, x["name"], x["status"], x.get("reason", ""), flush=True)
    res.sort(key=lambda r: r["name"])
    json.dump(res, open(args.report, "w"), indent=0)
    import collections
    print(collections.Counter(r["status"] for r in res), collections.Counter(r["reason"].split(":")[0].split("(")[0] for r in res if r["status"] != "ok"))
