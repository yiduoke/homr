"""Tests of the slot tracker (slot_tracking.py) and of merge_pages.py with synthetic page sets.

The synthetic pages are written like homr writes them: a part with one staff is called 'Voice' (here 'P<n>'), a part with two staves
('<staves>2</staves>') becomes 'P<n>-Staff1' and 'P<n>-Staff2' in music21. Each bar holds four quarter notes (a staff needs eight notes on a page before its register counts); the pitch tells the register of the
staff (T0 = C6, T1 = C5, B = C3, B2 = C2) and the octave stays the same on every page, so a note which lands in the wrong slot shows up as
a wrong octave in that part. No real score and no piece is involved.

run: poetry run pytest run/merge2_wt/tests  (or .venv/bin/python -m pytest run/merge2_wt/tests)
"""
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))
from slot_tracking import SlotTracker, StaffProfile  # noqa: E402

PY = sys.executable
# MERGER=/path/to/merge_pages.py runs the same page sets through another merger (the D24 merger fails the 2/3/4-staff tests)
MERGER = os.environ.get("MERGER", str(ROOT / "merge_pages.py"))
CENTRE = {"T0": ("G", "C", 6), "T1": ("G", "C", 5), "B": ("F", "C", 3), "B2": ("F", "C", 2)}


def midi(role: str) -> int:
    return {"T0": 84, "T1": 72, "B": 48, "B2": 36}[role]


def part_xml(part_id: str, roles: list[str], bars: int, step: str) -> str:
    """One MusicXML part with len(roles) staves, `bars` bars of 4/4, four quarter notes per staff and bar."""
    n = len(roles)
    measures = []
    for b in range(bars):
        attrs = ""
        if b == 0:
            clefs = "".join(f'<clef number="{i + 1}"><sign>{CENTRE[r][0]}</sign><line>{2 if CENTRE[r][0] == "G" else 4}</line></clef>' for i, r in enumerate(roles))
            attrs = f"<attributes><divisions>1</divisions><key><fifths>0</fifths></key><time><beats>4</beats><beat-type>4</beat-type></time>"
            attrs += (f"<staves>{n}</staves>" if n > 1 else "") + clefs + "</attributes>"
        body = ""
        for i, r in enumerate(roles):
            if i:
                body += "<backup><duration>4</duration></backup>"
            body += "".join(
                f'<note><pitch><step>{step}</step><octave>{CENTRE[r][2]}</octave></pitch><duration>1</duration><type>quarter</type>'
                f'<voice>{i + 1}</voice><staff>{i + 1}</staff></note>'
                for _ in range(4)
            )
        measures.append(f'<measure number="{b + 1}">{attrs}{body}</measure>')
    return f'<part id="{part_id}">' + "".join(measures) + "</part>"


def write_page(path: Path, parts: list[tuple[str, list[str]]], bars: int, step: str) -> None:
    """parts: [(part id, roles of its staves from the top)]."""
    score_parts = "".join(f'<score-part id="{pid}"><part-name>Voice</part-name></score-part>' for pid, _ in parts)
    body = "".join(part_xml(pid, roles, bars, step) for pid, roles in parts)
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?><score-partwise version="4.0"><part-list>{score_parts}</part-list>{body}</score-partwise>')


def write_set(folder: Path, pages: list[dict]) -> Path:
    """pages: dicts with parts (see write_page), bars, step. Returns the folder."""
    folder.mkdir(parents=True, exist_ok=True)
    for i, page in enumerate(pages, start=1):
        write_page(folder / f"page-{i:02d}.musicxml", page["parts"], page["bars"], page.get("step", "C"))
    return folder


