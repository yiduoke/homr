"""D32: evidence sheets for the by-eye check of the automatic octave-cause classes (and the 6 evidence figures).
A sheet = scan region of the crop (margin above and below so brackets and ledger lines show) | label measures engraved with Verovio
(brackets open at the window start re-opened) | full page thumbnail with the crop outlined. The header lists the label's and the read's
bracket events (bar.note:type) and the first differing notes (bar, label pitch, read pitch); it does NOT print the automatic class.

usage: /Users/yiduoke/Documents/homr/.venv/bin/python make_eye_sheets.py <outdir> <crop name> ...
"""
import csv
import glob
import importlib.util
import json
import os
import sys
import tempfile
import subprocess

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/octave_checks")
import octave_causes_crops as O  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

R = O.R
sys.path.insert(0, R + "scripts")
sys.path.insert(0, R + "batch2/scripts")
import verovio  # noqa: E402

verovio.enableLog(verovio.LOG_OFF)


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


SH1 = _load(R + "octave_review_scripts/sheet.py", "sheet_pilot")
try:
    SH2 = _load(R + "batch2/scripts/sheet2.py", "sheet_b2")
except Exception as e:  # noqa: BLE001
    print("batch2 sheet module failed", e)
    SH2 = None

CROPS = {c["name"]: c for c in O.load_all()}
RES = {r["name"]: r for r in json.load(open(O.OUT + "octave_causes_notes.json"))}


def ev_summary(tokens):
    st, sp, ev, stray = O.parse(tokens)
    out = []
    for s in ("upper", "lower"):
        for b, n, t in ev[s]:
            out.append(f"{s[0]}{b}.{n}:{t}")
    return " ".join(out) or "none"


def diff_notes(r, k=8):
    lst = []
    for e in r.get("events", [])[:k]:
        lst.append(f"{e['staff'][0]}b{e['bar']} wd{e['wd']:+d} sL{e['sL']:+d} sR{e['sR']:+d}")
    return "; ".join(lst)


def asap_and_window(c):
    row = c["row"]
    pid = row["pid"]
    if c["set"] == "pilot":
        asap = SH1.BY[pid]["asap"]
    else:
        asap = SH2.BY[pid]["asap"]
    a, b = row["asap_measure_range"].split("-") if "-" in row["asap_measure_range"] else (row["asap_measure_range"],) * 2
    return asap, int(a) - 1, int(b)


def make(name, out, W=1300, pad_top=90, pad_bot=60, with_label=True, header=True):
    c = CROPS[name]
    row = c["row"]
    base = c["base"]
    page = Image.open(base + row["page_image"]).convert("L")
    x0, y0, x1, y1 = map(int, row["page_bbox_xyxy"].split())
    reg = page.crop((max(0, x0 - 15), max(0, y0 - pad_top), min(page.width, x1 + 15), min(page.height, y1 + pad_bot)))
    reg = reg.resize((W, int(reg.height * W / reg.width)))
    ims = [("scan region (extra margin above/below)", reg)]
    if with_label and row["asap_measure_range"]:
        try:
            asap, a, b = asap_and_window(c)
            lab = tempfile.mktemp(suffix=".png")
            mod = SH1 if c["set"] == "pilot" else SH2
            mod.render_label(asap, a, b, lab, W)
            ims.append(("label measures (Verovio from the ASAP reference; open brackets re-opened)", Image.open(lab).convert("L")))
            os.remove(lab)
        except Exception as e:  # noqa: BLE001
            print("label render failed", name, e)
    left_h = sum(i.height for _, i in ims) + 22 * len(ims) + (62 if header else 0)
    # page thumbnail
    th_w = 380
    th = page.resize((th_w, int(page.height * th_w / page.width))).convert("RGB")
    d = ImageDraw.Draw(th)
    sx = th_w / page.width
    d.rectangle((x0 * sx, y0 * sx, x1 * sx, y1 * sx), outline=(255, 0, 0), width=3)
    H = max(left_h, th.height + 22)
    sheet = Image.new("RGB", (W + th_w + 10, H), (255, 255, 255))
    y = 0
    dr = ImageDraw.Draw(sheet)
    if header:
        r = RES.get(name, {})
        txt = [f"{name} | {row['piece']} | {row['edition']} | meas {row['asap_measure_range']} | page {os.path.basename(row['page_image'])} sys {row['system_index']}",
               f"label brackets: {ev_summary(c['label'])}   |   read brackets: {ev_summary(c['read'])}",
               f"first differing notes (written octave delta label-read, label/read shift state): {diff_notes(r)}"]
        for t in txt:
            dr.text((6, y + 2), t, fill=(0, 0, 0))
            y += 18
        y += 8
    for t, im in ims:
        dr.rectangle((0, y, W, y + 20), fill=(0, 0, 0))
        dr.text((6, y + 4), t, fill=(255, 255, 255))
        y += 22
        sheet.paste(im.convert("RGB"), (0, y))
        y += im.height
    sheet.paste(th, (W + 10, 22))
    dr.text((W + 12, 4), "full page (crop outlined)", fill=(0, 0, 0))
    sheet.save(out)
    return out


if __name__ == "__main__":
    os.makedirs(sys.argv[1], exist_ok=True)
    for n in sys.argv[2:]:
        make(n, os.path.join(sys.argv[1], n + ".png"))
