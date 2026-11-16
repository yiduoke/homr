"""
Piano music written on four staffs, two for each hand, becomes one part with two staves.

A system of four single staffs has no grand staff, so every staff would become a voice of
its own and the page a part with the wrong number of staves. If the clefs are two treble clefs
and two bass clefs, it is a piano system: the upper two staffs are read as the voices of the
right hand (positions upper and upper2), the lower two as the voices of the left hand (lower
and lower2). The tokens of the four staffs are merged measure by measure, by the time at which
each group starts.
"""

import copy
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction

from homr.music_xml_generator import GroupClock, SymbolChord
from homr.simple_logging import eprint
from homr.transformer.vocabulary import EncodedSymbol, nonote, sort_token_chords

STAFFS_PER_SYSTEM = 4
# Position of the voice which each staff (from the top) becomes
POSITIONS = ["upper", "upper2", "lower", "lower2"]
_CLOSING = ("barline", "repeatEnd")


@dataclass
class _Measure:
    """The groups of a measure of one staff."""

    header: list[list[EncodedSymbol]] = field(default_factory=list)
    # (onset, group) of notes, rests, dynamics and other symbols within the measure
    body: list[tuple[Fraction, list[EncodedSymbol]]] = field(default_factory=list)
    closing: list[EncodedSymbol] | None = None
    has_notes: bool = False


def _first_clef(staff: list[EncodedSymbol]) -> str | None:
    return next((s.rhythm for s in staff if s.rhythm.startswith("clef")), None)


def is_piano_system(staffs: list[list[EncodedSymbol]], piano_on_page: bool = False) -> bool:
    """
    Four staffs with treble, treble, bass and bass clef and no multi-measure rests. If the page
    shows piano otherwise, e.g. as a grand staff, the third staff can also start in the treble clef.
    """
    if len(staffs) != STAFFS_PER_SYSTEM:
        return False
    clefs = [_first_clef(staff) for staff in staffs]
    if any(clef is None for clef in clefs):
        return False
    kinds = [str(clef)[:6] for clef in clefs]
    third = ("clef_F", "clef_G") if piano_on_page else ("clef_F",)
    if (
        kinds[0] != "clef_G"
        or kinds[1] != "clef_G"
        or kinds[2] not in third
        or kinds[3] != "clef_F"
    ):
        return False
    return not any(
        s.rhythm.startswith(("note", "rest")) and s.rhythm.endswith("m")
        for staff in staffs
        for s in staff
    )


def _is_closing(rhythm: str) -> bool:
    return rhythm in _CLOSING or rhythm.startswith("barline") or rhythm.endswith("barline")


def _split_measures(staff: list[EncodedSymbol]) -> list[_Measure]:
    measures: list[_Measure] = []
    current = _Measure()
    clock = GroupClock()
    for symbols in sort_token_chords(staff):
        group = SymbolChord(symbols)
        rhythm = symbols[0].rhythm
        if _is_closing(rhythm) or rhythm == "repeatEndStart":
            current.closing = symbols
            measures.append(current)
            current, clock = _Measure(), GroupClock()
        elif rhythm.startswith(("note", "rest")):
            clock.wait_for_voices(group)
            current.body.append((clock.time, symbols))
            current.has_notes = True
            clock.advance(group)
        elif rhythm == "measureRest":
            current.body.append((Fraction(0), symbols))
        elif rhythm == "newline":
            continue
        elif not current.has_notes and not current.body:
            current.header.append(symbols)
        else:
            current.body.append((clock.time, symbols))
    if current.has_notes or current.body or current.header:
        measures.append(current)
    return measures


def _move_to(symbol: EncodedSymbol, staff_index: int) -> EncodedSymbol:
    """The symbol in the position of the voice of its staff."""
    if symbol.position == nonote:
        return symbol
    moved = copy.copy(symbol)
    moved.position = POSITIONS[staff_index]
    return moved


def _moved(group: list[EncodedSymbol], staff_index: int) -> list[EncodedSymbol]:
    return [_move_to(symbol, staff_index) for symbol in group]


def _clefs_of(measure: _Measure | None, staff_index: int) -> list[EncodedSymbol]:
    if measure is None:
        return []
    return [
        symbol
        for group in measure.header
        for symbol in _moved(group, staff_index)
        if symbol.rhythm.startswith("clef")
    ]


def _merge_measure(measures: list[_Measure | None]) -> list[list[EncodedSymbol]]:
    """The groups of the merged measure, in the order of the transformer's output."""
    result: list[list[EncodedSymbol]] = []
    clefs = _clefs_of(measures[0], 0) + _clefs_of(measures[2], 2)
    if clefs:
        result.append(clefs)
    for measure in measures:
        if measure is None:
            continue
        others = [g for g in measure.header if not g[0].rhythm.startswith("clef")]
        if others:
            result.extend(others)
            break
    events: list[tuple[Fraction, int, int, list[EncodedSymbol]]] = []
    has_notes = any(m is not None and m.has_notes for m in measures)
    for staff_index, measure in enumerate(measures):
        if measure is None:
            continue
        for order, (onset, group) in enumerate(measure.body):
            rhythm = group[0].rhythm
            if rhythm == "measureRest":
                if has_notes:
                    continue
                events.append((onset, 0, staff_index * 1000 + order, _moved(group, staff_index)))
                continue
            kind = 1 if rhythm.startswith(("note", "rest")) else 0
            events.append((onset, kind, staff_index * 1000 + order, _moved(group, staff_index)))
    events.sort(key=lambda e: (e[0], e[1], e[2]))
    seen_other: set[tuple[Fraction, str, bool]] = set()
    notes_at: dict[Fraction, list[EncodedSymbol]] = {}
    for onset, kind, _order, group in events:
        if kind == 1:
            if onset in notes_at:
                notes_at[onset].extend(group)
                continue
            notes_at[onset] = list(group)
            result.append(notes_at[onset])
        else:
            lower = group[0].position.startswith("lower")
            key = (onset, group[0].rhythm, lower)
            if key in seen_other:
                continue
            seen_other.add(key)
            result.append(group)
    closings = [m.closing for m in measures if m is not None and m.closing is not None]
    if closings:
        heavy = [c for c in closings if c[0].rhythm != "barline"]
        result.append((heavy or closings)[0])
    return result


def _flatten(groups: list[list[EncodedSymbol]]) -> list[EncodedSymbol]:
    result: list[EncodedSymbol] = []
    for group in groups:
        for i, symbol in enumerate(group):
            if i > 0:
                result.append(EncodedSymbol("chord"))
            result.append(symbol)
    return result


def merge_piano_system(staffs: list[list[EncodedSymbol]]) -> list[EncodedSymbol]:
    """
    One staff with upper and lower positions from the four staffs of a piano system (top to
    bottom). Check is_piano_system first. The staffs are merged measure by measure, a staff
    with another number of measures than most is cut or padded with empty measures.
    """
    per_staff = [_split_measures(staff) for staff in staffs]
    count = Counter(len(m) for m in per_staff).most_common(1)[0][0]
    if any(len(m) != count for m in per_staff):
        eprint("Measures of the staffs of a piano system:", [len(m) for m in per_staff])
    groups: list[list[EncodedSymbol]] = []
    for i in range(count):
        measures = [m[i] if i < len(m) else None for m in per_staff]
        groups.extend(_merge_measure(measures))
    return _flatten(groups)
