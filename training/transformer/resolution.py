"""Positional embeddings for a larger input grid (HOMR_INPUT_SCALE, see configs.py).

The encoder learns one embedding per row (pos_embed_h, 16 rows) and one per column
(pos_embed_w, 80 columns). A finer grid has more rows and columns that cover the same
staff, so the learned rows are resampled along their axis: the token whose centre lies at
fraction f of the canvas gets the embedding the old grid has at f (linear interpolation,
align_corners=False, which is exactly that mapping). At scale 1 nothing changes.
"""

import torch
import torch.nn.functional as F  # noqa: N812

POS_EMBED_KEYS = ("encoder.pos_embed_h", "encoder.pos_embed_w")


def resample_axis(embedding: torch.Tensor, new_length: int) -> torch.Tensor:
    """(1, old_length, dim) -> (1, new_length, dim)"""
    if embedding.shape[1] == new_length:
        return embedding
    moved = embedding.float().permute(0, 2, 1)  # (1, dim, length)
    resized = F.interpolate(moved, size=new_length, mode="linear", align_corners=False)
    return resized.permute(0, 2, 1).to(embedding.dtype).contiguous()


def adapt_positional_embeddings(
    old_state: dict[str, torch.Tensor], model_state: dict[str, torch.Tensor]
) -> list[str]:
    """Resamples the checkpoint's positional embeddings in place to the model's grid."""
    changed = []
    for key in POS_EMBED_KEYS:
        if key in old_state and old_state[key].shape != model_state[key].shape:
            old_state[key] = resample_axis(old_state[key], model_state[key].shape[1])
            changed.append(f"{key} -> {tuple(old_state[key].shape)}")
    return changed
