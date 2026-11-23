# ruff: noqa: S101, S314
"""A tempo marking is written as a direction in the first measure of its own page."""

import xml.etree.ElementTree as ET

import numpy as np

from homr.main import RecognizedPage, write_page
from homr.music_xml_generator import TimeSignatureMemory, XmlGeneratorArguments
from homr.relieur import process_concat
from homr.title_detection import TextBox, _merge_texts
from training.transformer.training_vocabulary import read_token_lines


def test_ocr_direction_is_local_to_page_and_first_part(tmp_path):
    args = XmlGeneratorArguments(metronome=80, tempo=75)
    memory = TimeSignatureMemory()
    before = vars(args).copy()
    tokens = read_token_lines(
        ["clef_G2 . . . . upper", "note_4 C4 _ _ _ upper", "barline . . . . ."]
    )
    marks = ["", "Lento", "Presto", ""]
    paths = []
    for index, mark in enumerate(marks):
        page = RecognizedPage(str(tmp_path / f"{index}.xml"), [tokens, tokens], "Suite", mark)
        path = write_page(page, args, memory)
        paths.append(path)
        xml = ET.parse(path)
        assert xml.findtext("work/work-title") == "Suite"
        assert [w.text for w in xml.findall("part/measure/direction/direction-type/words")] == (
            [mark] if mark else []
        )
        assert not xml.findall("part[2]/measure/direction/direction-type/words")
        assert xml.find("part/measure/direction/direction-type/metronome/per-minute").text == "80"
        assert [sound.get("tempo") for sound in xml.findall("part/measure/direction/sound")] == [
            "75"
        ]
        if mark:
            first = xml.find("part/measure")
            assert first.find("direction/direction-type/words").text == mark
            assert first.find("direction").get("placement") == "above"
            assert list(first).index(first.find("direction")) < list(first).index(
                first.find("note")
            )
    joined, count, _ = process_concat(paths)
    assert count == 4
    assert [
        [w.text for w in m.findall("direction/direction-type/words")]
        for m in joined.findall("part[1]/measure")
    ] == [[], ["Lento"], ["Presto"], []]
    assert vars(args) == before


def test_tempo_heading_joins_adjacent_words_and_keeps_stacked_expression_separate():

    def box(word, left, top, right, bottom):
        return TextBox(word, np.array([[left, top], [right, top], [right, bottom], [left, bottom]]))

    fragments = [
        box("Andante", 0, 0, 75, 24),
        box("con moto", 78, 1, 155, 24),
        box("dolce", 12, 11, 62, 34),
    ]
    assert [r.text for r in _merge_texts(fragments)] == ["Andante con moto", "dolce"]
