"""Inserts octave brackets into MusicXML which has none.

Octave brackets are rare in the training scores, and the ones there are mostly long and
above the upper staff. Real editions also print short brackets over a few notes of a bar,
often bar after bar, brackets over the lower staff of a piano system and octave-lower
brackets under the bass. A model sees almost none of those and misses them on real pages.

An <octave-shift> changes how the notes are *printed*, not how they sound: the <pitch>
elements stay as they are and the engraver prints the notes an octave lower (8va) or
higher (8vb) under a bracket. So adding the element to an existing score gives a new,
correct picture, and the tokens come from the same file through the usual parser
(written pitches plus octaveShift tokens). Nothing has to be labelled by hand.

Brackets are only put where they could plausibly stand: an octave-higher bracket over
notes high in their clef, an octave-lower one under low bass notes. Scores which already
have octave shifts are left alone.

    PYTHONPATH=. python training/omr_datasets/augment_octave_shifts.py OUT_DIR FILES_OR_DIRS...
"""

import hashlib
import json
import os
import random
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

_STEP_TO_SEMITONE = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
# Lowest note of an octave-higher bracket: printed an octave lower it still sits on or
# just below the staff. Per clef sign.
_MIN_MIDI_FOR_8VA = {"G": 72, "F": 55}
# Highest note of an octave-lower bracket under the bass clef
_MAX_MIDI_FOR_8VB = 50
# Chance that a bracket starts at a measure where one is possible, per staff
_P_START = {"8va": 0.16, "8vb": 0.2}
_MAX_MEASURES = 4


def _random_for(name: str) -> random.Random:
    return random.Random(
        int(hashlib.sha256(("octave" + name).encode()).hexdigest(), 16)
    )  # noqa: S311


def _midi(note: ET.Element) -> int | None:
    pitch = note.find("pitch")
    if pitch is None:
        return None
    step = pitch.findtext("step") or "C"
    octave = int(pitch.findtext("octave") or 4)
    alter = round(float(pitch.findtext("alter") or 0))
    return 12 * (octave + 1) + _STEP_TO_SEMITONE[step] + alter


def _staff_of(note: ET.Element) -> int:
    return int(note.findtext("staff") or 1)


def _has_tie(note: ET.Element, kind: str) -> bool:
    return any(tie.get("type") == kind for tie in note.findall("tie"))


def _direction(shift_type: str, staff: int | None, placement: str | None) -> ET.Element:
    direction = ET.Element("direction")
    if placement:
        direction.set("placement", placement)
    direction_type = ET.SubElement(direction, "direction-type")
    ET.SubElement(direction_type, "octave-shift", type=shift_type, size="8", number="1")
    if staff is not None:
        ET.SubElement(direction, "staff").text = str(staff)
    return direction


class _MeasureOfStaff:
    """The notes of one staff in one measure, in document order, grouped into chords."""

    def __init__(self, measure: ET.Element, staff: int) -> None:
        self.measure = measure
        notes = [n for n in measure.findall("note") if _staff_of(n) == staff]
        self.groups: list[list[ET.Element]] = []
        for note in notes:
            if note.find("chord") is not None and self.groups:
                self.groups[-1].append(note)
            else:
                self.groups.append([note])
        self.voices = {n.findtext("voice") or "1" for n in notes}
        self.has_grace = any(n.find("grace") is not None for n in notes)

    def pitches(self, first: int, last: int) -> list[int]:
        return [
            m
            for group in self.groups[first : last + 1]
            for n in group
            if (m := _midi(n)) is not None
        ]

    def pitched_groups(self) -> list[int]:
        return [i for i, group in enumerate(self.groups) if _midi(group[0]) is not None]

    def ties_cross(self, first: int, last: int) -> bool:
        return any(_has_tie(n, "stop") for n in self.groups[first]) or any(
            _has_tie(n, "start") for n in self.groups[last]
        )


def _kind_for(pitches: list[int], clef: str) -> str | None:
    if not pitches:
        return None
    if clef in _MIN_MIDI_FOR_8VA and min(pitches) >= _MIN_MIDI_FOR_8VA[clef]:
        return "8va"
    if clef == "F" and max(pitches) <= _MAX_MIDI_FOR_8VB:
        return "8vb"
    return None


def _insert(  # noqa: PLR0913
    start: _MeasureOfStaff,
    first: int,
    end: _MeasureOfStaff,
    last: int,
    kind: str,
    staff: int | None,
) -> None:
    shift_type, placement = ("down", "above") if kind == "8va" else ("up", "below")
    first_note = start.groups[first][0]
    children = list(start.measure)
    start.measure.insert(children.index(first_note), _direction(shift_type, staff, placement))
    last_note = end.groups[last][-1]
    children = list(end.measure)
    end.measure.insert(children.index(last_note) + 1, _direction("stop", staff, None))


