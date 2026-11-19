"""Score-level continuation of tuplet ratios (D54).

Reads the MusicXML of a transcription (after systems and pages are joined), and, per voice, applies the last explicit
tuplet ratio (for example 3 in the time of 2) to a later group of ordinary durations of the same shape, but ONLY when the
evidence of the bar distinguishes the two readings. Nothing is trained, no recognition code is touched, the default is OFF:
`apply_if_enabled()` returns the input unchanged unless the environment variable HOMR_TUPLET_PASS=1 is set.

What is written: `<time-modification>` on the notes of a converted group and the shortened `<duration>`; the `<backup>` and
`<forward>` elements of the bar are recomputed so that the other voices keep their onsets. No `<tuplet>` notation is added, so
no numeral or bracket is drawn (the group looks as it looks in the print).

Evidence used (all of it from the MusicXML; the page geometry, and therefore the physical beam width, is not available here):
  bar    the sum of the voice in the bar against the bar length of the time signature: ordinary reading overfull and the
         ratio reading exactly full (an ordinary bar that fits is never changed)
  align  onsets of the other voices of the part (and the other part): the ratio reading makes more onsets of the other
         voices coincide with the converted group's own onsets
  shape  same number of slots, same written value, same beam endpoints, same rests as the last explicit group of the voice

Ambiguity rules: a bar where more than one subset of the candidate groups would fit, a group whose edge falls inside a note
of another voice, a voice without an explicit group earlier, a bar with a voice change of staff are left as read.
"""
from __future__ import annotations

import copy
import os
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations

TYPE_Q = {  # written note value -> quarter notes
    "whole": Fraction(4), "half": Fraction(2), "quarter": Fraction(1), "eighth": Fraction(1, 2),
    "16th": Fraction(1, 4), "32nd": Fraction(1, 8), "64th": Fraction(1, 16), "128th": Fraction(1, 32),
}
BEAMABLE = {"eighth", "16th", "32nd", "64th", "128th"}


def enabled() -> bool:
    """On by default (homr/combined_switches.py); HOMR_TUPLET_PASS=0 or HOMR_COMBINED_OFF=C turns it off."""
    try:
        from homr.combined_switches import tuplet_pass
    except ImportError:  # the script is used without the homr package on the path
        return os.environ.get("HOMR_TUPLET_PASS") == "1"
    return tuplet_pass()


# ---------------------------------------------------------------------------------------------------------------------
# parsing


@dataclass
class Note:
    el: ET.Element
    part: int
    mi: int            # measure index within the part
    voice: str
    staff: int
    onset: Fraction    # quarters from the start of the bar (in the file's timeline)
    dur: Fraction      # quarters
    type: str | None
    dots: int
    tm: tuple[int, int] | None  # (actual, normal)
    tup: str | None    # 'start' / 'stop' / None (explicit tuplet notation)
    beam: str | None   # level-1 beam state
    rest: bool
    chord: bool
    grace: bool
    whole_bar_rest: bool = False
    sidx: int = -1     # index among the notes the scorer counts in this bar (pitched, visible), -1 for rests
    pitch: str = ""


@dataclass
class Slot:
    """Notes of one voice which start together (a chord, or one rest)."""
    notes: list[Note]

    @property
    def onset(self) -> Fraction:
        return self.notes[0].onset

    @property
    def dur(self) -> Fraction:
        return max(n.dur for n in self.notes)

    @property
    def type(self):
        return self.notes[0].type

    @property
    def rest(self) -> bool:
        return all(n.rest for n in self.notes)

    @property
    def tm(self):
        return self.notes[0].tm

    @property
    def beam(self):
        for n in self.notes:
            if n.beam:
                return n.beam
        return None

    @property
    def dots(self):
        return self.notes[0].dots

    @property
    def tup(self):
        for n in self.notes:
            if n.tup:
                return n.tup
        return None


@dataclass
class VoiceBar:
    part: int
    mi: int
    voice: str
    slots: list[Slot] = field(default_factory=list)

    @property
    def total(self) -> Fraction:
        return max((s.onset + s.dur for s in self.slots), default=Fraction(0))


@dataclass
class Bar:
    part: int
    mi: int
    el: ET.Element
    number: str
    length: Fraction | None        # nominal length from the time signature (quarters)
    divisions: int
    voices: dict[str, VoiceBar] = field(default_factory=dict)
    notes: list[Note] = field(default_factory=list)
    new_time: bool = False
    beats: int | None = None
    beat_type: int | None = None


def _frac(text: str | None, default: int = 0) -> int:
    return int(text) if text not in (None, "") else default


