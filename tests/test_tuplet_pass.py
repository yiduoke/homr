"""Tests of the score-level tuplet continuation pass (research_scripts/tuplet_pass.py)."""
import os
import sys
import xml.etree.ElementTree as ET
from fractions import Fraction

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "research_scripts"))
import tuplet_pass as TP  # noqa: E402

DIV = 12  # a quarter note is 12 divisions: eighth 6, triplet eighth 4, sixteenth 3


def note(step, typ, dur, voice="1", tm=False, beam=None, rest=False, tup=None):
    parts = ["<note>"]
    parts.append("<rest/>" if rest else f"<pitch><step>{step}</step><octave>4</octave></pitch>")
    parts.append(f"<duration>{dur}</duration><voice>{voice}</voice><type>{typ}</type>")
    if tm:
        parts.append("<time-modification><actual-notes>3</actual-notes><normal-notes>2</normal-notes><normal-type>eighth</normal-type></time-modification>")
    if beam:
        parts.append(f'<beam number="1">{beam}</beam>')
    if tup:
        parts.append(f'<notations><tuplet type="{tup}" bracket="no" show-number="actual"/></notations>')
    parts.append("</note>")
    return "".join(parts)


def triplet(steps="CDE", voice="1"):
    return [note(steps[0], "eighth", 4, voice, True, "begin", tup="start"), note(steps[1], "eighth", 4, voice, True, "continue"),
            note(steps[2], "eighth", 4, voice, True, "end", tup="stop")]


def plain(steps="CDE", voice="1"):
    return [note(steps[0], "eighth", 6, voice, beam="begin"), note(steps[1], "eighth", 6, voice, beam="continue"), note(steps[2], "eighth", 6, voice, beam="end")]


def quarter(step, voice="2", dur=12):
    return note(step, "quarter", dur, voice)


def backup(d):
    return f"<backup><duration>{d}</duration></backup>"


def measure(n, body, time=None):
    attrs = f"<attributes><divisions>{DIV}</divisions>" + (f"<time><beats>{time[0]}</beats><beat-type>{time[1]}</beat-type></time>" if time else "") + "</attributes>"
    return f'<measure number="{n}">{attrs if n == 1 else ""}{"".join(body)}</measure>'


def score(measures):
    return ET.fromstring('<score-partwise><part-list/><part id="P1">' + "".join(measures) + "</part></score-partwise>")


def voice_durs(root, voice="1", bar=0):
    bars = TP.parse_score(root)[0]
    return [(s.onset, s.dur, s.tm) for s in bars[bar].voices[voice].slots]


def test_converts_overfull_bar_when_ratio_fits_and_keeps_other_voice():
    # 2/4: bar 1 explicit triplets (two); bar 2 two plain groups = 3 quarters in a 2/4 bar, left hand two quarters
    m1 = measure(1, triplet() + triplet() + [backup(24)] + [quarter("C"), quarter("G")], (2, 4))
    m2 = measure(2, plain() + plain() + [backup(36)] + [quarter("C"), quarter("G")])
    root = score([m1, m2])
    log, cnt = TP.process(root)
    assert cnt.get("converted") == 1
    d = voice_durs(root, "1", 1)
    assert [x[1] for x in d] == [Fraction(1, 3)] * 6
    assert all(x[2] == (3, 2) for x in d)
    # the left hand keeps its onsets 0 and 1
    bars = TP.parse_score(root)[0]
    assert [s.onset for s in bars[1].voices["2"].slots] == [Fraction(0), Fraction(1)]
    assert bars[1].voices["1"].total == Fraction(2)
    # no numeral or bracket is added
    assert len(list(root.iter("tuplet"))) == 4


def test_ordinary_bar_that_fits_is_not_touched():
    # 4/4: explicit triplets in bar 1; bar 2 has two plain groups of three eighths and a quarter = 4 quarters: it fits, so the ordinary reading stays
    root = score([measure(1, triplet() * 4, (4, 4)), measure(2, plain() + plain() + [note("F", "quarter", 12)])])
    log, cnt = TP.process(root)
    assert "converted" not in cnt
    assert cnt.get("skip:bar_fits") == 1


def test_compound_meter_groups_are_not_converted():
    # 6/8 after a 2/4 bar with explicit triplets: three plain groups of three eighths are the beat grouping of the meter
    m2 = '<measure number="2"><attributes><time><beats>6</beats><beat-type>8</beat-type></time></attributes>' + "".join(plain() + plain() + plain()) + "</measure>"
    root = score([measure(1, triplet() + triplet(), (2, 4)), m2])
    log, cnt = TP.process(root)
    assert "converted" not in cnt


def test_no_explicit_group_earlier_nothing_happens():
    root = score([measure(1, plain() + plain() + plain(), (2, 4))])
    log, cnt = TP.process(root)
    assert cnt == {}


def test_ambiguous_subset_is_left_alone():
    # 4/4, explicit earlier; bar with three plain groups and the voice overfull by exactly one group's reduction: which one is a triplet is unknown
    m1 = measure(1, triplet() * 4, (4, 4))
    m2 = measure(2, plain() + plain() + plain() + [note("F", "eighth", 6, rest=True)])  # 4.5 + 0.5 = 5 > 4; excess 1
    root = score([m1, m2])
    log, cnt = TP.process(root)
    # reductions are 0.5 each: two of three groups must change, three subsets fit
    assert "converted" not in cnt
    assert cnt.get("skip:ambiguous_subset") == 1


def test_default_off(tmp_path, monkeypatch):
    monkeypatch.delenv("HOMR_TUPLET_PASS", raising=False)
    root = score([measure(1, triplet() + triplet(), (2, 4)), measure(2, plain() + plain())])
    src = tmp_path / "a.musicxml"
    dst = tmp_path / "b.musicxml"
    ET.ElementTree(root).write(src)
    log, cnt = TP.apply_if_enabled(str(src), str(dst))
    assert log == [] and src.read_bytes() == dst.read_bytes()
    monkeypatch.setenv("HOMR_TUPLET_PASS", "1")
    log, cnt = TP.apply_if_enabled(str(src), str(dst))
    assert cnt.get("converted") == 1 and src.read_bytes() != dst.read_bytes()


def test_continuation_across_bars_and_systems_uses_the_same_voice_only():
    # the explicit group is in voice 1; the plain groups are in voice 2: not the same voice, nothing happens
    m1 = measure(1, triplet() + triplet(), (2, 4))
    m2 = measure(2, plain("CDE", "2") + plain("CDE", "2"))
    root = score([m1, m2])
    log, cnt = TP.process(root)
    assert "converted" not in cnt


def test_group_of_rests_alone_is_not_converted():
    rest_triplet = [note("C", "eighth", 4, rest=True, tm=True) for _ in range(3)]
    rests = [note("C", "eighth", 6, rest=True) for _ in range(3)]
    mk = lambda: score([measure(1, rest_triplet * 2, (2, 4)), measure(2, rests + rests)])  # noqa: E731
    log, cnt = TP.process(mk())
    assert "converted" not in cnt
    log, cnt = TP.process(mk(), {"skip_rest_only": False})
    assert cnt.get("converted") == 1
