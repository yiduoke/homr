# mypy: ignore-errors
# ruff: noqa: S101, E501
"""Tests of fuse_staves.py: run with `python -m pytest run/eval_run1/beam_export/test_fuse_staves.py`."""

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research_scripts"))
import fuse_staves as F  # noqa: E402

D = 10080


def note(step, octave, dur, voice, beam=None, rest=False, chord=False):
    b = f'<beam number="1">{beam}</beam>' if beam else ""
    pitch = "<rest/>" if rest else f"<pitch><step>{step}</step><octave>{octave}</octave></pitch>"
    return f"<note>{'<chord/>' if chord else ''}{pitch}<duration>{dur}</duration><voice>{voice}</voice><type>16th</type>{b}</note>"


def fwd(d):
    return f"<forward><duration>{d}</duration></forward>"


def bck(d):
    return f"<backup><duration>{d}</duration></backup>"


def part(pid, *measures):
    ms = "".join(f'<measure number="{i}">{m}</measure>' for i, m in enumerate(measures, 1))
    return f'<part id="{pid}">{ms}</part>'


def score(*parts, ids=None):
    ids = ids or [f"P{i}" for i in range(len(parts))]
    pl = "".join(f'<score-part id="{i}"><part-name/></score-part>' for i in ids)
    return ET.fromstring(  # noqa: S314
        f"<score-partwise><part-list>{pl}</part-list>{''.join(parts)}</score-partwise>"
    )


ATTR = f"<attributes><divisions>{D}</divisions><time><beats>1</beats><beat-type>4</beat-type></time><clef><sign>{{c}}</sign><line>{{l}}</line></clef></attributes>"
RH = ATTR.format(c="G", l=2)
LH = ATTR.format(c="F", l=4)
S = D // 4  # a sixteenth


def rows(root):
    out = []
    for n in root.iter("note"):
        p = n.find("pitch")
        out.append(
            (
                n.findtext("staff"),
                n.findtext("voice"),
                None if p is None else p.findtext("step") + p.findtext("octave"),
                "".join(b.text[0] for b in n.findall("beam") if b.get("number") == "1"),
            )
        )
    return out


def lower_to_upper(left_voice="6", right_voice="6"):
    # A3 (left hand) begins the beam which goes on in the right hand; accompaniment quarter in the left hand
    rh = part(
        "P0",
        RH
        + fwd(S)
        + note("C", 4, S, right_voice, "continue")
        + note("E", 4, S, right_voice, "continue")
        + note("C", 4, S, right_voice, "end"),
    )
    lh = part(
        "P1",
        LH
        + note("A", 3, S, left_voice, "begin")
        + fwd(3 * S)
        + bck(4 * S)
        + note("A", 2, 4 * S, "5"),
    )
    return score(rh, lh)


def test_cross_staff_voice_becomes_one_stream_in_time_order():
    root = lower_to_upper()
    stats = F.fuse(root, [[0, 1]])
    assert len(root.findall("part")) == 1
    assert root.findtext("part/measure/attributes/staves") == "2"
    voice6 = [r for r in rows(root) if r[1] == "6"]
    assert voice6 == [
        ("2", "6", "A3", "b"),
        ("1", "6", "C4", "c"),
        ("1", "6", "E4", "c"),
        ("1", "6", "C4", "e"),
    ]
    assert ("2", "5", "A2", "") in rows(root)  # the accompaniment keeps its voice and staff
    assert stats.cross_staff_voices == 1
    # the clefs belong to their staves
    assert {c.get("number"): c.findtext("sign") for c in root.iter("clef")} == {"1": "G", "2": "F"}


def test_beam_runs_on_two_staves_with_different_voices_are_stitched():
    root = lower_to_upper(left_voice="5", right_voice="1")
    # the left hand voice 5 also holds the accompaniment: give the accompaniment its own voice
    for n in root.iter("note"):
        if n.findtext("duration") == str(4 * S):
            n.find("voice").text = "7"
    stats = F.fuse(root, [[0, 1]])
    voices = {r[1] for r in rows(root) if r[3]}
    assert len(voices) == 1
    assert [r[3] for r in rows(root) if r[3]] == ["b", "c", "c", "e"]
    assert stats.stitched_beams == 1


def test_complete_groups_on_each_staff_are_not_joined():
    rh = part("P0", RH + note("C", 5, S, "1", "begin") + note("D", 5, S, "1", "end") + fwd(2 * S))
    lh = part("P1", LH + note("C", 3, S, "5", "begin") + note("D", 3, S, "5", "end") + fwd(2 * S))
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]])
    assert stats.stitched_beams == 0
    assert {(r[0], r[1]) for r in rows(root)} == {("1", "1"), ("2", "5")}


