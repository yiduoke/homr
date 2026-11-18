"""Concatenate homr's per-page MusicXML into one score, then write MusicXML + MIDI.

homr transcribes one image at a time, so every page writes a time signature at its
own first measure -- 4/4 by default, since pages 2..9 don't print one. Carrying the
signature across the page break drops those, keeping only the changes actually
printed in the score.
"""
import glob
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from slot_tracking import SlotTracker, StaffProfile  # noqa: E402

PAGES = os.environ.get("HOMR_PAGES", "run/pages150")
OUT = os.environ.get("HOMR_OUT", "run/pathetique_homr")
TRUST_PAGE_TIME = os.environ.get("HOMR_TRUST_PAGE_TIME") == "1"
from music21 import clef as m21clef
from music21 import common, converter, duration, meter, note, spanner, stream, tie
from music21 import pitch as m21pitch

pages = sorted((f for f in glob.glob(f"{PAGES}/page-*.musicxml") if "_teaser" not in f),
               key=lambda p: int(re.search(r"page-(\d+)", os.path.basename(p)).group(1)))

def insert_rest(container, at: float, length: float) -> None:
    """Fill `length` quarters with rests MusicXML can actually spell.

    A gap like 2.5 quarters has no single note value, so music21 refuses to export
    it; splitAtDurations breaks it into the tied components an engraver would write.
    """
    filler = note.Rest(quarterLength=length)
    for piece in filler.splitAtDurations():
        container.insert(at, piece)
        at += float(piece.quarterLength)


def staff_profile(part) -> StaffProfile:
    """The clef and the pitches of one staff of a page, for matching it with the staves of other pages."""
    clefs = part.recurse().getElementsByClass(m21clef.Clef)
    sign = getattr(clefs[0], "sign", None) if len(clefs) else None
    pitches: Counter = Counter()
    for n in part.recurse().notes:
        for p in n.pitches:
            pitches[round(p.ps)] += 1
    return StaffProfile(sign, pitches)


def rest_measure(length) -> stream.Measure:
    """A bar of rests of the given length. The offsets are kept exact (fractions): a length like 8/3 summed in
    floats leaves gaps of 1e-16, which music21 fills with an unwritable rest when it writes the file."""
    filler = stream.Measure()
    at = common.opFrac(0)
    for piece in note.Rest(quarterLength=common.opFrac(length)).splitAtDurations():
        filler.insert(at, piece)
        at = common.opFrac(at + piece.quarterLength)
    return filler


merged = stream.Score()
tracker = SlotTracker()
slot_parts: dict[str, stream.Part] = {}   # slot key -> the part holding that staff of the whole piece
real_bars: dict[str, int] = {}            # bars a slot got from staves of pages (not rest fill)
in_effect: dict[str, str] = {}
dropped = 0
spanners = 0
padded_bars = 0
filled_bars = 0
filled = {"bars": 0}  # bars of rests a slot got for the pages before it was opened

