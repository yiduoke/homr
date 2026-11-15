"""Count individual MusicXML noteheads, with pitch and timing metrics.

See validation/note_scoring.md for the alignment rules and limitations.
This module uses only the standard library and never rewrites its inputs.
"""

import argparse
import hashlib
import json
import math
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Literal

Metric = Literal["pitch_inventory", "pitch_onset", "pitch_onset_duration"]
METRICS: tuple[Metric, ...] = ("pitch_inventory", "pitch_onset", "pitch_onset_duration")
DEFAULT_TOLERANCE = 1 / 96  # quarter notes; covers small MusicXML tuplet rounding errors
_SEMITONES = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


@dataclass(frozen=True)
class Note:
    staff: int
    pitch: float
    onset: float
    duration: float
    grace: bool = False


@dataclass(frozen=True)
class Measure:
    number: str
    notes: tuple[Note, ...]


@dataclass(frozen=True)
class Score:
    measures: tuple[Measure, ...]
    staves: int


@dataclass(frozen=True)
class Counts:
    matched: int
    reference: int
    predicted: int

    def report(self) -> dict[str, int | float]:
        empty = self.reference == self.predicted == 0
        return {
            "matched": self.matched,
            "reference": self.reference,
            "predicted": self.predicted,
            "unmatched_reference": self.reference - self.matched,
            "unmatched_prediction": self.predicted - self.matched,
            "precision": self.matched / self.predicted if self.predicted else float(empty),
            "recall": self.matched / self.reference if self.reference else float(empty),
            "f1": 2 * self.matched / (self.reference + self.predicted) if not empty else 1.0,
        }


def _read_part(part: ET.Element, staff_offset: int) -> tuple[list[Measure], int]:
    staff_count = max(
        [1]
        + [int(s.text or "1") for s in part.iter("staves")]
        + [int(n.findtext("staff") or "1") for n in part.findall("measure/note")]
    )
    if staff_count < 1:
        raise ValueError("Staff numbers must be positive")
    divisions = Fraction(1)
    measures = []
    for measure in part.findall("measure"):
        cursor = Fraction(0)
        last_onset: Fraction | None = None
        notes = []
        for element in measure:
            if element.tag == "attributes":
                text = element.findtext("divisions")
                if text is not None:
                    divisions = Fraction(text)
                    if divisions <= 0:
                        raise ValueError("MusicXML divisions must be positive")
                if element.find("transpose") is not None:
                    raise ValueError("Convert transposing instruments to concert pitch first")
            elif element.tag in ("backup", "forward"):
                duration = Fraction(element.findtext("duration") or "0") / divisions
                if duration < 0:
                    raise ValueError("Negative backup/forward duration")
                cursor += duration if element.tag == "forward" else -duration
                last_onset = None
                if cursor < 0:
                    raise ValueError(f"Backup before start of measure {measure.get('number')}")
            elif element.tag == "note":
                chord = element.find("chord") is not None
                grace = element.find("grace") is not None
                if not grace and element.find("duration") is None:
                    raise ValueError("Non-grace notes and rests must have a duration")
                duration = Fraction(element.findtext("duration") or "0") / divisions
                if duration < 0:
                    raise ValueError("Negative note duration")
                if chord and last_onset is None:
                    raise ValueError("Chord member without a preceding note")
                onset = last_onset if chord else cursor
                if not chord:
                    last_onset = cursor
                    if not grace:
                        cursor += duration
                pitch = element.find("pitch")
                if element.find("unpitched") is not None:
                    raise ValueError("Unpitched percussion is not supported")
                if pitch is None:
                    continue
                staff = int(element.findtext("staff") or "1")
                if staff < 1:
                    raise ValueError("Staff numbers must be positive")
                midi = (
                    12 * (int(pitch.findtext("octave") or "0") + 1)
                    + _SEMITONES[pitch.findtext("step") or ""]
                    + float(pitch.findtext("alter") or "0")
                )
                if not math.isfinite(midi):
                    raise ValueError("Non-finite pitch")
                # MusicXML already encodes sounding pitch for octave brackets. Do not
                # apply octave-shift directions again. Rests still advance the cursor.
                notes.append(
                    Note(staff_offset + staff, midi, float(onset or 0), float(duration), grace)
                )
        measures.append(Measure(measure.get("number", ""), tuple(notes)))
    return measures, staff_count


