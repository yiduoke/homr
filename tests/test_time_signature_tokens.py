# ruff: noqa: S101
import pytest

from homr.transformer.vocabulary import (
    EncodedSymbol,
    Vocabulary,
    parse_time_signature_token,
    remove_duplicated_symbols,
)
from training.omr_datasets.convert_lieder import MeasureCutter
from training.omr_datasets.humdrum_kern_parser import convert_kern_to_tokens
from training.omr_datasets.music_xml_parser import music_xml_string_to_tokens
from training.omr_datasets.time_signatures import UnsupportedTimeSignatureError


def _measure(time: str, note_count: int = 1) -> str:
    notes = "".join(
        "<note><pitch><step>C</step><octave>5</octave></pitch><duration>1</duration>"
        "<voice>1</voice><type>quarter</type></note>"
        for _ in range(note_count)
    )
    return f"<measure><attributes><divisions>1</divisions>{time}</attributes>{notes}</measure>"


def _score(*measures: str) -> str:
    return (
        f'<score-partwise version="4.0"><part id="P1">{"".join(measures)}</part></score-partwise>'
    )


def _time(beats: str, beat_type: str, attributes: str = "") -> str:
    return f"<time {attributes}><beats>{beats}</beats><beat-type>{beat_type}</beat-type></time>"


def _time_tokens(xml: str) -> list[str]:
    voices = music_xml_string_to_tokens(xml)
    return [
        s.rhythm
        for voice in voices
        for measure in voice
        for s in measure
        if "timeSignature" in s.rhythm
    ]


def _staff_time_tokens(xml: str, measures: int = 1) -> list[str]:
    voice = music_xml_string_to_tokens(xml)[0]
    return [s.rhythm for s in MeasureCutter(voice).extract_measures(measures) if "time" in s.rhythm]


@pytest.mark.parametrize(
    ("beats", "beat_type"),
    [("3", "4"), ("4", "4"), ("6", "8"), ("5", "4"), ("12", "8"), ("2", "2")],
)
def test_numeric_time_signature_keeps_both_numbers(beats: str, beat_type: str) -> None:
    xml = _score(_measure(_time(beats, beat_type)))
    assert _time_tokens(xml) == [f"timeSignature_{beats}/{beat_type}"]


def test_common_and_cut_symbols() -> None:
    assert _time_tokens(_score(_measure(_time("4", "4", 'symbol="common"')))) == [
        "timeSignature_common"
    ]
    assert _time_tokens(_score(_measure(_time("2", "2", 'symbol="cut"')))) == ["timeSignature_cut"]


def test_symbol_wins_over_the_numbers() -> None:
    # MuseScore draws C and cut C whatever the numbers say, also cut C on 4/4
    assert _time_tokens(_score(_measure(_time("4", "4", 'symbol="cut"')))) == ["timeSignature_cut"]
    assert _time_tokens(_score(_measure(_time("2", "4", 'symbol="common"')))) == [
        "timeSignature_common"
    ]


def test_hidden_time_signature_has_no_token() -> None:
    assert _time_tokens(_score(_measure(_time("3", "4", 'print-object="no"')))) == []
    assert (
        _time_tokens(_score(_measure(_time("4", "4", 'symbol="common" print-object="no"')))) == []
    )


@pytest.mark.parametrize(
    "time",
    [
        _time("7", "32"),
        _time("3+2", "8"),
        _time("3", "5"),
        _time("3", "4", 'symbol="single-number"'),
        "<time><senza-misura/></time>",
    ],
)
def test_time_signature_outside_the_vocabulary_is_unsupported(time: str) -> None:
    with pytest.raises(UnsupportedTimeSignatureError):
        music_xml_string_to_tokens(_score(_measure(time)))


def test_unsupported_time_signature_is_a_value_error() -> None:
    # The dataset conversions skip a sample on ValueError
    assert issubclass(UnsupportedTimeSignatureError, ValueError)


def test_staff_starts_with_the_time_signature_of_its_first_measure_only() -> None:
    xml = _score(_measure(_time("3", "4")), _measure(""), _measure(_time("4", "4")))
    voice = music_xml_string_to_tokens(xml)[0]
    cutter = MeasureCutter(voice)
    assert [s.rhythm for s in cutter.extract_measures(1) if "time" in s.rhythm] == [
        "timeSignature_3/4"
    ]
    # No signature in the first bar: nothing is drawn, so there is no token
    assert [s.rhythm for s in cutter.extract_measures(1) if "time" in s.rhythm] == []
    assert [s.rhythm for s in cutter.extract_measures(1) if "time" in s.rhythm] == [
        "timeSignature_4/4"
    ]


def test_same_denominator_change_is_kept_in_the_middle_of_a_staff() -> None:
    xml = _score(_measure(_time("3", "4")), _measure(_time("4", "4")))
    assert _staff_time_tokens(xml, 2) == ["timeSignature_3/4", "timeSignature_4/4"]


def test_change_from_numbers_to_the_symbol_is_kept() -> None:
    xml = _score(_measure(_time("4", "4")), _measure(_time("4", "4", 'symbol="common"')))
    assert _staff_time_tokens(xml, 2) == ["timeSignature_4/4", "timeSignature_common"]


def _symbols(*rhythms: str) -> list[EncodedSymbol]:
    return [EncodedSymbol(r) for r in rhythms]


