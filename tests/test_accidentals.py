# ruff: noqa: E501, S101, S314

import xml.etree.ElementTree as ET

import pytest

from homr.accidentals import (
    AccidentalState,
    UnsupportedAccidentalError,
    key_alteration,
    printed_lifts_from_sounding,
    sign_from_mei,
    sign_from_music_xml,
    sounding_lift,
)
from homr.music_xml_generator import XmlGeneratorArguments, generate_xml
from homr.transformer.vocabulary import EncodedSymbol
from training.omr_datasets.humdrum_kern_parser import convert_kern_to_tokens
from training.omr_datasets.music_xml_parser import (
    SKIPPED_ACCIDENTALS,
    music_xml_string_to_tokens,
)
from training.transformer.training_vocabulary import read_token_lines, token_lines_to_str


def _note(
    pitch: str, alter: int, position: str = "upper", slur: str = "_", **marks: bool
) -> EncodedSymbol:
    return EncodedSymbol("note_4", pitch, sounding_lift(alter, **marks), "_", slur, position)


def _signs(symbols: list[EncodedSymbol], given: list[str | None] | None = None) -> list[str]:
    return [
        s.lift for s in printed_lifts_from_sounding(symbols, given) if s.pitch not in ("_", ".")
    ]


BAR = EncodedSymbol("barline")


def key(fifths: int) -> EncodedSymbol:
    return EncodedSymbol(f"keySignature_{fifths}")


def test_key_alterations() -> None:
    assert [key_alteration(2, s) for s in "FCGDAEB"] == [1, 1, 0, 0, 0, 0, 0]
    assert [key_alteration(-3, s) for s in "FCGDAEB"] == [0, 0, 0, 0, -1, -1, -1]
    assert key_alteration(0, "F") == 0


def test_key_signature_sharp_has_no_sign() -> None:
    assert _signs([key(1), _note("F4", 1), _note("G4", 0)]) == ["_", "_"]


def test_altered_note_against_the_key_gets_a_sign() -> None:
    assert _signs([key(1), _note("F4", 0), _note("C4", 1), _note("B3", -1)]) == ["N", "#", "b"]


def test_repeated_accidental_in_the_bar_is_not_printed_again() -> None:
    assert _signs([_note("C4", 1), _note("C4", 1), BAR, _note("C4", 1)]) == ["#", "_", "#"]


def test_carried_accidental_is_cancelled_by_a_natural() -> None:
    assert _signs([_note("C4", 1), _note("C4", 0), _note("C4", 0)]) == ["#", "N", "_"]


def test_other_octave_is_printed_again() -> None:
    assert _signs([_note("C4", 1), _note("C5", 1), _note("C4", 1)]) == ["#", "#", "_"]


def test_staffs_carry_independently() -> None:
    notes = [_note("C4", 1, "upper"), _note("C4", 1, "lower"), _note("C4", 1, "upper")]
    assert _signs(notes) == ["#", "#", "_"]


def test_double_sharp_and_double_flat() -> None:
    assert _signs([_note("F4", 2), _note("B4", -2), _note("F4", 2)]) == ["##", "bb", "_"]


def test_kern_natural_is_always_printed() -> None:
    # A natural in a key where F is natural anyway
    assert _signs([key(0), _note("F4", 0, natural=True), _note("F4", 0)]) == ["N", "_"]


def test_kern_force_prints_and_hide_hides() -> None:
    notes = [key(1), _note("F4", 1, force=True), _note("C4", 1, hide=True), _note("C4", 1)]
    # Hidden signs aren't carried, so the next C needs one
    assert _signs(notes) == ["#", "_", "#"]


def test_tie_across_barline_has_no_sign() -> None:
    notes = [
        _note("C4", 1, slur="slurStart"),
        BAR,
        _note("C4", 1, slur="slurStop"),
        # The sign of a tied note isn't carried into the bar
        _note("C4", 1),
    ]
    assert _signs(notes) == ["#", "_", "#"]


def test_tie_in_a_chord_across_barline() -> None:
    notes = [
        _note("C4", 1, slur="slurStart"),
        EncodedSymbol("chord"),
        _note("E4", 0, slur="slurStart"),
        BAR,
        _note("E4", 0, slur="slurStop"),
        EncodedSymbol("chord"),
        _note("C4", 1, slur="slurStop"),
    ]
    assert _signs(notes) == ["#", "_", "_", "_"]


def test_slur_to_a_far_note_is_not_a_tie() -> None:
    notes = [
        _note("C4", 1, slur="slurStart"),
        _note("D4", 0),
        BAR,
        _note("C4", 1, slur="slurStop"),
    ]
    assert _signs(notes) == ["#", "_", "#"]


def test_two_voices_on_one_staff_share_the_signs() -> None:
    notes = [
        _note("F4", 0, "upper"),
        EncodedSymbol("chord"),
        _note("F4", 0, "upper2"),
        _note("F4", 0, "upper"),
    ]
    assert _signs([key(2)] + notes) == ["N", "_", "_"]


