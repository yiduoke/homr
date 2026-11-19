# ruff: noqa: S101
import xml.etree.ElementTree as ET

import pytest

from homr.music_xml_generator import XmlGeneratorArguments, generate_xml
from homr.transformer.vocabulary import split_slur_and_beam
from training.omr_datasets.humdrum_kern_parser import convert_kern_to_tokens
from training.omr_datasets.music_xml_parser import music_xml_string_to_tokens
from training.transformer.training_vocabulary import (
    read_token_lines,
    token_lines_to_str,
)


def _xml_note(step: str, note_type: str, duration: int, beam: str = "", chord: bool = False) -> str:
    chord_tag = "<chord/>" if chord else ""
    beam_tag = f'<beam number="1">{beam}</beam>' if beam else ""
    return f"""<note>{chord_tag}<pitch><step>{step}</step><octave>5</octave></pitch>
      <duration>{duration}</duration><voice>1</voice><type>{note_type}</type>
      <staff>1</staff>{beam_tag}</note>"""


def _xml(*notes: str) -> str:
    return f"""<score-partwise version="4.0"><part id="P1"><measure>
      <attributes><divisions>2</divisions>
      <time><beats>2</beats><beat-type>4</beat-type></time>
      <clef><sign>G</sign><line>2</line></clef></attributes>
      {"".join(notes)}
    </measure></part></score-partwise>"""


def _tokens(xml: str) -> str:
    parts = music_xml_string_to_tokens(xml)
    return token_lines_to_str([s for part in parts for measure in part for s in measure])


def _generate(tokens: str, beam_export: bool = True) -> ET.Element:
    # The cross-staff beam writer is the default (HOMR_BEAM_EXPORT=0 turns it off)
    args = XmlGeneratorArguments(beam_export=beam_export, join_beam_voices=True)
    return generate_xml(args, [read_token_lines(tokens.splitlines())], "")


def _beams(xml: ET.Element) -> list[list[str]]:
    return [
        [f"{b.get('number')}:{b.text}" for b in note.findall("beam")] for note in xml.iter("note")
    ]


def test_music_xml_beam_is_on_the_chord() -> None:
    xml = _xml(
        _xml_note("C", "eighth", 1, "begin"),
        _xml_note("E", "eighth", 1, chord=True),
        _xml_note("D", "eighth", 1, "end"),
        _xml_note("E", "quarter", 2),
    )
    assert _tokens(xml) == """clef_G2 _ _ _ _ upper
timeSignature_2/4 . . . . .
note_8 E5 _ _ beamStart upper&note_8 C5 _ _ _ upper
note_8 D5 _ _ beamStop upper
note_4 E5 _ _ _ upper
barline . . . . ."""


def test_kern_beams_count_all_levels() -> None:
    kern = """**kern\t**kern
*clefF4\t*clefG2
*M2/4\t*M2/4
4C\t16ccLL
.\t16ddJ
.\t8eeJ
4D\t8dd 8ffL
.\t8ccJ
=\t=
*-\t*-"""
    tokens = token_lines_to_str(convert_kern_to_tokens(kern.splitlines()))
    upper = [line.split("&")[0] for line in tokens.splitlines() if "upper" in line]
    beams = [split_slur_and_beam(line.split()[4])[1] for line in upper if line.startswith("note")]
    assert beams == ["beamStart", "beamContinue", "beamStop", "beamStart", "beamStop"]


def test_generator_adds_secondary_beams_and_hooks() -> None:
    xml = _generate("""clef_G2 _ _ _ _ upper
timeSignature_2/4 . . . . .
note_8. C5 _ _ beamStart upper
note_16 D5 _ _ beamStop upper
note_16 E5 _ _ beamStart upper
note_16 F5 _ _ beamContinue upper
note_8 G5 _ _ beamStop upper
barline . . . . .""")
    assert _beams(xml) == [
        ["1:begin"],
        ["1:end", "2:backward hook"],
        ["1:begin", "2:begin"],
        ["1:continue", "2:end"],
        ["1:end"],
    ]


def test_generator_repairs_beams() -> None:
    # A beam which starts but never continues, a quarter in a beam and a group
    # without a start
    xml = _generate("""clef_G2 _ _ _ _ upper
timeSignature_2/4 . . . . .
note_8 C5 _ _ beamStart upper
note_4 D5 _ _ beamContinue upper
note_8 E5 _ _ beamContinue upper
note_8 F5 _ _ beamStop upper
note_8 G5 _ _ beamStart upper
barline . . . . .""")
    assert _beams(xml) == [[], [], ["1:begin"], ["1:end"], []]


def test_generator_beams_chords_on_the_first_note() -> None:
    xml = _generate("""clef_G2 _ _ _ _ upper
timeSignature_2/4 . . . . .
note_8 C5 _ _ beamStart upper&note_8 E5 _ _ _ upper
note_8 D5 _ _ beamStop upper&note_8 F5 _ _ _ upper
barline . . . . .""")
    assert _beams(xml) == [["1:begin"], [], ["1:end"], []]


