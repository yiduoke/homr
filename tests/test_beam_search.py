"""
Beam search in the decoder: width 1 must be the greedy decoding token for token, and the
score a beam reports must be what the model gives its tokens. Needs the model weights and
real staff crops (the development crops of the research folder, or HOMR_DEV_CROPS); the
tests are skipped without them.
"""

import os
import unittest
from pathlib import Path
from typing import Any

import numpy as np

from homr.transformer.configs import Config
from homr.transformer.decoder_inference import _log_softmax

CROPS = ["A10_p-01_s0.png", "A2_p-070_s0.png", "B3_p-20_s1.png", "C2_p-10_s0.png"]


def _crop_dir() -> Path | None:
    if os.environ.get("HOMR_DEV_CROPS"):
        return Path(os.environ["HOMR_DEV_CROPS"])
    for parent in Path(__file__).resolve().parents:
        for sub in ("run/eval_kit/data/crops/images", "eval_kit/data/crops/images"):
            if (parent / sub).is_dir():
                return parent / sub
    return None


def _available() -> bool:
    config = Config()
    crops = _crop_dir()
    return (
        os.path.exists(config.filepaths.decoder_path)
        and os.path.exists(config.filepaths.encoder_path)
        and crops is not None
    )


@unittest.skipUnless(_available(), "needs the model weights and real staff crops")
class BeamSearchTest(unittest.TestCase):
    model: Any
    decoder: Any
    contexts: list[tuple[str, np.ndarray]]

    @classmethod
    def setUpClass(cls) -> None:
        import cv2  # noqa: PLC0415

        from homr.staff_parsing import add_image_into_tr_omr_canvas  # noqa: PLC0415
        from homr.transformer.staff2score import Staff2Score, _transform  # noqa: PLC0415

        config = Config()
        config.use_gpu_inference = False
        cls.model = Staff2Score(config, decoder_threads=1)
        cls.decoder = cls.model._decoders.get()
        crop_dir = _crop_dir()
        if crop_dir is None:
            raise unittest.SkipTest("no crops")
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
        return self.decoder.generate_beams(start, nonote, width, context)

    def test_width_one_is_greedy_token_for_token(self) -> None:
        self.assertGreaterEqual(len(self.contexts), 3)
        for name, context in self.contexts:
            greedy = [str(s) for s in self._greedy(context)]
            beams = self._beams(context, 1)
            self.assertEqual(len(beams), 1)
            self.assertEqual([str(s) for s in beams[0].symbols], greedy, name)
            self.assertGreater(len(greedy), 20, name)

    def test_beam_scores_are_the_model_scores_of_their_tokens(self) -> None:
        config = self.decoder.config
        vocabs = [
            config.rhythm_vocab,
            config.pitch_vocab,
            config.lift_vocab,
            config.articulation_vocab,
            config.slur_vocab,
        ]
        name, context = self.contexts[0]
        for hypothesis in self._beams(context, 3):
            cache, _, _ = self.decoder.init_cache()
            inputs = [1, 0, 0, 0, 0]
            total = 0.0
            for step, symbol in enumerate(hypothesis.symbols):
                outputs = self.decoder._run_step(
                    inputs, cache, context if step == 0 else context[:, :1], step
                )
                heads = [_log_softmax(outputs[i].numpy()[0, -1, :]) for i in range(6)]
                ids = [
                    vocabs[0][symbol.rhythm],
                    vocabs[1][symbol.pitch],
                    vocabs[2][symbol.lift],
                    vocabs[3][symbol.articulation],
                    vocabs[4][symbol.slur],
                ]
                position = config.position_vocab[symbol.position]
                total += sum(float(heads[h][i]) for h, i in zip([0, 1, 2, 4, 5], ids, strict=True))
                total += float(heads[3][position])
                cache = outputs[7:]
                inputs = ids
            outputs = self.decoder._run_step(inputs, cache, context[:, :1], len(hypothesis.symbols))
            eos = float(_log_softmax(outputs[0].numpy()[0, -1, :])[config.eos_token])
            self.assertTrue(
                abs(total + eos - hypothesis.log_prob) < 1e-3
                or abs(total - hypothesis.log_prob) < 1e-3,
                f"{name}: {hypothesis.log_prob} vs {total} (+ EOS {eos})",
            )


if __name__ == "__main__":
    unittest.main()
