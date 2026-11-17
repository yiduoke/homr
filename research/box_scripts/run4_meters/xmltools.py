"""MusicXML window / meter tools for the meter arm (all on MuseScore-exported score-partwise files).

segment(root, part_idx, m0, m1)  -> bars m0..m1-1 of one part with the attribute state in front
assemble(segments)               -> one score with one part (segments joined at barlines)
set_meter(measures, beats, beat_type, symbol)   same-duration meter relabel (bars stay as they are)
retime(measures, factor)         note values x factor (0.5 halves, 2 doubles), meter beat-type x 1/factor
check_bars(root)                 every bar fills its meter (pickup allowed in the first bar)
Everything works on copies; sources are never changed.
"""
import copy
import xml.etree.ElementTree as ET

TYPES = ["1024th", "512th", "256th", "128th", "64th", "32nd", "16th", "eighth", "quarter", "half", "whole", "breve", "long"]
TYPE_IDX = {t: i for i, t in enumerate(TYPES)}
STATE_ORDER = ["divisions", "key", "time", "staves", "clef"]
DROP_ATTRS = ("default-x", "default-y", "relative-x", "relative-y", "font-size", "font-family", "font-weight", "font-style")


# ----------------------------------------------------------------------------- state
def _first_attr_block(measure):
    """Attribute elements before the first note/backup/forward of the measure."""
    out = []
    for el in measure:
        if el.tag == "attributes":
            out.append(el)
        elif el.tag in ("note", "backup", "forward"):
            break
    return out


def attribute_state(part, upto, include_first_block=True):
    """The divisions/key/time/staves/clef in force at the start of measure `upto` (0-based) of the part element."""
    state = {"clef": {}}
    for mi, m in enumerate(part.findall("measure")):
        if mi > upto:
            break
        blocks = m.findall("attributes") if mi < upto else (_first_attr_block(m) if include_first_block else [])
        for att in blocks:
            for ch in att:
                if ch.tag in ("divisions", "key", "time", "staves"):
                    if ch.tag == "time" and "time" in state and False:
                        pass
                    state[ch.tag] = copy.deepcopy(ch)
                elif ch.tag == "clef":
                    state["clef"][ch.get("number", "1")] = copy.deepcopy(ch)
    return state


def state_element(state):
    att = ET.Element("attributes")
    for tag in STATE_ORDER:
        if tag == "clef":
            for k in sorted(state.get("clef", {})):
                att.append(copy.deepcopy(state["clef"][k]))
        elif tag in state:
            att.append(copy.deepcopy(state[tag]))
    return att


def _sig(el):
    """Canonical content of an attribute child (key: fifths+mode, time: beats/type/symbol, clef: sign/line)."""
    if el is None:
        return None
    if el.tag == "key":
        return ("key", el.findtext("fifths"), el.findtext("mode") or "")
    if el.tag == "time":
        return ("time", el.findtext("beats"), el.findtext("beat-type"), el.get("symbol") or "")
    if el.tag == "clef":
        return ("clef", el.findtext("sign"), el.findtext("line"), el.findtext("clef-octave-change") or "")
    return (el.tag, (el.text or "").strip())


def apply_attributes(state, att):
    for ch in att:
        if ch.tag in ("divisions", "key", "time", "staves"):
            state[ch.tag] = copy.deepcopy(ch)
        elif ch.tag == "clef":
            state["clef"][ch.get("number", "1")] = copy.deepcopy(ch)


def end_state_of(measures, start_state):
    st = {k: (dict(v) if k == "clef" else v) for k, v in start_state.items()}
    for m in measures:
        for att in m.findall("attributes"):
            apply_attributes(st, att)
    return st