def merge(folder: Path, out: Path, keep_minor: bool = True) -> list[list[list[tuple[str, int]]]]:
    """Run merge_pages.py on a folder; returns, per part, per bar, the (step, octave) of its notes (a rest is an empty list)."""
    env = {**os.environ, "HOMR_PAGES": str(folder), "HOMR_OUT": str(out), "HOMR_TRUST_PAGE_TIME": "1"}
    if keep_minor:
        env["HOMR_KEEP_MINOR_PARTS"] = "1"
    result = subprocess.run([PY, MERGER], env=env, capture_output=True, text=True, cwd=str(HERE.parent))
    assert result.returncode == 0, result.stderr[-2000:]
    root = ET.parse(f"{out}.musicxml").getroot()
    parts = []
    for part in root.findall("part"):
        bars = []
        for measure in part.findall("measure"):
            bars.append([(n.findtext("pitch/step"), int(n.findtext("pitch/octave"))) for n in measure.findall("note") if n.find("pitch") is not None])
        parts.append(bars)
    return parts


def octaves(part: list[list[tuple[str, int]]]) -> list[set[int]]:
    return [{o for _, o in bar} for bar in part]


# ---------------------------------------------------------------- tracker, no files


def profile(role: str, notes: int = 40) -> StaffProfile:
    return StaffProfile(CENTRE[role][0], Counter({midi(role): notes}))


def track(pages: list[list[str]]) -> tuple[list[list[int]], int]:
    tracker = SlotTracker()
    slots_of_page = []
    for roles in pages:
        result = tracker.assign([profile(r) for r in roles], [f"k{i}" for i in range(len(roles))])
        order = {id(s): n for n, s in enumerate(tracker.slots)}
        slots_of_page.append([order[id(s)] for s, _ in result])
    return slots_of_page, len(tracker.slots)


def test_same_stack_keeps_roles():
    slots, k = track([["T0", "B"], ["T0", "B"], ["T0", "B"]])
    assert slots == [[0, 1]] * 3 and k == 2


def test_three_staff_page_after_two_adds_middle_slot():
    slots, k = track([["T0", "B"], ["T0", "T1", "B"], ["T0", "B"]])
    assert k == 3
    assert slots[1] == [0, 1, 2]
    assert slots[2] == [0, 2]  # the two-staff page leaves the middle slot empty


def test_four_staff_page_adds_a_slot_and_lower_pages_keep_theirs():
    slots, k = track([["T0", "T1", "B"], ["T0", "T1", "B", "B2"], ["T0", "T1", "B"], ["T0", "B"], ["T1", "B"]])
    assert k == 4
    assert slots[1] == [0, 1, 2, 3]
    assert slots[2] == [0, 1, 2]
    assert slots[3] == [0, 2]
    assert slots[4] == [1, 2]  # a page of the lower two staves lands on the lower two slots


def test_first_page_with_more_staves_than_later_ones():
    slots, k = track([["T0", "T1", "B", "B2"], ["T0", "B"], ["T1", "B2"]])
    assert k == 4
    assert slots == [[0, 1, 2, 3], [0, 2], [1, 3]]


def test_page_never_opens_a_slot_unless_it_has_more_staves():
    slots, k = track([["T0", "T1", "B"], ["T0", "B"], ["T1"], ["B"]])
    assert k == 3
    assert slots == [[0, 1, 2], [0, 2], [1], [2]]


def test_surplus_staff_is_placed_by_register_among_skipped_slots():
    # slots T0 B; a page [T0 T1 B] opens a middle slot, the next page [T0 T1] must not move B
    slots, k = track([["T0", "B"], ["T0", "T1", "B"], ["T0", "T1"]])
    assert slots == [[0, 1], [0, 1, 2], [0, 1]]


def test_staff_without_notes_follows_its_clef():
    tracker = SlotTracker()
    tracker.assign([profile("T0"), profile("B")], ["a", "b"])
    result = tracker.assign([StaffProfile("F", Counter())], ["x"])  # an empty bass staff
    assert result[0][0].key == "b"


# ---------------------------------------------------------------- merge_pages.py on synthetic pages