def parse_part(part: ET.Element, pi: int) -> list[Bar]:
    divisions = 1
    length: Fraction | None = None
    beats = beat_type = None
    bars: list[Bar] = []
    for mi, meas in enumerate(part.findall("measure")):
        new_time = False
        cursor = 0
        bar = Bar(pi, mi, meas, meas.get("number", str(mi + 1)), None, divisions)
        last_onset = 0
        scorer_idx = 0
        for el in list(meas):
            tag = el.tag
            if tag == "attributes":
                d = el.find("divisions")
                if d is not None:
                    divisions = int(d.text)
                t = el.find("time")
                if t is not None:
                    b, bt = t.findtext("beats"), t.findtext("beat-type")
                    try:
                        length = Fraction(int(b)) * 4 / int(bt)
                        beats, beat_type = int(b), int(bt)
                    except (TypeError, ValueError):
                        length = None
                        beats = beat_type = None
                    new_time = True
            elif tag == "backup":
                cursor -= int(el.findtext("duration"))
            elif tag == "forward":
                cursor += int(el.findtext("duration"))
            elif tag == "note":
                grace = el.find("grace") is not None
                chord = el.find("chord") is not None
                dur = Fraction(0) if grace else Fraction(int(el.findtext("duration", "0")), divisions)
                onset = Fraction(last_onset, divisions) if chord else Fraction(cursor, divisions)
                if not chord:
                    last_onset = cursor
                if not grace and not chord:
                    cursor += int(el.findtext("duration", "0"))
                tm = el.find("time-modification")
                tmv = None
                if tm is not None:
                    tmv = (int(tm.findtext("actual-notes")), int(tm.findtext("normal-notes")))
                tup = None
                for t in el.findall("notations/tuplet"):
                    tup = t.get("type")
                beam = None
                for b in el.findall("beam"):
                    if b.get("number", "1") == "1":
                        beam = b.text
                rest_el = el.find("rest")
                pitch_el = el.find("pitch")
                hidden = el.get("print-object") == "no" or any((h.text or "").strip() == "none" for h in el.findall("notehead"))
                n = Note(el, pi, mi, el.findtext("voice", "1"), _frac(el.findtext("staff"), 1), onset, dur,
                         el.findtext("type"), len(el.findall("dot")), tmv, tup, beam, rest_el is not None, chord, grace,
                         rest_el is not None and rest_el.get("measure") == "yes")
                if pitch_el is not None and not hidden:
                    n.sidx = scorer_idx
                    scorer_idx += 1
                if pitch_el is not None:
                    n.pitch = (pitch_el.findtext("step") or "") + (pitch_el.findtext("alter") or "") + (pitch_el.findtext("octave") or "")
                bar.notes.append(n)
        bar.divisions = divisions
        bar.length = length
        bar.new_time = new_time
        bar.beats, bar.beat_type = beats, beat_type
        for n in bar.notes:
            if n.grace:
                continue
            vb = bar.voices.setdefault(n.voice, VoiceBar(pi, mi, n.voice))
            if vb.slots and not n.chord and vb.slots[-1].notes[0].onset == n.onset and n.rest == vb.slots[-1].rest:
                vb.slots[-1].notes.append(n)
            elif vb.slots and n.chord:
                vb.slots[-1].notes.append(n)
            else:
                vb.slots.append(Slot([n]))
        for vb in bar.voices.values():
            vb.slots.sort(key=lambda s: s.onset)
        bars.append(bar)
    return bars


def parse_score(root: ET.Element) -> list[list[Bar]]:
    return [parse_part(p, i) for i, p in enumerate(root.findall("part"))]


# ---------------------------------------------------------------------------------------------------------------------
# groups


def slot_sig(s: Slot) -> tuple:
    return (s.type, s.dots, s.rest, s.beam if s.type in BEAMABLE else None)


@dataclass
class Group:
    vb: VoiceBar
    i0: int
    i1: int                       # slots [i0, i1)
    sig: tuple
    ratio: tuple[int, int] | None  # (actual, normal) for an explicit group
    tm_el: ET.Element | None = None  # <time-modification> element of an explicit group (to copy)

    @property
    def slots(self) -> list[Slot]:
        return self.vb.slots[self.i0:self.i1]

    @property
    def start(self) -> Fraction:
        return self.vb.slots[self.i0].onset

    @property
    def end(self) -> Fraction:
        return max(s.onset + s.dur for s in self.slots)

    @property
    def span(self) -> Fraction:
        return sum((s.dur for s in self.slots), Fraction(0))