def augment(root: ET.Element, rng: random.Random) -> dict[str, int]:  # noqa: C901, PLR0912, PLR0915
    """Adds brackets in place, returns how many of each kind."""
    added = {"8va": 0, "8vb": 0, "short": 0, "lower_staff": 0}
    if root.find(".//octave-shift") is not None:
        return added
    for part in root.findall("part"):
        measures = part.findall("measure")
        staves = max((int(s.text or 1) for s in part.iter("staves")), default=1)
        for staff in range(1, staves + 1):
            clef = "G" if staff == 1 else "F"
            index = 0
            # A run of short brackets, bar after bar, as in virtuoso figuration
            run_left = 0
            while index < len(measures):
                measure = measures[index]
                clef_changes = [
                    c for c in measure.iter("clef") if int(c.get("number", "1")) == staff
                ]
                view = _MeasureOfStaff(measure, staff)
                if clef_changes:
                    # A clef in the middle of a bar would split the bracket's notes between
                    # two clefs, skip the bar and carry on with the new clef
                    clef = clef_changes[-1].findtext("sign") or clef
                    index += 1
                    run_left = 0
                    continue
                pitched = view.pitched_groups()
                if not pitched or view.has_grace:
                    index += 1
                    run_left = 0
                    continue
                whole = _kind_for(view.pitches(0, len(view.groups) - 1), clef)
                single_voice = len(view.voices) == 1

                if run_left > 0 or (whole and rng.random() < _P_START[whole]):
                    style = (
                        "short" if run_left > 0 else rng.choice(["short", "short", "bar", "long"])
                    )
                    if style == "short" and single_voice and len(pitched) >= 2:  # noqa: PLR2004
                        # Mostly a few notes, now and then a single one
                        shortest = 1 if rng.random() < 0.2 else 2  # noqa: PLR2004
                        length = rng.randint(
                            min(shortest, len(pitched) - 1), min(6, len(pitched) - 1)
                        )
                        first_at = rng.randint(0, len(pitched) - length)
                        first, last = pitched[first_at], pitched[first_at + length - 1]
                        kind = _kind_for(view.pitches(first, last), clef)
                        if kind and not view.ties_cross(first, last):
                            _insert(view, first, view, last, kind, staff if staves > 1 else None)
                            added[kind] += 1
                            added["short"] += 1
                            added["lower_staff"] += staff > 1
                            if run_left == 0:
                                run_left = rng.choice([0, 0, 2, 3, 5])
                            else:
                                run_left -= 1
                        else:
                            run_left = 0
                        index += 1
                        continue
                    run_left = 0
                    if whole is None:
                        index += 1
                        continue
                    # Whole measures: extend while the following ones qualify too
                    wanted = 1 if style != "long" else rng.randint(2, _MAX_MEASURES)
                    views = [view]
                    while len(views) < wanted and index + len(views) < len(measures):
                        following = measures[index + len(views)]
                        if any(int(c.get("number", "1")) == staff for c in following.iter("clef")):
                            break
                        next_view = _MeasureOfStaff(following, staff)
                        if (
                            not next_view.pitched_groups()
                            or next_view.has_grace
                            or _kind_for(next_view.pitches(0, len(next_view.groups) - 1), clef)
                            != whole
                        ):
                            break
                        views.append(next_view)
                    first = views[0].pitched_groups()[0]
                    last = views[-1].pitched_groups()[-1]
                    if not (views[0].ties_cross(first, first) or views[-1].ties_cross(last, last)):
                        # The stop goes after the last note of the staff in document order,
                        # which with several voices is the end of the last voice
                        _insert(
                            views[0],
                            0,
                            views[-1],
                            len(views[-1].groups) - 1,
                            whole,
                            staff if staves > 1 else None,
                        )
                        added[whole] += 1
                        added["lower_staff"] += staff > 1
                    index += len(views)
                    continue
                index += 1
    return added


def augment_file(source: Path, destination: Path) -> dict[str, int]:
    tree = ET.parse(source)  # noqa: S314
    added = augment(tree.getroot(), _random_for(source.stem))
    if added["8va"] + added["8vb"] > 0:
        tree.write(destination, encoding="UTF-8", xml_declaration=True)
    return added


def main() -> None:
    out_dir = Path(sys.argv[1])
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []
    for arg in sys.argv[2:]:
        path = Path(arg)
        files.extend(sorted(path.rglob("*.musicxml")) if path.is_dir() else [path])
    # AUG_SHARE picks a fixed part of the files, the same ones on every run
    share = float(os.environ.get("AUG_SHARE", "1"))
    files = [f for f in files if _random_for("pick" + f.stem).random() < share]
    totals = {
        "files_in": len(files),
        "files_out": 0,
        "8va": 0,
        "8vb": 0,
        "short": 0,
        "lower_staff": 0,
    }
    for file in files:
        try:
            # The name tells the copies apart from the originals, which keep their tokens
            added = augment_file(file, out_dir / f"{file.stem}oct.musicxml")
        except (ET.ParseError, ValueError, KeyError) as error:
            sys.stderr.write(f"skipping {file}: {error!r}\n")
            continue
        if added["8va"] + added["8vb"] > 0:
            totals["files_out"] += 1
            for key in ("8va", "8vb", "short", "lower_staff"):
                totals[key] += added[key]
    sys.stdout.write(json.dumps(totals) + "\n")


if __name__ == "__main__":
    main()