def diff_state(prev, cur, force=()):
    """Attributes element holding what changes from prev to cur (None if nothing); divisions always shown for the first."""
    att = ET.Element("attributes")
    for tag in STATE_ORDER:
        if tag == "clef":
            for k in sorted(cur.get("clef", {})):
                if prev is None or _sig(prev.get("clef", {}).get(k)) != _sig(cur["clef"][k]) or "clef" in force:
                    att.append(copy.deepcopy(cur["clef"][k]))
        elif tag in cur:
            if prev is None or _sig(prev.get(tag)) != _sig(cur[tag]) or tag in force:
                att.append(copy.deepcopy(cur[tag]))
    return att if len(att) else None


# ----------------------------------------------------------------------------- cleaning
def strip_layout(el):
    for e in el.iter():
        for a in DROP_ATTRS:
            if a in e.attrib:
                del e.attrib[a]
        for a in ("width",):
            if e.tag == "measure" and a in e.attrib:
                del e.attrib[a]


def _remove(parent_map, el):
    p = parent_map.get(el)
    if p is not None:
        p.remove(el)


def clean_measures(measures):
    """Layout hints, lyrics, endings, text-only directions' offsets removed; unmatched spanners dropped."""
    for m in measures:
        for pr in m.findall("print"):
            m.remove(pr)
        for el in list(m):
            if el.tag == "barline":
                for e in el.findall("ending"):
                    el.remove(e)
        strip_layout(m)
        for n in m.findall("note"):
            for ly in n.findall("lyric"):
                n.remove(ly)
    _drop_unmatched(measures)


def _drop_unmatched(measures):
    pmap = {}
    for m in measures:
        for p in m.iter():
            for c in p:
                pmap[c] = p
    # ties: <tie> and <tied> by (staff, voice, pitch)
    pending = {}
    notes = [n for m in measures for n in m.findall("note")]
    for n in notes:
        pitch = n.find("pitch")
        key = None
        if pitch is not None:
            key = (n.findtext("staff"), pitch.findtext("step"), pitch.findtext("octave"), pitch.findtext("alter") or "0")
        ties = n.findall("tie")
        tieds = n.findall(".//tied")
        types = {t.get("type") for t in ties} | {t.get("type") for t in tieds}
        if key is None:
            continue
        if "stop" in types:
            if key in pending:
                del pending[key]
            else:
                for t in ties + tieds:
                    if t.get("type") == "stop":
                        _remove(pmap, t)
        if "start" in types:
            pending[key] = n
    for key, n in pending.items():
        for t in n.findall("tie") + n.findall(".//tied"):
            if t.get("type") == "start":
                _remove(pmap, t)
    # slurs and other spanners
    for tag in ("slur", "wedge", "bracket", "dashes", "pedal", "glissando", "slide"):
        pend = {}
        for m in measures:
            for el in m.iter(tag):
                ty = el.get("type")
                num = (tag, el.get("number", "1"))
                if ty in ("stop",):
                    if num in pend:
                        pend.pop(num)
                    else:
                        _remove_spanner(pmap, el)
                elif ty in ("start", "crescendo", "diminuendo"):
                    if num in pend:
                        pass
                    pend[num] = el
        for el in pend.values():
            _remove_spanner(pmap, el)


def _remove_spanner(pmap, el):
    p = pmap.get(el)
    if p is None:
        return
    p.remove(el)
    # direction-type left empty: remove it and an empty direction
    if p.tag == "direction-type" and len(p) == 0:
        d = pmap.get(p)
        if d is not None:
            d.remove(p)
            if d.tag == "direction" and d.find("direction-type") is None:
                dd = pmap.get(d)
                if dd is not None:
                    dd.remove(d)


# ----------------------------------------------------------------------------- segments
def part_measures(root, part_idx):
    return root.findall("part")[part_idx].findall("measure")