def parse_musicxml(xml: str) -> Score:
    """Read score-partwise XML; flatten parts/staves in document order.

    One two-staff piano part and two single-staff parts become the same staff layout.
    Different measure counts between parts are rejected rather than silently aligned.
    """
    root = ET.fromstring(xml)  # noqa: S314 - caller-provided local score, never fetched here
    for element in root.iter():
        element.tag = element.tag.rsplit("}", 1)[-1]
    if root.tag != "score-partwise":
        raise ValueError("Expected uncompressed score-partwise MusicXML")
    parts = []
    staff_offset = 0
    for part in root.findall("part"):
        measures, staves = _read_part(part, staff_offset)
        parts.append(measures)
        staff_offset += staves
    if not parts or not parts[0]:
        raise ValueError("Score has no measures")
    if any(len(part) != len(parts[0]) for part in parts):
        raise ValueError("Parts have different measure counts; establish their alignment first")
    combined = tuple(
        Measure(parts[0][i].number, tuple(note for part in parts for note in part[i].notes))
        for i in range(len(parts[0]))
    )
    return Score(combined, staff_offset)


def _inventory(notes: tuple[Note, ...]) -> Counter[tuple[int, float]]:
    return Counter((note.staff, note.pitch) for note in notes)


def align_measures(reference: Score, prediction: Score) -> list[tuple[int, int]]:
    """Joint monotonic alignment for all staves, maximizing pitch inventory overlap.

    Ties prefer fewer skipped bars, then a diagonal match. Every note in a skipped
    bar remains in the precision/recall denominators. Alignment is heuristic, not
    ground truth; the report exposes all pairs for review.
    """
    if reference.staves != prediction.staves:
        raise ValueError("Reference and prediction must have the same staff layout")
    ref = [_inventory(m.notes) for m in reference.measures]
    pred = [_inventory(m.notes) for m in prediction.measures]
    n, m = len(ref), len(pred)
    costs = [[(0, 0)] * (m + 1) for _ in range(n + 1)]
    paths = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        costs[i][0], paths[i][0] = (0, -i), 1
    for j in range(1, m + 1):
        costs[0][j], paths[0][j] = (0, -j), 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            overlap = sum((ref[i - 1] & pred[j - 1]).values())
            diagonal = (costs[i - 1][j - 1][0] + overlap, costs[i - 1][j - 1][1])
            skip_ref = (costs[i - 1][j][0], costs[i - 1][j][1] - 1)
            skip_pred = (costs[i][j - 1][0], costs[i][j - 1][1] - 1)
            options = [diagonal, skip_ref, skip_pred]
            choice = max(range(3), key=lambda k: options[k])
            costs[i][j], paths[i][j] = options[choice], choice
    i, j = n, m
    pairs = []
    while i or j:
        if i and j and paths[i][j] == 0:
            pairs.append((i - 1, j - 1))
            i, j = i - 1, j - 1
        elif i and (not j or paths[i][j] == 1):
            i -= 1
        else:
            j -= 1
    return list(reversed(pairs))


def count_matches(
    reference: tuple[Note, ...], prediction: tuple[Note, ...], metric: Metric, tolerance: float
) -> int:
    """Maximum one-to-one matching; a prediction can never explain two notes."""
    if metric == "pitch_inventory":
        return sum((_inventory(reference) & _inventory(prediction)).values())
    edges = [
        [
            j
            for j, actual in enumerate(prediction)
            if expected.staff == actual.staff
            and expected.pitch == actual.pitch
            and expected.grace == actual.grace
            and abs(expected.onset - actual.onset) <= tolerance + 1e-9
            and (
                metric != "pitch_onset_duration"
                or abs(expected.duration - actual.duration) <= tolerance + 1e-9
            )
        ]
        for expected in reference
    ]
    assigned: dict[int, int] = {}

    def augment(index: int, seen: set[int]) -> bool:
        for candidate in edges[index]:
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate not in assigned or augment(assigned[candidate], seen):
                assigned[candidate] = index
                return True
        return False

    for index in sorted(range(len(reference)), key=lambda k: len(edges[k])):
        augment(index, set())
    return len(assigned)