def explicit_groups(vb: VoiceBar) -> list[Group]:
    """Runs of slots which carry a time-modification, cut at tuplet start/stop notations and at changes of the ratio."""
    out: list[Group] = []
    i = 0
    sl = vb.slots
    while i < len(sl):
        if sl[i].tm is None:
            i += 1
            continue
        j = i + 1
        while j < len(sl) and sl[j].tm == sl[i].tm and sl[j].tup != "start" and sl[j - 1].tup != "stop":
            j += 1
        tm_el = sl[i].notes[0].el.find("time-modification")
        out.append(Group(vb, i, j, tuple(slot_sig(s) for s in sl[i:j]), sl[i].tm, tm_el))
        i = j
    return out


def plain_slot(s: Slot) -> bool:
    return s.tm is None and s.type in TYPE_Q and not any(n.grace for n in s.notes)


def candidate_windows(vb: VoiceBar, sig: tuple) -> list[Group]:
    """Non-overlapping windows of ordinary slots, contiguous in time, with the signature `sig` (value, dots, rest, beam
    position of each slot). The slot before the window must not continue its beam and the slot after must not be a
    continuation of it, so a window is a complete group."""
    k = len(sig)
    out: list[Group] = []
    sl = vb.slots
    i = 0
    while i + k <= len(sl):
        w = sl[i:i + k]
        ok = all(plain_slot(s) for s in w) and tuple(slot_sig(s) for s in w) == sig
        if ok:
            for a, b in zip(w, w[1:]):
                if a.onset + a.dur != b.onset:
                    ok = False
        if ok and i > 0:  # the slot before must not carry on the beam
            prev = sl[i - 1]
            if prev.beam in ("begin", "continue") and sig[0][3] != "begin":
                ok = False
        if ok and i + k < len(sl):
            nxt = sl[i + k]
            if nxt.beam in ("continue", "end"):
                ok = False
        if ok:
            out.append(Group(vb, i, i + k, sig, None))
            i += k
        else:
            i += 1
    return out


# ---------------------------------------------------------------------------------------------------------------------
# decision

DEFAULTS = dict(
    compound="skip",      # 'skip': never convert a group of the beat unit in a compound meter (6/8, 9/8, 12/8, 9/16 ...)
    align="tiebreak",     # alignment with the other voices only chooses between several subsets which fit the bar (margin of 2 onsets), it never vetoes (dev: a veto lost 54 recoveries for 1 false correction); "veto" and "off" are kept for the record
    max_gap_bars=64,      # an explicit group older than this many bars (in the same voice) is forgotten
    min_excess=Fraction(1, 96),
    merger_voices="skip",  # a bar of a part where merge_pages split a voice (ids >= 90) is not touched
    quarter_groups=True,  # 3 quarters in the time of 2 etc.
    same_voice_only=True,
    barfill=None,         # None: barfill_enabled() (HOMR_TUPLET_BARFILL, default on)
    skip_rest_only=True,  # D54: False reproduces the configuration of the final run (rest-only groups were converted in 3 bars of Petrushka)
)
EPS = Fraction(1, 192)


def is_merger_voice(v: str) -> bool:
    return v.isdigit() and int(v) >= 90


def is_compound(length: Fraction | None, bar: Bar) -> bool:
    if length is None:
        return False
    # nominal numerator/denominator from the time signature element (length is in quarters): 6/8 = 3, 9/8 = 4.5, 12/8 = 6
    num = bar.beats
    den = bar.beat_type
    return num is not None and den is not None and num in (6, 9, 12) and den in (4, 8, 16)


@dataclass
class Decision:
    part: int
    mi: int
    number: str
    voice: str
    status: str             # 'converted' or 'skip:<reason>'
    evidence: str
    meter: str
    length: Fraction
    total: Fraction
    ratio: tuple[int, int]
    sig: tuple
    n_candidates: int
    n_converted: int
    windows: list = field(default_factory=list)   # [(start_quarters, end_quarters, [(sidx, pitch)...])]
    after_explicit: bool = False                  # the group directly follows an explicit group of the voice (previous slot run)
    state_age: int = 0                            # bars since the explicit group was last seen
    align_before: int = 0
    align_after: int = 0


@dataclass
class Known:
    ratio: tuple[int, int]
    tm_el: ET.Element
    last_mi: int


def _new_time(t: Fraction, windows: list[tuple[Fraction, Fraction, Fraction]]) -> Fraction:
    """Old onset -> new onset of a voice whose windows (start, end, factor n/a) are compressed."""
    shift = Fraction(0)
    for s, e, f in windows:
        if e <= t:
            shift += (e - s) * (1 - f)
        elif s < t:
            shift += (t - s) * (1 - f)
    return t - shift


