# ruff: noqa: S101
import pytest
import torch

from homr.transformer.vocabulary import Vocabulary, numeric_time_signature_tokens
from training.transformer.meter_vocabulary import (
    grow_rows,
    old_time_signature_token,
    time_signature_source_row,
)

OLD_DENOMINATORS = [1, 2, 3, 4, 6, 8, 12, 16, 32, 48]


def _old_index() -> dict[str, int]:
    """The layout before complete time signatures: timeSignature/<denominator> in the middle."""
    tokens = ["PAD", "BOS", "keySignature_0"]
    tokens += [f"timeSignature/{d}" for d in OLD_DENOMINATORS]
    tokens += ["note_4", "rest_4", "octaveShiftStop"]
    return {token: index for index, token in enumerate(tokens)}


def _new_index() -> dict[str, int]:
    tokens = ["PAD", "BOS", "keySignature_0", "note_4", "rest_4", "octaveShiftStop"]
    tokens += numeric_time_signature_tokens() + ["timeSignature_common", "timeSignature_cut"]
    return {token: index for index, token in enumerate(tokens)}


@pytest.mark.parametrize(
    ("token", "old"),
    [
        ("timeSignature_3/4", "timeSignature/4"),
        ("timeSignature_4/4", "timeSignature/4"),
        ("timeSignature_6/8", "timeSignature/8"),
        ("timeSignature_17/16", "timeSignature/16"),
        ("timeSignature_3/2", "timeSignature/2"),
        ("timeSignature_common", "timeSignature/4"),
        ("timeSignature_cut", "timeSignature/2"),
        ("note_4", None),
        ("keySignature_0", None),
    ],
)
def test_old_time_signature_of_a_new_token(token: str, old: str | None) -> None:
    assert old_time_signature_token(token) == old


def test_every_new_time_signature_of_the_vocabulary_has_a_source_row() -> None:
    old_index = _old_index()
    for token in Vocabulary().rhythm:
        if token.startswith("timeSignature"):
            assert time_signature_source_row(token, old_index) is not None, token


@pytest.mark.parametrize("columns", [None, 5])
def test_rows_are_matched_by_name_and_new_time_signatures_start_from_their_denominator(
    columns: int | None,
) -> None:
    old_index, new_index = _old_index(), _new_index()
    shape = (len(old_index),) if columns is None else (len(old_index), columns)
    old = torch.arange(len(old_index), dtype=torch.float32) + 1  # a distinct value per row
    if columns is not None:
        old = old.unsqueeze(1).expand(shape).clone() * torch.arange(1, columns + 1)
    template = torch.zeros((len(new_index),) + shape[1:])

    result, remapped, fresh = grow_rows(
        old, template, old_index, new_index, time_signature_source_row
    )

    assert result.shape == template.shape
    # Everything which was there before keeps its values although the rows moved
    for token in ["PAD", "BOS", "keySignature_0", "note_4", "rest_4", "octaveShiftStop"]:
        assert torch.equal(result[new_index[token]], old[old_index[token]]), token
    # New time signatures copy the row of their denominator
    for token, old_token in [
        ("timeSignature_3/4", "timeSignature/4"),
        ("timeSignature_4/4", "timeSignature/4"),
        ("timeSignature_6/8", "timeSignature/8"),
        ("timeSignature_2/2", "timeSignature/2"),
        ("timeSignature_common", "timeSignature/4"),
        ("timeSignature_cut", "timeSignature/2"),
    ]:
        assert torch.equal(result[new_index[token]], old[old_index[old_token]]), token
    assert remapped == 6
    assert fresh == len(new_index) - 6


def test_old_time_signature_rows_are_dropped() -> None:
    old_index, new_index = _old_index(), _new_index()
    old = torch.arange(len(old_index), dtype=torch.float32) + 100
    template = torch.zeros(len(new_index))
    result, _, _ = grow_rows(old, template, old_index, new_index, time_signature_source_row)
    # The row of timeSignature/3 (no new token has this denominator) isn't in the result
    assert float(old[old_index["timeSignature/3"]]) not in result.tolist()
    assert len(result) == len(new_index)


def test_tokens_without_a_source_start_from_the_mean() -> None:
    old_index = {"a": 0, "b": 1}
    new_index = {"a": 0, "c": 1, "b": 2}
    old = torch.tensor([[2.0, 4.0], [4.0, 8.0]])
    result, remapped, fresh = grow_rows(
        old, torch.zeros(3, 2), old_index, new_index, lambda _token, _index: None
    )
    assert result.tolist() == [[2.0, 4.0], [3.0, 6.0], [4.0, 8.0]]
    assert (remapped, fresh) == (2, 1)


def test_rows_which_do_not_match_the_vocabulary_are_rejected() -> None:
    with pytest.raises(ValueError, match="vs vocabulary"):
        grow_rows(
            torch.zeros(3), torch.zeros(2), {"a": 0, "b": 1}, {"a": 0, "b": 1}, lambda _t, _i: None
        )