def segment(root, part_idx, m0, m1, drop_lyrics=True):
    """Copy of bars m0..m1-1 of the part, with attributes state at the front; returns (measures, end_state)."""
    part = root.findall("part")[part_idx]
    meas = part.findall("measure")
    state = attribute_state(part, m0)
    out = [copy.deepcopy(m) for m in meas[m0:m1]]
    # the state at m0 includes the leading attribute blocks of that measure: take them out of the copy
    for att in _first_attr_block(out[0]):
        out[0].remove(att)
    clean_measures(out)
    # end state
    end_state = attribute_state(part, m1 - 1, include_first_block=True)
    for mi in range(m1 - 1, m1):
        for att in meas[mi].findall("attributes"):
            for ch in att:
                if ch.tag in ("divisions", "key", "time", "staves"):
                    end_state[ch.tag] = copy.deepcopy(ch)
                elif ch.tag == "clef":
                    end_state["clef"][ch.get("number", "1")] = copy.deepcopy(ch)
    return out, state, end_state


def scale_divisions(measures, state, factor):
    """Multiply durations (and divisions) by an integer factor."""
    if factor == 1:
        return
    for m in measures:
        for tag in ("duration",):
            for d in m.iter(tag):
                d.text = str(int(d.text) * factor)
        for att in m.findall("attributes"):
            d = att.find("divisions")
            if d is not None:
                d.text = str(int(d.text) * factor)
        for off in m.iter("offset"):
            off.text = str(int(float(off.text)) * factor)
    if "divisions" in state:
        state["divisions"].text = str(int(state["divisions"].text) * factor)


def double_divisions(measures, state):
    """Halving the note values: durations stay, divisions double."""
    for m in measures:
        for att in m.findall("attributes"):
            d = att.find("divisions")
            if d is not None:
                d.text = str(int(d.text) * 2)
    if "divisions" in state:
        state["divisions"].text = str(int(state["divisions"].text) * 2)


def assemble(segments):
    """segments: list of (measures, start_state); returns a score-partwise root with a single part.
    Attributes at the junction: the first segment gets the full state, later ones only what changes
    against the state at the end of the previous segment."""
    root = ET.Element("score-partwise", version="4.0")
    pl = ET.SubElement(root, "part-list")
    sp = ET.SubElement(pl, "score-part", id="P1")
    ET.SubElement(sp, "part-name").text = ""
    part = ET.SubElement(root, "part", id="P1")
    prev_end = None
    num = 0
    for measures, state in segments:
        att = diff_state(prev_end, state) if prev_end is not None else state_element(state)
        if att is not None:
            idx = 0
            for i, el in enumerate(measures[0]):
                if el.tag == "barline":
                    idx = i + 1
                else:
                    break
            measures[0].insert(idx, att)
        for m in measures:
            num += 1
            m.set("number", str(num))
            part.append(m)
        prev_end = end_state_of(measures, state)
    return root


def to_string(root):
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" "http://www.musicxml.org/dtds/partwise.dtd">\n' + ET.tostring(root, encoding="unicode")


# ----------------------------------------------------------------------------- meter operations
def _time_elements(measures):
    return [t for m in measures for att in m.findall("attributes") for t in att.findall("time")]


def set_time_el(t, beats, beat_type, symbol=""):
    for ch in list(t):
        t.remove(ch)
    for k in list(t.attrib):
        del t.attrib[k]
    if symbol:
        t.set("symbol", symbol)
    ET.SubElement(t, "beats").text = str(beats)
    ET.SubElement(t, "beat-type").text = str(beat_type)


def set_meter(measures, state, beats, beat_type, symbol=""):
    """Relabel the meter of these bars (same duration): the time element at the front and every restatement."""
    if "time" in state:
        set_time_el(state["time"], beats, beat_type, symbol)
    for m in measures:
        for att in m.findall("attributes"):
            for t in att.findall("time"):
                set_time_el(t, beats, beat_type, symbol)


def _shift_type(el, k):
    t = el.text
    if t not in TYPE_IDX:
        return False
    i = TYPE_IDX[t] + k
    if i < TYPE_IDX["64th"] or i > TYPE_IDX["whole"]:
        return False
    el.text = TYPES[i]
    return True


