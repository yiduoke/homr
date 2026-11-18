"""Rhythm checks on token texts: per-bar durations per voice tag, note events (bar, onset, pitch, duration), agreement metrics label vs read,
and a ledger of the true (MusicXML) durations per measure and voice tag.  Durations are Fractions of a whole note, token durations as the decoder reads them
(kern k not a power of two: 1/k times the dots)."""
import sys, os, json, zipfile, collections, re
from fractions import Fraction
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/tuplet_wt")
from unittest import mock
for _m in ("augraphy","augraphy.base","augraphy.base.augmentationpipeline","augraphy.base.augmentation","augraphy.utilities","augraphy.utilities.overlaybuilder"):
    sys.modules.setdefault(_m, mock.MagicMock())
from homr.transformer.vocabulary import EncodedSymbol
import xml.etree.ElementTree as ET
ASAP = "/Users/yiduoke/Documents/homr/run/box_scripts/r6_extra/asap_mxl/"

def sym_duration(rhythm):
    """Fraction of a whole note, None for rests of a measure / multirests / graces / unreadable"""
    if "G" in rhythm.split("_")[-1] and re.search(r"_\d+G", rhythm): return None
    try:
        if rhythm.endswith("m") or rhythm in ("rest_0",): return None
        return EncodedSymbol(rhythm).get_duration().fraction
    except Exception:  # noqa: BLE001
        return None

def parse(text):
    """-> list of bars; bar = list of lines; line = list of (rhythm,pitch,lift,art,slur,pos)"""
    bars = [[]]
    for ln in text.splitlines():
        ln = ln.strip()
        if not ln: continue
        syms = []
        for part in ln.split("&"):
            f = part.split(" ")
            if len(f) < 6: f = f + ["_"] * (6 - len(f))
            syms.append((f[0], f[1], f[2], f[3], f[4], f[5]))
        r0 = syms[0][0]
        if "barline" in r0 or r0.startswith("repeat"):
            bars.append([]); continue
        bars[-1].append(syms)
    return bars

def events(text):
    """per bar: (list of dict(tag,onset,pitch,dur,rhythm), per-tag duration sums).
    onset = time of the line in the bar: the lines are in time order, the next line comes when the first voice (tag) which is sounding ends
    (end of the tag's last symbol), so the onset does not depend on how the notes are spread over the voice tags."""
    out = []
    for bi, bar in enumerate(parse(text)):
        cur = collections.defaultdict(Fraction); evs = []; end = {}; t = Fraction(0)
        for line in bar:
            bytag = collections.defaultdict(list)
            for s in line:
                if s[0].startswith(("note", "rest")): bytag[s[5]].append(s)
            if not bytag: continue
            for tag, ss in bytag.items():
                ds = [d for d in (sym_duration(x[0]) for x in ss) if d is not None]
                d = min(ds) if ds else None
                for x in ss:
                    if x[0].startswith("note") and x[1] not in ("_", "."):
                        evs.append(dict(bar=bi, tag=tag, onset=t, pitch=x[1], dur=sym_duration(x[0]), rhythm=x[0]))
                if d is not None:
                    end[tag] = t + d; cur[tag] += d if sym_duration(ss[0][0]) is None else sym_duration(ss[0][0])
            later = [e for e in end.values() if e > t]
            if later: t = min(later)
            elif end: t = max(end.values())
        out.append((evs, dict(cur)))
    return out

def bar_info(text):
    """per bar: tag -> dict(sum, lines, rests, pitched) (lines = lines carrying that tag)"""
    out = []
    for bar in parse(text):
        info = collections.defaultdict(lambda: dict(sum=Fraction(0), lines=0, rests=0, pitched=0))
        for line in bar:
            bytag = collections.defaultdict(list)
            for s in line:
                if s[0].startswith(("note", "rest")): bytag[s[5]].append(s)
            for tag, ss in bytag.items():
                d = sym_duration(ss[0][0]); i = info[tag]
                i["lines"] += 1; i["rests"] += ss[0][0].startswith("rest"); i["pitched"] += sum(s[0].startswith("note") for s in ss)
                if d is not None: i["sum"] += d
        out.append(dict(info))
    return out

def bar_sums(text):
    """per bar dict tag -> total token duration (measure rests / multirests not counted)"""
    return [sums for _, sums in events(text)]

def f1c(a, b):
    ca, cb = collections.Counter(a), collections.Counter(b)
    if not ca and not cb: return 1.0
    tp = sum((ca & cb).values())
    if tp == 0: return 0.0
    p, r = tp / sum(cb.values()), tp / sum(ca.values())
    return 2 * p * r / (p + r)

