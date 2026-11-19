# mypy: ignore-errors
# ruff: noqa: S101, S314, E501, E731
"""Tests of the bar-fill deduction of unnumbered tuplets (research_scripts/tuplet_pass.py, branch tuplet-barfill)."""

import os
import sys
from fractions import Fraction

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research_scripts"))
import tuplet_pass as TP  # noqa: E402
from test_tuplet_pass import backup, measure, note, plain, quarter, score, triplet, voice_durs  # noqa: E402


def sixteenths(steps="CDEFGA"):
    kinds = ["begin"] + ["continue"] * 4 + ["end"]
    return [note(steps[i], "16th", 3, beam=kinds[i]) for i in range(6)]


def durs(root, voice="1", bar=0):
    return [x[1] for x in voice_durs(root, voice, bar)]


def test_triplet_eighths_in_2_4():
    # two plain beam groups of three eighths in a 2/4 bar: 3 quarters, excess 1, both groups are triplets
    root = score([measure(1, plain() + plain(), (2, 4))])
    log, cnt = TP.process(root)
    assert cnt.get("converted:barfill") == 1
    assert durs(root) == [Fraction(1, 3)] * 6
    assert TP.parse_score(root)[0][0].voices["1"].total == Fraction(2)
    assert len(list(root.iter("tuplet"))) == 0  # unnumbered: no numeral, no bracket
    assert [tm.findtext("actual-notes") + ":" + tm.findtext("normal-notes") for tm in root.iter("time-modification")] == ["3:2"] * 6


def test_sextuplets():
    # two groups of six sixteenths in 2/4: each is 6 in the time of 4
    root = score([measure(1, sixteenths() + sixteenths(), (2, 4))])
    log, cnt = TP.process(root)
    assert cnt.get("converted:barfill") == 1
    assert durs(root) == [Fraction(1, 6)] * 12
    assert {tm.findtext("actual-notes") + ":" + tm.findtext("normal-notes") for tm in root.iter("time-modification")} == {"6:4"}


def test_mixed_bar_one_numbered_one_unnumbered_group():
    # 2/4: a numbered eighth triplet (1 quarter) and an unnumbered group of six sixteenths (1.5): 2.5, the sixteenths are the sextuplet
    root = score([measure(1, triplet() + sixteenths(), (2, 4))])
    log, cnt = TP.process(root)
    assert cnt.get("converted:barfill") == 1
    d = durs(root)
    assert d == [Fraction(1, 3)] * 3 + [Fraction(1, 6)] * 6
    assert TP.parse_score(root)[0][0].voices["1"].total == Fraction(2)
    assert len(list(root.iter("tuplet"))) == 2  # only the numbered group has tuplet marks


def test_ambiguous_bar_is_left_alone():
    # 4/4: two plain groups (3 quarters) and 1.5 quarters of other notes: 4.5, excess 0.5; either group would make the bar fit
    body = plain("CDE") + plain("FGA") + [note("B", "quarter", 12), note("C", "eighth", 6)]
    root = score([measure(1, body, (4, 4))])
    log, cnt = TP.process(root)
    assert "converted:barfill" not in cnt
    assert cnt.get("skip:barfill_ambiguous") == 1
    assert len(list(root.iter("time-modification"))) == 0


def test_wrong_meter_is_left_alone():
    # three plain groups are 4.5 quarters: read as 2/4 (excess 2.5) no assignment fits; read as 4/4 it is overfull by 0.5 and
    # each of the three groups could be the triplet: ambiguous; read as 6/4 it fits and is not touched
    body = plain("CDE") + plain("FGA") + plain("BCD")
    for meter, expect in (((2, 4), "skip:barfill_no_fit"), ((4, 4), "skip:barfill_ambiguous")):
        root = score([measure(1, body, meter)])
        log, cnt = TP.process(root)
        assert "converted:barfill" not in cnt and cnt.get(expect) == 1
        assert len(list(root.iter("time-modification"))) == 0
    root = score([measure(1, body, (6, 4))])
    log, cnt = TP.process(root)
    assert cnt == {}


def test_other_voice_keeps_its_onsets():
    body = plain() + plain() + [backup(36)] + [quarter("C"), quarter("G")]
    root = score([measure(1, body, (2, 4))])
    log, cnt = TP.process(root)
    assert cnt.get("converted:barfill") == 1
    bars = TP.parse_score(root)[0]
    assert [s.onset for s in bars[0].voices["2"].slots] == [Fraction(0), Fraction(1)]
    assert bars[0].voices["1"].total == Fraction(2)


def test_unbeamed_quarters_three_in_the_time_of_two():
    # 2/4: three plain quarters without beams are overfull by 1: a quarter triplet
    root = score([measure(1, [note("C", "quarter", 12), note("D", "quarter", 12), note("E", "quarter", 12)], (2, 4))])
    log, cnt = TP.process(root)
    assert cnt.get("converted:barfill") == 1
    assert durs(root) == [Fraction(2, 3)] * 3


def test_switch_off():
    root = score([measure(1, plain() + plain(), (2, 4))])
    log, cnt = TP.process(root, {"barfill": False})
    assert cnt == {}