def test_given_signs_replace_the_rule() -> None:
    notes = [
        key(1),
        _note("F4", 1),
        _note("C4", 1),
        _note("G4", 0, natural=True),
        _note("A4", 0, force=True),
    ]
    # Verovio draws the sharp of C only; n adds the natural of G, X the natural of A
    assert _signs(notes, [None, "#", None, None]) == ["_", "#", "N", "N"]
    with pytest.raises(ValueError):
        _signs(notes, [None])


def test_mei_and_music_xml_signs() -> None:
    assert [sign_from_mei(a) for a in ("s", "f", "n", "ss", "x", "ff", None)] == [
        "#",
        "b",
        "N",
        "##",
        "##",
        "bb",
        None,
    ]
    assert sign_from_music_xml("double-sharp", True) == "##"
    assert sign_from_music_xml("flat-flat", True) == "bb"
    assert sign_from_music_xml("natural-sharp", True) == "#"
    with pytest.raises(UnsupportedAccidentalError):
        sign_from_music_xml("quarter-sharp", True)
    assert sign_from_music_xml("three-quarters-flat", False) == "b"


def test_kern_end_to_end() -> None:
    kern = """**kern\t**kern
*clefF4\t*clefG2
*k[f#]\t*k[f#]
*M4/4\t*M4/4
=-\t=-
4c\t4f#
.\t4fn
.\t4f
.\t4cc#
=\t=
4c#\t4f#
.\t4cc#
.\t4cc#
.\t4cc#
=\t=
*-\t*-
"""
    symbols = convert_kern_to_tokens(kern.splitlines())
    lifts = [s.lift for s in symbols if s.pitch not in ("_", ".")]
    # Bar 1: F# of the key, c natural, kern n, f natural carried from it, C#5 against the key.
    # Bar 2: C#4 and C#5 are different octaves and both printed, then C#5 is carried.
    assert lifts == ["_", "_", "N", "_", "#", "_", "#", "#", "_", "_"]


# MusicXML


def _xml_note(
    step: str,
    octave: int,
    alter: int | None,
    accidental: str | None,
    duration: int = 1,
    voice: int = 1,
    tie: str = "",
    staff: int = 1,
) -> str:
    kind = {1: "quarter", 2: "half", 4: "whole"}[duration]
    alter_xml = f"<alter>{alter}</alter>" if alter is not None else ""
    accidental_xml = f"<accidental>{accidental}</accidental>" if accidental else ""
    tie_xml = f'<tie type="{tie}"/>' if tie else ""
    tied_xml = f'<notations><tied type="{tie}"/></notations>' if tie else ""
    return (
        f"<note><pitch><step>{step}</step>{alter_xml}<octave>{octave}</octave></pitch>"
        f"<duration>{duration}</duration>{tie_xml}<voice>{voice}</voice><type>{kind}</type>"
        f"{accidental_xml}<staff>{staff}</staff>{tied_xml}</note>"
    )


def _xml_score(measures: list[str], fifths: int) -> str:
    body = ""
    for number, measure in enumerate(measures, start=1):
        attributes = (
            f"<attributes><divisions>1</divisions><key><fifths>{fifths}</fifths></key>"
            "<time><beats>4</beats><beat-type>4</beat-type></time>"
            "<clef><sign>G</sign><line>2</line></clef></attributes>"
            if number == 1
            else ""
        )
        body += f'<measure number="{number}">{attributes}{measure}</measure>'
    return f'<score-partwise version="4.0"><part-list><score-part id="P1"/></part-list><part id="P1">{body}</part></score-partwise>'


def _lifts(xml: str, sounding_pitch: bool = False) -> list[str]:
    tokens = music_xml_string_to_tokens(xml, sounding_pitch)[0]
    symbols = [s for measure in tokens for s in measure if s.pitch not in ("_", ".")]
    return [s.lift for s in symbols]


def test_music_xml_label_is_the_printed_sign_only() -> None:
    xml = _xml_score(
        [
            _xml_note("F", 4, 1, None)  # key signature
            + _xml_note("C", 5, 1, "sharp")
            + _xml_note("C", 5, 1, None)  # carried
            + _xml_note("C", 4, 0, "natural"),
            _xml_note("G", 4, 2, "double-sharp")
            + _xml_note("B", 4, -2, "flat-flat")
            + _xml_note("D", 4, 0, None)
            + _xml_note("E", 4, -1, "flat"),
        ],
        fifths=1,
    )
    assert _lifts(xml) == ["_", "#", "_", "N", "##", "bb", "_", "b"]


