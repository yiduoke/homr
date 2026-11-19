# ruff: noqa: S101
import xml.etree.ElementTree as ET
from fractions import Fraction

from homr.music_xml_generator import TimeSignatureMemory, XmlGeneratorArguments, generate_xml
from homr.transformer.vocabulary import EncodedSymbol
from training.transformer.training_vocabulary import read_token_lines


def _staff(*lines: str) -> list[EncodedSymbol]:
    return read_token_lines([line if " " in line else line + " . . . . ." for line in lines])


def _write(lines: list[str], carried: str | None = "timeSignature_3/4") -> ET.Element:
    memory = TimeSignatureMemory()
    if carried is not None:
        memory.part(0).token = carried
    header = ["clef_G2 . . . . upper&clef_F4 . . . . lower"]
    return generate_xml(XmlGeneratorArguments(), [_staff(*header, *lines)], "", memory)


def _upper_bar() -> str:
    return "note_4 C5 _ _ _ upper&rest_4 . . . . lower"


def _clock(measure: ET.Element) -> dict[str, list[tuple[Fraction, int, bool]]]:
    """Per staff: start, duration and whether it is a rest, for what the staff holds."""
    time = Fraction(0)
    last_start = Fraction(0)
    result: dict[str, list[tuple[Fraction, int, bool]]] = {}
    for child in measure:
        duration = int(child.findtext("duration", "0"))
        if child.tag == "note":
            staff = child.findtext("staff", "1")
            start = last_start if child.find("chord") is not None else time
            if child.find("chord") is None:
                last_start = time
                time += duration
            result.setdefault(staff, []).append((start, duration, child.find("rest") is not None))
        elif child.tag == "forward":
            time += duration
        elif child.tag == "backup":
            time -= duration
    return result


def _bar_length(xml: ET.Element) -> int:
    divisions = int(xml.findtext("part/measure/attributes/divisions", "1"))
    return 3 * divisions


def test_whole_rest_in_a_three_four_bar_becomes_a_bar_rest() -> None:
    lines = [
        "note_4 C5 _ _ _ upper&rest_1 . . . . lower",
        "note_4 D5 _ _ _ upper",
        "note_4 E5 _ _ _ upper",
        "barline",
        "note_2. C5 _ _ _ upper&rest_1 . . . . lower",
        "barline",
    ]
    xml = _write(lines)

    first, second = xml.findall("part/measure")
    # The first bar of the part may be a pickup and is left alone, the second is a bar rest
    clock = _clock(second)
    assert clock["2"] == [(0, _bar_length(xml), True)]
    rest = [n for n in second.findall("note") if n.find("rest") is not None][0]
    assert rest.find("rest").get("measure") == "yes"
    assert rest.find("type") is None
    assert clock["1"][0][:2] == (0, _bar_length(xml))
    assert first is not None


def test_dotted_half_rest_in_a_two_four_bar_is_cut_to_the_bar() -> None:
    lines = [
        "note_4 C5 _ _ _ upper&rest_2. . . . . lower",
        "note_4 D5 _ _ _ upper",
        "barline",
        "note_4 C5 _ _ _ upper&rest_2. . . . . lower",
        "note_4 D5 _ _ _ upper",
        "barline",
    ]
    xml = _write(lines, "timeSignature_2/4")

    second = xml.findall("part/measure")[1]
    bar = 2 * int(xml.findtext("part/measure/attributes/divisions", "1"))
    clock = _clock(second)
    assert clock["2"] == [(0, bar, True)]
    assert [start for start, _, _ in clock["1"]] == [0, bar // 2]


def test_a_bar_with_several_rests_in_a_staff_is_left_alone() -> None:
    lines = [
        "note_4 C5 _ _ _ upper&rest_4 . . . . lower",
        "note_4 D5 _ _ _ upper&rest_4 . . . . lower",
        "note_4 E5 _ _ _ upper",
        "barline",
        "note_4 C5 _ _ _ upper&rest_4 . . . . lower",
        "note_4 D5 _ _ _ upper&rest_4 . . . . lower",
        "note_4 E5 _ _ _ upper",
        "barline",
    ]
    xml = _write(lines)

    second = xml.findall("part/measure")[1]
    assert [d for _, d, _ in _clock(second)["2"]] == [_bar_length(xml) // 3] * 2
    assert all(
        n.find("rest").get("measure") is None
        for n in second.findall("note")
        if n.find("rest") is not None
    )


def test_a_rest_of_a_staff_with_notes_is_left_alone() -> None:
    lines = [
        "note_4 C5 _ _ _ upper&rest_4 . . . . lower",
        "note_4 D5 _ _ _ upper&note_4 C3 _ _ _ lower",
        "note_4 E5 _ _ _ upper",
        "barline",
    ]
    xml = _write(lines)

    measure = xml.findall("part/measure")[0]
    assert [
        n.find("rest").get("measure") for n in measure.findall("note") if n.find("rest") is not None
    ] == [None]


def test_the_first_bar_of_a_score_may_be_a_pickup() -> None:
    lines = ["note_4 C5 _ _ _ upper&rest_4 . . . . lower", "barline"]

    xml = _write(lines, carried=None)

    measure = xml.findall("part/measure")[0]
    rests = [n for n in measure.findall("note") if n.find("rest") is not None]
    assert [r.find("rest").get("measure") for r in rests] == [None]


def test_a_correct_bar_rest_is_unchanged() -> None:
    lines = [
        "note_4 C5 _ _ _ upper&rest_2. . . . . lower",
        "note_4 D5 _ _ _ upper",
        "note_4 E5 _ _ _ upper",
        "barline",
        "note_4 C5 _ _ _ upper&rest_2. . . . . lower",
        "note_4 D5 _ _ _ upper",
        "note_4 E5 _ _ _ upper",
        "barline",
    ]
    xml = _write(lines)

    second = xml.findall("part/measure")[1]
    assert _clock(second)["2"] == [(0, _bar_length(xml), True)]