def retime(measures, state, factor):
    """Halve (factor 0.5) or double (factor 2) every note value; returns False when a value leaves the vocabulary range."""
    k = 1 if factor == 2 else -1  # TYPES run from short to long
    # check first
    for m in measures:
        for tag in ("type", "normal-type", "tuplet-type"):
            for el in m.iter(tag):
                t = el.text
                if t not in TYPE_IDX:
                    return False
                i = TYPE_IDX[t] + k
                if i < TYPE_IDX["64th"] or i > TYPE_IDX["whole"]:
                    return False
    for m in measures:
        for tag in ("type", "normal-type", "tuplet-type"):
            for el in m.iter(tag):
                _shift_type(el, k)
        for n in m.iter("note"):
            beams = n.findall("beam")
            if not beams:
                continue
            old = {int(b.get("number", "1")): b.text for b in beams}
            idx = list(n).index(beams[0])
            for b in beams:
                n.remove(b)
            new = {}
            if factor == 0.5:
                new[1] = old.get(1)
                new[2] = old.get(1)
                for kk, v in old.items():
                    if kk >= 2:
                        new[kk + 1] = v
            else:
                for kk, v in old.items():
                    if kk >= 2:
                        new[kk - 1] = v
            for j, num in enumerate(sorted(x for x in new if new[x])):
                b = ET.Element("beam", number=str(num))
                b.text = new[num]
                n.insert(idx + j, b)
    # divisions and meter
    def fix_time(t):
        beats, bt = t.findtext("beats"), int(t.findtext("beat-type"))
        nbt = bt * 2 if factor == 0.5 else bt // 2
        set_time_el(t, beats, nbt, "")

    if factor == 0.5:
        double_divisions(measures, state)
    if "time" in state:
        fix_time(state["time"])
    for m in measures:
        for att in m.findall("attributes"):
            for t in att.findall("time"):
                fix_time(t)
    return True