def test_music_xml_quarter_tone_skips_the_piece_for_training() -> None:
    xml = _xml_score(
        [_xml_note("C", 5, None, "quarter-sharp") + _xml_note("D", 5, None, None)], fifths=0
    )
    before = SKIPPED_ACCIDENTALS["quarter-sharp"]
    with pytest.raises(UnsupportedAccidentalError):
        music_xml_string_to_tokens(xml)
    assert SKIPPED_ACCIDENTALS["quarter-sharp"] == before + 1
    assert _lifts(xml, sounding_pitch=True) == ["#", "_"]


# Decoding and the writer


def _generate(xml: str) -> ET.Element:
    parts = music_xml_string_to_tokens(xml)
    lines = token_lines_to_str(parts[0] and [s for m in parts[0] for s in m]).splitlines()
    return generate_xml(XmlGeneratorArguments(), [read_token_lines(lines)], "")


def _written(xml: ET.Element) -> list[tuple[int, str, str, str, str | None]]:
    """Measure, step, octave, alter and printed sign of each note."""
    result = []
    for number, measure in enumerate(xml.iter("measure"), start=1):
        for note in measure.findall("note"):
            if note.find("pitch") is None:
                continue
            result.append(
                (
                    number,
                    note.findtext("pitch/step", ""),
                    note.findtext("pitch/octave", ""),
                    note.findtext("pitch/alter", "0"),
                    note.findtext("accidental"),
                )
            )
    return result


def _source(xml: str) -> list[tuple[int, str, str, str, str | None]]:
    result = []
    for number, measure in enumerate(ET.fromstring(xml).iter("measure"), start=1):
        for note in measure.findall("note"):
            result.append(
                (
                    number,
                    note.findtext("pitch/step", ""),
                    note.findtext("pitch/octave", ""),
                    note.findtext("pitch/alter", "0"),
                    note.findtext("accidental"),
                )
            )
    return result


def test_round_trip_of_labels_to_sounding_alterations() -> None:
    xml = _xml_score(
        [
            _xml_note("F", 5, 1, None)
            + _xml_note("F", 5, 0, "natural")
            + _xml_note("F", 5, 0, None)
            + _xml_note("F", 4, 1, None),
            _xml_note("F", 5, 1, None)
            + _xml_note("C", 5, 1, "sharp")
            + _xml_note("G", 4, 2, "double-sharp")
            + _xml_note("G", 4, 2, None),
            _xml_note("B", 4, -2, "flat-flat")
            + _xml_note("B", 4, -2, None)
            + _xml_note("B", 3, 0, "natural")  # courtesy natural
            + _xml_note("E", 4, -1, "flat", tie="start"),
            _xml_note("E", 4, -1, None, tie="stop")
            + _xml_note("A", 4, 0, None, duration=2)
            + _xml_note("D", 4, 0, None),
        ],
        fifths=2,
    )
    xml_out = _generate(xml)
    assert _written(xml_out) == _source(xml)
    # The tie across the barline is recognised because the alteration was resolved first
    assert [t.get("type") for t in xml_out.iter("tie")] == ["start", "stop"]


def test_two_voices_on_one_staff_share_the_carried_sign() -> None:
    # The lower voice writes a natural before the upper voice plays the same note later
    xml = _xml_score(
        [
            _xml_note("A", 4, 0, None, duration=2)
            + _xml_note("F", 5, 0, None, duration=2)
            + "<backup><duration>4</duration></backup>"
            + _xml_note("F", 5, 0, "natural", duration=2, voice=2)
            + _xml_note("D", 5, 0, None, duration=2, voice=2)
        ],
        fifths=2,
    )
    xml_out = _generate(xml)
    written = _written(xml_out)
    # The natural written by the lower voice at the same time is carried to the upper voice
    assert (1, "F", "5", "0", None) in written
    assert sorted(written, key=str) == sorted(_source(xml), key=str)


def test_writer_has_alter_and_accidental() -> None:
    tokens = """clef_G2 _ _ _ _ upper
keySignature_-1 . . . . .
timeSignature_4/4 . . . . .
note_4 B4 _ _ _ upper
note_4 B4 N _ _ upper
note_4 B4 _ _ _ upper
note_4 F4 # _ _ upper
barline . . . . ."""
    xml = generate_xml(XmlGeneratorArguments(), [read_token_lines(tokens.splitlines())], "")
    notes = list(xml.iter("note"))
    alters = [n.findtext("pitch/alter") for n in notes]
    accidentals = [n.findtext("accidental") for n in notes]
    assert alters == ["-1", "0", None, "1"]
    assert accidentals == [None, "natural", None, "sharp"]


def test_state_converts_in_both_directions() -> None:
    labels, sounding = AccidentalState(2), AccidentalState(2)
    for step, octave, alter in [("F", 4, 0), ("F", 4, 0), ("C", 4, 1), ("F", 5, 1), ("F", 4, 2)]:
        sign = labels.printed_sign("a", step, octave, alter)
        assert sounding.sounding_alter("a", step, octave, sign) == alter
