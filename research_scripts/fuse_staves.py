"""Fuse the per-staff parts of a joined homr MusicXML back into one part with k staves.

merge_pages.py reads every page through music21, which splits a two-staff piano part into two parts
(one per staff), and writes them as two parts. A beam which starts on one staff and goes on
on the other one (a left-hand note joining a right-hand group) lies in one MusicXML voice that visits
both staves. Two parts cannot hold it: the group is cut in two and nothing in the output says
it was one beam. This module writes the staves of a piano part as one part with <staves>k</staves>, each
note with its <staff>, and gives every voice that has notes on several staves a single stream in time
order, which is how MusicXML writes a cross-staff beam.

    fuse(root, [[0, 1]])      # parts 0 and 1 of the file become the staves 1 and 2 of one part

Beams. The merger keeps the begin, continue and end marks of the primary beams on the notes but works per voice, so the
notes of a beam which changes staff end up in different voices and the audit (and a reader) no longer sees one beam. Two rules
give the notes of such a beam the voice of its first note: `_stitch_beams` ("runs", the default, D39) joins a run which starts
and does not end on one staff to the run which ends on the other; `_stitch_chains` ("chains", D48) forms the beams of a measure
note by note the way the page writer did (`convert_beams`) and so also covers A-B-A beams, several staff changes and interleaved runs;
in a measure whose states do not form complete beams it falls back to the run rule.

Only the parts named are touched. A voice which would overlap itself in time across the staves (two sounding
notes of one voice at once) is not fused, the notes of the second staff get a voice of their own. Rests
of a voice which fall under notes the same voice has on the other staff are dropped (they are padding).
"""
import copy
import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field
from itertools import permutations

_BEFORE_VOICE = {"grace", "chord", "pitch", "rest", "unpitched", "duration", "tie", "cue", "instrument", "footnote", "level"}
_AFTER_STAFF = {"beam", "notations", "lyric", "play", "listen"}


@dataclass
class Item:
    kind: str  # "note" (a chord head with its members) or "ctrl"
    time: int
    staff: int
    order: int
    elements: list[ET.Element]
    voice: str | None = None
    duration: int = 0
    is_rest: bool = False

    def beam(self) -> str | None:
        """State of the primary beam of the chord, if it has one."""
        for note in self.elements:
            for beam in note.findall("beam"):
                if beam.get("number", "1") == "1":
                    return beam.text
        return None


@dataclass
class FuseStats:
    parts_fused: int = 0
    measures: int = 0
    stitched_beams: int = 0  # beam runs on one staff joined to the run which goes on on the other staff
    stitched_groups: int = 0  # whole beams (any number of staff changes) put into one voice by the chain rule
    skipped_measures: int = 0  # measures where the beam states could not be read as complete groups (left as they are)
    cross_staff_voices: int = 0  # (measure, voice) pairs with notes on several staves
    voice_conflicts: int = 0  # voices left apart because they overlapped
    rests_dropped: int = 0
    notes: dict = field(default_factory=dict)


def _int(el: ET.Element | None) -> int:
    return int(el.findtext("duration", "0")) if el is not None else 0


def _timed_items(measure: ET.Element, staff: int) -> list[Item]:
    items: list[Item] = []
    cursor = 0
    order = 0
    for child in measure:
        order += 1
        if child.tag == "backup":
            cursor -= _int(child)
        elif child.tag == "forward":
            cursor += _int(child)
        elif child.tag == "note":
            if child.find("chord") is not None:
                for item in reversed(items):
                    if item.kind == "note":
                        item.elements.append(child)
                        break
                continue
            duration = _int(child) if child.find("grace") is None else 0
            items.append(Item("note", cursor, staff, order, [child], child.findtext("voice"), duration, child.find("rest") is not None))
            cursor += duration
        else:
            items.append(Item("ctrl", cursor, staff, order, [child]))
    return items