def retime_double(measures, state):
    """Doubling note values: durations stay, divisions halve. Needs every divisions value even."""
    d = state.get("divisions")
    if d is None or int(d.text) % 2:
        return False
    for m in measures:
        for att in m.findall("attributes"):
            dd = att.find("divisions")
            if dd is not None and int(dd.text) % 2:
                return False
    ok = retime(measures, state, 2)
    if not ok:
        return False
    d.text = str(int(d.text) // 2)
    for m in measures:
        for att in m.findall("attributes"):
            dd = att.find("divisions")
            if dd is not None:
                dd.text = str(int(dd.text) // 2)
    return True


# ----------------------------------------------------------------------------- checks
def bar_duration(measure):
    cursor = maxc = 0
    for el in measure:
        if el.tag == "note":
            if el.find("grace") is not None:
                continue
            if el.find("chord") is None:
                cursor += int(el.findtext("duration") or 0)
        elif el.tag == "backup":
            cursor -= int(el.findtext("duration") or 0)
        elif el.tag == "forward":
            cursor += int(el.findtext("duration") or 0)
        maxc = max(maxc, cursor)
    return maxc


def check_bars(root, allow_pickup=True):
    """(ok, problems): every bar must fill its meter."""
    problems = []
    part = root.find("part")
    divisions = None
    meter = None
    for i, m in enumerate(part.findall("measure")):
        for att in m.findall("attributes"):
            d = att.findtext("divisions")
            if d:
                divisions = int(d)
            for t in att.findall("time"):
                meter = (int(t.findtext("beats")), int(t.findtext("beat-type")))
        if meter is None or divisions is None:
            problems.append((i + 1, "no meter"))
            continue
        exp = meter[0] * 4 * divisions / meter[1]
        got = bar_duration(m)
        if abs(got - exp) > 1e-6 and not (allow_pickup and i == 0 and m.get("implicit") == "yes" and got < exp):
            problems.append((i + 1, f"{got}/{exp}"))
    return not problems, problems


TYPE_Q = {"1024th": 1 / 256, "512th": 1 / 128, "256th": 1 / 64, "128th": 1 / 32, "64th": 1 / 16, "32nd": 1 / 8, "16th": 1 / 4,
          "eighth": 1 / 2, "quarter": 1, "half": 2, "whole": 4, "breve": 8, "long": 16}


def check_types(root):
    """Every note's <type> (with dots and tuplet ratio) must match its <duration> in divisions."""
    problems = []
    part = root.find("part")
    divisions = None
    for i, m in enumerate(part.findall("measure")):
        for att in m.findall("attributes"):
            d = att.findtext("divisions")
            if d:
                divisions = int(d)
        for n in m.findall("note"):
            if n.find("grace") is not None or n.findtext("type") is None or n.findtext("duration") is None:
                continue
            if n.find("rest") is not None and n.find("rest").get("measure") == "yes":
                continue
            q = TYPE_Q[n.findtext("type")] * (2 - 2 ** -len(n.findall("dot")))
            tm = n.find("time-modification")
            if tm is not None:
                q *= int(tm.findtext("normal-notes")) / int(tm.findtext("actual-notes"))
            got = int(n.findtext("duration")) / divisions
            if abs(got - q) > 1e-9:
                problems.append((i + 1, n.findtext("type"), got, q))
    return not problems, problems


def meters_of(root):
    out = []
    meter = None
    for m in root.find("part").findall("measure"):
        for att in m.findall("attributes"):
            for t in att.findall("time"):
                meter = f"{t.findtext('beats')}/{t.findtext('beat-type')}" + (":" + t.get("symbol") if t.get("symbol") else "")
        out.append(meter)
    return out


# ----------------------------------------------------------------------------- merging bars
def merge_measures(bars, beats, beat_type, symbol=""):
    """One bar from several consecutive bars (same divisions): the later bars' notes follow in time.
    The time element of the result (if the first bar carries one) is set to beats/beat-type."""
    first = copy.deepcopy(bars[0])
    # right barline of the first bar goes (the last bar's one is kept)
    out = ET.Element("measure", dict(first.attrib))
    total = 0
    for j, bar in enumerate(bars):
        bar = copy.deepcopy(bar)
        dur = bar_duration(bar)
        cursor = 0
        for el in list(bar):
            if el.tag == "barline":
                loc = el.get("location", "right")
                if (j > 0 and loc == "left") or (j < len(bars) - 1 and loc == "right"):
                    continue
            if el.tag == "attributes" and j > 0:
                for t in el.findall("time"):
                    el.remove(t)
                if len(el) == 0:
                    continue
            if el.tag == "note" and el.find("grace") is None and el.find("chord") is None:
                cursor += int(el.findtext("duration") or 0)
            elif el.tag == "backup":
                cursor -= int(el.findtext("duration") or 0)
            elif el.tag == "forward":
                cursor += int(el.findtext("duration") or 0)
            out.append(el)
        if j < len(bars) - 1 and cursor < dur:
            fw = ET.SubElement(out, "forward")
            ET.SubElement(fw, "duration").text = str(dur - cursor)
        elif j < len(bars) - 1 and cursor > dur:
            raise ValueError("cursor beyond bar")
        total += dur
    for att in out.findall("attributes"):
        for t in att.findall("time"):
            set_time_el(t, beats, beat_type, symbol)
    return out, total


def merge_k(measures, state, k, new_beats, new_type, symbol=""):
    """Merge every k consecutive bars (len(measures) must be a multiple of k) into one bar of the new meter."""
    out = []
    for i in range(0, len(measures), k):
        m, _ = merge_measures(measures[i : i + k], new_beats, new_type, symbol)
        out.append(m)
    if "time" in state:
        set_time_el(state["time"], new_beats, new_type, symbol)
    return out
