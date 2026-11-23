# ruff: noqa: S101, S314
"""Meter changes survive the page joiner, and repeated meters are dropped.

Each case lists the <time> elements written at the start of each page and the
<time> elements expected in each joined bar.
"""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from homr.relieur import process_concat


def time(*pairs, extra="", symbol="", staff="", child=""):
    attrs = dict(([("number", staff)] if staff else []) + ([("symbol", symbol)] if symbol else []))
    el = ET.Element("time", attrs)
    for beats, unit in pairs:
        ET.SubElement(el, "beats").text = str(beats)
        ET.SubElement(el, "beat-type").text = str(unit)
    if child:
        el.append(ET.fromstring(child))
    if extra:
        el.set("default-x", extra)
    return ET.tostring(el, encoding="unicode")


def _cases() -> dict:
    a, b = time((3, 4)), time((5, 8))
    c, d = time((2, 4), (3, 8)), time((3, 4), (3, 8))
    upper, lower = time((3, 4), staff="1"), time((2, 4), staff="2")
    return {
        "meter and repeats over four pages": ([a, a, b, b], [[a], [], [b], []]),
        "missing on first page": (["", b, b], [[], [b], []]),
        "additive numerator": (
            [time(("2+3", 8)), time(("3+2", 8))],
            [[time(("2+3", 8))], [time(("3+2", 8))]],
        ),
        "first pair of composite meter": ([c, d, d], [[c], [d], []]),
        "separate staves, repeated then changed": (
            [upper + lower, upper + lower, a, a],
            [[upper, lower], [], [a], []],
        ),
        "numbered staff inherits all-staves meter": ([a, upper + lower], [[a], [lower]]),
        "common time after numeric": (
            [time((4, 4)), time((4, 4), symbol="common")],
            [[time((4, 4))], [time((4, 4), symbol="common")]],
        ),
        "unmeasured": (
            [a, time(child="<senza-misura />")],
            [[a], [time(child="<senza-misura />")]],
        ),
        "interchangeable alternative": (
            [
                time(
                    (3, 4),
                    child="<interchangeable><beats>6</beats><beat-type>8</beat-type></interchangeable>",
                ),
                time(
                    (3, 4),
                    child="<interchangeable><beats>12</beats><beat-type>16</beat-type></interchangeable>",
                ),
            ],
            None,
        ),
        "layout offset only": ([a, time((3, 4), extra="36")], [[a], []]),
        "midmeasure change and return": (
            [
                a,
                a
                + "</attributes><note><rest/></note><attributes>"
                + b
                + "</attributes><note><rest/></note><attributes>"
                + a,
                a,
            ],
            [[a], [b, a], []],
        ),
    }


CASES = _cases()


@pytest.mark.parametrize("name", list(CASES))
def test_joined_pages_keep_meter_changes(name: str, tmp_path: Path) -> None:
    pages, expected = CASES[name]
    if expected is None:
        expected = [[p] for p in pages]
    paths = []
    for index, attrs in enumerate(pages):
        path = tmp_path / f"page-{index}.xml"
        path.write_text(
            '<score-partwise><part id="p"><measure number="1"><attributes>'
            + attrs
            + "</attributes></measure></part></score-partwise>"
        )
        paths.append(str(path))
    root, _, _ = process_concat(paths)
    actual = [
        [ET.tostring(t, encoding="unicode") for t in bar.findall("attributes/time")]
        for bar in root.findall("part/measure")
    ]
    assert actual == expected
