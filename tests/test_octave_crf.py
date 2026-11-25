import itertools
import os
import unittest
from typing import Any
from unittest import mock

import numpy as np

from homr.transformer.decoder_inference import ScoreDecoder
from homr.transformer.octave_crf import STATES, OctaveCrf, apply_octave_crf
from homr.transformer.vocabulary import EncodedSymbol


def _random_crf(rng: np.random.Generator) -> OctaveCrf:
    return OctaveCrf(rng.uniform(0.2, 2.0), rng.normal(0, 2, (len(STATES), len(STATES))))


def _brute_force(crf: OctaveCrf, emissions: np.ndarray) -> tuple[float, list[tuple[int, ...]]]:
    scores = {
        labels: crf.sequence_score(emissions, labels)
        for labels in itertools.product(range(3), repeat=len(emissions))
    }
    best = max(scores.values())
    return best, [labels for labels, score in scores.items() if np.isclose(score, best)]


def _note(position: str, logits: list[float]) -> EncodedSymbol:
    symbol = EncodedSymbol("note_4", "C5", "_", position=position)
    symbol.octave_logits = np.array(logits, dtype=np.float32)
    symbol.octave_mark = ("_", "8va", "8vb")[int(np.argmax(logits))]
    return symbol


# Strong preference to stay in a bracket once in it, weak preference not to start one
STICKY = OctaveCrf(
    1.0,
    [
        [0.0, 0.0, -1.0, -1.0],
        [0.0, 0.0, -3.0, -3.0],
        [0.0, -3.0, 0.0, -6.0],
        [0.0, -3.0, -6.0, 0.0],
    ],
)


class ViterbiTest(unittest.TestCase):
    def test_viterbi_is_exact_against_brute_force(self) -> None:
        rng = np.random.default_rng(0)
        for _ in range(300):
            crf = _random_crf(rng)
            n = int(rng.integers(1, 7))
            emissions = crf.emissions(rng.normal(0, 3, (n, 3)))
            path = crf.viterbi(emissions)
            best, argmaxes = _brute_force(crf, emissions)
            self.assertAlmostEqual(crf.sequence_score(emissions, path), best, places=9)
            self.assertIn(tuple(path), argmaxes)

    def test_empty_chain(self) -> None:
        self.assertEqual(STICKY.viterbi(np.zeros((0, 3))), [])

    def test_zero_transitions_and_unit_scale_are_the_per_note_argmax(self) -> None:
        rng = np.random.default_rng(1)
        crf = OctaveCrf(1.0, np.zeros((4, 4)))
        logits = rng.normal(0, 3, (50, 3))
        self.assertEqual(crf.viterbi(crf.emissions(logits)), list(logits.argmax(axis=1)))

    def test_single_dropout_inside_a_bracket_is_filled(self) -> None:
        sure_8va, weak_none = [0.0, 6.0, -6.0], [0.6, 0.0, -6.0]
        logits = np.array([sure_8va, sure_8va, weak_none, sure_8va, sure_8va])
        self.assertEqual(STICKY.viterbi(STICKY.emissions(logits)), [1, 1, 1, 1, 1])


# No stickiness at all: only one-note islands are priced (gap: 8va, none, 8va; blip: none, 8va, none)
ISLANDS = OctaveCrf(
    1.0,
    np.zeros((4, 4)),
    island_gap=[3.0, 3.0],
    island_blip=[3.0, 3.0],
)
# Fit B of the first version (scale 0.22, strong stay-in-bracket transitions), seed 7
FIT_B = OctaveCrf(
    0.2239728778745164,
    [
        [0.0, 0.457655, -0.135324, -0.322331],
        [0.388319, 1.726769, -0.90816, -1.03812],
        [-0.083301, -0.947496, 2.047875, -0.867949],
        [-0.305018, -1.068119, -0.855263, 1.910464],
    ],
)
SURE_8VA, WEAK_8VA, WEAK_NONE, SURE_NONE = (
    [0.0, 6.0, -6.0],
    [0.0, 0.9, -6.0],
    [0.6, 0.0, -6.0],
    [6.0, 0.0, -6.0],
)