def test_round_trip() -> None:
    tokens = """clef_G2 _ _ _ _ upper
timeSignature_2/4 . . . . .
note_8 C5 _ _ beamStart_slurStart upper
note_16 D5 _ _ beamContinue upper
note_16 E5 _ _ beamStop_slurStop upper
note_8 F5 _ _ _ upper
note_8 G5 _ _ _ upper
barline . . . . ."""
    assert _tokens(ET.tostring(_generate(tokens), encoding="unicode")) == tokens


def test_generator_joins_cross_staff_beams() -> None:
    xml = _generate("""clef_G2 _ _ _ _ upper&clef_F4 _ _ _ _ lower
timeSignature_2/4 . . . . .
note_8 C5 _ _ beamStart upper
note_8 C3 _ _ beamContinue lower
note_8 D5 _ _ beamStop upper
note_8 D3 _ _ _ lower
barline . . . . .""")
    notes = list(xml.iter("note"))
    assert _beams(xml) == [["1:begin"], ["1:continue"], ["1:end"], []]
    # A beam is drawn within one voice, the lower note moves into it
    assert notes[1].findtext("staff") == "2"
    assert notes[1].findtext("voice") == notes[0].findtext("voice")


def _staff_voice_beams(xml: ET.Element) -> list[tuple[str, str, str]]:
    return [
        (
            note.findtext("staff", "1"),
            note.findtext("voice", "1"),
            ",".join(b.text or "" for b in note.findall("beam") if b.get("number") == "1"),
        )
        for note in xml.iter("note")
        if note.find("rest") is None
    ]


_TWO_STAVES = """clef_G2 _ _ _ _ upper&clef_F4 _ _ _ _ lower
timeSignature_2/4 . . . . ."""


def test_beam_from_the_lower_to_the_upper_staff_stays_one_group() -> None:
    # Debussy, Pour le piano, bar 1, beat 1: A3 of the left hand starts the beam of the right
    xml = _generate(f"""{_TWO_STAVES}
note_16 A3 _ _ beamStart lower2
note_16 C4 _ _ beamContinue upper
note_16 E4 _ _ beamContinue upper
note_16 C4 _ _ beamStop upper
note_4 A3 _ _ _ lower
barline . . . . .""")
    rows = _staff_voice_beams(xml)
    assert [r[2] for r in rows[:4]] == ["begin", "continue", "continue", "end"]
    assert [r[0] for r in rows[:4]] == ["2", "1", "1", "1"]
    assert len({r[1] for r in rows[:4]}) == 1


def test_beam_from_the_upper_to_the_lower_staff_stays_one_group() -> None:
    xml = _generate(f"""{_TWO_STAVES}
note_16 E5 _ _ beamStart upper
note_16 C3 _ _ beamContinue lower
note_16 D3 _ _ beamContinue lower
note_16 E3 _ _ beamStop lower
barline . . . . .""")
    rows = _staff_voice_beams(xml)
    assert [r[2] for r in rows] == ["begin", "continue", "continue", "end"]
    assert [r[0] for r in rows] == ["1", "2", "2", "2"]
    assert len({r[1] for r in rows}) == 1


def test_beam_which_changes_staff_twice_stays_one_group() -> None:
    xml = _generate(f"""{_TWO_STAVES}
note_16 C3 _ _ beamStart lower
note_16 C5 _ _ beamContinue upper
note_16 D5 _ _ beamContinue upper
note_16 D3 _ _ beamContinue lower
note_16 E3 _ _ beamStop lower
note_8 G4 _ _ _ upper
barline . . . . .""")
    rows = _staff_voice_beams(xml)
    assert [r[2] for r in rows[:5]] == ["begin", "continue", "continue", "continue", "end"]
    assert len({r[1] for r in rows[:5]}) == 1


def test_accompaniment_keeps_its_own_beam_under_a_beam_which_changes_staff() -> None:
    # Left hand eighths beamed together while a sixteenth beam goes from the left to the right hand
    xml = _generate("""clef_G2 _ _ _ _ upper&clef_F4 _ _ _ _ lower
timeSignature_4/4 . . . . .
note_8 C2 _ _ beamStart lower
note_16 A3 _ _ beamStart lower2
note_16 C4 _ _ beamContinue upper
note_16 E4 _ _ beamContinue upper
note_16 C4 _ _ beamStop upper
note_8 D2 _ _ beamStop lower
barline . . . . .""")
    rows = _staff_voice_beams(xml)
    by_beam: dict = {}
    for staff, voice, state in rows:
        by_beam.setdefault(voice, []).append((staff, state))
    groups = sorted(by_beam.values())
    assert [[s for _, s in g] for g in groups] == [
        ["begin", "continue", "continue", "end"],
        ["begin", "end"],
    ]
    # the accompaniment stays on the lower staff, the sixteenths cross
    assert sorted(len({st for st, _ in g}) for g in groups) == [1, 2]