for page_idx, path in enumerate(pages):
    score = converter.parse(path, forceSource=True)
    staves = list(score.parts)
    if not staves:
        continue
    # Every staff of a page starts where the score so far ends. The main part is the one with the
    # most measures so far.
    main = max(
        slot_parts.values(),
        key=lambda p: len(p.getElementsByClass("Measure")),
        default=None,
    )
    page_start = main.highestTime if main is not None else 0.0
    # The staff of each slot of the stack of this page (see slot_tracking.py): the n-th staff of a page
    # with as many staves as the piece has slots, otherwise matched by register and clef.
    seen_on_page: dict[str, int] = {}
    keys = []
    for part in staves:
        seen_on_page[part.id] = seen_on_page.get(part.id, 0) + 1
        keys.append(part.id if seen_on_page[part.id] == 1 else f"{part.id}#{seen_on_page[part.id]}")
    assignment = tracker.assign([staff_profile(p) for p in staves], keys)
    # The bars the slots already hold, as a template for a slot which a page opens late (see open_part);
    # read before this page changes them
    main_bars = []
    if main is not None and any(is_new for _, is_new in assignment):
        for bar in main.getElementsByClass("Measure"):
            main_bars.append((common.opFrac(bar.offset), common.opFrac(bar.highestTime) or 4.0, [ts.ratioString for ts in bar.getElementsByClass("TimeSignature")]))
    on_page = {slot.key for slot, _ in assignment}
    # the longest staff of the page gives the length of the bars a missing staff is filled with
    template = max(staves, key=lambda p: len(list(p.getElementsByClass("Measure"))))
    template_measures = list(template.getElementsByClass("Measure"))
    # (offset in the page, length) of each bar, read now: a measure's offset changes once it is inserted in a part
    template_bars = [(common.opFrac(tm.offset), common.opFrac(tm.highestTime) or 4.0) for tm in template_measures]
    template_meter = {}
    for t_idx, tm in enumerate(template_measures):
        for ts in tm.getElementsByClass("TimeSignature"):
            if not (t_idx == 0 and page_idx > 0 and TRUST_PAGE_TIME is False):
                template_meter[t_idx] = ts.ratioString

    def open_part(slot, is_new: bool) -> stream.Part:
        """The part of a slot; a slot which this page opens gets rests for the bars before it."""
        target = slot_parts.get(slot.key)
        if target is None:
            target = stream.Part()
            target.id = slot.key
            slot_parts[slot.key] = target
            real_bars[slot.key] = 0
            if is_new and main_bars:
                for b_offset, b_length, b_meters in main_bars:
                    filler = rest_measure(b_length)
                    for ratio in b_meters:
                        if ratio != in_effect.get(slot.key):
                            filler.insert(0, meter.TimeSignature(ratio))
                            in_effect[slot.key] = ratio
                    target.insert(b_offset, filler)
                filled["bars"] += len(main_bars)
        return target

    # (target part, bars it received from this page, offset where they end), per staff of the page
    page_group: list[tuple[stream.Part, int, float]] = []
    # Slots are in vertical order in `tracker.slots`; the merged score lists them in that order below.
    for part, (slot, is_new) in zip(staves, assignment):
        key = slot.key
        target = open_part(slot, is_new)
        start = page_start

        measures = list(part.getElementsByClass("Measure"))
        for m_idx, m in enumerate(measures):
            for ts in list(m.getElementsByClass("TimeSignature")):
                # MusicXML needs a time signature to open a part, so homr before the
                # meter work (model 566) writes one at every page's first measure
                # whether or not the page prints it: past page 1 it carries no
                # information. homr with complete time signatures (branch meter-run1)
                # carries the meter across pages itself, so its page-start signature is
                # real: HOMR_TRUST_PAGE_TIME=1 keeps it when it differs.
                synthetic = m_idx == 0 and page_idx > 0 and TRUST_PAGE_TIME is False
                if synthetic or ts.ratioString == in_effect.get(key):
                    m.remove(ts)
                    dropped += 1
                    continue
                in_effect[key] = ts.ratioString
            target.insert(start + m.offset, m)
        real_bars[key] += len(measures)

        # Slurs are spanners: they sit on the part, not inside a measure, and only
        # hold references to the notes they connect. Moving measures alone leaves
        # them behind on the page's part, which is then discarded.
        for sp in part.getElementsByClass(spanner.Spanner):
            target.insert(0, sp)
            spanners += 1
        page_group.append((target, len(measures), float(target.highestTime)))

    # All staves of a page hold the same bars (they are the staves of the same systems). Where a page output
    # lost bars of one of them (Schott Sonata p. 15: five bars of the right hand), the shorter staff gets
    # rests for the missing bars at the end of the page. Otherwise its next page would start early and
    # the staves would drift apart for the rest of the piece. The lost bars cannot be located within the page.
    most = max(count for _, count, _ in page_group)
    for target, count, end in page_group:
        if count == most:
            continue
        bar = float(meter.TimeSignature(in_effect[target.id]).barDuration.quarterLength) if in_effect.get(target.id) else 4.0
        for _ in range(most - count):
            filler = stream.Measure()
            insert_rest(filler, 0.0, bar)
            target.insert(end, filler)
            end += bar
            padded_bars += 1
    # A slot which no staff of this page fills (a staff the piece has on other pages) gets rests for
    # the bars of the page, so every slot keeps one bar per bar of the piece.
    for key, target in slot_parts.items():
        if key in on_page:
            continue
        for t_idx, (t_offset, t_length) in enumerate(template_bars):
            filler = rest_measure(t_length)
            if t_idx in template_meter and template_meter[t_idx] != in_effect.get(key):
                filler.insert(0, meter.TimeSignature(template_meter[t_idx]))
                in_effect[key] = template_meter[t_idx]
            target.insert(page_start + t_offset, filler)
            filled_bars += 1
    print(f"{path.split('/')[-1]}: appended at offset {page_start:.1f}")