class IslandTest(unittest.TestCase):
    def test_viterbi_with_islands_is_exact_against_brute_force(self) -> None:
        rng = np.random.default_rng(2)
        for _ in range(300):
            crf = OctaveCrf(
                rng.uniform(0.2, 2.0),
                rng.normal(0, 2, (len(STATES), len(STATES))),
                rng.uniform(0, 4, (2, int(rng.integers(1, 4)))),
                rng.uniform(0, 4, (2, int(rng.integers(1, 3)))),
            )
            n = int(rng.integers(1, 9))
            emissions = crf.emissions(rng.normal(0, 3, (n, 3)))
            path = crf.viterbi(emissions)
            best, argmaxes = _brute_force(crf, emissions)
            self.assertAlmostEqual(crf.sequence_score(emissions, path), best, places=9)
            self.assertIn(tuple(path), argmaxes)

    def _decode(self, crf: OctaveCrf, rows: list[list[float]]) -> list[int]:
        return crf.viterbi(crf.emissions(np.array(rows)))

    def test_one_note_gap_in_a_bracket_is_filled(self) -> None:
        rows = [SURE_8VA] * 3 + [WEAK_NONE] + [SURE_8VA] * 3
        self.assertEqual(self._decode(ISLANDS, rows), [1] * 7)

    def test_a_three_note_gap_is_filled_only_when_penalised_that_far(self) -> None:
        rows = [SURE_8VA] * 3 + [WEAK_NONE] * 3 + [SURE_8VA] * 3
        self.assertEqual(self._decode(ISLANDS, rows), [1] * 3 + [0] * 3 + [1] * 3)
        reach = OctaveCrf(1.0, np.zeros((4, 4)), [[3.0, 3.0, 3.0]] * 2, [[3.0]] * 2)
        self.assertEqual(self._decode(reach, rows), [1] * 9)
        # a long and confident gap between two brackets is a real close and reopening
        rows = [SURE_8VA] * 3 + [SURE_NONE] * 3 + [SURE_8VA] * 3
        self.assertEqual(self._decode(reach, rows), [1] * 3 + [0] * 3 + [1] * 3)

    def test_one_note_bracket_is_removed(self) -> None:
        rows = [SURE_NONE] * 3 + [WEAK_8VA] + [SURE_NONE] * 3
        self.assertEqual(self._decode(ISLANDS, rows), [0] * 7)

    def test_a_confident_one_note_bracket_survives(self) -> None:
        rows = [SURE_NONE] * 3 + [[0.0, 12.0, -6.0]] + [SURE_NONE] * 3
        self.assertEqual(self._decode(ISLANDS, rows), [0, 0, 0, 1, 0, 0, 0])

    def test_a_close_after_two_notes_is_kept(self) -> None:
        # the head closes after 2 notes with modest confidence; runs of none are not penalised
        rows = [SURE_8VA] * 2 + [WEAK_8VA] * 0 + [[3.0, 0.0, -6.0]] * 4
        self.assertEqual(self._decode(ISLANDS, rows), [1, 1, 0, 0, 0, 0])

    def test_a_close_is_kept_where_the_refitted_first_order_crf_stays_open(self) -> None:
        rows = [SURE_8VA] * 5 + [[2.0, 0.0, -6.0]] * 3
        self.assertEqual(self._decode(ISLANDS, rows), [1] * 5 + [0] * 3)
        self.assertEqual(self._decode(FIT_B, rows), [1] * 8)  # the first version (fit B): stuck open


class ApplyTest(unittest.TestCase):
    def test_chains_are_per_staff_and_skip_symbols_without_logits(self) -> None:
        sure_8va, weak_none, sure_none = [0.0, 6.0, -6.0], [0.6, 0.0, -6.0], [6.0, 0.0, 0.0]
        rest = EncodedSymbol("rest_4", position="upper")
        symbols = [
            _note("upper", sure_8va),
            _note("lower", sure_none),
            rest,
            _note("upper", weak_none),
            _note("lower2", sure_none),
            _note("upper2", sure_8va),
        ]
        apply_octave_crf(symbols, STICKY)
        self.assertEqual([s.octave_mark for s in symbols], ["8va", "_", None, "8va", "_", "8va"])


class SwitchTest(unittest.TestCase):
    def _decoder(self, symbols: list[Any]) -> ScoreDecoder:
        decoder = object.__new__(ScoreDecoder)
        decoder.per_note_octaves = True
        decoder.generate_greedy = lambda *_a, **_k: symbols  # type: ignore[method-assign]
        return decoder

    def _symbols(self) -> list[Any]:
        sure_8va, weak_none = [0.0, 6.0, -6.0], [0.6, 0.0, -6.0]
        return [_note("upper", sure_8va), _note("upper", weak_none), _note("upper", sure_8va)]

    def test_switch_off_keeps_the_per_note_argmax(self) -> None:
        with mock.patch.dict(os.environ, {"HOMR_OCTAVE_CRF": "0"}):
            out = self._decoder(self._symbols()).generate(
                np.array([[1]]), np.array([[0]]), context=None, beam_width=1
            )
        self.assertEqual([s.octave_mark for s in out], ["8va", "_", "8va"])

    def test_switch_on_decodes_with_the_crf(self) -> None:
        with (
            mock.patch.dict(os.environ, {"HOMR_OCTAVE_CRF": "1"}),
            mock.patch("homr.transformer.octave_crf._crf", STICKY),
        ):
            out = self._decoder(self._symbols()).generate(
                np.array([[1]]), np.array([[0]]), context=None, beam_width=1
            )
        self.assertEqual([s.octave_mark for s in out], ["8va", "8va", "8va"])