def test_regular_two_staff_piece_is_unchanged(tmp_path):
    """Pages which are all one grand staff: two parts, every bar in place (the behaviour of the D24 merger)."""
    pages = [{"parts": [("P1", ["T0", "B"])], "bars": 3, "step": s} for s in "CDE"]
    parts = merge(write_set(tmp_path / "p", pages), tmp_path / "o")
    assert len(parts) == 2 and [len(p) for p in parts] == [9, 9]
    assert all(o == {6} for o in octaves(parts[0])) and all(o == {3} for o in octaves(parts[1]))


def test_two_three_and_four_staves_per_system_give_fixed_parts(tmp_path):
    """Pages with 2, 3 and 4 staves: every slot has one bar per bar of the piece; each note sits in the slot of its register."""
    pages = [
        {"parts": [("P1", ["T0", "B"])], "bars": 2, "step": "C"},
        {"parts": [("P1", ["T0", "T1"]), ("P2", ["B"])], "bars": 3, "step": "D"},  # three staves, paired 0-1
        {"parts": [("P1", ["T0"]), ("P2", ["T1", "B"])], "bars": 2, "step": "E"},  # same staves, paired 1-2
        {"parts": [("P1", ["T0", "T1"]), ("P2", ["B", "B2"])], "bars": 2, "step": "F"},  # four staves
        {"parts": [("P1", ["T0", "B"])], "bars": 2, "step": "G"},
    ]
    parts = merge(write_set(tmp_path / "p", pages), tmp_path / "o")
    assert len(parts) == 4
    assert [len(p) for p in parts] == [11] * 4
    by_octave = [octaves(p) for p in parts]
    # slot 0 = T0 (octave 6) in every bar that has a staff there; empty bars are rests
    assert all(o <= {6} for o in by_octave[0])
    assert all(o <= {5} for o in by_octave[1])
    assert all(o <= {3} for o in by_octave[2])
    assert all(o <= {2} for o in by_octave[3])
    # the bars of the three-staff pages (bars 3-5 and 6-7) hold notes in slots 0,1,2; the four-staff pages (8-9) in all four
    assert [bool(o) for o in by_octave[1]] == [False, False, True, True, True, True, True, True, True, False, False]
    assert [bool(o) for o in by_octave[3]] == [False] * 7 + [True, True, False, False]


def test_half_paired_pages_land_in_the_same_slots(tmp_path):
    """The same three staves written once as grand+single and once as single+grand are the same three parts (not five)."""
    pages = []
    for i, step in enumerate("CDEFGAB"):
        parts = [("P1", ["T0", "T1"]), ("P2", ["B"])] if i % 2 == 0 else [("P1", ["T0"]), ("P2", ["T1", "B"])]
        pages.append({"parts": parts, "bars": 2, "step": step})
    out = merge(write_set(tmp_path / "p", pages), tmp_path / "o")
    assert len(out) == 3 and [len(p) for p in out] == [14] * 3
    for part, octave in zip(out, (6, 5, 3)):
        assert all(o == {octave} for o in octaves(part))


def test_voice_pages_and_grand_pages_continue_each_other(tmp_path):
    pages = [
        {"parts": [("P1", ["T0"]), ("P2", ["B"])], "bars": 2, "step": "C"},  # two parts, as 'Voice', 'Voice'
        {"parts": [("P1", ["T0", "B"])], "bars": 2, "step": "D"},  # one grand part
    ]
    out = merge(write_set(tmp_path / "p", pages), tmp_path / "o")
    assert len(out) == 2 and [len(p) for p in out] == [4, 4]


def test_a_page_with_a_missing_staff_bar_is_padded_to_its_longest_staff(tmp_path):
    pages = [
        {"parts": [("P1", ["T0"]), ("P2", ["T1"]), ("P3", ["B"])], "bars": 3, "step": "C"},
        {"parts": [("P1", ["T0", "T1"]), ("P2", ["B"])], "bars": 3, "step": "D"},
    ]
    folder = write_set(tmp_path / "p", pages)
    # cut one bar of the single part of page 2: the staff has lost a bar
    text = (folder / "page-02.musicxml").read_text()
    text = re.sub(r'(<part id="P2">.*)<measure number="3">.*?</measure>', r"\1", text, flags=re.S)
    (folder / "page-02.musicxml").write_text(text)
    out = merge(folder, tmp_path / "o")
    assert [len(p) for p in out] == [6, 6, 6]