def test_loader_keeps_changes_of_numerator_and_symbol() -> None:
    result = remove_duplicated_symbols(
        _symbols(
            "timeSignature_3/4",
            "barline",
            "timeSignature_4/4",
            "barline",
            "timeSignature_common",
            "barline",
            "timeSignature_cut",
        ),
        cleanup_tuplets=False,
    )
    assert [s.rhythm for s in result if s.rhythm.startswith("timeSignature")] == [
        "timeSignature_3/4",
        "timeSignature_4/4",
        "timeSignature_common",
        "timeSignature_cut",
    ]


def test_loader_removes_an_identical_repeat() -> None:
    result = remove_duplicated_symbols(
        _symbols("timeSignature_3/4", "barline", "timeSignature_3/4"), cleanup_tuplets=False
    )
    assert [s.rhythm for s in result] == ["timeSignature_3/4", "barline"]


def test_vocabulary_has_the_34_numeric_meters_and_the_symbols() -> None:
    rhythm = Vocabulary().rhythm
    meters = [t for t in rhythm if t.startswith("timeSignature")]
    assert len(meters) == 34 + 2
    assert "timeSignature_common" in meters
    assert "timeSignature_cut" in meters
    assert "timeSignature_17/16" in meters
    assert not any(t.startswith("timeSignature/") for t in rhythm)
    # Appended after everything else
    assert max(rhythm.values()) == len(rhythm) - 1
    assert [rhythm[t] for t in meters] == list(range(len(rhythm) - len(meters), len(rhythm)))


def test_parse_time_signature_token() -> None:
    assert parse_time_signature_token("timeSignature_6/8") == (6, 8, None)
    assert parse_time_signature_token("timeSignature_common") == (4, 4, "common")
    assert parse_time_signature_token("timeSignature_cut") == (2, 2, "cut")
    with pytest.raises(ValueError, match="Not a time signature"):
        parse_time_signature_token("timeSignature/4")


def _kern(*time_lines: str, notes: str = "4c\t4e\n4d\t4f\n") -> list[str]:
    header = "**kern\t**kern\n*clefF4\t*clefG2\n*k[]\t*k[]\n"
    controls = "".join(line + "\t" + line + "\n" for line in time_lines)
    return (header + controls + "=-\t=-\n" + notes + "=\t=\n*-\t*-\n").splitlines()


def _kern_time_tokens(lines: list[str]) -> list[str]:
    return [s.rhythm for s in convert_kern_to_tokens(lines) if s.rhythm.startswith("timeSignature")]


def test_kern_numeric() -> None:
    assert _kern_time_tokens(_kern("*M3/4")) == ["timeSignature_3/4"]
    assert _kern_time_tokens(_kern("*M6/8")) == ["timeSignature_6/8"]


@pytest.mark.parametrize("symbol", ["*met(c)", "*met(C)"])
def test_kern_met_c_is_common(symbol: str) -> None:
    assert _kern_time_tokens(_kern("*M4/4", symbol)) == ["timeSignature_common"]


@pytest.mark.parametrize("symbol", ["*met(c|)", "*met(C|)"])
def test_kern_met_cut_is_cut(symbol: str) -> None:
    assert _kern_time_tokens(_kern("*M2/2", symbol)) == ["timeSignature_cut"]


def test_kern_without_meter_has_no_time_signature() -> None:
    assert _kern_time_tokens(_kern()) == []


def test_kern_common_on_a_three_x_meter_is_skipped() -> None:
    for meter in ("*M3/4", "*M3/8"):
        with pytest.raises(UnsupportedTimeSignatureError):
            convert_kern_to_tokens(_kern(meter, "*met(c)"))


def test_kern_meter_outside_the_vocabulary_is_unsupported() -> None:
    with pytest.raises(UnsupportedTimeSignatureError):
        convert_kern_to_tokens(_kern("*M7/32"))


def test_kern_ignores_metronome_marks() -> None:
    assert _kern_time_tokens(_kern("*M4/4", "*MM120")) == ["timeSignature_4/4"]


def test_kern_same_denominator_change_is_kept() -> None:
    kern = (
        "**kern\t**kern\n*clefF4\t*clefG2\n*k[]\t*k[]\n*M3/4\t*M3/4\n=-\t=-\n"
        "4c\t4e\n4d\t4f\n4e\t4g\n=\t=\n*M4/4\t*M4/4\n4c\t4e\n4d\t4f\n4e\t4g\n4f\t4a\n=\t=\n*-\t*-\n"
    )
    assert _kern_time_tokens(kern.splitlines()) == ["timeSignature_3/4", "timeSignature_4/4"]


def test_kern_change_to_the_symbol_replaces_the_number() -> None:
    kern = (
        "**kern\t**kern\n*clefF4\t*clefG2\n*k[]\t*k[]\n*M3/4\t*M3/4\n=-\t=-\n"
        "4c\t4e\n4d\t4f\n4e\t4g\n=\t=\n*M4/4\t*M4/4\n*met(c)\t*met(c)\n"
        "4c\t4e\n4d\t4f\n4e\t4g\n4f\t4a\n=\t=\n*-\t*-\n"
    )
    assert _kern_time_tokens(kern.splitlines()) == ["timeSignature_3/4", "timeSignature_common"]