def _align_score(vb: VoiceBar, sel: list[Group], factors: list[Fraction], others: set[Fraction]) -> int:
    wins = [(g.start, g.end, f) for g, f in zip(sel, factors)]
    return sum(1 for s in vb.slots if _new_time(s.onset, wins) in others)


def _other_onsets(bars_by_part: list[list[Bar]], pi: int, mi: int, vid: str) -> set[Fraction] | None:
    """Onsets of every other voice of the bar (same part, and the other parts when all parts have the same number of bars)."""
    out: set[Fraction] = set()
    for qi, bars in enumerate(bars_by_part):
        if qi != pi and len(bars) != len(bars_by_part[pi]):
            continue
        if mi >= len(bars):
            continue
        for v, ovb in bars[mi].voices.items():
            if qi == pi and v == vid:
                continue
            for s in ovb.slots:
                out.add(s.onset)
    return out


def fit_subsets(vb: VoiceBar, L: Fraction, windows: list[Group], known_for: dict, params: dict):
    """All subsets of the candidate windows whose conversion makes the voice exactly as long as the bar. Needs an overfull voice."""
    if L is None:
        return [], "no_length"
    excess = vb.total - L
    if excess < params["min_excess"]:
        return [], "bar_fits"
    ratios = [known_for[w] for w in range(len(windows))]
    factors = [Fraction(r.ratio[1], r.ratio[0]) for r in ratios]
    reductions = [w.span * (1 - f) for w, f in zip(windows, factors)]
    k = len(windows)
    sols: list[tuple[int, ...]] = []
    if k <= 14:
        for m in range(1, k + 1):
            for sub in combinations(range(k), m):
                if sum(reductions[i] for i in sub) == excess:
                    sols.append(sub)
    if not sols:
        return [], "no_fit"
    return sols, ""


def apply_windows(bar: Bar, sel: list[Group], ratios: list[Known]) -> bool:
    """Write time-modification and shortened durations on the notes of the selected windows. Returns False (and leaves the
    notes alone) when a duration would not stay an integer number of divisions."""
    for g, r in zip(sel, ratios):
        a, n = r.ratio
        for s in g.slots:
            for note in s.notes:
                old = int(note.el.findtext("duration"))
                if (old * n) % a:
                    return False
    for g, r in zip(sel, ratios):
        a, n = r.ratio
        for s in g.slots:
            for note in s.notes:
                el = note.el
                old = int(el.findtext("duration"))
                el.find("duration").text = str(old * n // a)
                tm = copy.deepcopy(r.tm_el)
                # time-modification goes after type/dot/accidental, before stem/beam/notations
                idx = 0
                for i, ch in enumerate(list(el)):
                    if ch.tag in ("duration", "tie", "cue", "voice", "type", "dot", "accidental"):
                        idx = i + 1
                el.insert(idx, tm)
    return True


def retime_bar(bar: Bar, converted: dict[str, list[tuple[Group, Known]]]) -> None:
    """Rewrite the backup / forward elements of the bar after the durations of some voices changed, so that every note
    keeps its place (notes of unchanged voices keep their onsets; notes of a changed voice follow their shortened group)."""
    meas = bar.el
    div = bar.divisions
    wins: dict[str, list[tuple[Fraction, Fraction, Fraction]]] = {}
    for v, lst in converted.items():
        wins[v] = sorted((g.start, g.end, Fraction(r.ratio[1], r.ratio[0])) for g, r in lst)
    note_of = {id(n.el): n for n in bar.notes}
    # recorded durations before the edit are not available any more for converted notes; use the parsed old values
    c_old = Fraction(0)
    c_new = Fraction(0)
    children = list(meas)
    # index of the last note element, to keep trailing backup/forward untouched
    last_note = max((i for i, ch in enumerate(children) if ch.tag == "note"), default=-1)
    for i, el in enumerate(children):
        if el.tag == "note":
            note = note_of[id(el)]
            if note.grace or note.chord:
                continue
            v = note.voice
            s_old = note.onset
            s_new = _new_time(s_old, wins[v]) if v in wins else s_old
            if s_new != c_new:
                d = c_new - s_new
                new_el = ET.Element("backup" if d > 0 else "forward")
                ET.SubElement(new_el, "duration").text = str(int(abs(d) * div))
                el_idx = list(meas).index(el)
                meas.insert(el_idx, new_el)
                c_new = s_new
            if v in wins:
                end_new = _new_time(s_old + note.dur, wins[v])
            else:
                end_new = s_old + note.dur
            c_new = end_new
        elif el.tag in ("backup", "forward"):
            if i > last_note:
                continue
            meas.remove(el)


def _follows_tuplet(bars: list[Bar], mi: int, vid: str, g: Group) -> bool:
    """The slot before the window (in the voice, also in the previous bar) carries a time-modification."""
    if g.i0 > 0:
        return g.vb.slots[g.i0 - 1].tm is not None
    if mi > 0 and vid in bars[mi - 1].voices and bars[mi - 1].voices[vid].slots:
        return bars[mi - 1].voices[vid].slots[-1].tm is not None
    return False


def _midi(pitch: str) -> int | None:
    """Midi number of the 'step alter octave' string of Note.pitch, None for a rest."""
    import re as _re
    m = _re.fullmatch(r"([A-G])(-?\d+(?:\.\d+)?)?(-?\d+)", pitch)
    if not m:
        return None
    base = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}[m[1]]
    return 12 * (int(m[3]) + 1) + base + int(float(m[2] or 0))


