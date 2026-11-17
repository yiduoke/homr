"""Checks on token files of the meter arm: time signatures (start / mid-staff), bars, and "every bar adds up to its meter".
Used by verify_montage.py and compose_lists.py.
"""
import json
import re
import xml.etree.ElementTree as ET
from fractions import Fraction

BAR_RE = re.compile(r"^(barline|doublebarline|bolddoublebarline|repeatEnd|repeatEndStart)")
NOTE_RE = re.compile(r"^(note|rest)_(\d+)(\.*)$")


def parse_lines(text):
    return [[s.strip().split(" ") for s in ln.split("&")] for ln in text.strip("\n").split("\n") if ln.strip()]


def meter_events(text):
    """(start meter or None, [(bar_index, meter)] mid-staff changes, number of bars).
    bar_index: 0-based index of the bar in which the signature appears; start = before the first note/barline."""
    start = None
    mids = []
    bar = 0
    seen = False
    for ln in parse_lines(text):
        first = ln[0][0]
        ts = [s[0] for s in ln if s[0].startswith("timeSignature_")]
        if ts:
            m = ts[0][len("timeSignature_"):]
            if not seen:
                start = m
            else:
                mids.append((bar, m))
            continue
        if first.startswith(("note", "rest")):
            seen = True
        if BAR_RE.match(first):
            seen = True
            bar += 1
    return start, mids, bar


def meter_duration(m):
    if m in ("common",):
        return Fraction(1)
    if m in ("cut",):
        return Fraction(1)
    b, d = m.split("/")
    return Fraction(int(b), int(d))


def bar_sums(text):
    """List of per-bar dict position -> Fraction (whole notes)."""
    bars = [{}]
    for ln in parse_lines(text):
        first = ln[0][0]
        if BAR_RE.match(first):
            bars.append({})
            continue
        seen = {}
        for sym in ln:
            m = NOTE_RE.match(sym[0])
            if not m or len(sym) < 6:
                continue
            d = Fraction(1, int(m.group(2)))
            add = d
            for _ in range(len(m.group(3))):
                d = d / 2
                add += d
            pos = sym[-1]
            seen[pos] = max(seen.get(pos, 0), add)
        for pos, v in seen.items():
            bars[-1][pos] = bars[-1].get(pos, 0) + v
    if bars and not bars[-1]:
        bars.pop()
    return bars


def check_staff(text, bar_meters, tuplet_bars=()):
    """bar_meters: expected meter per bar of this staff (list of 'n/d'/'common'/'cut'); returns (n_checked, n_bad, bad list)."""
    sums = bar_sums(text)
    bad = []
    checked = 0
    for i, s in enumerate(sums):
        if i >= len(bar_meters) or i in tuplet_bars:
            continue
        exp = meter_duration(bar_meters[i])
        got = max(s.values()) if s else Fraction(0)
        checked += 1
        if got != exp:
            bad.append((i, str(got), str(exp)))
    return checked, len(bad), bad


def window_bar_info(xml_path):
    """Per bar of a window: meter string ('n/d', 'common', 'cut') and whether the bar has a tuplet."""
    root = ET.parse(xml_path).getroot()
    out = []
    meter = None
    for m in root.find("part").findall("measure"):
        for att in m.findall("attributes"):
            for t in att.findall("time"):
                sym = t.get("symbol")
                meter = sym if sym in ("common", "cut") else f"{t.findtext('beats')}/{t.findtext('beat-type')}"
        out.append((meter, m.find(".//time-modification") is not None, m.get("implicit") == "yes"))
    return out


def staff_infos(records, plan_by_wid):
    """records: staff records of one renderer run (dicts with spec, image, tokens, ...). Adds per-staff analysis:
    start, mids [(bar, meter)], nbars, bar_off, checked, bad, bad_list, sig_after_change, meters (all meters in the staff), ok_offset."""
    by_wid = {}
    for r in records:
        if "image" in r:
            by_wid.setdefault(r["spec"], []).append(r)
    out = []
    for wid, rs in by_wid.items():
        spec = plan_by_wid[wid]
        xml = f"/workspace/run4/meters/xml/{spec['round']}/{wid}.musicxml"
        info = window_bar_info(xml)

        def order_key(r):
            m = re.search(r"-(?:vrv-)?(\d+)(?:-(\d+))?\.png$", r["image"])
            return (int(m.group(1)), int(m.group(2) or 0))

        rs = sorted(rs, key=order_key)
        texts = [open(r["tokens"]).read() for r in rs]
        evs = [meter_events(t) for t in texts]
        total = sum(e[2] for e in evs)
        ok_offset = total == len(info)
        off = 0
        for r, t, (start, mids, nb) in zip(rs, texts, evs):
            d = dict(r)
            d.update(start=start, mids=mids, nbars=nb, ok_offset=ok_offset, bar_off=off, checked=0, bad=0, bad_list=[],
                     window_kind=spec["kind"])
            meters = {start} if start else set()
            meters |= {m for _b, m in mids}
            printed = sorted(x for x in meters if x)
            sig_after_change = False
            if ok_offset:
                exp = [info[off + i][0] for i in range(nb)]
                tup = {i for i in range(nb) if info[off + i][1]}
                imp = {i for i in range(nb) if info[off + i][2]}
                c, b, bl = check_staff(t, exp, tup | imp)
                d.update(checked=c, bad=b, bad_list=bl, bar_meters=exp)
                meters |= set(exp)
                if start and off > 0 and info[off - 1][0] != start:
                    sig_after_change = True
            d.update(meters=sorted(x for x in meters if x), printed=printed, sig_after_change=sig_after_change)
            out.append(d)
            off += nb
    return out
