"""Re-initialise the lift branch of a checkpoint whose lift meant something else.

Up to the first meter run the lift of a note was the sounding alteration; from the printed
accidentals run on it is the accidental sign which is printed before the note (see
Vocabulary.md and homr/accidentals.py). The classes keep their names and indices (the
vocabulary doesn't change), so the old weights load without an error but mean the wrong thing:
`#` used to read "sounds sharp" and now reads "a sharp sign is drawn". The output layer and the
embedding which feeds the previous lift back into the decoder are therefore started again,
everything else is kept.

finetune_octave.py does this when FT_RESET_LIFT=1 is set, for a warm start from a .pth
(FT_CKPT) and for weights from a safetensors file (FT_INIT). It doesn't touch a resumed
training (FT_RESUME), whose lift branch was already reset by the run it continues.
"""

import torch

LIFT_OUTPUT_WEIGHT = "decoder.net.to_logits_lift.weight"
LIFT_OUTPUT_BIAS = "decoder.net.to_logits_lift.bias"
LIFT_EMBEDDING = "decoder.net.lift_emb.emb.weight"
LIFT_TENSORS = (LIFT_OUTPUT_WEIGHT, LIFT_OUTPUT_BIAS, LIFT_EMBEDDING)

# The standard deviation of the decoder's own initialisation (decoder.py, init_)
INIT_STD = 0.02


def reset_lift_tensors(
    state: dict[str, torch.Tensor], seed: int = 0, std: float = INIT_STD
) -> list[str]:
    """
    Re-initialises the lift tensors of a state dict in place: weights and embedding normal
    with `std`, bias zero. Returns the names of the tensors which were reset.
    """
    missing = [name for name in LIFT_TENSORS if name not in state]
    if missing:
        raise KeyError(f"state dict has no {missing}")
    generator = torch.Generator().manual_seed(seed)
    for name in (LIFT_OUTPUT_WEIGHT, LIFT_EMBEDDING):
        tensor = state[name]
        state[name] = torch.randn(tensor.shape, generator=generator).mul_(std).to(tensor.dtype)
    state[LIFT_OUTPUT_BIAS] = torch.zeros_like(state[LIFT_OUTPUT_BIAS])
    return list(LIFT_TENSORS)


def reset_lift_head(model: torch.nn.Module, seed: int = 0, std: float = INIT_STD) -> list[str]:
    """Re-initialises the lift branch of a model, see reset_lift_tensors."""
    state = model.state_dict()
    names = reset_lift_tensors(state, seed, std)
    model.load_state_dict(state, strict=True)
    return names
