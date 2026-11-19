# ruff: noqa: S101
import pytest

from homr import combined_switches as cs

_NAMES = (
    "HOMR_COMBINED",
    "HOMR_COMBINED_OFF",
    "HOMR_STRICT_BRACKET_CUT",
    "HOMR_BEAM_EXPORT",
    "HOMR_TUPLET_PASS",
)


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in _NAMES:
        monkeypatch.delenv(name, raising=False)


def test_beams_and_tuplets_are_on_and_strict_cut_is_off_by_default() -> None:
    assert cs.strict_cut_level() == ""
    assert cs.beam_export() is True
    assert cs.tuplet_pass() is True


def test_combined_switches_all_three_on(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMR_COMBINED", "1")
    assert cs.strict_cut_level() == "2"
    assert cs.beam_export() is True
    assert cs.tuplet_pass() is True


@pytest.mark.parametrize("letter", ["A", "B", "C"])
def test_one_letter_can_be_left_off(monkeypatch: pytest.MonkeyPatch, letter: str) -> None:
    monkeypatch.setenv("HOMR_COMBINED", "1")
    monkeypatch.setenv("HOMR_COMBINED_OFF", letter.lower())
    state = {"A": cs.strict_cut_level() == "2", "B": cs.beam_export(), "C": cs.tuplet_pass()}
    assert [k for k, v in state.items() if not v] == [letter]


def test_b_and_c_can_be_left_off_without_combined(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMR_COMBINED_OFF", "B,C")
    assert cs.beam_export() is False
    assert cs.tuplet_pass() is False
    assert cs.strict_cut_level() == ""


def test_an_explicit_variable_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMR_COMBINED", "1")
    monkeypatch.setenv("HOMR_STRICT_BRACKET_CUT", "1")
    assert cs.strict_cut_level() == "1"
    monkeypatch.setenv("HOMR_BEAM_EXPORT", "0")
    assert cs.beam_export() is False
    monkeypatch.setenv("HOMR_TUPLET_PASS", "0")
    assert cs.tuplet_pass() is False


def test_the_individual_switches_work_alone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOMR_STRICT_BRACKET_CUT", "2")
    assert cs.strict_cut_level() == "2"
    monkeypatch.setenv("HOMR_BEAM_EXPORT", "0")
    monkeypatch.setenv("HOMR_TUPLET_PASS", "1")
    assert cs.beam_export() is False
    assert cs.tuplet_pass() is True