print(f"\ndropped {dropped} redundant time signatures, carried {spanners} spanners, padded {padded_bars} lost bars of simultaneous parts, filled {filled_bars + filled['bars']} bars of slots a page does not use")

# The parts of the merged score, in the order of the staves from the top of the system
for slot in tracker.slots:
    merged.insert(0, slot_parts[slot.key])
part_streams = slot_parts

# A part which covers only a few pages is an ossia or a small extra staff (e.g.
# Mazeppa's "Piano a 7 octaves"): an alternative to the main staves, not more music to
# play along. HOMR_KEEP_MINOR_PARTS=1 keeps them.
if os.environ.get("HOMR_KEEP_MINOR_PARTS") != "1" and len(part_streams) > 1:
    # counted in bars of staves of pages, not in the rests which fill a slot on the pages it is missing from
    longest = max(real_bars.values())
    for part_id, p in list(part_streams.items()):
        if real_bars[part_id] < 0.5 * longest:
            merged.remove(p)
            del part_streams[part_id]
            print(f"dropped minor part {part_id} ({real_bars[part_id]} measures)")

for part in merged.parts:
    for i, m in enumerate(part.getElementsByClass("Measure"), start=1):
        m.number = i


def same_sounding(a, b) -> bool:
    """True if the two notes/chords carry identical pitches."""
    if a.isChord != b.isChord:
        return False
    pa = sorted(p.nameWithOctave for p in a.pitches)
    pb = sorted(p.nameWithOctave for p in b.pitches)
    return pa == pb and bool(pa)


# homr's model never predicts its tieStart/tieStop tokens -- every curved line in
# the movement came back as a slur. A curve joining two notes of the same pitch is
# a tie, one joining different pitches is a slur, so the two can be told apart
# after the fact without touching the model.
converted = 0
for part in merged.parts:
    for sp in list(part.getElementsByClass(spanner.Spanner)):
        if not isinstance(sp, spanner.Slur):
            continue
        spanned = sp.getSpannedElements()
        if len(spanned) != 2:
            continue                      # a tie only ever joins two notes
        first, second = spanned
        if not same_sounding(first, second):
            continue
        first.tie = tie.Tie("start")
        second.tie = tie.Tie("stop")
        part.remove(sp)
        converted += 1

print(f"converted {converted} same-pitch slurs into ties")


# An accidental holds to the end of its measure, and homr is trained on targets
# that already obey that. What it actually does is drift back to the key signature
# partway through a long bar.
#
# Repairing this by "the first accidental wins" is too blunt: a score may legally
# re-mark a pitch mid-bar, and forcing the first spelling destroys those. The
# narrower claim is the one worth acting on -- a pitch that took a non-key
# accidental earlier in the bar and later reverts to exactly the key signature's
# spelling is the model falling back on its prior, not the score changing its mind.
# Kept per staff, which is the actual rule: an accidental governs its own staff
# only, so the same pitch in the other staff of a grand staff takes the key
# signature. Widening this to cover both staves would paper over homr's
# staff-assignment mistakes at the cost of being wrong wherever it gets them right.
accidental_fixes: list[str] = []
for part in merged.parts:
    for m in part.getElementsByClass("Measure"):
        key_sig = m.getContextByClass("KeySignature")
        seen: dict[tuple[str, int], float] = {}
        occurrences = sorted(
            ((float(e.offset), e) for e in m.flatten().notes), key=lambda pair: pair[0]
        )
        for offset, element in occurrences:
            for p in element.pitches:
                ident = (p.step, p.octave)
                alter = float(p.alter)
                key_acc = key_sig.accidentalByStep(p.step) if key_sig else None
                key_alter = float(key_acc.alter) if key_acc else 0.0
                previous = seen.get(ident)
                # A printed sign (MusicXML <accidental>, written by homr since the
                # printed-accidental labels, branch accidentals-run2) is what the page
                # shows, e.g. a natural cancelling the earlier sharp: never "repair" it.
                printed = p.accidental is not None and p.accidental.displayStatus is True
                drifted_to_key = (
                    previous is not None
                    and not printed
                    and previous != alter
                    and previous != key_alter      # earlier note defied the key
                    and alter == key_alter         # this one snapped back to it
                )
                if drifted_to_key:
                    was = p.nameWithOctave
                    p.accidental = m21pitch.Accidental(previous) if previous else None
                    accidental_fixes.append(
                        f"m.{m.number} off={offset:.2f} {was} -> {p.nameWithOctave}"
                    )
                else:
                    seen[ident] = alter

