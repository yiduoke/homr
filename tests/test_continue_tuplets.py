# ruff: noqa: S101, S314
import os
import xml.etree.ElementTree as ET

import pytest

from homr.main import continue_tuplets

DIVISIONS = 12  # a quarter note is 12 divisions: eighth 6, triplet eighth 4


def _note(step: str, duration: int, triplet: bool, beam: str, tuplet: str | None = None) -> str:
    ratio = (
        "<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes>"
        "<normal-type>eighth</normal-type></time-modification>"
        if triplet
        else ""
    )
    mark = f'<notations><tuplet type="{tuplet}"/></notations>' if tuplet else ""
    return (
        f"<note><pitch><step>{step}</step><octave>4</octave></pitch><duration>{duration}</duration>"
        f'<voice>1</voice><type>eighth</type>{ratio}<beam number="1">{beam}</beam>{mark}</note>'
    )


def _triplets() -> str:
    return (
        _note("C", 4, True, "begin", "start")
        + _note("D", 4, True, "continue")
        + _note("E", 4, True, "end", "stop")
    )


def _plain() -> str:
    return (
        _note("C", 6, False, "begin")
        + _note("D", 6, False, "continue")
        + _note("E", 6, False, "end")
    )


def _page(measures: list[str], first: bool) -> str:
    bars = []
    for number, body in enumerate(measures, start=1):
        attributes = (
            f"<attributes><divisions>{DIVISIONS}</divisions>"
            "<time><beats>2</beats><beat-type>4</beat-type></time></attributes>"
            if number == 1
            else ""
        )
        bars.append(f'<measure number="{number}">{attributes}{body}</measure>')
    return '<score-partwise><part-list/><part id="P1">' + "".join(bars) + "</part></score-partwise>"


def _durations(path: str) -> list[str]:
    root = ET.parse(path).getroot()
    return [d.text or "" for d in root.iterfind("part/measure/note/duration")]


def _write(tmp_path: str, name: str, content: str) -> str:
    path = os.path.join(tmp_path, name)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path


def test_a_ratio_read_on_one_page_continues_on_the_next(tmp_path: pytest.TempPathFactory) -> None:
    first = _write(str(tmp_path), "page-1.musicxml", _page([_triplets() + _triplets()], True))
    # Three quarters of eighth notes in a 2/4 bar: only the triplet reading fits
    second = _write(str(tmp_path), "page-2.musicxml", _page([_plain() + _plain()], False))

    continue_tuplets([first, second])

    assert _durations(second) == ["4"] * 6
    assert _durations(first) == ["4"] * 6


def test_the_pass_can_be_switched_off(
    tmp_path: pytest.TempPathFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOMR_TUPLET_PASS", "0")
    first = _write(str(tmp_path), "page-1.musicxml", _page([_triplets() + _triplets()], True))
    second = _write(str(tmp_path), "page-2.musicxml", _page([_plain() + _plain()], False))

    continue_tuplets([first, second])

    assert _durations(second) == ["6"] * 6


def test_a_page_where_nothing_changes_is_not_written(tmp_path: pytest.TempPathFactory) -> None:
    content = _page([_plain() + _plain() + _plain()], True)
    path = _write(str(tmp_path), "page-1.musicxml", content)

    continue_tuplets([path])

    with open(path, encoding="utf-8") as f:
        assert f.read() == content