def test_pitched_notes_of_one_voice_at_the_same_time_stay_apart():
    rh = part("P0", RH + note("C", 5, S, "1", "begin") + note("D", 5, S, "1", "end") + fwd(2 * S))
    lh = part("P1", LH + note("C", 3, S, "1") + fwd(3 * S))
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]])
    assert stats.voice_conflicts == 1
    by_staff = {r[0]: r[1] for r in rows(root)}
    assert by_staff["1"] != by_staff["2"]


def test_padding_rests_under_notes_of_the_other_staff_are_dropped():
    rh = part("P0", RH + fwd(S) + note("C", 4, S, "6", "end") + fwd(2 * S))
    lh = part("P1", LH + note("A", 3, S, "6", "begin") + note(None, None, 3 * S, "6", rest=True))
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]])
    assert [r[2] for r in rows(root)] == ["A3", "C4"]
    assert stats.rests_dropped == 1


def test_staff_groups_pairs_only_the_staves_of_one_part():
    ids = ["P1", "P2-Staff1", "P2-Staff2", "P3"]
    assert F.staff_groups(ids) == [[1, 2]]
    assert F.staff_groups(["Voice", "Voice#2"]) == []
    assert F.staff_groups(["P1-Staff1", "P1-Staff2", "P1-Staff3"]) == [[0, 1, 2]]


def test_a_voice_part_next_to_the_piano_is_left_alone():
    voice = part("P0", ATTR.format(c="G", l=2) + note("C", 5, 4 * S, "1"))
    rh = part("P1", RH + note("C", 5, S, "1", "begin") + note("D", 5, S, "1", "end") + fwd(2 * S))
    lh = part("P2", LH + note("C", 3, 4 * S, "5"))
    root = score(voice, rh, lh, ids=["P1", "P2-Staff1", "P2-Staff2"])
    before = ET.tostring(root.findall("part")[0])
    F.fuse(root, F.staff_groups(["P1", "P2-Staff1", "P2-Staff2"]))
    parts = root.findall("part")
    assert len(parts) == 2
    assert ET.tostring(parts[0]) == before
    assert parts[1].findtext("measure/attributes/staves") == "2"


# --- chain stitching (D48): beams followed note by note, as the page writer formed them -------------------------------------------


def beam_voices(root):
    """(staff, pitch, voice) of every pitched note with a primary beam state, in file order."""
    return [
        (
            n.findtext("staff"),
            n.find("pitch").findtext("step") + n.find("pitch").findtext("octave"),
            n.findtext("voice"),
        )
        for n in root.iter("note")
        if n.find("beam") is not None and n.find("pitch") is not None
    ]


def aba_beam(voice_lh_first="5", voice_rh="1", voice_lh_last="5"):
    # left hand A3 begins, two right-hand notes continue, the left hand A3 ends: a beam which goes back to its first staff
    rh = part(
        "P0",
        RH
        + fwd(S)
        + note("C", 4, S, voice_rh, "continue")
        + note("E", 4, S, voice_rh, "continue")
        + fwd(S),
    )
    lh = part(
        "P1",
        LH
        + note("A", 3, S, voice_lh_first, "begin")
        + fwd(2 * S)
        + note("A", 3, S, voice_lh_last, "end"),
    )
    return score(rh, lh)


def test_a_beam_which_goes_back_to_its_first_staff_is_one_voice_with_chains_only():
    # the run rule needs a run which starts and does not end and a run which ends and did not start: the middle run is neither
    runs = aba_beam()
    F.fuse(runs, [[0, 1]])  # default: the run rule
    assert len({r[2] for r in beam_voices(runs)}) == 2
    chains = aba_beam()
    stats = F.fuse(chains, [[0, 1]], stitch="chains")
    assert beam_voices(chains) == [
        ("2", "A3", "5"),
        ("1", "C4", "5"),
        ("1", "E4", "5"),
        ("2", "A3", "5"),
    ]
    assert stats.stitched_groups == 1


def test_chains_follow_a_beam_whose_runs_interleave_in_time():
    # A begins, B continues, A continues, B ends: the staves take turns, each note on the other staff than the one before
    rh = part(
        "P0", RH + fwd(S) + note("C", 4, S, "1", "continue") + fwd(S) + note("D", 4, S, "1", "end")
    )
    lh = part("P1", LH + note("A", 3, S, "5", "begin") + fwd(S) + note("G", 3, S, "5", "continue"))
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]], stitch="chains")
    assert len({v for _, _, v in beam_voices(root)}) == 1
    assert stats.stitched_groups == 1