print(f"restored {len(accidental_fixes)} accidentals to their measure's first spelling")
for line in accidental_fixes[:10]:
    print(f"    {line}")
if len(accidental_fixes) > 10:
    print(f"    ... and {len(accidental_fixes) - 10} more")


# homr writes a staff as one linear stream, so when a staff carries two voices at
# once it lays them end to end and the measure comes out too long. The overflow is
# the second voice: everything sitting past the barline gets moved into voice 2,
# restarting at the top of the measure. Guesses the split point purely from
# arithmetic -- the stem directions that would say for certain never reach here.
MIN_OVERFLOW = 0.5  # quarters; below this it's rounding noise, not a second voice


def deinterleave(lengths: list[float], target: float) -> list[int] | None:
    """Split a run of note lengths into two voices that each fit the bar.

    Returns a 0/1 assignment per note, or None if no split works. The two voices
    are braided together in homr's output rather than laid end to end, so this
    searches orderings instead of just cutting at the barline. Voice 0 has to fill
    the bar exactly; voice 1 only has to fit inside it.
    """
    n = len(lengths)
    if n > 16:
        return None                    # search space isn't worth it past this
    best: list[int] | None = None

    def walk(i: int, sum0: float, sum1: float, choices: list[int]) -> bool:
        nonlocal best
        if sum0 > target + 1e-6 or sum1 > target + 1e-6:
            return False
        if i == n:
            if abs(sum0 - target) < 1e-6 and sum1 > 1e-6:
                best = list(choices)
                return True
            return False
        for bucket in (0, 1):
            choices.append(bucket)
            hit = walk(
                i + 1,
                sum0 + (lengths[i] if bucket == 0 else 0.0),
                sum1 + (lengths[i] if bucket == 1 else 0.0),
                choices,
            )
            choices.pop()
            if hit:
                return True
        return False

    walk(0, 0.0, 0.0, [])
    return best


split_count = 0
still_wrong = 0
next_voice_id = 90
for part in merged.parts:
    for m in part.getElementsByClass("Measure"):
        ts = m.getContextByClass("TimeSignature")
        if ts is None:
            continue
        expected = float(ts.barDuration.quarterLength)

        # Each voice is checked on its own -- homr often gets one voice right and
        # crams the rest into another.
        containers = list(m.voices) if m.voices else [m]
        for container in containers:
            elements = list(container.notesAndRests)
            if not elements:
                continue
            total = sum(float(e.quarterLength) for e in elements)
            if total - expected < MIN_OVERFLOW:
                if total - expected > 1e-6:
                    still_wrong += 1
                continue

            assignment = deinterleave([float(e.quarterLength) for e in elements], expected)
            if assignment is None:
                still_wrong += 1
                continue

            extra = stream.Voice(id=str(next_voice_id))
            next_voice_id += 1
            keep_at = 0.0
            move_at = 0.0
            for element, bucket in zip(elements, assignment):
                container.remove(element)
                if bucket == 0:
                    container.insert(keep_at, element)
                    keep_at += float(element.quarterLength)
                else:
                    extra.insert(move_at, element)
                    move_at += float(element.quarterLength)
            m.insert(0.0, extra)
            split_count += 1