def _insert_voice_and_staff(note: ET.Element, voice: str, staff: int) -> None:
    voice_el = note.find("voice")
    if voice_el is None:
        index = max([i for i, c in enumerate(note) if c.tag in _BEFORE_VOICE] + [-1]) + 1
        voice_el = ET.Element("voice")
        note.insert(index, voice_el)
    voice_el.text = voice
    staff_el = note.find("staff")
    if staff_el is None:
        index = next((i for i, c in enumerate(note) if c.tag in _AFTER_STAFF), len(note))
        staff_el = ET.Element("staff")
        note.insert(index, staff_el)
    staff_el.text = str(staff)


def _merge_attributes(elements: list[tuple[int, ET.Element]], k: int) -> ET.Element:
    """One attributes element from those of the staves; clefs get the number of their staff."""
    merged = ET.Element("attributes")
    first = {}
    clefs: list[ET.Element] = []
    for staff, attributes in elements:
        for child in attributes:
            if child.tag == "clef":
                clef = copy.deepcopy(child)
                clef.set("number", str(staff))
                clefs.append(clef)
            elif child.tag in ("divisions", "key", "time", "staves", "part-symbol", "transpose", "staff-details"):
                first.setdefault(child.tag, copy.deepcopy(child))
            else:
                first.setdefault(child.tag, copy.deepcopy(child))
    for tag in ("divisions", "key", "time"):
        if tag in first:
            merged.append(first.pop(tag))
    staves = ET.SubElement(merged, "staves")
    staves.text = str(k)
    first.pop("staves", None)
    for child in first.values():
        merged.append(child)
    for clef in sorted(clefs, key=lambda c: int(c.get("number"))):
        merged.append(clef)
    return merged


def _stream_events(items: list[Item]) -> list[Item]:
    return sorted(items, key=lambda i: (i.time, i.staff, i.order))


def _merge_voice(items: list[Item], stats: FuseStats) -> tuple[list[Item], list[Item]]:
    """Items of one voice from several staves in time order, and the items which had to be left out (conflict)."""
    kept: list[Item] = []
    leftover: list[Item] = []
    for item in _stream_events(items):
        end = kept[-1].time + kept[-1].duration if kept else 0
        if kept and item.time < end and item.duration > 0:
            previous = kept[-1]
            if item.is_rest:
                stats.rests_dropped += 1
                continue
            if previous.is_rest:
                kept.pop()
                stats.rests_dropped += 1
            else:
                leftover.append(item)
                continue
        kept.append(item)
    return kept, leftover


@dataclass
class Run:
    items: list[Item]
    staff: int
    voice: str

    @property
    def starts_open(self) -> bool:
        return self.items[0].beam() != "begin"

    @property
    def ends_open(self) -> bool:
        return self.items[-1].beam() != "end"


def _beam_runs(items: list[Item]) -> list[Run]:
    """The runs of primary beam states per (staff, voice) in time order; rests don't interrupt a run."""
    runs: list[Run] = []
    streams: dict[tuple[int, str | None], list[Item]] = defaultdict(list)
    for item in items:
        if item.kind == "note" and not item.is_rest and item.duration > 0:
            streams[item.staff, item.voice].append(item)
    for (staff, voice), stream in streams.items():
        current: list[Item] = []
        for item in sorted(stream, key=lambda i: (i.time, i.order)):
            state = item.beam()
            if state == "begin":
                if current:
                    runs.append(Run(current, staff, voice))
                current = [item]
            elif state in ("continue", "end"):
                current.append(item)
                if state == "end":
                    runs.append(Run(current, staff, voice))
                    current = []
            elif current:
                runs.append(Run(current, staff, voice))
                current = []
        if current:
            runs.append(Run(current, staff, voice))
    return runs


