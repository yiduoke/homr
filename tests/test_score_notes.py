import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from validation.score_notes import (
    Counts,
    Measure,
    Note,
    Score,
    align_measures,
    count_matches,
    parse_musicxml,
    score_notes,
)


def _note(step: str = "C", extra: str = "", staff: int = 1) -> str:
    return (
        f"<note>{extra}<pitch><step>{step}</step><octave>4</octave></pitch>"
        f"<duration>2</duration><staff>{staff}</staff></note>"
    )


def _xml(content: str) -> str:
    return (
        '<score-partwise><part id="P1"><measure number="1">'
        "<attributes><divisions>2</divisions></attributes>"
        + content
        + "</measure></part></score-partwise>"
    )


def _score(*bars: tuple[Note, ...], staves: int = 1) -> Score:
    return Score(tuple(Measure(str(i + 1), bar) for i, bar in enumerate(bars)), staves)


class TestMusicXMLNotes(unittest.TestCase):
    def test_chords_backups_forwards_and_rests(self) -> None:
        xml = _xml(
            _note()
            + _note("E", "<chord/>")
            + "<note><rest/><duration>2</duration></note>"
            + "<backup><duration>4</duration></backup>"
            + "<forward><duration>1</duration></forward>"
            + _note("G", staff=2)
        )
        score = parse_musicxml(xml)
        self.assertEqual(score.staves, 2)
        self.assertEqual(
            score.measures[0].notes,
            (Note(1, 60, 0, 1), Note(1, 64, 0, 1), Note(2, 67, 0.5, 1)),
        )

    def test_divisions_persist_and_can_change(self) -> None:
        xml = (
            '<score-partwise><part id="P1"><measure number="1">'
            "<attributes><divisions>2</divisions></attributes>"
            + _note()
            + '</measure><measure number="2">'
            + _note()
            + "<attributes><divisions>4</divisions></attributes>"
            + _note("D")
            + "</measure></part></score-partwise>"
        )
        measures = parse_musicxml(xml).measures
        self.assertEqual(measures[1].notes, (Note(1, 60, 0, 1), Note(1, 62, 1, 0.5)))

    def test_octave_direction_is_not_applied_twice(self) -> None:
        score = parse_musicxml(
            _xml(
                '<direction><direction-type><octave-shift type="up" size="8"/>'
                "</direction-type></direction>" + _note()
            )
        )
        self.assertEqual(score.measures[0].notes[0].pitch, 60)

    def test_grace_does_not_advance_time(self) -> None:
        grace = "<note><grace/><pitch><step>D</step><octave>4</octave></pitch></note>"
        score = parse_musicxml(_xml(grace + _note()))
        self.assertEqual(score.measures[0].notes, (Note(1, 62, 0, 0, True), Note(1, 60, 0, 1)))

    def test_two_parts_equal_one_grand_staff(self) -> None:
        grand = parse_musicxml(
            _xml(_note() + "<backup><duration>2</duration></backup>" + _note("E", staff=2))
        )
        separate = (
            '<score-partwise><part id="a"><measure number="1">'
            "<attributes><divisions>2</divisions></attributes>"
            + _note()
            + '</measure></part><part id="b"><measure number="1">'
            + "<attributes><divisions>2</divisions></attributes>"
            + _note("E")
            + "</measure></part></score-partwise>"
        )
        self.assertEqual(grand, parse_musicxml(separate))

    def test_reject_ambiguous_or_invalid_input(self) -> None:
        cases = [
            _xml("<backup><duration>2</duration></backup>"),
            _xml(_note(extra="<chord/>")),
            _xml(_note(staff=0)),
            _xml("<attributes><transpose><chromatic>2</chromatic></transpose></attributes>"),
            _xml("<note><unpitched/><duration>2</duration></note>"),
            _xml("<note><rest/></note>"),
            '<score-partwise><part id="a"><measure number="1"/></part>'
            '<part id="b"/></score-partwise>',
            "<score-timewise/>",
        ]
        for xml in cases:
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                parse_musicxml(xml)