print(f"split {split_count} braided voices apart, {still_wrong} measures still overfull")


# Both staves of a grand staff share their barlines, so bar N starts at the same
# moment in each -- but homr sizes every measure from its own contents, so one
# short bar shifts everything after it and the two hands drift apart for the rest
# of the movement. Anchoring each measure to where its barline belongs keeps a bad
# measure's damage inside that measure.
grid: list[float] = []
running = 0.0
reference = merged.parts[0].getElementsByClass("Measure")
for m in reference:
    grid.append(running)
    ts = m.getContextByClass("TimeSignature")
    running += float(ts.barDuration.quarterLength) if ts else float(m.duration.quarterLength)

# MusicXML has no notion of where a measure sits -- measures are implicitly
# sequential, so their length IS their position. Anchoring therefore means padding
# a short measure with silence until it reaches the bar length, which is also what
# an engraver would have drawn.
padded = 0
overfull = 0
for part in merged.parts:
    for i, m in enumerate(part.getElementsByClass("Measure")):
        ts = m.getContextByClass("TimeSignature")
        if ts is None:
            continue
        expected = float(ts.barDuration.quarterLength)
        containers = list(m.voices) if m.voices else [m]
        for container in containers:
            if not list(container.notesAndRests):
                continue
            # Pad from where the container actually ends, not from the sum of its
            # durations -- the two differ whenever anything sits at a gap or an
            # offset of its own, and inserting at the sum overlaps what's there.
            end = float(container.highestTime)
            gap = expected - end
            if gap > 1e-6:
                insert_rest(container, end, gap)
                padded += 1
            elif gap < -1e-6:
                overfull += 1

print(f"padded {padded} short measures with rests, {overfull} still overfull")


# The bar length that survives is whichever staff claims the most, since notes can
# only be padded in, never thrown away. Both staves are then stretched to it, so a
# measure homr got wrong stays wrong on its own but no longer shifts the staves
# against each other for the rest of the movement.
measures_by_part = [list(p.getElementsByClass("Measure")) for p in merged.parts]
equalized = 0
for row in zip(*measures_by_part):
    longest = max(float(m.highestTime) for m in row)
    if longest < 1e-6:
        continue
    for m in row:
        containers = list(m.voices) if m.voices else [m]
        for container in containers:
            if not list(container.notesAndRests):
                continue
            gap = longest - float(container.highestTime)
            if gap > 1e-6:
                insert_rest(container, float(container.highestTime), gap)
                equalized += 1

print(f"stretched {equalized} measures so both staves share every barline")

# Without makeNotation, music21 can't write a note whose length isn't one notated
# value (e.g. 5/16 in a cadenza bar); split those into tied notes first.
split = 0
for element in list(merged.recurse().notesAndRests):
    if element.isRest and element.quarterLength > 4 and element.activeSite is not None:
        # Padding rests can run longer than any note value; write them as whole rests
        site, offset, left = element.activeSite, element.offset, element.quarterLength
        site.remove(element)
        while left > 1e-9:
            piece = note.Rest(quarterLength=min(4.0, round(left * 24) / 24) or 1 / 24)
            site.insert(offset, piece)
            offset += piece.quarterLength
            left -= piece.quarterLength
        split += 1
        continue
    if element.duration.type == "inexpressible" and element.quarterLength > 0:
        # A length no combination of note values gives (e.g. 0.2 of a quarter):
        # round it to the nearest 1/24 of a quarter, which covers triplets.
        element.duration = duration.Duration(max(1 / 24, round(element.quarterLength * 24) / 24))
    if element.duration.type == "complex" and element.activeSite is not None:
        site, offset = element.activeSite, element.offset
        pieces = element.splitAtDurations()
        if len(pieces) > 1:
            site.remove(element)
            for piece in pieces:
                site.insert(offset, piece)
                offset += piece.quarterLength
            split += 1
print(f"split {split} notes or rests of a length no single note value has")

