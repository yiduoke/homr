"""
Beam search in the decoder: width 1 must be the greedy decoding token for token, and the
score a beam reports must be what the model gives its tokens. Needs the model weights and
real staff crops (the development crops of the research folder, or HOMR_DEV_CROPS); the
tests are skipped without them. The second test class runs the same checks on a model with
position feedback and a per-note octave head (COMB6; HOMR_BEAM_TEST_COMB6=<folder with
encoder*.onnx and decoder*.onnx, fp32>, else the research folder's copy).
"""

import glob
import os
import unittest
from pathlib import Path
from typing import Any

import numpy as np

from homr.transformer.beam_search import (
    _log_softmax,
    _may_branch,
    _run_step,
    beam_search,
    generate_beams,
)
from homr.transformer.configs import Config

CROPS = ["A10_p-01_s0.png", "A2_p-070_s0.png", "B3_p-20_s1.png", "C2_p-10_s0.png"]
COMB6 = "run/round5_prep/results/weights/round5_COMB6_s7_ema_onnx"


def _research_dir(sub: str) -> Path | None:
    for parent in Path(__file__).resolve().parents:
        for prefix in ("", "run/"):
            candidate = parent / (prefix + sub.removeprefix("run/"))
            if candidate.is_dir():
                return candidate
    return None


def _crop_dir() -> Path | None:
    if os.environ.get("HOMR_DEV_CROPS"):
        return Path(os.environ["HOMR_DEV_CROPS"])
    return _research_dir("run/eval_kit/data/crops/images")


def _comb6_paths() -> tuple[str, str] | None:
    folder = os.environ.get("HOMR_BEAM_TEST_COMB6") or _research_dir(COMB6)
    if folder is None:
        return None
    encoders = [p for p in glob.glob(f"{folder}/encoder*.onnx") if not p.endswith("_fp16.onnx")]
    decoders = [p for p in glob.glob(f"{folder}/decoder*.onnx") if not p.endswith("_fp16.onnx")]
    if not encoders or not decoders:
        return None
    return encoders[0], decoders[0]


def _released_config() -> Config | None:
    config = Config()
    if not (
        os.path.exists(config.filepaths.decoder_path)
        and os.path.exists(config.filepaths.encoder_path)
    ):
        return None
    return config


def _comb6_config() -> Config | None:
    paths = _comb6_paths()
    if paths is None:
        return None
    config = Config()
    config.filepaths.encoder_path, config.filepaths.decoder_path = paths
    config.per_note_octaves = True
    return config