def score_notes(reference: Score, prediction: Score, tolerance: float = DEFAULT_TOLERANCE) -> dict:
    if not math.isfinite(tolerance) or tolerance < 0:
        raise ValueError("Timing tolerance must be finite and nonnegative")
    pairs = align_measures(reference, prediction)
    ref_matched, pred_matched = {i for i, _ in pairs}, {j for _, j in pairs}
    metrics = {}
    for metric in METRICS:
        staff_counts = []
        for staff in range(1, reference.staves + 1):
            ref_notes = [tuple(n for n in m.notes if n.staff == staff) for m in reference.measures]
            pred_notes = [
                tuple(n for n in m.notes if n.staff == staff) for m in prediction.measures
            ]
            matched = sum(
                count_matches(ref_notes[i], pred_notes[j], metric, tolerance) for i, j in pairs
            )
            staff_counts.append(
                Counts(matched, sum(map(len, ref_notes)), sum(map(len, pred_notes)))
            )
        total = Counts(
            sum(c.matched for c in staff_counts),
            sum(c.reference for c in staff_counts),
            sum(c.predicted for c in staff_counts),
        )
        metrics[metric] = {
            "combined": total.report(),
            "staves": [c.report() for c in staff_counts],
        }
    return {
        "tolerance_quarters": tolerance,
        "reference_measures": len(reference.measures),
        "predicted_measures": len(prediction.measures),
        "matched_measures": len(pairs),
        "alignment": [
            {
                "reference_index": i + 1,
                "reference_number": reference.measures[i].number,
                "prediction_index": j + 1,
                "prediction_number": prediction.measures[j].number,
                "reference_notes": len(reference.measures[i].notes),
                "predicted_notes": len(prediction.measures[j].notes),
                "matches": {
                    metric: count_matches(
                        reference.measures[i].notes, prediction.measures[j].notes, metric, tolerance
                    )
                    for metric in METRICS
                },
            }
            for i, j in pairs
        ],
        "unmatched_reference_measures": [
            i + 1 for i in range(len(reference.measures)) if i not in ref_matched
        ],
        "unmatched_prediction_measures": [
            j + 1 for j in range(len(prediction.measures)) if j not in pred_matched
        ],
        "metrics": metrics,
    }


def _read_score(path: Path) -> tuple[Score, dict[str, str]]:
    data = path.read_bytes()
    return parse_musicxml(data.decode("utf-8-sig")), {
        "path": str(path.resolve()),
        "sha256": hashlib.sha256(data).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("predictions", nargs="+", metavar="NAME=FILE.musicxml")
    parser.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE, metavar="QUARTERS")
    parser.add_argument(
        "--json", type=Path, dest="json_path", help="Write counts and bar alignments"
    )
    args = parser.parse_args()
    try:
        reference, ref_metadata = _read_score(args.reference)
        results = []
        input_paths = {args.reference.resolve()}
        for argument in args.predictions:
            name, separator, filename = argument.partition("=")
            if not separator or not name or not filename:
                raise ValueError("Predictions must have the form NAME=FILE.musicxml")
            path = Path(filename)
            prediction, metadata = _read_score(path)
            input_paths.add(path.resolve())
            results.append(
                {
                    "name": name,
                    "input": metadata,
                    **score_notes(reference, prediction, args.tolerance),
                }
            )
        if args.json_path and args.json_path.resolve() in input_paths:
            raise ValueError("JSON output must not overwrite an input score")
        report = {"schema_version": 1, "reference": ref_metadata, "results": results}
        if args.json_path:
            args.json_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, ET.ParseError, ZeroDivisionError) as error:
        parser.error(str(error))
    sys.stdout.write("All pitched noteheads; all staves combined; percentages are micro F1.\n")
    sys.stdout.write(
        "Pitch inventory ignores ordering/timing; onset is relative to the aligned bar.\n"
    )
    sys.stdout.write("model\tpitch inventory\tpitch+onset\tpitch+onset+duration\n")
    for result in results:
        values = [f"{100 * result['metrics'][metric]['combined']['f1']:.2f}" for metric in METRICS]
        sys.stdout.write(result["name"] + "\t" + "\t".join(values) + "\n")
        strict = result["metrics"]["pitch_onset_duration"]["combined"]
        sys.stdout.write(
            f"  Full match: {strict['matched']}/{strict['reference']} reference notes; "
            f"{strict['unmatched_reference']} unmatched reference, "
            f"{strict['unmatched_prediction']} unmatched prediction; "
            f"precision {strict['precision']:.2%}, recall {strict['recall']:.2%}\n"
        )


if __name__ == "__main__":
    main()
