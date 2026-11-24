import os
import unittest
import unittest.mock
from fractions import Fraction

from homr.transformer.bar_fill import (
    Hypothesis,
    choose,
    closed_bars,
    last_printed_meter,
    misfit_bars,
    rerank,
)
from training.transformer.training_vocabulary import read_token_lines


def _symbols(text: str) -> list:
    return read_token_lines([line for line in text.strip().split("\n") if line.strip()])


THREE_FOUR = """
clef_G2 _ _ _ _ upper&clef_F4 _ _ _ _ lower
timeSignature_3/4 . . . . .
note_4 C5 _ _ _ upper&note_2. C3 _ _ _ lower
note_4 D5 _ _ _ upper
note_4 E5 _ _ _ upper
barline . . . . .
note_12 C5 _ _ _ upper&rest_2. _ _ _ _ lower
note_12 D5 _ _ _ upper
note_12 E5 _ _ _ upper
note_2 F5 _ _ _ upper
barline . . . . .
note_4 G5 _ _ _ upper
"""


class BarFillTest(unittest.TestCase):
    def test_only_closed_bars_count_and_tuplets_fill(self) -> None:
        bars = closed_bars(_symbols(THREE_FOUR))
        self.assertEqual(len(bars), 2)
        self.assertEqual([b.length for b in bars], [Fraction(3, 4), Fraction(3, 4)])
        self.assertEqual(misfit_bars(_symbols(THREE_FOUR)), (0, 2))

    def test_a_wrong_duration_is_a_misfit_of_the_printed_meter(self) -> None:
        wrong = THREE_FOUR.replace("note_4 D5", "note_8 D5", 1)
        self.assertEqual(misfit_bars(_symbols(wrong)), (1, 2))

    def test_the_meter_from_earlier_staffs_counts_without_a_printed_one(self) -> None:
        text = THREE_FOUR.replace("timeSignature_3/4 . . . . .\n", "")
        self.assertEqual(misfit_bars(_symbols(text), Fraction(3, 4)), (0, 2))
        self.assertEqual(misfit_bars(_symbols(text), Fraction(1)), (2, 2))

    def test_a_staff_with_only_rests_is_a_bar_rest(self) -> None:
        text = THREE_FOUR.replace("rest_2. _ _ _ _ lower", "rest_1 _ _ _ _ lower")
        self.assertEqual(misfit_bars(_symbols(text)), (0, 2))

    def test_grace_notes_take_no_time(self) -> None:
        text = THREE_FOUR.replace(
            "note_4 E5 _ _ _ upper\n", "note_8G D5 _ _ _ upper\nnote_4 E5 _ _ _ upper\n", 1
        )
        self.assertEqual(misfit_bars(_symbols(text)), (0, 2))

    def test_last_printed_meter(self) -> None:
        self.assertEqual(last_printed_meter(_symbols(THREE_FOUR)), Fraction(3, 4))
        self.assertIsNone(last_printed_meter(_symbols("note_4 C5 _ _ _ upper")))

    def test_rerank_prefers_bar_fill_then_likelihood(self) -> None:
        good = _symbols(THREE_FOUR)
        bad = _symbols(THREE_FOUR.replace("note_4 D5", "note_8 D5", 1))
        chosen = rerank([Hypothesis(bad, -1.0), Hypothesis(good, -2.0)])
        self.assertIs(chosen.symbols, good)
        chosen = rerank([Hypothesis(good, -3.0), Hypothesis(list(good), -2.0)])
        self.assertEqual(chosen.log_prob, -2.0)

    def test_rerank_does_not_prefer_a_hypothesis_without_bar_lines(self) -> None:
        bad = _symbols(THREE_FOUR.replace("note_4 D5", "note_8 D5", 1))
        no_bars = [s for s in bad if s.rhythm != "barline"]
        chosen = rerank([Hypothesis(no_bars, -1.0), Hypothesis(bad, -2.0)])
        self.assertIs(chosen.symbols, bad)


class ChooseTest(unittest.TestCase):
    def setUp(self) -> None:
        self.good = _symbols(THREE_FOUR)
        self.bad = _symbols(THREE_FOUR.replace("note_4 D5", "note_8 D5", 1))
        self.env = unittest.mock.patch.dict(os.environ, {}, clear=False)
        self.env.start()
        for key in ("HOMR_BEAM_RERANK", "HOMR_BEAM_MARGIN"):
            os.environ.pop(key, None)

    def tearDown(self) -> None:
        self.env.stop()

    def test_anchored_takes_a_hypothesis_whose_bars_fill_better(self) -> None:
        greedy = Hypothesis(self.bad, -5.0)
        chosen = choose([Hypothesis(self.bad, -4.0), Hypothesis(self.good, -6.0)], None, greedy)
        self.assertIs(chosen.symbols, self.good)

    def test_anchored_keeps_greedy_when_the_bars_are_no_better(self) -> None:
        greedy = Hypothesis(self.good, -5.0)
        other = Hypothesis(list(self.good), -4.0)
        self.assertIs(choose([other, Hypothesis(self.good, -5.0)], None, greedy), greedy)

    def test_a_decisive_lead_of_the_model_replaces_greedy(self) -> None:
        greedy = Hypothesis(self.good, -50.0)
        top = Hypothesis(list(self.good), -30.0)
        self.assertIs(choose([top], None, greedy), top)
        os.environ["HOMR_BEAM_MARGIN"] = "none"
        self.assertIs(choose([top], None, greedy), greedy)

    def test_fill_and_most_likely_modes(self) -> None:
        greedy = Hypothesis(self.good, -5.0)
        hyps = [Hypothesis(self.bad, -1.0), Hypothesis(self.good, -2.0)]
        os.environ["HOMR_BEAM_RERANK"] = "fill"
        self.assertIs(choose(hyps, None, greedy), hyps[1])
        os.environ["HOMR_BEAM_RERANK"] = "0"
        self.assertIs(choose(hyps, None, greedy), hyps[0])


if __name__ == "__main__":
    unittest.main()
