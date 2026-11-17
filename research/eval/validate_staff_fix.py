"""Check that a staff-corrected reference only changed staff numbers.

usage: validate_staff_fix.py ORIGINAL.musicxml CORRECTED.musicxml [--allow-missing-staves 1,2]

Checks: both parse; <staves> equals the highest staff used; every <staff>/<clef number> is in range;
per measure, the multiset of notes (voice, pitch or rest, duration, type, chord, grace) is the same
as in the original (apart from notes of the staves named in --allow-missing-staves, which were moved
to another file); per measure and voice, the summed duration of the non-chord notes is the same as
in the original; the onset of every kept note is unchanged. Also lists the measures where a voice
does not fill the bar in the original (so they are not blamed on the correction).
"""

from __future__ import annotations

import argparse
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from fractions import Fraction


def note_key(n: ET.Element) -> tuple:
    pitch = n.find("pitch")
    if pitch is not None:
        p = (pitch.findtext("step"), pitch.findtext("alter") or "0", pitch.findtext("octave"))
    else:
        p = ("rest",) if n.find("rest") is not None else ("?",)
    return (
        n.findtext("voice"),
        p,
        n.findtext("duration"),
        n.findtext("type"),
        n.find("chord") is not None,
        n.find("grace") is not None,
    )


def read(path: str):
    """Return per measure: list of (staff, key, onset) and per-voice sums, plus meta."""
    tree = ET.parse(path)
    root = tree.getroot()
    out = []
    divisions = None
    beats = beat_type = None
    for part in root.findall("part"):
        for m in part.findall("measure"):
            cursor = 0
            last_start = 0
            notes = []
            voice_sum: Counter = Counter()
            for e in m:
                a = e if e.tag == "attributes" else None
                if a is not None:
                    if a.findtext("divisions"):
                        divisions = int(a.findtext("divisions"))
                    t = a.find("time")
                    if t is not None:
                        beats, beat_type = int(t.findtext("beats").split("+")[0]), int(
                            t.findtext("beat-type")
                        )
                        beats_full = t.findtext("beats")
                        if "+" in beats_full:
                            beats = sum(int(x) for x in beats_full.split("+"))
                if e.tag == "note":
                    d = int(e.findtext("duration") or 0)
                    chord = e.find("chord") is not None
                    start = last_start if chord else cursor
                    notes.append((e.findtext("staff"), note_key(e), start))
                    if not chord:
                        last_start = cursor
                        cursor += d
                        voice_sum[e.findtext("voice")] += d
                elif e.tag == "backup":
                    cursor -= int(e.findtext("duration"))
                elif e.tag == "forward":
                    cursor += int(e.findtext("duration"))
            bar = Fraction(divisions * 4 * beats, beat_type) if divisions and beats else None
            out.append((m.get("number"), notes, voice_sum, bar))
    return root, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("original")
    ap.add_argument("corrected")
    ap.add_argument("--allow-missing-staves", default="")
    args = ap.parse_args()
    missing = set(filter(None, args.allow_missing_staves.split(",")))
    root_o, orig = read(args.original)
    root_c, corr = read(args.corrected)
    problems = []
    if len(orig) != len(corr):
        problems.append(f"measure count {len(orig)} -> {len(corr)}")
    n_o = n_c = p_o = p_c = 0
    for (num, no, vo, bar), (num2, nc, vc, _) in zip(orig, corr):
        kept_o = [x for x in no if x[0] not in missing]
        n_o += len(no)
        n_c += len(nc)
        p_o += sum(1 for x in no if x[1][1][0] != "rest")
        p_c += sum(1 for x in nc if x[1][1][0] != "rest")
        a = Counter((x[1], x[2]) for x in kept_o)
        b = Counter((x[1], x[2]) for x in nc)
        if a != b:
            problems.append(f"bar {num}: notes or onsets differ")
        sums_o = Counter()
        for v in {x[1][0] for x in kept_o}:
            sums_o[v] = sum(
                int(x[1][2] or 0) for x in kept_o if x[1][0] == v and not x[1][4]
            )
        sums_c = Counter()
        for v in {x[1][0] for x in nc}:
            sums_c[v] = sum(int(x[1][2] or 0) for x in nc if x[1][0] == v and not x[1][4])
        if +sums_o != +sums_c:
            problems.append(f"bar {num}: voice sums differ {dict(sums_o)} vs {dict(sums_c)}")
    # staff ranges
    staves_tags = [int(s.text) for s in root_c.iter("staves")]
    used = [int(s.text) for e in root_c.iter() if e.tag in ("note", "direction", "forward")
            for s in e.findall("staff")]
    top = max(used)
    if staves_tags and max(staves_tags) != top:
        problems.append(f"<staves> {max(staves_tags)} but highest staff used {top}")
    for c in root_c.iter("clef"):
        if int(c.get("number", "1")) > top:
            problems.append("clef number beyond staves")
            break
    for sl in root_c.iter("staff-layout"):
        if int(sl.get("number", "1")) > top:
            problems.append("staff-layout beyond staves")
            break
    print(f"notes (incl. rests) original {n_o} (of which moved elsewhere: "
          f"{sum(1 for _, no, _, _ in orig for x in no if x[0] in missing)}), corrected {n_c}; "
          f"pitched original {p_o}, corrected {p_c}")
    # bars where a voice does not fill the bar in the original
    short = []
    for num, no, vo, bar in orig:
        for v, s in vo.items():
            if bar and s != bar and s != 0:
                short.append((num, v, s, int(bar)))
    print(f"voices not filling the bar in the original: {len(short)} (first {short[:5]})")
    if problems:
        print("PROBLEMS:")
        for p in problems[:30]:
            print("  ", p)
        return 1
    print("OK: every kept note, onset and per-voice duration sum is unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