def agreement(label_text, read_text):
    """label = reference, read = model. metrics are F1 of multisets"""
    L = [e for bar, _ in events(label_text) for e in bar]
    R = [e for bar, _ in events(read_text) for e in bar]
    nb = lambda t: len([1 for _ in parse(t)])
    m = dict(
        pitch_f1=f1c([e["pitch"] for e in L], [e["pitch"] for e in R]),
        onset_f1=f1c([(e["bar"], e["onset"], e["pitch"]) for e in L], [(e["bar"], e["onset"], e["pitch"]) for e in R]),
        note_f1=f1c([(e["bar"], e["onset"], e["pitch"], e["dur"]) for e in L], [(e["bar"], e["onset"], e["pitch"], e["dur"]) for e in R]),
        rhythm_f1=f1c([(e["bar"], e["onset"], e["dur"]) for e in L], [(e["bar"], e["onset"], e["dur"]) for e in R]),
        dur_f1=f1c([(e["pitch"], e["bar"], e["dur"]) for e in L], [(e["pitch"], e["bar"], e["dur"]) for e in R]),
        n_label=len(L), n_read=len(R), bars_label=len(parse(label_text)), bars_read=len(parse(read_text)))
    return m

def meters(name):
    """per measure (0-based) meter as a Fraction of a whole note, from the time signature in force (None if missing)"""
    from labels2 import xml_text
    root = ET.fromstring(xml_text(name).encode())
    cur = None; out = []
    for m in root.find("part").findall("measure"):
        t = m.find("attributes/time")
        if t is not None and t.find("beats") is not None and t.find("beat-type") is not None:
            try: cur = sum(Fraction(int(x)) for x in t.find("beats").text.replace("+", " ").split()) / int(t.find("beat-type").text)
            except Exception: pass  # noqa: BLE001
        out.append(cur)
    return out

def ledger(name):
    """true durations per measure and voice tag (visible notes, no chords/graces), from the MusicXML via the converter's own bookkeeping.
    -> list per measure: dict tag -> Fraction (true), plus 'invisible' time"""
    import training.omr_datasets.music_xml_parser as mxp
    rows = []   # (measure, tag, true duration)
    oa, orr = mxp.TokensPart.append_note, mxp.TokensPart.append_rest
    def log(self, staff, voice, is_chord, duration, invisible, symbol):
        m = self.current_measure
        main = getattr(m, "main_voice", {}).get(staff) if m is not None else None
        tag = ("upper" if staff == 0 else "lower") + ("" if voice == main else "2")
        grace = "G" in symbol.rhythm
        rows.append((len(self.measures), tag, Fraction(duration, self.divisions * 4), is_chord, invisible, grace, symbol.rhythm))
    def an(self, staff, voice, is_chord, duration, invisible, symbol):
        log(self, staff, voice, is_chord, duration, invisible, symbol); return oa(self, staff, voice, is_chord, duration, invisible, symbol)
    def ar(self, staff, voice, is_chord, duration, invisible, symbol):
        log(self, staff, voice, is_chord, duration, invisible, symbol); return orr(self, staff, voice, is_chord, duration, invisible, symbol)
    mxp.TokensPart.append_note, mxp.TokensPart.append_rest = an, ar
    osh = mxp._process_octave_shift
    def shift(part, el, staff):
        try: osh(part, el, staff)
        except ValueError: pass
    mxp._process_octave_shift = shift
    try:
        from labels2 import xml_text
        txt = xml_text(name)
        from training.omr_datasets.tuplet_tokens import fixed_tuplets
        with fixed_tuplets():
            mxp.music_xml_string_to_tokens(txt)
    finally:
        mxp.TokensPart.append_note, mxp.TokensPart.append_rest = oa, orr
        mxp._process_octave_shift = osh
    nm = max(r[0] for r in rows) + 1
    out = [collections.defaultdict(Fraction) for _ in range(nm)]
    for m, tag, d, ch, inv, gr, rh in rows:
        if ch or gr or inv or rh.startswith("rest_") and False: continue
        if rh.startswith("rest_0") : continue
        out[m][tag] += d
    return [dict(o) for o in out]

if __name__ == "__main__":
    t = open(sys.argv[1]).read()
    for bi, (evs, s) in enumerate(events(t)): print(bi, {k: str(v) for k, v in s.items()}, len(evs))