def _window_record(g: Group, bars: list[Bar], mi: int, vid: str) -> dict:
    notes = [(n.sidx, n.pitch) for s in g.slots for n in s.notes if not n.rest]
    events = [tuple(sorted((n.staff, _midi(n.pitch)) for n in s.notes if not n.rest)) for s in g.slots if not s.rest]
    return dict(start=g.start, end=g.end, notes=notes, after_tuplet=_follows_tuplet(bars, mi, vid, g), events=events, rests=sum(1 for s in g.slots if s.rest),
                n_slots=len(g.slots), value=g.sig[0][0])


def _post_onsets(vb: VoiceBar, sel: list[Group], factors: list[Fraction]) -> set[Fraction]:
    wins = [(g.start, g.end, f) for g, f in zip(sel, factors)]
    return {_new_time(s.onset, wins) for s in vb.slots}



# ---------------------------------------------------------------------------------------------------------------------
# bar fill: unnumbered tuplets deduced from the meter (branch tuplet-barfill)

# n notes of one written value in the time of m of them (only reductions: the plain reading overfills the bar)
TUPLET_NORMAL = {3: 2, 5: 4, 6: 4, 7: 4, 9: 8, 10: 8, 11: 8, 12: 8, 13: 8}
MAX_NODES = 100000


def barfill_enabled() -> bool:
    """On unless HOMR_TUPLET_BARFILL=0."""
    return os.environ.get("HOMR_TUPLET_BARFILL", "1") != "0"


@dataclass
class _Unit:
    i0: int
    i1: int
    options: list  # [(key, [(i0, i1, (actual, normal))...])]


def _same_shape(slots: list[Slot]) -> bool:
    return len({(s.type, s.dots) for s in slots}) == 1


def _contiguous(slots: list[Slot]) -> bool:
    return all(a.onset + a.dur == b.onset for a, b in zip(slots, slots[1:]))


def barfill_units(vb: VoiceBar) -> list[_Unit]:
    """Candidate groups of a voice: beam groups (begin ... end) and, without beams, maximal runs of one written value, each of
    plain slots of one written value in a row, with at least one sounding slot, all on one staff. A group has the options
    'n in the time of m' (TUPLET_NORMAL) and, when n is a multiple of 3 and above 3, 'triplets of three'."""
    sl = vb.slots
    units: list[_Unit] = []
    i = 0
    while i < len(sl):
        s = sl[i]
        if not plain_slot(s):
            i += 1
            continue
        j = i + 1
        if s.beam == "begin" and s.type in BEAMABLE:
            while j < len(sl) and plain_slot(sl[j]) and sl[j - 1].beam != "end" and (sl[j].beam in ("continue", "end") or (sl[j].beam is None and sl[j].rest)):
                j += 1
            if sl[j - 1].beam != "end":
                i += 1
                continue
        elif s.beam is None:
            while j < len(sl) and plain_slot(sl[j]) and sl[j].beam is None and (sl[j].type, sl[j].dots) == (s.type, s.dots):
                j += 1
        else:  # a beam continuation without its start in this bar
            i = j
            continue
        w = sl[i:j]
        n = len(w)
        if (n in TUPLET_NORMAL and _same_shape(w) and _contiguous(w) and any(not x.rest for x in w)
                and len({nn.staff for x in w for nn in x.notes}) == 1):
            m = TUPLET_NORMAL[n]
            options = [(("all", n, m), [(i, j, (n, m))])]
            if n % 3 == 0 and n > 3:
                options.append((("triples", n), [(i + k, i + k + 3, (3, 2)) for k in range(0, n, 3)]))
            units.append(_Unit(i, j, options))
        i = j
    return units


