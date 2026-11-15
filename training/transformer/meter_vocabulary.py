"""Rows of a checkpoint for the complete time signature tokens.

The vocabulary used to have timeSignature/<denominator> tokens. They are replaced by
timeSignature_<numerator>/<denominator>, timeSignature_common and timeSignature_cut
(see homr/transformer/vocabulary.py). The new tokens are appended to the end of the rhythm
vocabulary, the old ones are removed, so the rows of the tokens behind them move. Therefore
rows are copied by token name (finetune_octave.warm_start does this for every grown tensor):

- Tokens which exist in both vocabularies keep their row.
- A new time signature starts from the old row of the same denominator, so timeSignature_3/4
  and timeSignature_4/4 start from timeSignature/4. C starts from timeSignature/4 and cut C
  from timeSignature/2, the denominators of 4/4 and 2/2.
- The old timeSignature/<denominator> rows are dropped, nothing refers to them any more.
- Any other new token starts from the mean of the old rows.

The three tensors of the rhythm head which grow with the vocabulary are in RHYTHM_TENSORS.
"""

from typing import Callable

import torch

from homr.transformer.vocabulary import (
    TIME_SIGNATURE_COMMON,
    TIME_SIGNATURE_CUT,
    TIME_SIGNATURE_PREFIX,
    parse_time_signature_token,
)

OLD_TIME_SIGNATURE_PREFIX = "timeSignature/"

RHYTHM_TENSORS = [
    "decoder.net.rhythm_emb.emb.weight",
    "decoder.net.to_logits_rhythm.weight",
    "decoder.net.to_logits_rhythm.bias",
]


def old_time_signature_token(token: str) -> str | None:
    """The old timeSignature/<denominator> token a new time signature token starts from."""
    if token == TIME_SIGNATURE_COMMON:
        return f"{OLD_TIME_SIGNATURE_PREFIX}4"
    if token == TIME_SIGNATURE_CUT:
        return f"{OLD_TIME_SIGNATURE_PREFIX}2"
    if token.startswith(TIME_SIGNATURE_PREFIX):
        _beats, beat_type, _symbol = parse_time_signature_token(token)
        return f"{OLD_TIME_SIGNATURE_PREFIX}{beat_type}"
    return None


def time_signature_source_row(token: str, old_index: dict[str, int]) -> int | None:
    """The row of the old checkpoint a new time signature token starts from, if there is one."""
    old_token = old_time_signature_token(token)
    if old_token is None:
        return None
    return old_index.get(old_token)


def grow_rows(
    old: torch.Tensor,
    template: torch.Tensor,
    old_index: dict[str, int],
    new_index: dict[str, int],
    source_row: Callable[[str, dict[str, int]], int | None],
) -> tuple[torch.Tensor, int, int]:
    """
    Rows of the new vocabulary, matching tokens by name. Returns the tensor with the shape
    and dtype of template, the number of rows which were copied by name and the number of
    new tokens. A new token starts from the old row source_row gives or else from the mean
    of the old rows. Old tokens which aren't in the new vocabulary are dropped.
    """
    if old.shape[0] != len(old_index) or template.shape[0] != len(new_index):
        raise ValueError(f"{tuple(old.shape)} / {tuple(template.shape)} vs vocabulary")
    target = old.mean(dim=0, keepdim=True).expand_as(template).clone().to(template.dtype)
    remapped = fresh = 0
    for token, new_row in new_index.items():
        old_row = old_index.get(token)
        if old_row is None:
            old_row = source_row(token, old_index)
            fresh += 1
        else:
            remapped += 1
        if old_row is not None:
            target[new_row] = old[old_row]
    return target, remapped, fresh
