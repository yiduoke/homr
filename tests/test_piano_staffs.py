# ruff: noqa: S101
from fractions import Fraction

from homr.music_xml_generator import GroupClock, SymbolChord
from homr.piano_staffs import is_piano_system, merge_piano_system
from homr.transformer.vocabulary import EncodedSymbol, sort_token_chords
from training.transformer.training_vocabulary import read_token_lines


def _staff(*lines: str) -> list[EncodedSymbol]:
    return read_token_lines([line if " " in line else line + " . . . . ." for line in lines])


def _four_staffs(third_clef: str = "clef_F4") -> list[list[EncodedSymbol]]:
    # Bar 1: the right hand has quarters in the upper staff and a half note in the second,
    # the left hand a whole note in the lowest. The second bar repeats the first.
    bar = [
        ["note_4 C5 _ _ _ upper"] * 4,
        ["note_2 E4 _ _ _ upper"] * 2,
        ["note_4 G3 _ _ _ upper"] * 4,
        ["note_1 C2 _ _ _ upper"],
    ]
    clefs = ["clef_G2", "clef_G2", third_clef, "clef_F4"]
    return [
        _staff(f"{clef} . . . . upper", "timeSignature_4/4", *notes, "barline", *notes, "barline")
        for clef, notes in zip(clefs, bar, strict=True)
    ]


def _groups(symbols: list[EncodedSymbol]) -> list[list[EncodedSymbol]]:
    return sort_token_chords(symbols)


def test_piano_system_needs_two_treble_and_two_bass_clefs() -> None:
    assert is_piano_system(_four_staffs())
    assert not is_piano_system(_four_staffs("clef_G2"))
    assert not is_piano_system(_four_staffs()[:3])


def test_third_staff_in_treble_clef_is_allowed_if_the_page_shows_piano() -> None:
    assert is_piano_system(_four_staffs("clef_G2"), piano_on_page=True)


def test_staffs_become_the_positions_of_two_hands() -> None:
    merged = merge_piano_system(_four_staffs())

    notes = [s for s in merged if s.rhythm.startswith("note")]
    positions = {(s.pitch, s.position) for s in notes}
    assert positions == {("C5", "upper"), ("E4", "upper2"), ("G3", "lower"), ("C2", "lower2")}
    clefs = [(s.rhythm, s.position) for s in merged if s.rhythm.startswith("clef")]
    assert clefs == [("clef_G2", "upper"), ("clef_F4", "lower")]
    assert [s.rhythm for s in merged].count("barline") == 2
    assert [s.rhythm for s in merged].count("timeSignature_4/4") == 1


def test_groups_which_start_together_are_joined_in_time_order() -> None:
    merged = merge_piano_system(_four_staffs())

    clock = GroupClock()
    onsets = []
    for symbols in _groups(merged):
        if symbols[0].rhythm.startswith("note"):
            clock.wait_for_voices(SymbolChord(symbols))
            onsets.append((clock.time, sorted(s.position for s in symbols)))
            clock.advance(SymbolChord(symbols))
        elif symbols[0].rhythm == "barline":
            clock = GroupClock()
    first_bar = onsets[:4]
    assert [onset for onset, _ in first_bar] == [Fraction(i, 4) for i in range(4)]
    assert first_bar[0][1] == ["lower", "lower2", "upper", "upper2"]
    assert first_bar[1][1] == ["lower", "upper"]
    assert first_bar[2][1] == ["lower", "upper", "upper2"]


def test_a_staff_with_fewer_measures_is_padded() -> None:
    staffs = _four_staffs()
    staffs[1] = staffs[1][: len(staffs[1]) // 2]

    merged = merge_piano_system(staffs)

    assert [s.rhythm for s in merged].count("barline") == 2
    second_bar = [s for s in merged if s.position == "upper2"]
    assert len(second_bar) == 2