def test_chains_leave_a_beam_on_one_staff_and_a_group_on_each_staff_alone():
    rh = part(
        "P0",
        RH
        + note("C", 5, S, "1", "begin")
        + note("D", 5, S, "1", "continue")
        + note("E", 5, S, "1", "end")
        + fwd(S),
    )
    lh = part("P1", LH + note("C", 3, S, "5", "begin") + note("D", 3, S, "5", "end") + fwd(2 * S))
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]], stitch="chains")
    assert {(s, v) for s, _, v in beam_voices(root)} == {("1", "1"), ("2", "5")}
    assert stats.stitched_groups == 0 and stats.skipped_measures == 0


def test_chains_take_the_stream_before_the_other_staff_when_two_beams_end_together():
    # the beam of each staff ends at the same moment: every note goes on in its own stream, nothing crosses
    rh = part("P0", RH + note("C", 5, S, "1", "begin") + note("D", 5, S, "1", "end") + fwd(2 * S))
    lh = part("P1", LH + note("C", 3, S, "5", "begin") + note("D", 3, S, "5", "end") + fwd(2 * S))
    root = score(rh, lh)
    F.fuse(root, [[0, 1]], stitch="chains")
    assert [(s, v) for s, _, v in beam_voices(root)] == [
        ("1", "1"),
        ("1", "1"),
        ("2", "5"),
        ("2", "5"),
    ]


def test_chains_try_the_orders_of_notes_which_start_together():
    # two beams begin together; at the end the left hand's note carries another voice than its begin, and the right hand's note
    # ends where the left hand's beam is open: taken in the order staff 1, staff 2 the left-hand note has no beam to go on in
    rh = part(
        "P0", RH + note("F", 6, S, "1", "begin") + fwd(S) + note("D", 4, S, "1", "end") + fwd(S)
    )
    lh = part(
        "P1", LH + note("F", 4, S, "6", "begin") + fwd(S) + note("F", 3, S, "5", "end") + fwd(S)
    )
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]], stitch="chains")
    voices = {(s, p): v for s, p, v in beam_voices(root)}
    assert (
        voices[("1", "F6")] == voices[("2", "F3")] == "1"
    )  # right-hand beam ends in the left hand
    assert (
        voices[("2", "F4")] == voices[("1", "D4")] == "6"
    )  # left-hand beam ends in the right hand
    assert stats.stitched_groups == 2 and stats.skipped_measures == 0


def test_a_measure_whose_states_do_not_form_complete_beams_is_left_to_the_run_rule():
    # a lone continue with no beam to continue: the voices are not the positions of the model, no chain is trusted
    rh = part(
        "P0", RH + note("C", 4, S, "1", "continue") + note("E", 4, S, "1", "end") + fwd(2 * S)
    )
    lh = part("P1", LH + note("A", 3, S, "5", "begin") + note("A", 3, S, "5", "end") + fwd(2 * S))
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]], stitch="chains")
    assert stats.skipped_measures == 1 and stats.stitched_groups == 0
    assert {(s, v) for s, _, v in beam_voices(root)} == {("1", "1"), ("2", "5")}


def test_two_chords_of_one_beam_cannot_start_together():
    # the right-hand note at S could join the left-hand beam, but the left hand's own next note starts at S as well: the
    # streams (staff, voice) are then not the positions of the model, so the measure is not read as a chain
    rh = part("P0", RH + fwd(S) + note("C", 4, S, "1", "continue") + fwd(2 * S))
    lh = part(
        "P1",
        LH
        + note("A", 3, S, "5", "begin")
        + note("B", 3, S, "5", "continue")
        + note("C", 3, S, "5", "continue")
        + note("D", 3, S, "5", "end"),
    )
    root = score(rh, lh)
    stats = F.fuse(root, [[0, 1]], stitch="chains")
    assert stats.stitched_groups == 0 and stats.skipped_measures == 1


def _notes_without_voices(root):
    return sorted(
        (
            n.findtext("staff"),
            n.find("pitch").findtext("step") if n.find("pitch") is not None else "rest",
            n.findtext("duration"),
        )
        for n in root.iter("note")
    )


def test_chains_keep_every_note_and_only_change_voices():
    before, after = aba_beam(), aba_beam()
    F.fuse(before, [[0, 1]])
    F.fuse(after, [[0, 1]], stitch="chains")
    assert _notes_without_voices(before) == _notes_without_voices(after)