class TestIndividualNoteScoring(unittest.TestCase):
    def test_every_chord_member_counts_and_order_does_not(self) -> None:
        notes = (Note(1, 60, 0, 1), Note(1, 64, 0, 1), Note(1, 67, 0, 1))
        result = score_notes(_score(notes), _score(tuple(reversed(notes))))
        self.assertEqual(
            result["metrics"]["pitch_onset_duration"]["combined"], Counts(3, 3, 3).report()
        )

    def test_swapped_sequential_notes_fail_onset_metric(self) -> None:
        reference = _score((Note(1, 60, 0, 1), Note(1, 62, 1, 1)))
        actual = _score((Note(1, 62, 0, 1), Note(1, 60, 1, 1)))
        result = score_notes(reference, actual)["metrics"]
        self.assertEqual(result["pitch_inventory"]["combined"]["matched"], 2)
        self.assertEqual(result["pitch_onset"]["combined"]["matched"], 0)

    def test_wrong_duration_is_separate_from_wrong_onset(self) -> None:
        result = score_notes(_score((Note(1, 60, 0, 1),)), _score((Note(1, 60, 0, 2),)))["metrics"]
        self.assertEqual(result["pitch_onset"]["combined"]["matched"], 1)
        self.assertEqual(result["pitch_onset_duration"]["combined"]["matched"], 0)

    def test_repeated_pitch_cannot_reuse_prediction(self) -> None:
        ref = (Note(1, 60, 0, 1), Note(1, 60, 0, 1))
        self.assertEqual(count_matches(ref, ref[:1], "pitch_onset", 0), 1)

    def test_tolerance_uses_maximum_matching_not_greedy(self) -> None:
        ref = (Note(1, 60, 0.10, 1), Note(1, 60, 0.20, 1))
        hyp = (Note(1, 60, 0.15, 1), Note(1, 60, 0.06, 1))
        self.assertEqual(count_matches(ref, hyp, "pitch_onset", 0.06), 2)

    def test_extra_and_missing_bars_stay_in_denominators(self) -> None:
        a, b, c = (Note(1, p, 0, 1) for p in [60, 62, 64])
        ref, hyp = _score((a,), (b,), (c,)), _score((a,), (c,))
        result = score_notes(ref, hyp)
        self.assertEqual(result["unmatched_reference_measures"], [2])
        self.assertEqual(
            result["metrics"]["pitch_onset_duration"]["combined"], Counts(2, 3, 2).report()
        )
        reverse = score_notes(hyp, ref)
        self.assertEqual(reverse["unmatched_prediction_measures"], [2])
        self.assertEqual(
            reverse["metrics"]["pitch_onset_duration"]["combined"], Counts(2, 2, 3).report()
        )

    def test_staves_cannot_choose_different_bar_alignments(self) -> None:
        upper, lower = Note(1, 60, 0, 1), Note(2, 48, 0, 1)
        ref = _score((upper, lower), (), staves=2)
        hyp = _score((upper,), (lower,), staves=2)
        result = score_notes(ref, hyp)
        self.assertEqual(len(align_measures(ref, hyp)), 2)
        self.assertEqual(result["metrics"]["pitch_inventory"]["combined"]["matched"], 1)

    def test_staves_with_different_bar_counts_align_per_staff(self) -> None:
        def part(pid: str, staff_notes: list[str]) -> str:
            bars = "".join(
                f'<measure number="{i + 1}">'
                + ("<attributes><divisions>2</divisions></attributes>" if i == 0 else "")
                + _note(n)
                + "</measure>"
                for i, n in enumerate(staff_notes)
            )
            return f'<part id="{pid}">{bars}</part>'

        grand = (
            '<score-partwise><part id="P1">'
            '<measure number="1"><attributes><divisions>2</divisions></attributes>'
            + _note("C")
            + "<backup><duration>2</duration></backup>"
            + _note("C", staff=2)
            + '</measure><measure number="2">'
            + _note("D")
            + "<backup><duration>2</duration></backup>"
            + _note("D", staff=2)
            + '</measure><measure number="3">'
            + _note("E")
            + "<backup><duration>2</duration></backup>"
            + _note("E", staff=2)
            + "</measure></part></score-partwise>"
        )
        # Staff 1 keeps all three bars; staff 2 lost its middle bar.
        split = (
            "<score-partwise>"
            + part("a", ["C", "D", "E"])
            + part("b", ["C", "E"])
            + "</score-partwise>"
        )
        ref, hyp = parse_musicxml(grand), parse_musicxml(split)
        self.assertEqual(len(hyp.staff_measures), 2)
        result = score_notes(ref, hyp)
        self.assertEqual(result["alignment_mode"], "per_staff")
        self.assertEqual(result["matched_measures"], [3, 2])
        self.assertEqual(result["staff_alignment"][1]["unmatched_reference_measures"], [2])
        strict = result["metrics"]["pitch_onset_duration"]
        self.assertEqual(strict["staves"][0], Counts(3, 3, 3).report())
        self.assertEqual(strict["staves"][1], Counts(2, 3, 2).report())
        self.assertEqual(strict["combined"], Counts(5, 6, 5).report())
        # Equal bar counts keep the joint alignment.
        self.assertEqual(score_notes(ref, ref)["alignment_mode"], "joint")

    def test_staff_and_grace_status_must_match(self) -> None:
        ref = (Note(1, 60, 0, 0, True),)
        self.assertEqual(count_matches(ref, (Note(2, 60, 0, 0, True),), "pitch_onset", 0), 0)
        self.assertEqual(count_matches(ref, (Note(1, 60, 0, 0),), "pitch_onset", 0), 0)

    def test_empty_bar_adds_no_free_credit(self) -> None:
        ref = _score((), (Note(1, 60, 0, 1),))
        hyp = _score((), (Note(1, 62, 0, 1),))
        self.assertEqual(score_notes(ref, hyp)["metrics"]["pitch_inventory"]["combined"]["f1"], 0)

    def test_invalid_tolerance_and_staff_layout(self) -> None:
        score = _score((Note(1, 60, 0, 1),))
        for tolerance in [-1, float("nan"), float("inf")]:
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                score_notes(score, score, tolerance)
        with self.assertRaises(ValueError):
            align_measures(score, _score((), staves=2))

    def test_extra_staff_maps_to_nearest_reference_staff(self) -> None:
        high, low = Note(1, 72, 0, 1), Note(2, 48, 0, 1)
        ref = _score((high, low), (high, low), staves=2)
        # Three staves: a middle-high staff (mean 70) and a low staff in bar 1; in bar 2 the
        # extra staff sits low (mean 50), so it goes to the other reference staff.
        hyp = _score(
            (Note(1, 72, 0, 1), Note(2, 69, 0, 1), Note(3, 48, 0, 1)),
            (Note(1, 72, 0, 1), Note(2, 50, 0, 1), Note(3, 48, 0, 1)),
            staves=3,
        )
        result = score_notes(ref, hyp)
        self.assertEqual(result["staff_remap"], {"predicted_staves": 3, "reference_staves": 2})
        strict = result["metrics"]["pitch_onset_duration"]
        self.assertEqual(strict["staves"][0], Counts(2, 2, 3).report())
        self.assertEqual(strict["staves"][1], Counts(2, 2, 3).report())
        # Matching layouts are untouched.
        self.assertNotIn("staff_remap", score_notes(ref, ref))
        # Fewer staves than the reference also works.
        self.assertEqual(
            score_notes(hyp, ref)["metrics"]["pitch_inventory"]["combined"]["reference"], 6
        )

    def test_cli_json_and_input_protection(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            reference = Path(tmp) / "reference.musicxml"
            output = Path(tmp) / "result.json"
            text = _xml(_note())
            reference.write_text(text)
            command = [
                sys.executable,
                "-m",
                "validation.score_notes",
                str(reference),
                f"same={reference}",
            ]
            result = subprocess.run(  # noqa: S603
                command + ["--json", str(output)], capture_output=True, check=False
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())
            report = json.loads(output.read_text())
            self.assertEqual(
                report["results"][0]["metrics"]["pitch_onset_duration"]["combined"]["f1"], 1
            )
            protected = subprocess.run(  # noqa: S603
                command + ["--json", str(reference)], capture_output=True, check=False
            )
            self.assertNotEqual(protected.returncode, 0)
            self.assertEqual(reference.read_text(), text)


if __name__ == "__main__":
    unittest.main()
