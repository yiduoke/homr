"""Helpers for the reference-hygiene check of octave brackets (D33): bar-level pitch comparison of reference and prediction,
bracket spans of reference / output / page XML, with the scorer's own parser (validation/score_notes.py, res_wt = integration_wt)."""
import glob
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter

R = "/Users/yiduoke/Documents/homr/run"
T = f"{R}/out/testset"
sys.path.insert(0, f"{R}/res_wt")
from validation import score_notes as sn  # noqa: E402


def ref_path(piece, edition=False):
    return f"{T}/{piece}/{piece}-reference{'-edition' if edition else ''}.musicxml"


def pred_path(piece, tag="layout1"):
    return f"{T}/{piece}/{piece}-{tag}.musicxml"


def parse(path):
    return sn.parse_musicxml(open(path, encoding="utf-8-sig").read())


def match_pooled(ref_notes, pred_notes, shift=0, staff=None):
    a = Counter(round(n.pitch) for n in ref_notes if staff is None or n.staff == staff)
    b = Counter(round(n.pitch) + shift for n in pred_notes if staff is None or n.staff == staff)
    return sum((a & b).values()), sum(a.values()), sum(b.values())


def bar_pairs(ref, pred):
    """(ref index, pred index) pairs, pooled alignment."""
    return sn.align_measures(ref, pred, ignore_staff=True)


def shift_events(path):
    """[(part, measure index 1-based, measure number, type, size, number, staff)] of the octave-shift directions in a MusicXML file."""
    t = ET.parse(path)
    out = []
    for pi, part in enumerate(t.findall(".//part")):
        for mi, m in enumerate(part.findall("measure")):
            for d in m.iter("direction"):
                for o in d.iter("octave-shift"):
                    out.append((pi, mi + 1, m.get("number"), o.get("type"), o.get("size"), o.get("number"), d.findtext("staff")))
    return out


def page_info(piece, tag="layout1"):
    d = f"{R}/eval_run1/testset/{tag}/{piece}/page-xml"
    files = sorted(glob.glob(d + "/page-*.musicxml"), key=lambda f: int(re.findall(r"page-(\d+)", f)[0]))
    off, rows = 0, []
    for f in files:
        pg = int(re.findall(r"page-(\d+)", f)[0])
        parts = ET.parse(f).findall(".//part")
        n = max(len(p.findall("measure")) for p in parts)
        ev = []
        for pi, p in enumerate(parts):
            for mi, m in enumerate(p.findall("measure")):
                for dd in m.iter("direction"):
                    for o in dd.iter("octave-shift"):
                        ev.append((pi, mi + 1, o.get("type"), o.get("number"), dd.findtext("staff")))
        rows.append((pg, off, n, len(parts), ev))
        off += n
    return rows
