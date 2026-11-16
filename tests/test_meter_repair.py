# ruff: noqa: S101
import xml.etree.ElementTree as ET

from homr.music_xml_generator import (
    PartTimeSignature,
    TimeSignatureMemory,
    XmlGeneratorArguments,
    generate_xml,
)
from homr.transformer.vocabulary import EncodedSymbol
from training.transformer.training_vocabulary import read_token_lines


def _staff(*lines: str) -> list[EncodedSymbol]:
    return read_token_lines([line if " " in line else line + " . . . . ." for line in lines])


def _bar(*notes: str) -> list[str]:
    return [*(f"note_{note} C4 _ _ _ upper" for note in notes), "barline"]


def _meters(xml: ET.Element) -> list[tuple[int, str]]:
    """The measures (from 1) with a time signature and the signature."""
    result = []
    for i, measure in enumerate(xml.iter("measure"), start=1):
        for time in measure.iter("time"):
            result.append((i, time.findtext("beats", "") + "/" + time.findtext("beat-type", "")))
    return result


def _write(lines: list[str], carried: str | None = None) -> tuple[ET.Element, TimeSignatureMemory]:
    memory = TimeSignatureMemory()
    if carried is not None:
        memory.part(0).token = carried
    xml = generate_xml(
        XmlGeneratorArguments(), [_staff("clef_G2 . . . . upper", *lines)], "", memory
    )
    return xml, memory


def test_carried_meter_which_fits_nothing_is_replaced_by_the_length_of_the_bars() -> None:
    # Five bars of 3/4 under a carried 4/4
    xml, memory = _write(sum((_bar("4", "4", "4") for _ in range(5)), []), "timeSignature_4/4")

    assert _meters(xml) == [(1, "3/4")]
    assert memory.part(0).token == "timeSignature_3/4"


def test_the_meter_returns_after_the_misfit_bars() -> None:
    odd = _bar("4", "4", "4")
    usual = _bar("4", "4", "4", "4")
    xml, memory = _write(odd * 3 + usual * 2, "timeSignature_4/4")

    assert _meters(xml) == [(1, "3/4"), (4, "4/4")]
    assert memory.part(0).token == "timeSignature_4/4"


def test_two_odd_bars_keep_the_carried_meter() -> None:
    lines = (
        _bar("4", "4", "4", "4")
        + _bar("4", "4", "4")
        + _bar("4", "4", "4")
        + _bar("4", "4", "4", "4")
    )

    xml, _ = _write(lines, "timeSignature_4/4")

    assert _meters(xml) == [(1, "4/4")]


def test_bars_which_fit_the_recognised_meter_keep_it() -> None:
    lines = ["timeSignature_3/4", *sum((_bar("4", "4", "4") for _ in range(4)), [])]

    xml, _ = _write(lines, "timeSignature_4/4")

    assert _meters(xml) == [(1, "3/4")]


def test_misread_recognised_meter_is_replaced_too() -> None:
    lines = ["timeSignature_3/4", *sum((_bar("4", "4") for _ in range(4)), [])]

    xml, _ = _write(lines)

    assert _meters(xml) == [(1, "2/4")]


def test_bars_of_different_lengths_keep_the_meter() -> None:
    lines = _bar("4", "4") + _bar("4", "4", "4") + _bar("4", "4") + _bar("4", "4", "4")

    xml, _ = _write(lines, "timeSignature_4/4")

    assert _meters(xml) == [(1, "4/4")]


def test_part_time_signature_is_unchanged_without_misfit() -> None:
    memory = TimeSignatureMemory()
    memory.part(0).token = "timeSignature_4/4"
    generate_xml(
        XmlGeneratorArguments(),
        [_staff("clef_G2 . . . . upper", *sum((_bar("4", "4", "4", "4") for _ in range(4)), []))],
        "",
        memory,
    )

    assert isinstance(memory.part(0), PartTimeSignature)
    assert memory.part(0).token == "timeSignature_4/4"