def _factors(vb: VoiceBar, segments: list) -> tuple:
    f = {}
    for a, b, (n, m) in segments:
        for k in range(a, b):
            f[k] = Fraction(m, n)
    return tuple(sorted(f.items()))


def barfill_solve(vb: VoiceBar, length: Fraction) -> tuple[str, list]:
    """('ok', segments) when exactly one assignment of tuplets to the groups of the voice makes it exactly as long as the bar,
    else ('no_fit' | 'ambiguous' | 'no_groups' | 'fits', [])."""
    excess = vb.total - length
    if excess < Fraction(1, 96):
        return "fits", []
    units = barfill_units(vb)
    if not units:
        return "no_groups", []
    sl = vb.slots
    found: dict[tuple, list] = {}
    nodes = [0]

    def red(segments) -> Fraction:
        return sum((sl[k].dur * (1 - Fraction(m, n)) for a, b, (n, m) in segments for k in range(a, b)), Fraction(0))

    def go(u: int, acc: Fraction, chosen: list) -> None:
        nodes[0] += 1
        if nodes[0] > MAX_NODES or len(found) > 1:
            return
        if acc == excess:
            key = _factors(vb, chosen)
            found.setdefault(key, list(chosen))
            return
        if u == len(units) or acc > excess:
            return
        go(u + 1, acc, chosen)
        for _, segs in units[u].options:
            go(u + 1, acc + red(segs), chosen + segs)

    go(0, Fraction(0), [])
    if nodes[0] > MAX_NODES or len(found) > 1:
        return "ambiguous", []
    if not found:
        return "no_fit", []
    return "ok", next(iter(found.values()))


def barfill_bar(bar: Bar, skip_voices: set[str], length: Fraction | None = None) -> tuple[dict[str, list], str]:
    """All overfull voices of the bar (those not in skip_voices) must each have exactly one fitting assignment; else nothing is
    changed. Returns ({voice: [(Group, Known)]}, status)."""
    length = bar.length if length is None else length  # the argument is for measurements (ceiling with the reference meter)
    if length is None or bar.el.get("implicit") == "yes":
        return {}, "no_length"
    out: dict[str, list] = {}
    for vid, vb in bar.voices.items():
        if vid in skip_voices or is_merger_voice(vid):
            continue
        status, segs = barfill_solve(vb, length)
        if status in ("fits", "no_groups") and vb.total - length < Fraction(1, 96):
            continue
        if status != "ok":
            return {}, status if status != "no_groups" else "no_groups"
        lst = []
        for a, b, (n, m) in segs:
            tm = ET.Element("time-modification")
            ET.SubElement(tm, "actual-notes").text = str(n)
            ET.SubElement(tm, "normal-notes").text = str(m)
            g = Group(vb, a, b, tuple(slot_sig(x) for x in vb.slots[a:b]), (n, m), tm)
            lst.append((g, Known((n, m), tm, bar.mi)))
        out[vid] = sorted(lst, key=lambda gk: gk[0].i0)
    return out, "ok" if out else "fits"