def _stitch_beams(items: list[Item], stats: FuseStats) -> None:
    """Give the runs of one beam which changes staff the voice of its first run.

    The page writer ends every beam it writes, so a run which has a start but no end, followed on the other staff
    by a run which has an end but no start, is one beam. A group goes with the run which follows it
    most closely in time, and only if that run also takes the group as its predecessor.
    """
    runs = [r for r in _beam_runs(items) if r.starts_open or r.ends_open]
    heads = [r for r in runs if r.ends_open]  # may be followed
    tails = [r for r in runs if r.starts_open]  # may follow
    after: dict[int, Run] = {}
    for first in heads:
        end = first.items[-1].time + first.items[-1].duration
        options = [r for r in tails if r.staff != first.staff and r.items[0].time >= end]
        if options:
            after[id(first)] = min(options, key=lambda r: (r.items[0].time, r.staff))
    before: dict[int, Run] = {}
    for second in tails:
        options = [r for r in heads if r.staff != second.staff and r.items[-1].time + r.items[-1].duration <= second.items[0].time]
        if options:
            before[id(second)] = max(options, key=lambda r: (r.items[-1].time, -r.staff))
    for first in sorted(heads, key=lambda r: (r.items[0].time, r.staff)):
        second = after.get(id(first))
        if second is None or before.get(id(second)) is not first:
            continue
        for item in second.items:
            item.voice = first.voice
        second.voice = first.voice
        stats.stitched_beams += 1


@dataclass
class _Chain:
    """An open beam: its chords in time order and the streams (staff, voice) which write into it."""

    items: list[Item]
    keys: set

    @property
    def last_end(self) -> int:
        return self.items[-1].time + self.items[-1].duration


def _clone(open_chains: dict[tuple, _Chain]) -> dict[tuple, _Chain]:
    """Copy of the open groups (a group shared by two streams stays one group)."""
    copies: dict[int, _Chain] = {}
    out = {}
    for key, chain in open_chains.items():
        if id(chain) not in copies:
            copies[id(chain)] = _Chain(list(chain.items), set(chain.keys))
        out[key] = copies[id(chain)]
    return out


def _run_slot(open_chains: dict[tuple, _Chain], events: list[Item], groups: list[list[Item]]) -> int:
    """Take the chords of one moment in the given order, as `convert_beams` does. Returns the number of orphans:
    chords with a continue or end state which could join no open group (they start a group of their own)."""
    orphans = 0

    def close(key: tuple) -> None:
        chain = open_chains.get(key)
        if chain is None:
            return
        for member in chain.keys:
            open_chains.pop(member, None)
        if len(chain.items) >= 2:
            groups.append(chain.items)

    for event in events:
        key = (event.staff, event.voice)
        state = event.beam()
        if state is None:
            close(key)
            continue
        if state == "begin":
            close(key)
        elif key in open_chains:
            chain = open_chains[key]
            if chain.items[-1].time >= event.time:  # two chords of one beam cannot start together: the streams are not the positions
                orphans += 1
            chain.items.append(event)
            if state == "end":
                close(key)
            continue
        else:
            candidates = {
                id(c): c
                for c in open_chains.values()
                if c.items[-1].staff != event.staff and c.last_end <= event.time and c.items[-1].time < event.time
            }
            if len(candidates) > 1:
                candidates = {i: c for i, c in candidates.items() if c.last_end == event.time}
            if len(candidates) == 1:
                chain = next(iter(candidates.values()))
                chain.items.append(event)
                chain.keys.add(key)
                open_chains[key] = chain
                if state == "end":
                    close(key)
                continue
            orphans += 1
        chain = _Chain([event], {key})
        open_chains[key] = chain
        if state == "end":
            close(key)
    return orphans


