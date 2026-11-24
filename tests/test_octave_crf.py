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
