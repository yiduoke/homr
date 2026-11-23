# ruff: noqa: S101
from pathlib import Path

import numpy as np
import pytest

# The training model needs the training dependencies
pytest.importorskip("x_transformers")
pytest.importorskip("timm")
pytest.importorskip("pytorch_lightning")
pytest.importorskip("segmentation_models_pytorch")

import onnxruntime as ort  # noqa: E402
import torch  # noqa: E402

from homr.transformer.configs import Config  # noqa: E402
from homr.transformer.decoder_inference import ScoreDecoder as OnnxDecoder  # noqa: E402
from training.architecture.transformer.decoder import (  # noqa: E402
    ScoreDecoder,
    get_score_wrapper,
    init_cache,
)
from training.onnx.convert import DecoderWrapper, decoder_io_names  # noqa: E402


def _small_config(monkeypatch: pytest.MonkeyPatch, per_note_octaves: bool) -> Config:
    monkeypatch.setenv("HOMR_PER_NOTE_OCTAVES", "1" if per_note_octaves else "0")
    config = Config()
    config.max_width = config.max_height = 2 * config.patch_size
    return config


def test_octave_head_trains_only_on_next_note_targets(monkeypatch: pytest.MonkeyPatch) -> None:
    config = _small_config(monkeypatch, per_note_octaves=True)
    wrapper = get_score_wrapper(config, attn_flash=False)
    decoder = ScoreDecoder(wrapper, config)
    zero = torch.zeros((1, 4), dtype=torch.int64)
    fields = dict.fromkeys(
        ("rhythms", "pitchs", "lifts", "articulations", "slurs", "positions"), zero
    )
    fields["context"] = torch.randn(1, 4, config.encoder_dim)
    fields["mask"] = torch.tensor([[True, True, True, False]])

    with pytest.raises(ValueError, match="Octave labels are required"):
        decoder(**fields)
    targets = torch.tensor([[-100, 1, -100, 2]])
    result = decoder(**fields, octaves=targets)
    octave_logits = result["logits"][-1]
    assert octave_logits.shape == (1, 3, 3)
    expected = torch.nn.functional.cross_entropy(octave_logits[:, 0], targets[:, 1])
    torch.testing.assert_close(result["loss_octave"], expected)
    assert torch.isfinite(result["loss"])
    result["loss"].backward()
    assert wrapper.to_logits_octave is not None
    assert wrapper.to_logits_octave.weight.grad is not None
    assert wrapper.to_logits_octave.weight.grad.abs().sum() > 0


def test_older_checkpoint_loads_with_zero_position_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config = _small_config(monkeypatch, per_note_octaves=False)
    model = get_score_wrapper(config, attn_flash=False)
    state = {k: v for k, v in model.state_dict().items() if k != "position_emb.weight"}
    model.position_emb.weight.data.fill_(1.0)
    model.load_state_dict(state, strict=True)
    assert model.position_emb.weight.abs().sum() == 0


def _export(model: torch.nn.Module, config: Config, path: Path) -> ort.InferenceSession:
    wrapper = DecoderWrapper(model).eval()
    cache, _, _, dynamic, _ = init_cache(0, torch.device("cpu"))
    inputs, outputs = decoder_io_names(config)
    tokens = torch.tensor([[0]], dtype=torch.int64)
    dynamic["context"] = {1: "cache_exists"}
    torch.onnx.export(
        wrapper,
        (*([tokens] * 6), torch.randn(1, 4, config.encoder_dim), torch.tensor([0]), *cache),
        str(path),
        input_names=inputs,
        output_names=outputs,
        dynamic_axes=dynamic,
        opset_version=18,
        dynamo=False,
    )
    options = ort.SessionOptions()
    options.intra_op_num_threads = 1
    return ort.InferenceSession(str(path), options, providers=["CPUExecutionProvider"])


def test_onnx_octave_output_reaches_the_note(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = _small_config(monkeypatch, per_note_octaves=True)
    config.max_seq_len = 2
    model = get_score_wrapper(config, attn_flash=False).eval()
    with torch.no_grad():
        model.to_logits_rhythm.weight.zero_()
        model.to_logits_rhythm.bias.fill_(-10)
        model.to_logits_rhythm.bias[config.rhythm_vocab["octaveShift_8va"]] = 10
        model.to_logits_rhythm.bias[config.rhythm_vocab["note_4"]] = 5
        assert model.to_logits_octave is not None
        model.to_logits_octave.weight.zero_()
        model.to_logits_octave.bias.copy_(torch.tensor([-4.0, -2.0, 4.0]))
    session = _export(model, config, tmp_path / "octaves.onnx")
    assert "out_octaves" in [output.name for output in session.get_outputs()]

    # Inference finds the octave head in the model, without HOMR_PER_NOTE_OCTAVES
    monkeypatch.delenv("HOMR_PER_NOTE_OCTAVES")
    inference_config = Config()
    inference_config.max_seq_len = 2
    assert not inference_config.per_note_octaves
    decoder = OnnxDecoder(session, fp16=False, use_gpu=False, config=inference_config)
    assert decoder.per_note_octaves and decoder.has_position_feedback
    context = np.random.default_rng(0).standard_normal((1, 4, config.encoder_dim))
    symbols = decoder.generate(np.array([[1]]), np.array([[0]]), context=context.astype(np.float32))
    # The legacy octave direction is never generated, the mark is on the note
    assert [(symbol.rhythm, symbol.octave_mark) for symbol in symbols] == [("note_4", "8vb")] * 2
