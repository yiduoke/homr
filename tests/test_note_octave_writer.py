# ruff: noqa: S101
import xml.etree.ElementTree as ET

import pytest

from homr.music_xml_generator import XmlGeneratorArguments, generate_xml
from homr.transformer.vocabulary import EncodedSymbol


def _note(pitch: str, marker: str = "_", staff: str = "upper") -> EncodedSymbol:
    return EncodedSymbol("note_4", pitch, "_", "_", "_", staff, octave_mark=marker)


def _write(*symbols: EncodedSymbol) -> ET.Element:
    return generate_xml(XmlGeneratorArguments(), [list(symbols)], "")


def _events(measure: ET.Element) -> list[str]:
    events = []
    for child in measure:
        shift = child.find("direction-type/octave-shift")
        if shift is not None:
            events.append(f"{shift.get('type')}:{child.findtext('staff')}")
        elif child.tag == "note":
            if child.find("rest") is not None:
                events.append("rest")
            else:
                pitch = child.findtext("pitch/step", "") + child.findtext("pitch/octave", "")
                events.append(f"{pitch}:{child.findtext('staff')}")
    return events


def test_bracket_spans_rest_and_barline_but_ends_at_last_marked_chord() -> None:
    score = _write(
        EncodedSymbol("timeSignature_3/4"),
        _note("C5", "8va"),
        EncodedSymbol("rest_4", "_", "_", "_", "_", "upper"),
        _note("D5", "8va"),
        EncodedSymbol("barline"),
        _note("E5", "8va"),
        EncodedSymbol("chord"),
        _note("G5", "8va"),
        EncodedSymbol("rest_4", "_", "_", "_", "_", "upper"),
        _note("F5"),
    )
    first, second = score.findall("part/measure")
    assert _events(first) == ["down:1", "C6:1", "rest", "D6:1"]
    assert _events(second) == ["G6:1", "E6:1", "stop:1", "rest", "F5:1"]
    assert second.findall("note")[1].find("chord") is not None
    assert all("homr-octave-mark" not in note.attrib for note in score.iter("note"))


def test_two_staves_have_independent_pitches_and_brackets() -> None:
    score = _write(
        EncodedSymbol("clef_G2_8vb", position="upper"),
        _note("C5", "8va"),
        EncodedSymbol("chord"),
        _note("C3", "8vb", "lower"),
        _note("D5"),
        EncodedSymbol("chord"),
        _note("D3", "8vb", "lower"),
        _note("E3", "_", "lower"),
    )
    assert [
        (note.findtext("pitch/step"), note.findtext("pitch/octave"), note.findtext("staff"))
        for note in score.iter("note")
    ] == [("C", "5", "1"), ("C", "2", "2"), ("D", "4", "1"), ("D", "2", "2"), ("E", "3", "2")]
    directions = [
        (direction.find("direction-type/octave-shift"), direction.get("placement"))
        for direction in score.iter("direction")
    ]
    assert [
        (shift.get("type"), shift.get("number"), placement)
        for shift, placement in directions
        if shift is not None
    ] == [
        ("down", "1", "above"),
        ("stop", "1", "above"),
        ("up", "2", "below"),
        ("stop", "2", "below"),
    ]


def test_mixed_chord_retains_each_notes_pitch_and_keeps_chord_contiguous() -> None:
    score = _write(
        _note("E5"),
        EncodedSymbol("chord"),
        _note("C5", "8va"),
    )
    measure = score.find("part/measure")
    assert measure is not None
    assert _events(measure) == ["down:1", "E5:1", "C6:1", "stop:1"]
    assert measure.findall("note")[1].find("chord") is not None


def test_legacy_direction_and_note_marks_cannot_share_a_part() -> None:
    with pytest.raises(ValueError, match="cannot be combined"):
        _write(EncodedSymbol("octaveShift_8va", position="upper"), _note("C5"))
