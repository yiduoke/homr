# ruff: noqa: S101

import torch

from training.transformer.lift_reset import (
    LIFT_EMBEDDING,
    LIFT_OUTPUT_BIAS,
    LIFT_OUTPUT_WEIGHT,
    reset_lift_head,
    reset_lift_tensors,
)

DIM = 64
LIFTS = 7
OTHER = "decoder.net.pitch_emb.emb.weight"


def _state() -> dict[str, torch.Tensor]:
    return {
        LIFT_OUTPUT_WEIGHT: torch.ones(LIFTS, DIM),
        LIFT_OUTPUT_BIAS: torch.ones(LIFTS),
        LIFT_EMBEDDING: torch.ones(LIFTS, DIM),
        OTHER: torch.ones(5, DIM),
    }


def test_resets_only_the_lift_tensors() -> None:
    state = _state()
    names = reset_lift_tensors(state)
    assert sorted(names) == sorted([LIFT_OUTPUT_WEIGHT, LIFT_OUTPUT_BIAS, LIFT_EMBEDDING])
    assert torch.equal(state[OTHER], torch.ones(5, DIM))
    assert torch.equal(state[LIFT_OUTPUT_BIAS], torch.zeros(LIFTS))
    for name in (LIFT_OUTPUT_WEIGHT, LIFT_EMBEDDING):
        assert state[name].shape == (LIFTS, DIM)
        assert abs(state[name].std().item() - 0.02) < 0.005
        assert abs(state[name].mean().item()) < 0.01
    assert not torch.equal(state[LIFT_OUTPUT_WEIGHT], state[LIFT_EMBEDDING])


def test_reset_is_reproducible() -> None:
    first, second = _state(), _state()
    reset_lift_tensors(first, seed=3)
    reset_lift_tensors(second, seed=3)
    assert torch.equal(first[LIFT_EMBEDDING], second[LIFT_EMBEDDING])


def test_reset_keeps_the_dtype() -> None:
    state = {name: tensor.bfloat16() for name, tensor in _state().items()}
    reset_lift_tensors(state)
    assert state[LIFT_OUTPUT_WEIGHT].dtype == torch.bfloat16


def test_reset_of_a_model() -> None:
    class Net(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.to_logits_lift = torch.nn.Linear(DIM, LIFTS)
            self.lift_emb = torch.nn.Module()
            self.lift_emb.emb = torch.nn.Embedding(LIFTS, DIM)  # type: ignore[assignment]
            self.pitch = torch.nn.Linear(DIM, 3)

    class Decoder(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.net = Net()

    class Model(torch.nn.Module):
        def __init__(self) -> None:
            super().__init__()
            self.decoder = Decoder()

    model = Model()
    pitch_before = model.decoder.net.pitch.weight.clone()
    reset_lift_head(model)
    assert torch.equal(model.decoder.net.pitch.weight, pitch_before)
    assert torch.equal(model.decoder.net.to_logits_lift.bias, torch.zeros(LIFTS))
