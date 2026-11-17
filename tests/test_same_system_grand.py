# ruff: noqa: S101
import os
from unittest import mock

import numpy as np

from homr.staff_relations import GRAND_STAFF, SAME_SYSTEM, SEPARATE, _pairs_as_grand_staffs


def _probabilities(*classes: int) -> np.ndarray:
    result = np.zeros((len(classes), 3))
    for k, c in enumerate(classes):
        result[k, c] = 1.0
    return result


def _find_for(systems: list[list[int]]):  # type: ignore[no-untyped-def]
    root = {i: system[0] for system in systems for i in system}
    return lambda i: root[i]


def test_pairs_of_a_page_without_grand_staffs_become_grand_staffs() -> None:
    pairs = [(0, 1), (1, 2), (2, 3)]
    probabilities = _probabilities(SAME_SYSTEM, SEPARATE, SAME_SYSTEM)
    result = _pairs_as_grand_staffs(4, pairs, probabilities, _find_for([[0, 1], [2, 3]]))
    assert result == {0: 1, 2: 3}


def test_a_system_of_three_staffs_keeps_the_model_result() -> None:
    pairs = [(0, 1), (1, 2)]
    probabilities = _probabilities(SAME_SYSTEM, SAME_SYSTEM)
    assert _pairs_as_grand_staffs(3, pairs, probabilities, _find_for([[0, 1, 2]])) == {}


def test_single_staffs_are_not_touched() -> None:
    pairs = [(0, 1)]
    probabilities = _probabilities(SEPARATE)
    assert _pairs_as_grand_staffs(2, pairs, probabilities, _find_for([[0], [1]])) == {}


def test_a_pair_the_model_calls_a_grand_staff_is_left_to_the_model() -> None:
    pairs = [(0, 1)]
    probabilities = _probabilities(GRAND_STAFF)
    assert _pairs_as_grand_staffs(2, pairs, probabilities, _find_for([[0, 1]])) == {}


def test_opt_out_switch() -> None:
    pairs = [(0, 1)]
    probabilities = _probabilities(SAME_SYSTEM)
    with mock.patch.dict(os.environ, {"HOMR_NO_SAME_SYSTEM_GRAND": "1"}):
        assert _pairs_as_grand_staffs(2, pairs, probabilities, _find_for([[0, 1]])) == {}