def test_late_new_slot_gets_rests_for_the_earlier_pages(tmp_path):
    pages = [
        {"parts": [("P1", ["T0", "B"])], "bars": 2, "step": "C"},
        {"parts": [("P1", ["T0", "T1", "B"])], "bars": 2, "step": "D"},
    ]
    out = merge(write_set(tmp_path / "p", pages), tmp_path / "o")
    assert [len(p) for p in out] == [4, 4, 4]
    assert octaves(out[1]) == [set(), set(), {5}, {5}]


def test_minor_part_rule_counts_staves_not_fill(tmp_path):
    """A slot which exists on one page of ten is an ossia: dropped (as before); the fill rests do not make it a part of the piece."""
    pages = [{"parts": [("P1", ["T0", "B"])], "bars": 2, "step": "C"} for _ in range(9)]
    pages.append({"parts": [("P1", ["T0", "T1", "B"])], "bars": 2, "step": "D"})
    out = merge(write_set(tmp_path / "p", pages), tmp_path / "o", keep_minor=False)
    assert len(out) == 2


def test_ambiguous_surplus_pair_keeps_the_top_pair_on_the_slots():
    """Two grand pairs of similar range on one page: the stack is read from the top, so the first pair continues the slots."""
    tracker = SlotTracker()
    tracker.assign([StaffProfile("G", Counter({70: 50})), StaffProfile("F", Counter({57: 50}))], ["a", "b"])
    result = tracker.assign([StaffProfile("G", Counter({70: 50})), StaffProfile("F", Counter({54: 50})),
                             StaffProfile("G", Counter({69: 50})), StaffProfile("F", Counter({56: 50}))], ["c", "d", "e", "f"])
    assert [(s.key, new) for s, new in result] == [("a", False), ("b", False), ("e", True), ("f", True)]


def test_small_staff_above_a_piano_page_opens_its_own_slot():
    """A page whose first staff is an extra small staff (higher than the piano staves): the piano staves keep their slots."""
    tracker = SlotTracker()
    tracker.assign([StaffProfile("G", Counter({71: 50})), StaffProfile("F", Counter({52: 50}))], ["a", "b"])
    result = tracker.assign([StaffProfile("G", Counter({80: 50})), StaffProfile("G", Counter({68: 50})), StaffProfile("F", Counter({45: 50}))], ["x", "y", "z"])
    assert [(s.key, new) for s, new in result] == [("x", True), ("a", False), ("b", False)]
    assert [s.key for s in tracker.slots] == ["x", "a", "b"]


def test_a_few_pages_with_extra_staves_do_not_split_the_piece():
    """Ordinary two-staff pages, a spurious three- and four-staff page, then ordinary pages again: the staves keep their slots."""
    tracker = SlotTracker()
    pages = [["T0", "B"]] * 4 + [["T0", "T1", "B"], ["T0", "T1", "B", "B2"]] + [["T0", "B"]] * 6
    used = []
    for roles in pages:
        result = tracker.assign([profile(r) for r in roles], [f"k{i}" for i in range(len(roles))])
        used.append([slot.key for slot, _ in result])
    first_top, first_bass = used[0]
    assert all(u == [first_top, first_bass] for u in used[:4] + used[6:])
    assert len(tracker.slots) == 4


def test_established_slot_is_used_again_by_a_page_with_fewer_staves():
    slots, k = track([["T0", "T1", "B"]] * 5 + [["T0", "B"]] + [["T0", "T1", "B"]] * 2)
    assert slots[5] == [0, 2] and slots[-1] == [0, 1, 2] and k == 3