def test_a_new_beam_after_a_crossing_one_is_separate() -> None:
    xml = _generate(f"""{_TWO_STAVES}
note_16 E5 _ _ beamStart upper
note_16 C3 _ _ beamStop lower
note_16 D3 _ _ beamStart lower
note_16 E3 _ _ beamStop lower
barline . . . . .""")
    assert [r[2] for r in _staff_voice_beams(xml)] == ["begin", "end", "begin", "end"]


def test_an_unbeamed_note_ends_the_group_of_a_crossing_beam() -> None:
    xml = _generate(f"""{_TWO_STAVES}
note_16 E5 _ _ beamStart upper
note_16 C3 _ _ beamContinue lower
note_8 D3 _ _ _ lower
note_16 E3 _ _ beamStop lower
barline . . . . .""")
    # E5 and C3 stay a group, the stop without its start is repaired away
    assert [r[2] for r in _staff_voice_beams(xml)] == ["begin", "end", "", ""]


def test_ordinary_groups_on_both_staves_are_unchanged() -> None:
    xml = _generate(f"""{_TWO_STAVES}
note_16 C5 _ _ beamStart upper
note_16 D5 _ _ beamContinue upper
note_16 E5 _ _ beamContinue upper
note_16 F5 _ _ beamStop upper
note_16 C3 _ _ beamStart lower
note_16 D3 _ _ beamContinue lower
note_16 E3 _ _ beamContinue lower
note_16 F3 _ _ beamStop lower
barline . . . . .""")
    rows = _staff_voice_beams(xml)
    assert [r[2] for r in rows] == ["begin", "continue", "continue", "end"] * 2
    assert [r[0] for r in rows] == ["1"] * 4 + ["2"] * 4
    assert len({r[1] for r in rows[:4]}) == 1
    assert len({r[1] for r in rows[4:]}) == 1
    assert rows[0][1] != rows[4][1]


def test_voices_of_a_crossing_beam_can_stay_with_their_positions() -> None:
    # The page merger repairs overfull voices per voice label; with join_beam_voices off the labels
    # are those of the positions and the beam states alone tell the group.
    tokens = f"""{_TWO_STAVES}
note_16 A3 _ _ beamStart lower2
note_16 C4 _ _ beamContinue upper
note_16 E4 _ _ beamContinue upper
note_16 C4 _ _ beamStop upper
note_4 A3 _ _ _ lower
barline . . . . ."""
    joined = _staff_voice_beams(_generate(tokens))
    staffs = [read_token_lines(tokens.splitlines())]
    apart = _staff_voice_beams(
        generate_xml(XmlGeneratorArguments(join_beam_voices=False, beam_export=True), staffs, "")
    )
    states = ["begin", "continue", "continue", "end", ""]
    assert [r[2] for r in apart] == [r[2] for r in joined] == states
    assert len({r[1] for r in joined[:4]}) == 1
    assert apart[0][1] != apart[1][1]


def test_default_writer_is_the_unchanged_one_and_the_switch_selects_the_new_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    tokens = f"""{_TWO_STAVES}
note_16 A3 _ _ beamStart lower2
note_16 C4 _ _ beamContinue upper
note_16 E4 _ _ beamContinue upper
note_16 C4 _ _ beamStop upper
note_4 A3 _ _ _ lower
barline . . . . ."""
    staffs = [read_token_lines(tokens.splitlines())]
    for name in ("HOMR_BEAM_EXPORT", "HOMR_COMBINED", "HOMR_COMBINED_OFF"):
        monkeypatch.delenv(name, raising=False)
    assert XmlGeneratorArguments().beam_export is True
    monkeypatch.setenv("HOMR_BEAM_EXPORT", "0")
    default = XmlGeneratorArguments()
    assert default.beam_export is False
    assert default.join_beam_voices is True
    old = _staff_voice_beams(generate_xml(default, staffs, ""))
    # the run of two notes on the second staff splits the group in the default writer
    assert [r[2] for r in old[:4]] != ["begin", "continue", "continue", "end"]
    monkeypatch.delenv("HOMR_BEAM_EXPORT")
    on = XmlGeneratorArguments()
    assert on.beam_export is True
    assert on.join_beam_voices is False
    new = _staff_voice_beams(generate_xml(on, staffs, ""))
    assert [r[2] for r in new[:4]] == ["begin", "continue", "continue", "end"]
    monkeypatch.setenv("HOMR_COMBINED", "1")
    assert XmlGeneratorArguments().beam_export is True
    monkeypatch.setenv("HOMR_COMBINED_OFF", "B")
    assert XmlGeneratorArguments().beam_export is False
