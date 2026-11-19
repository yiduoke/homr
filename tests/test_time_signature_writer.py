# ruff: noqa: S101
import os
import tempfile
import xml.etree.ElementTree as ET

import pytest

from homr.music_xml_generator import (
    TimeSignatureMemory,
    XmlGeneratorArguments,
    generate_xml,
)
from homr.relieur import get_children_of_type, process_concat
from homr.transformer.vocabulary import EncodedSymbol
from training.transformer.training_vocabulary import read_token_lines


def _staff(*lines: str) -> list[EncodedSymbol]:
    # A line without columns is a symbol without note attributes
    return read_token_lines([line if " " in line else line + " . . . . ." for line in lines])


def _times(xml: ET.Element) -> list[tuple[str, str, str | None]]:
    return [
        (t.findtext("beats", ""), t.findtext("beat-type", ""), t.get("symbol"))
        for t in xml.iter("time")
    ]


def _measure_rest_duration(xml: ET.Element) -> list[int]:
    return [
        int(n.findtext("duration", "0"))
        for n in xml.iter("note")
        if n.find("rest[@measure]") is not None
    ]


def _divisions(xml: ET.Element) -> int:
    return int(xml.findtext("part/measure/attributes/divisions", "1"))


def _with_measure_rest(*lines: str) -> list[EncodedSymbol]:
    return _staff(*lines) + [
        EncodedSymbol("measureRest", position="upper"),
        EncodedSymbol("barline"),
    ]


def test_numeric_time_signature_is_written_from_the_token() -> None:
    xml = generate_xml(
        XmlGeneratorArguments(),
        [
            _staff(
                "clef_G2 . . . . upper",
                "timeSignature_5/8",
                "note_8 C4 _ _ _ upper",
                "barline . . . . .",
            )
        ],
        "",
    )
    assert _times(xml) == [("5", "8", None)]


@pytest.mark.parametrize(
    ("token", "expected"),
    [
        ("timeSignature_common", ("4", "4", "common")),
        ("timeSignature_cut", ("2", "2", "cut")),
        ("timeSignature_4/4", ("4", "4", None)),
        ("timeSignature_2/2", ("2", "2", None)),
    ],
)
def test_symbols_are_written_with_the_symbol_attribute(
    token: str, expected: tuple[str, str, str | None]
) -> None:
    xml = generate_xml(
        XmlGeneratorArguments(),
        [
            _staff(
                "clef_G2 . . . . upper",
                token + " . . . . .",
                "note_1 C4 _ _ _ upper",
                "barline . . . . .",
            )
        ],
        "",
    )
    assert _times(xml) == [expected]


def test_measure_length_comes_from_the_recognised_meter() -> None:
    # The notes fill 2/4 only, the recognised meter says 3/4
    xml = generate_xml(
        XmlGeneratorArguments(),
        [
            _with_measure_rest(
                "clef_G2 . . . . upper",
                "timeSignature_3/4 . . . . .",
                "note_4 C4 _ _ _ upper",
                "note_4 C4 _ _ _ upper",
                "barline . . . . .",
            )
        ],
        "",
    )
    assert _measure_rest_duration(xml) == [3 * _divisions(xml)]


def test_meter_is_carried_across_systems() -> None:
    xml = generate_xml(
        XmlGeneratorArguments(),
        [
            _with_measure_rest(
                "clef_G2 . . . . upper",
                "timeSignature_3/4 . . . . .",
                "note_4 C4 _ _ _ upper",
                "note_4 C4 _ _ _ upper",
                "note_4 C4 _ _ _ upper",
                "barline . . . . .",
                "newline . . . . .",
                "clef_G2 . . . . upper",
            )
        ],
        "",
    )
    assert _times(xml) == [("3", "4", None)]
    assert _measure_rest_duration(xml) == [3 * _divisions(xml)]


def test_meter_change_in_a_later_system_replaces_the_carried_one() -> None:
    xml = generate_xml(
        XmlGeneratorArguments(),
        [
            _with_measure_rest(
                "clef_G2 . . . . upper",
                "timeSignature_3/4 . . . . .",
                "note_4 C4 _ _ _ upper",
                "note_4 C4 _ _ _ upper",
                "note_4 C4 _ _ _ upper",
                "barline . . . . .",
                "newline . . . . .",
                "clef_G2 . . . . upper",
                "timeSignature_4/4 . . . . .",
            )
        ],
        "",
    )
    assert _times(xml) == [("3", "4", None), ("4", "4", None)]
    assert _measure_rest_duration(xml) == [4 * _divisions(xml)]


def test_meter_is_carried_across_pages() -> None:
    memory = TimeSignatureMemory()
    first = generate_xml(
        XmlGeneratorArguments(),
        [
            _staff(
                "clef_G2 . . . . upper",
                "timeSignature_3/4",
                "note_2. C4 _ _ _ upper",
                "barline . . . . .",
            )
        ],
        "",
        memory,
    )
    assert _times(first) == [("3", "4", None)]

    second = generate_xml(
        XmlGeneratorArguments(),
        [_with_measure_rest("clef_G2 . . . . upper", "note_4 C4 _ _ _ upper", "barline . . . . .")],
        "",
        memory,
    )
    # The page continues with 3/4 although it shows no signature
    assert _times(second) == [("3", "4", None)]
    assert _measure_rest_duration(second) == [3 * _divisions(second)]
    time = second.find("part/measure/attributes/time")
    assert time is not None
    # The signature goes after the divisions
    attributes = second.find("part/measure/attributes")
    assert attributes is not None
    tags = [child.tag for child in attributes]
    assert tags.index("divisions") < tags.index("time")