def _beam_chains(items: list[Item]) -> tuple[list[list[Item]], bool]:
    """Form the beams of one measure from the begin, continue and end states, as `convert_beams` of the page writer forms them.

    The writer forms a group per position of the model (here: per stream, i.e. staff and voice, since the voice label of a
    note follows its position) and takes the chords of all staves of the part in time order. A chord with a state
    continues the open group of its own stream. If its stream has none, it joins the one open group whose last chord is on
    the other staff and ended before the chord starts (when several are open: the one which ended exactly at the start); the
    stream then writes into that group until it ends. A begin, an unbeamed chord or an end closes what is open on its stream.
    Rests do not interrupt a group. Returns the groups of two or more chords which close.

    The order of chords which start together is the order of the decoder's tokens, which the joined file no longer has.
    The pages end every group they write, so the right order leaves no chord without a group: of the orders of a moment
    (at most six chords, otherwise staff by staff) the first which leaves the fewest such chords is taken.
    """
    events = [i for i in items if i.kind == "note" and not i.is_rest and i.duration > 0]
    by_time: dict[int, list[Item]] = defaultdict(list)
    for event in events:
        by_time[event.time].append(event)
    open_chains: dict[tuple, _Chain] = {}
    groups: list[list[Item]] = []
    orphans_total = 0
    for time in sorted(by_time):
        here = sorted(by_time[time], key=lambda i: (i.staff, i.order))
        if len(here) > 1 and len(here) <= 6 and len({(e.staff, e.voice) for e in here}) > 1:
            best = None
            for order in permutations(here):
                trial = _clone(open_chains)
                trial_groups: list[list[Item]] = []
                orphans = _run_slot(trial, list(order), trial_groups)
                if best is None or orphans < best[0]:
                    best = (orphans, order)
                if orphans == 0:
                    break
            here = list(best[1])
        orphans_total += _run_slot(open_chains, here, groups)
    unclosed = len({id(c) for c in open_chains.values()})
    for key in list(open_chains):
        chain = open_chains.get(key)
        if chain is not None:
            for member in chain.keys:
                open_chains.pop(member, None)
            if len(chain.items) >= 2:
                groups.append(chain.items)
    return groups, orphans_total == 0 and unclosed == 0


def _stitch_chains(items: list[Item], stats: FuseStats) -> None:
    """Put every beam which lies on more than one staff into the voice of its first note.

    Unlike `_stitch_beams` this follows the beam note by note as the page writer did, so a beam which goes back to
    its first staff (A, B, A), changes staff several times, or whose runs interleave in time is one beam.
    A group is only changed if its states read begin, continue ..., end. Beams on one staff are never changed.
    """
    groups, consistent = _beam_chains(items)
    if not consistent:
        stats.skipped_measures += 1
        _stitch_beams(items, stats)
        return
    for group in groups:
        states = [i.beam() for i in group]
        if len({i.staff for i in group}) < 2 or states[0] != "begin" or states[-1] != "end" or any(s != "continue" for s in states[1:-1]):
            continue
        voice = group[0].voice
        if any(i.voice != voice for i in group):
            for item in group:
                item.voice = voice
            stats.stitched_groups += 1


