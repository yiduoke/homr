# ruff: noqa: S101
"""
The ONNX decoder reads which inputs and outputs a model has: the released meteracc model has
neither position feedback nor an octave head, comb6 has both.
"""

from typing import Any

import numpy as np
import pytest

from homr import download_utils
from homr.main import RELEASE_SHA256, transformer_release_url
from homr.transformer.configs import Config
from homr.transformer.decoder_inference import ScoreDecoder

LEGACY_INPUTS = ["rhythms", "pitchs", "lifts", "articulations", "slurs"]
LEGACY_OUTPUTS = [
    "out_rhythms",
    "out_pitchs",
    "out_lifts",
    "out_positions",
    "out_articulations",
    "out_slurs",
]


class _Named:
    def __init__(self, name: str) -> None:
        self.name = name


class _Value:
    def __init__(self, value: np.ndarray) -> None:
        self.value = value

    def numpy(self) -> np.ndarray:
        return self.value


class _Binding:
    def __init__(self, session: "_FakeSession") -> None:
        self.session = session
        self.inputs: dict[str, Any] = {}
        self.output_names: list[str] = []

    def bind_cpu_input(self, name: str, value: np.ndarray) -> None:
        self.inputs[name] = value

    def bind_ortvalue_input(self, name: str, value: Any) -> None:
        self.inputs[name] = value

    def bind_output(self, name: str, *args: Any) -> None:
        if name not in self.output_names:
            self.output_names.append(name)

    def get_outputs(self) -> list[_Value]:
        return [_Value(self.session.result[name]) for name in self.output_names]


class _FakeSession:
    """
    Plays a fixed sequence of rhythm tokens; every other head picks its index 1 (octave
    head: 8va). In the first step the legacy octave direction has the highest rhythm logit.
    """

    def __init__(self, config: Config, inputs: list[str], outputs: list[str], rhythms: list[str]):
        self.config = config
        self.input_list = [*inputs, "context", "cache_len"]
        self.output_list = [*outputs, "attention"]
        self.rhythms = rhythms
        self.binding = _Binding(self)
        self.steps: list[dict[str, Any]] = []
        self.result: dict[str, np.ndarray] = {}

    def get_inputs(self) -> list[_Named]:
        return [_Named(name) for name in self.input_list]

    def get_outputs(self) -> list[_Named]:
        return [_Named(name) for name in self.output_list]

    def io_binding(self) -> _Binding:
        return self.binding

    def run_with_iobinding(self, iobinding: _Binding) -> None:
        bound = set(iobinding.inputs)
        assert bound <= set(self.input_list) | {f"cache_in{i}" for i in range(32)}, bound
        self.steps.append(dict(iobinding.inputs))
        step = len(self.steps) - 1
        rhythm = np.full((1, 1, self.config.num_rhythm_tokens), -5.0, dtype=np.float32)
        if step == 0:
            rhythm[0, 0, self.config.rhythm_vocab["octaveShift_8va"]] = 10.0
        rhythm[0, 0, self.config.rhythm_vocab[self.rhythms[step]]] = 5.0

        def head(size: int) -> np.ndarray:
            logits = np.zeros((1, 1, size), dtype=np.float32)
            logits[0, 0, 1] = 1.0
            return logits

        self.result = {
            "out_rhythms": rhythm,
            "out_pitchs": head(self.config.num_pitch_tokens),
            "out_lifts": head(self.config.num_lift_tokens),
            "out_positions": head(self.config.num_position_tokens),
            "out_articulations": head(self.config.num_articulation_tokens),
            "out_slurs": head(self.config.num_slur_tokens),
            "out_octaves": head(3),
            "attention": np.zeros(2, dtype=np.float32),
        }
        for i in range(32):
            self.result[f"cache_out{i}"] = np.zeros((1, 8, step + 1, 64), dtype=np.float32)


def _decode(session: _FakeSession, config: Config) -> list[Any]:
    decoder = ScoreDecoder(session, fp16=False, use_gpu=False, config=config)  # type: ignore
    return decoder.generate(np.array([[1]]), np.array([[0]]), context=np.zeros((1, 4, 512)))


def test_legacy_model_is_decoded_as_before() -> None:
    config = Config()
    session = _FakeSession(config, LEGACY_INPUTS, LEGACY_OUTPUTS, ["note_4", "rest_4", "EOS"])
    decoder = ScoreDecoder(session, fp16=False, use_gpu=False, config=config)  # type: ignore
    assert not decoder.has_position_feedback and not decoder.per_note_octaves
    symbols = _decode(session, config)
    # The legacy octave direction has the highest logit and is generated as before
    assert [symbol.rhythm for symbol in symbols] == ["octaveShift_8va", "rest_4"]
    assert all(symbol.octave_mark is None for symbol in symbols)
    assert all("positions" not in step for step in session.steps)


def test_comb6_model_feeds_back_positions_and_reads_octaves() -> None:
    config = Config()
    session = _FakeSession(
        config,
        [*LEGACY_INPUTS, "positions"],
        [*LEGACY_OUTPUTS, "out_octaves"],
        ["note_4", "rest_4", "note_8", "EOS"],
    )
    symbols = _decode(session, config)
    assert [(symbol.rhythm, symbol.octave_mark) for symbol in symbols] == [
        ("note_4", "8va"),
        ("rest_4", None),
        ("note_8", "8va"),
    ]
    # The first step gets the nonote position, every later step the previous prediction
    position_1 = config.position_vocab[symbols[0].position]
    assert [int(step["positions"][0, 0]) for step in session.steps] == [0] + [position_1] * 3


def test_default_model_is_comb6_on_the_fork() -> None:
    config = Config()
    assert config.filepaths.decoder_path.endswith("decoder_pytorch_model_comb6-s7-ema-b918469.onnx")
    url = transformer_release_url(config.filepaths.decoder_path)
    assert url == "https://github.com/yiduoke/homr/releases/download/comb6-s7-ema/"
    assert transformer_release_url("decoder_pytorch_model_meteracc-r2s7-afae0e3.onnx").endswith(
        "/meteracc_checkpoints/"
    )
    for name in ("encoder", "decoder"):
        for suffix in ("", "_fp16"):
            assert f"{name}_pytorch_model_comb6-s7-ema-b918469{suffix}.zip" in RELEASE_SHA256


def test_checksum_mismatch_is_an_error(tmp_path: Any) -> None:
    path = tmp_path / "model.zip"
    path.write_bytes(b"abc")
    sha_abc = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    download_utils.verify_sha256(str(path), sha_abc)
    download_utils.verify_sha256(str(path), None)
    with pytest.raises(ValueError, match="Checksum mismatch"):
        download_utils.verify_sha256(str(path), "0" * 64)