def test_symbol_is_carried_across_pages() -> None:
    memory = TimeSignatureMemory()
    generate_xml(
        XmlGeneratorArguments(),
        [
            _staff(
                "clef_G2 . . . . upper",
                "timeSignature_cut",
                "note_1 C4 _ _ _ upper",
                "barline . . . . .",
            )
        ],
        "",
        memory,
    )
    second = generate_xml(
        XmlGeneratorArguments(),
        [_staff("clef_G2 . . . . upper", "note_1 C4 _ _ _ upper", "barline . . . . .")],
        "",
        memory,
    )
    assert _times(second) == [("2", "2", "cut")]


def test_a_new_meter_on_a_page_replaces_the_carried_one_for_the_next_page() -> None:
    memory = TimeSignatureMemory()
    for token in ("timeSignature_3/4", "timeSignature_6/8"):
        generate_xml(
            XmlGeneratorArguments(),
            [_staff("clef_G2 . . . . upper", token, "note_8 C4 _ _ _ upper", "barline . . . . .")],
            "",
            memory,
        )
    third = generate_xml(
        XmlGeneratorArguments(),
        [_staff("clef_G2 . . . . upper", "note_8 C4 _ _ _ upper", "barline . . . . .")],
        "",
        memory,
    )
    assert _times(third) == [("6", "8", None)]


def test_pages_do_not_share_a_meter_without_shared_memory() -> None:
    generate_xml(
        XmlGeneratorArguments(),
        [
            _staff(
                "clef_G2 . . . . upper",
                "timeSignature_3/4",
                "note_2. C4 _ _ _ upper",
                "barline . . . . .",
            )
        ],
        "",
    )
    second = generate_xml(
        XmlGeneratorArguments(),
        [_staff("clef_G2 . . . . upper", "note_2. C4 _ _ _ upper", "barline . . . . .")],
        "",
    )
    # Guessed from the notes
    assert _times(second) == [("3", "4", None)]


def test_meter_is_guessed_from_the_notes_if_none_was_recognised() -> None:
    xml = generate_xml(
        XmlGeneratorArguments(),
        [
            _staff(
                "clef_G2 . . . . upper",
                "note_4 C4 _ _ _ upper",
                "note_4 C4 _ _ _ upper",
                "barline . . . . .",
                "note_4 C4 _ _ _ upper",
                "note_4 C4 _ _ _ upper",
                "barline . . . . .",
            )
        ],
        "",
    )
    assert _times(xml) == [("2", "4", None)]


def test_a_page_without_meter_does_not_remember_a_guess() -> None:
    memory = TimeSignatureMemory()
    generate_xml(
        XmlGeneratorArguments(),
        [_staff("clef_G2 . . . . upper", "note_2 C4 _ _ _ upper", "barline . . . . .")],
        "",
        memory,
    )
    assert memory.part(0).token is None


def test_each_part_carries_its_own_meter() -> None:
    memory = TimeSignatureMemory()
    generate_xml(
        XmlGeneratorArguments(),
        [
            _staff(
                "clef_G2 . . . . upper",
                "timeSignature_3/4",
                "note_2. C4 _ _ _ upper",
                "barline . . . . .",
            ),
            _staff(
                "clef_F4 . . . . upper",
                "timeSignature_3/4",
                "note_2. C3 _ _ _ upper",
                "barline . . . . .",
            ),
        ],
        "",
        memory,
    )
    assert memory.part(0).token == "timeSignature_3/4"
    assert memory.part(1).token == "timeSignature_3/4"


def _merge_pages(pages: list[ET.Element]) -> ET.Element:
    with tempfile.TemporaryDirectory() as tmp:
        files = []
        for i, page in enumerate(pages):
            path = os.path.join(tmp, f"page{i}.musicxml")
            ET.ElementTree(page).write(path, encoding="unicode", xml_declaration=True)
            files.append(path)
        root, _, _ = process_concat(files)
    return root


def _page(memory: TimeSignatureMemory, *lines: str) -> ET.Element:
    return generate_xml(XmlGeneratorArguments(), [_staff(*lines)], "", memory)


def test_joined_pages_repeat_the_meter_only_where_it_changes() -> None:
    memory = TimeSignatureMemory()
    pages = [
        _page(
            memory,
            "clef_G2 . . . . upper",
            "timeSignature_3/4",
            "note_2. C4 _ _ _ upper",
            "barline . . . . .",
        ),
        _page(memory, "clef_G2 . . . . upper", "note_2. C4 _ _ _ upper", "barline . . . . ."),
        _page(
            memory,
            "clef_G2 . . . . upper",
            "timeSignature_4/4",
            "note_1 C4 _ _ _ upper",
            "barline . . . . .",
        ),
        _page(
            memory,
            "clef_G2 . . . . upper",
            "timeSignature_common",
            "note_1 C4 _ _ _ upper",
            "barline . . . . .",
        ),
    ]
    root = _merge_pages(pages)
    part = get_children_of_type(root, "part")[0]
    measures = get_children_of_type(part, "measure")
    assert len(measures) == 4
    assert [
        [(t.findtext("beats"), t.findtext("beat-type"), t.get("symbol")) for t in m.iter("time")]
        for m in measures
    ] == [
        [("3", "4", None)],
        [],
        [("4", "4", None)],
        [("4", "4", "common")],
    ]