def _fuse_measure(measures: list[ET.Element], stats: FuseStats, stitch: bool | str = True) -> ET.Element:
    k = len(measures)
    all_items: list[Item] = []
    for staff, measure in enumerate(measures, start=1):
        all_items.extend(_timed_items(measure, staff))
    explicit = {i.voice for i in all_items if i.kind == "note" and i.voice is not None}
    used = {int(v) for v in explicit if v.isdigit()}
    implicit_voice: dict[int, str] = {}
    for staff in range(1, k + 1):
        if any(i.kind == "note" and i.voice is None and i.staff == staff for i in all_items):
            candidate = 1
            while candidate in used:
                candidate += 1
            used.add(candidate)
            implicit_voice[staff] = str(candidate)
    for item in all_items:
        if item.kind == "note" and item.voice is None:
            item.voice = implicit_voice[item.staff]

    if stitch == "chains":
        _stitch_chains(all_items, stats)
    elif stitch:
        _stitch_beams(all_items, stats)

    by_voice: dict[str, list[Item]] = defaultdict(list)
    voice_order: list[str] = []
    for item in sorted((i for i in all_items if i.kind == "note"), key=lambda i: (i.staff, i.order)):
        if item.voice not in by_voice:
            voice_order.append(item.voice)
        by_voice[item.voice].append(item)

    next_id = max(used | {0}) + 1
    streams: list[tuple[str, list[Item]]] = []
    for voice in voice_order:
        items = by_voice[voice]
        if len({i.staff for i in items}) > 1:
            kept, leftover = _merge_voice(items, stats)
            if len({i.staff for i in kept}) > 1:
                stats.cross_staff_voices += 1
            if leftover:
                stats.voice_conflicts += 1
                streams.append((voice, kept))
                extra = [i for i in items if i in leftover]
                streams.append((str(next_id), sorted(extra, key=lambda i: (i.time, i.staff, i.order))))
                for item in extra:
                    item.voice = str(next_id)
                next_id += 1
                continue
            streams.append((voice, kept))
        else:
            streams.append((voice, sorted(items, key=lambda i: (i.time, i.order))))

    out = ET.Element("measure", measures[0].attrib)
    ctrl = sorted((i for i in all_items if i.kind == "ctrl"), key=lambda i: (i.time, i.staff, i.order))
    prints = [i for i in ctrl if i.elements[0].tag == "print"]
    barlines = [i for i in ctrl if i.elements[0].tag == "barline"]
    rest = [i for i in ctrl if i.elements[0].tag not in ("print", "barline")]
    if prints:
        out.append(prints[0].elements[0])
    cursor = 0

    def move(to: int) -> None:
        nonlocal cursor
        if to > cursor:
            forward = ET.SubElement(out, "forward")
            ET.SubElement(forward, "duration").text = str(to - cursor)
        elif to < cursor:
            backup = ET.SubElement(out, "backup")
            ET.SubElement(backup, "duration").text = str(cursor - to)
        cursor = to

    # attributes of one moment of all staves are one element, other control elements follow their staff
    index = 0
    while index < len(rest):
        item = rest[index]
        time = item.time
        group = []
        while index < len(rest) and rest[index].time == time:
            group.append(rest[index])
            index += 1
        move(time)
        attributes = [(i.staff, i.elements[0]) for i in group if i.elements[0].tag == "attributes"]
        if attributes:
            out.append(_merge_attributes(attributes, k))
        for i in group:
            el = i.elements[0]
            if el.tag == "attributes":
                continue
            if el.tag == "direction" and el.find("staff") is None:
                staff_el = ET.Element("staff")
                staff_el.text = str(i.staff)
                at = next((n for n, c in enumerate(el) if c.tag == "sound"), len(el))
                el.insert(at, staff_el)
            out.append(el)
    first_stream = True
    for voice, items in streams:
        if not first_stream or cursor:
            move(0)
        first_stream = False
        for item in items:
            move(item.time)
            for n, note in enumerate(item.elements):
                _insert_voice_and_staff(note, item.voice if item.voice is not None else voice, item.staff)
                out.append(note)
            cursor += item.duration
    seen = set()
    for item in barlines:
        key = ET.tostring(item.elements[0])
        if key not in seen:
            seen.add(key)
            out.append(item.elements[0])
    return out


def fuse(root: ET.Element, groups: list[list[int]], stitch: bool | str = True) -> FuseStats:
    """Replace each group of parts (indices in file order, staff 1 first) by one part with that many staves.

    stitch: True or "runs" (default) joins a beam run which starts and does not end on one staff to the run which ends on the other
    staff; "chains" follows every beam note by note (A-B-A, several changes, interleaved runs); False leaves the voices as they are.
    """
    stats = FuseStats()
    parts = root.findall("part")
    part_list = root.find("part-list")
    score_parts = part_list.findall("score-part") if part_list is not None else []
    for group in groups:
        members = [parts[i] for i in group]
        lead = members[0]
        measure_rows = list(zip(*[p.findall("measure") for p in members]))
        assert all(len(p.findall("measure")) == len(measure_rows) for p in members), "staves differ in measure count"
        for measure in lead.findall("measure"):
            lead.remove(measure)
        for row in measure_rows:
            lead.append(_fuse_measure(list(row), stats, stitch))
            stats.measures += 1
        for p in members[1:]:
            root.remove(p)
            if part_list is not None:
                for sp in score_parts:
                    if sp.get("id") == p.get("id"):
                        part_list.remove(sp)
        stats.parts_fused += 1
    return stats


def staff_groups(part_ids: list[str]) -> list[list[int]]:
    """Groups of consecutive parts named P-Staff1 ... P-Staffk (how music21 names the staves of a part)."""
    import re

    groups: list[list[int]] = []
    i = 0
    while i < len(part_ids):
        m = re.fullmatch(r"(.+)-Staff1", part_ids[i])
        if m:
            j = i + 1
            while j < len(part_ids) and part_ids[j] == f"{m.group(1)}-Staff{j - i + 1}":
                j += 1
            if j - i >= 2:
                groups.append(list(range(i, j)))
            i = j
        else:
            i += 1
    return groups
