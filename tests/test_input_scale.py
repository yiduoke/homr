# ruff: noqa: S101

import pytest
import torch

from homr.transformer.configs import _scaled_canvas
from training.transformer.resolution import adapt_positional_embeddings, resample_axis


def test_default_scale_is_the_released_canvas() -> None:
    assert _scaled_canvas(1.0) == (256, 1280)


def test_larger_canvas_keeps_whole_patches() -> None:
    assert _scaled_canvas(1.5) == (384, 1920)
    with pytest.raises(ValueError):
        _scaled_canvas(1.3)


def test_resampling_keeps_length_and_is_identity_at_the_same_size() -> None:
    embedding = torch.randn(1, 16, 8)
    assert torch.equal(resample_axis(embedding, 16), embedding)
    assert resample_axis(embedding, 24).shape == (1, 24, 8)


def test_resampling_maps_the_same_physical_position() -> None:
    # A linear ramp over the canvas stays a linear ramp at any resolution
    old = torch.linspace(0.5 / 16, 1 - 0.5 / 16, 16).reshape(1, 16, 1)
    new = resample_axis(old, 24)
    expected = torch.linspace(0.5 / 24, 1 - 0.5 / 24, 24).reshape(1, 24, 1)
    # Only the border tokens differ, where the old grid has to be extrapolated
    assert torch.allclose(new[:, 1:-1], expected[:, 1:-1], atol=1e-5)


def test_adapt_only_touches_positional_embeddings_with_another_shape() -> None:
    old = {
        "encoder.pos_embed_h": torch.randn(1, 16, 4),
        "encoder.pos_embed_w": torch.randn(1, 80, 4),
        "decoder.x": torch.randn(3),
    }
    model = {
        "encoder.pos_embed_h": torch.zeros(1, 24, 4),
        "encoder.pos_embed_w": old["encoder.pos_embed_w"],
    }
    kept = old["encoder.pos_embed_w"]
    assert len(adapt_positional_embeddings(old, model)) == 1
    assert old["encoder.pos_embed_h"].shape == (1, 24, 4)
    assert old["encoder.pos_embed_w"] is kept