# Splitting can leave slivers shorter than any note MusicXML can write (e.g. a "2048th" in
# Petrushka bar 194): drop such rests, and give such notes the shortest writable value.
slivers = 0
TOO_SHORT = {"256th", "512th", "1024th", "2048th"}
for element in list(merged.recurse().notesAndRests):
    too_short = 0 < element.quarterLength < 1 / 32 or element.duration.type in TOO_SHORT or any(
        c.type in TOO_SHORT for c in element.duration.components
    )
    if too_short and element.activeSite is not None:
        if element.isRest:
            element.activeSite.remove(element)
        else:
            element.duration = duration.Duration(1 / 32)
        slivers += 1
print(f"fixed {slivers} notes or rests too short for MusicXML")

# makeNotation=False: music21 otherwise recomputes beams on write and throws on
# any measure still longer than its time signature, which the repairs above can't
# always fix. Nothing downstream needs regenerated beaming.
for attempt in range(10):
    try:
        merged.write("musicxml", fp=f"{OUT}.musicxml", makeNotation=False)
        break
    except Exception as exc:  # noqa: BLE001
        # music21 decides a note value only while writing, so a sliver can still turn
        # out unwritable here ("Cannot convert 2048th ... measure (194)"): drop the
        # shortest notes and rests of the measure it names and write again.
        found = re.search(r"measure \((\d+)\)", str(exc))
        if not found or ("too short" not in str(exc) and "complex" not in str(exc)):
            raise
        number = int(found.group(1))
        removed = 0
        for part in merged.parts:
            measures = list(part.getElementsByClass("Measure"))
            # The message names the measure number, which may differ from its position
            suspects = [m for m in measures if m.number == number]
            if 0 < number <= len(measures):
                suspects.append(measures[number - 1])
            for m in suspects:
                for element in list(m.recurse()):
                    if getattr(element, "duration", None) is None:
                        continue
                    short = element.duration.type in TOO_SHORT or any(
                        c.type in TOO_SHORT for c in element.duration.components
                    )
                    if short and element.activeSite is not None:
                        element.activeSite.remove(element)
                        removed += 1
            # The sliver may also be a gap music21 fills with a rest while writing:
            # snap the measure's offsets and lengths to 1/12 and 1/16 of a quarter.
            for m in suspects:
                m.quantize((12, 16), processOffsets=True, processDurations=True, recurse=True, inPlace=True)
                for element in list(m.recurse().notesAndRests):
                    if element.duration.type == "complex" and element.activeSite is not None:
                        site, offset = element.activeSite, element.offset
                        pieces = element.splitAtDurations()
                        if len(pieces) > 1:
                            site.remove(element)
                            for piece in pieces:
                                site.insert(offset, piece)
                                offset += piece.quarterLength
        print(f"dropped {removed} unwritable slivers and quantized measure {number}")
        if attempt >= 4:
            # Still unwritable (an overfull bar whose voices music21 cannot lay out): replace the bar by rests
            # in the part which holds it rather than lose the whole file. A bar of this kind used to sit in a part
            # which was dropped; with the staves of every page in the same slots it can reach a main part.
            for part in merged.parts:
                measures = list(part.getElementsByClass("Measure"))
                for m in [m for m in measures if m.number == number] or ([measures[number - 1]] if 0 < number <= len(measures) else []):
                    bar = float(m.barDuration.quarterLength) if m.getContextByClass("TimeSignature") else 4.0
                    for element in list(m.recurse().notesAndRests):
                        element.activeSite.remove(element)
                    for voice in list(m.voices):
                        m.remove(voice)
                    insert_rest(m, 0.0, bar)
            print(f"blanked measure {number}: music21 cannot write it")
try:
    # music21 expands repeats before writing MIDI and refuses when homr's repeat
    # marks don't pair up. The WAV is rendered from the MusicXML, so a missing
    # MIDI shouldn't stop the run.
    merged.write("midi", fp=f"{OUT}.mid")
except Exception as exc:  # noqa: BLE001
    print(f"MIDI export skipped: {exc}")
total = len(merged.parts[0].getElementsByClass("Measure"))
print(f"\nparts={len(merged.parts)} measures={total} duration={merged.highestTime:.1f} quarter notes")