def process(root: ET.Element, params: dict | None = None, state: dict | None = None, mi_offset: int = 0) -> tuple[list[Decision], dict]:
    """Apply the pass to the score in place. Returns the decision log and counters.
    `state` (voice -> last explicit groups) and `mi_offset` let a caller carry the explicit ratios over several files in order (the page XML files)."""
    P = {**DEFAULTS, **(params or {})}
    bars_by_part = parse_score(root)
    if state is None:
        state = {}
    log: list[Decision] = []
    counters: dict[str, int] = {}
    nmax = max((len(b) for b in bars_by_part), default=0)
    equal_bars = len({len(b) for b in bars_by_part}) == 1
    for mi in range(nmax):
        items: dict[tuple[int, str], dict] = {}
        # ---- stage 1: candidates and the subsets which make the voice fit the bar
        for pi, bars in enumerate(bars_by_part):
            if mi >= len(bars):
                continue
            bar = bars[mi]
            has_merger = any(is_merger_voice(v) for v in bar.voices)
            for vid, vb in bar.voices.items():
                if is_merger_voice(vid) or not P.get("continuation", True):  # continuation=False: measurements of the bar-fill rule alone
                    continue
                st = state.setdefault((pi, vid) if P["same_voice_only"] else (pi, "*"), {})
                for sg in [sg for sg, k in st.items() if mi + mi_offset - k.last_mi > P["max_gap_bars"]]:
                    del st[sg]
                exp = explicit_groups(vb)
                wins: list[Group] = []
                known_for: list[Known] = []
                for sg, k in st.items():
                    for w in candidate_windows(vb, sg):
                        wins.append(w)
                        known_for.append(k)
                for g in exp:  # explicit groups earlier in this bar
                    for w in candidate_windows(vb, g.sig):
                        if w.start >= g.end and not any(x.i0 == w.i0 and x.i1 == w.i1 for x in wins):
                            wins.append(w)
                            known_for.append(Known(g.ratio, g.tm_el, mi + mi_offset))
                if P.get("skip_rest_only", False):  # added after the final run (D54 section 6): a group of rests alone is no evidence
                    keep = [i for i, w in enumerate(wins) if any(not n.rest for sl in w.slots for n in sl.notes)]
                    wins, known_for = [wins[i] for i in keep], [known_for[i] for i in keep]
                drop = set()
                for a in range(len(wins)):
                    for b in range(a + 1, len(wins)):
                        if wins[a].i0 < wins[b].i1 and wins[b].i0 < wins[a].i1:
                            drop.update((a, b))
                for g in exp:
                    st[g.sig] = Known(g.ratio, g.tm_el, mi + mi_offset)
                if not wins:
                    continue
                order = sorted((i for i in range(len(wins)) if i not in drop), key=lambda i: wins[i].i0)
                if not order:
                    counters["skip:overlap"] = counters.get("skip:overlap", 0) + 1
                    continue
                wins2 = [wins[i] for i in order]
                kf = [known_for[i] for i in order]
                it = dict(pi=pi, vid=vid, bar=bar, vb=vb, wins=wins2, kf=kf, st=st, reason="", sols=[], sel=None, evidence="")
                if has_merger and P["merger_voices"] == "skip":
                    it["reason"] = "merger_voice"
                elif any(len({n.staff for s in w.slots for n in s.notes}) > 1 for w in wins2):
                    it["reason"] = "cross_staff"   # a beam across the staves may have been cut: the voice assignment is uncertain
                elif P["compound"] == "skip" and is_compound(bar.length, bar) and all(
                    TYPE_Q.get(w.sig[0][0], 0) == Fraction(4, bar.beat_type or 4) and k.ratio == (3, 2) for w, k in zip(wins2, kf)
                ):
                    it["reason"] = "compound"
                elif bar.el.get("implicit") == "yes":
                    it["reason"] = "no_length"
                else:
                    it["sols"], it["reason"] = fit_subsets(vb, bar.length, wins2, {i: k for i, k in enumerate(kf)}, P)
                if not it["reason"]:
                    it["sel"] = list(it["sols"][0]) if len(it["sols"]) == 1 else None
                    it["evidence"] = "bar" if it["sel"] is not None else "bar+align?"
                items[(pi, vid)] = it
        # ---- stage 2: alignment with the onsets of the other voices (their state after their own conversion)
        def others_of(key):
            pi, vid = key
            out: set[Fraction] = set()
            for qi, bars in enumerate(bars_by_part):
                if qi != pi and not equal_bars:
                    continue
                if mi >= len(bars):
                    continue
                for v, ovb in bars[mi].voices.items():
                    if (qi, v) == key:
                        continue
                    it2 = items.get((qi, v))
                    if it2 is not None and it2["sel"]:
                        out |= _post_onsets(ovb, [it2["wins"][i] for i in it2["sel"]], [Fraction(it2["kf"][i].ratio[1], it2["kf"][i].ratio[0]) for i in it2["sel"]])
                    else:
                        out |= {s.onset for s in ovb.slots}
            return out
        def a_score(it, sel, others):
            f = [Fraction(it["kf"][i].ratio[1], it["kf"][i].ratio[0]) for i in sel]
            return len(_post_onsets(it["vb"], [it["wins"][i] for i in sel], f) & others)
        if P["align"] != "off":
            for _ in range(3):
                changed = False
                for key, it in items.items():
                    if it["reason"] or not it["sols"]:
                        continue
                    others = others_of(key)
                    if it["sel"] is None:  # several subsets fit the bar: the alignment must decide
                        sc = sorted(((a_score(it, list(sub), others), sub) for sub in it["sols"]), key=lambda x: -x[0])
                        if len(sc) > 1 and sc[0][0] - sc[1][0] >= 2:
                            it["sel"], it["evidence"] = list(sc[0][1]), "bar+align"
                            changed = True
                    if it["sel"] is not None and P["align"] == "veto":
                        if a_score(it, it["sel"], others) < a_score(it, [], others):
                            it["sel"], it["reason"], it["sols"] = None, "align_veto", []
                            changed = True
                if not changed:
                    break
        for key, it in items.items():  # record the alignment of every selection, whatever the mode
            if it["sel"] is not None and not it["reason"]:
                oth = others_of(key)
                it["a_with"], it["a_without"] = a_score(it, it["sel"], oth), a_score(it, [], oth)
        # ---- stage 3: apply and log
        converted_by_part: dict[int, dict[str, list[tuple[Group, Known]]]] = {}
        for key, it in items.items():
            pi, vid = key
            bar, vb, wins2, kf = it["bar"], it["vb"], it["wins"], it["kf"]
            reason = it["reason"] or ("" if it["sel"] is not None else "ambiguous_subset")
            sel = [wins2[i] for i in it["sel"]] if it["sel"] is not None else []
            rat = [kf[i] for i in it["sel"]] if it["sel"] is not None else []
            d = Decision(pi, mi, bar.number, vid, "converted" if sel else "skip:" + reason, it["evidence"] if sel else "", f"{bar.beats}/{bar.beat_type}",
                         bar.length or Fraction(0), vb.total, kf[0].ratio, wins2[0].sig, len(wins2), len(sel),
                         state_age=min(mi + mi_offset - k.last_mi for k in kf), align_before=it.get("a_without", 0), align_after=it.get("a_with", 0))
            if sel:
                if not apply_windows(bar, sel, rat):
                    d.status, d.n_converted, sel = "skip:non_integer", 0, []
                else:
                    converted_by_part.setdefault(pi, {})[vid] = list(zip(sel, rat))
                    for g, k in zip(sel, rat):
                        d.windows.append(_window_record(g, bars_by_part[pi], mi, vid))
                        it["st"][g.sig] = Known(k.ratio, k.tm_el, mi + mi_offset)
            for g in wins2:
                if not any(g is x for x in sel):
                    d.windows.append(_window_record(g, bars_by_part[pi], mi, vid))
            log.append(d)
            counters[d.status] = counters.get(d.status, 0) + 1
        if (P["barfill"] if P["barfill"] is not None else barfill_enabled()):
            for pi, bars in enumerate(bars_by_part):
                if mi >= len(bars):
                    continue
                bar = bars[mi]
                res, status = barfill_bar(bar, set(converted_by_part.get(pi, {})), (P.get("length_override") or {}).get((pi, mi)))
                if not res:
                    if status not in ("fits", "no_length"):
                        counters["skip:barfill_" + status] = counters.get("skip:barfill_" + status, 0) + 1
                    continue
                applied: dict[str, list] = {}
                failed = False
                for vid, lst in res.items():
                    if not apply_windows(bar, [g for g, _ in lst], [k for _, k in lst]):
                        failed = True
                        break
                    applied[vid] = lst
                if failed and applied:
                    counters["skip:barfill_non_integer_partial"] = counters.get("skip:barfill_non_integer_partial", 0) + 1
                for vid, lst in applied.items():
                    converted_by_part.setdefault(pi, {})[vid] = lst
                    vb = bar.voices[vid]
                    log.append(Decision(pi, mi, bar.number, vid, "converted", "barfill", f"{bar.beats}/{bar.beat_type}", bar.length or Fraction(0),
                                        vb.total, lst[0][1].ratio, lst[0][0].sig, len(lst), len(lst)))
                    counters["converted:barfill"] = counters.get("converted:barfill", 0) + 1
        for pi, conv in converted_by_part.items():
            retime_bar(bars_by_part[pi][mi], conv)
    return log, counters


def process_file(src: str, dst: str, params: dict | None = None):
    tree = ET.parse(src)
    log, counters = process(tree.getroot(), params)
    tree.write(dst, encoding="UTF-8", xml_declaration=True)
    return log, counters


def apply_if_enabled(src: str, dst: str, params: dict | None = None):
    """Default ON: copies src to dst unchanged when HOMR_TUPLET_PASS=0 (or HOMR_COMBINED_OFF=C)."""
    if not enabled():
        import shutil
        if os.path.abspath(src) != os.path.abspath(dst):
            shutil.copyfile(src, dst)
        return [], {}
    return process_file(src, dst, params)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--force", action="store_true", help="run even without HOMR_TUPLET_PASS=1")
    a = ap.parse_args()
    fn = process_file if a.force else apply_if_enabled
    log, c = fn(a.src, a.dst)
    print(c, file=sys.stderr)