class _BeamSearchChecks:
    config: Config | None = None
    model: Any
    decoder: Any
    contexts: list[tuple[str, np.ndarray]]

    @classmethod
    def setUpClass(cls) -> None:
        import cv2  # noqa: PLC0415

        from homr.staff_parsing import add_image_into_tr_omr_canvas  # noqa: PLC0415
        from homr.transformer.staff2score import Staff2Score, _transform  # noqa: PLC0415

        crop_dir = _crop_dir()
        if cls.config is None or crop_dir is None:
            raise unittest.SkipTest("needs the model weights and real staff crops")
        cls.config.use_gpu_inference = False
        cls.model = Staff2Score(cls.config, decoder_threads=1)
        cls.decoder = cls.model._decoders.get()
        cls.contexts = []
        for name in CROPS:
            path = crop_dir / name
            if not path.exists():
                continue
            pixels = cv2.imread(str(path), 0)
            if pixels is None:
                continue
            image = add_image_into_tr_omr_canvas(pixels)
            context = cls.model.encoder.generate(_transform(image=image)).copy()
            cls.contexts.append((name, context.astype(np.float32)))

    def _greedy(self, context: np.ndarray) -> list:
        start, nonote = np.array([[1]], dtype=np.int64), np.array([[0]], dtype=np.int64)
        return self.decoder.generate_greedy(start, nonote, context=context)

    def _beams(self, context: np.ndarray, width: int) -> list:
        start, nonote = np.array([[1]], dtype=np.int64), np.array([[0]], dtype=np.int64)
        return generate_beams(self.decoder, start, nonote, width, context)

    @staticmethod
    def _key(symbol: Any) -> tuple[str, Any]:
        return (str(symbol), symbol.octave_mark)

    def test_width_one_is_greedy_token_for_token(self) -> None:
        self.assertGreaterEqual(len(self.contexts), 3)
        for name, context in self.contexts:
            greedy = [self._key(s) for s in self._greedy(context)]
            beams = self._beams(context, 1)
            self.assertEqual(len(beams), 1)
            self.assertEqual([self._key(s) for s in beams[0].symbols], greedy, name)
            self.assertGreater(len(greedy), 20, name)

    def test_the_greedy_reading_of_a_wide_beam_is_the_greedy_decoding(self) -> None:
        start, nonote = np.array([[1]], dtype=np.int64), np.array([[0]], dtype=np.int64)
        for name, context in self.contexts:
            greedy = [self._key(s) for s in self._greedy(context)]
            result = beam_search(self.decoder, start, nonote, 3, context)
            self.assertEqual([self._key(s) for s in result.greedy.symbols], greedy, name)
            # the extra greedy path leaves the beam's own hypotheses as they were
            plain = generate_beams(self.decoder, start, nonote, 3, context)
            self.assertEqual(
                [[self._key(s) for s in h.symbols] for h in result.hypotheses],
                [[self._key(s) for s in h.symbols] for h in plain],
            )

    def test_generate_with_width_one_takes_the_greedy_path(self) -> None:
        name, context = self.contexts[0]
        start, nonote = np.array([[1]], dtype=np.int64), np.array([[0]], dtype=np.int64)
        via_generate = self.decoder.generate(start, nonote, context=context, beam_width=1)
        self.assertEqual(
            [self._key(s) for s in via_generate], [self._key(s) for s in self._greedy(context)]
        )

    def test_beam_scores_are_the_model_scores_of_their_tokens(self) -> None:
        config = self.decoder.config
        vocabs = [
            config.rhythm_vocab,
            config.pitch_vocab,
            config.lift_vocab,
            config.articulation_vocab,
            config.slur_vocab,
            config.position_vocab,
        ]
        heads = ["out_rhythms", "out_pitchs", "out_lifts", "out_articulations", "out_slurs"]
        mask = np.zeros(len(config.rhythm_vocab))
        mask[self.decoder.legacy_octave_rhythms] = -np.inf
        fed_back = 6 if self.decoder.has_position_feedback else 5
        name, context = self.contexts[0]
        for hypothesis in self._beams(context, 3):
            cache, _, _ = self.decoder.init_cache()
            inputs = [1, 0, 0, 0, 0, 0][:fed_back]
            total = 0.0
            for step, symbol in enumerate(hypothesis.symbols):
                out = _run_step(
                    self.decoder, inputs, cache, context if step == 0 else context[:, :1], step
                )
                ids = [
                    vocabs[0][symbol.rhythm],
                    vocabs[1][symbol.pitch],
                    vocabs[2][symbol.lift],
                    vocabs[3][symbol.articulation],
                    vocabs[4][symbol.slur],
                    vocabs[5][symbol.position],
                ]
                logits = [out[h].numpy()[0, -1, :] for h in [*heads, "out_positions"]]
                logits[0] = logits[0] + mask
                total += sum(float(_log_softmax(lg)[i]) for lg, i in zip(logits, ids, strict=True))
                cache = out["cache"]
                inputs = ids[:fed_back]
            out = _run_step(self.decoder, inputs, cache, context[:, :1], len(hypothesis.symbols))
            eos = float(_log_softmax(out["out_rhythms"].numpy()[0, -1, :] + mask)[config.eos_token])
            self.assertTrue(
                abs(total + eos - hypothesis.log_prob) < 1e-3
                or abs(total - hypothesis.log_prob) < 1e-3,
                f"{name}: {hypothesis.log_prob} vs {total} (+ EOS {eos})",
            )


class BranchRuleTest(unittest.TestCase):
    def test_timing_branches_only_between_notes_rests_and_chords(self) -> None:
        self.assertTrue(_may_branch("note_16", "note_24", "timing"))
        self.assertTrue(_may_branch("note_8", "rest_8", "timing"))
        self.assertTrue(_may_branch("chord", "note_4", "timing"))
        self.assertFalse(_may_branch("note_16", "octaveShiftStop", "timing"))
        self.assertFalse(_may_branch("note_16", "[EOS]", "timing"))
        self.assertFalse(_may_branch("note_16", "barline", "timing"))
        self.assertFalse(_may_branch("clef_G2", "note_4", "timing"))

    def test_durations_keeps_the_kind(self) -> None:
        self.assertTrue(_may_branch("note_16", "note_24", "durations"))
        self.assertFalse(_may_branch("note_8", "rest_8", "durations"))
        self.assertFalse(_may_branch("chord", "note_4", "durations"))

    def test_all_takes_anything(self) -> None:
        self.assertTrue(_may_branch("note_16", "[EOS]", "all"))


class ReleasedModelBeamSearchTest(_BeamSearchChecks, unittest.TestCase):
    config = _released_config()


class PositionFeedbackOctaveHeadBeamSearchTest(_BeamSearchChecks, unittest.TestCase):
    config = _comb6_config()

    def test_model_has_position_feedback_and_octave_head(self) -> None:
        self.assertTrue(self.decoder.has_position_feedback)
        self.assertTrue(self.decoder.per_note_octaves)
        marks = {s.octave_mark for _, c in self.contexts for s in self._beams(c, 3)[0].symbols}
        self.assertIn("_", marks)


if __name__ == "__main__":
    unittest.main()
