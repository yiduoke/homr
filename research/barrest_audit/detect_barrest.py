#!/usr/bin/env python3
"""
Detector for the typeless bar-rest label bug (D27).

Bug: a MusicXML rest without <type> and without measure="yes" (MuseScore bar rest of older
exports) is converted by training/omr_datasets/music_xml_parser.py to `rest_8`, whatever the bar.

Detector on token files (one staff image = one file, one line per time step, symbols joined by
'&', fields: rhythm pitch lift articulation slur position):

  * a measure is the run of lines between two barline-like lines (rhythm contains "barline" or
    starts with "repeat"); the staff's last measure needs no closing barline;
  * a track is one position tag (upper, upper2, lower, lower2): chords of one line count once;
  * bar length: the last timeSignature_* token at or before the measure (meter), else INFERRED as
    the most frequent longest-track total of the measures of the staff that hold at least one
    note (needs 2 agreeing measures, or all measures agree), else UNKNOWN;
  * a PRIMARY track (upper, lower) that holds only rest tokens (rest_N, no grace) in the measure:
        bug_rest8      the track is one rest_8 and the bar is longer than an eighth (the typeless
                       rest signature); an unknown bar length is counted as unknown_rest8
        allrest_short  every track of the measure is rest-only and none fills the bar (e.g.
                       rest_16 + rest_4 in 4/4), also when the staff has only such bars
        other_short    any other rest-only primary track shorter than the bar: informational,
                       mostly legitimate (voice 1 rests while a second voice carries the bar)
        over           longer than the bar (the bar-rest fallback rest_1 in 3/2 is not counted)
    A primary track that starts after the first time step of the bar while a second voice of the
    staff (upper2, lower2) has notes is skipped (a real rest in voice 1). A short measure (pickup / split bar: the track is as long as the longest track, which holds
    a note) and a single typed bar-rest token the converter writes for this bar length are never
    flagged. susp_bars = bars with bug_rest8 or allrest_short.

Usage:
    detect_barrest.py LIST [LIST ...] --out out.tsv
LIST lines are `image,tokens` or just `tokens`. Output: one TSV row per staff.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from fractions import Fraction

BARLINE = re.compile(r"barline|^repeat|^newline")
NOTE_REST = re.compile(r"^(note|rest)_(\d+)(G?)(\.{0,2})$")
MULTIREST = re.compile(r"^rest_(\d+)m$")
PRIMARY = ("upper", "lower")


def duration(rhythm: str) -> tuple[bool, bool, Fraction | None]:
    """(is_rest, is_note, duration as a fraction of a whole note; None for a grace note)."""
    m = NOTE_REST.match(rhythm)
    if not m:
        return (False, False, None)
    kind, num, grace, dots = m.groups()
    is_rest = kind == "rest"
    if grace:
        return (is_rest, not is_rest, None)
    n = int(num)
    base = Fraction(2) if n == 0 else Fraction(1, n)
    dur = base
    add = base
    for _ in dots:
        add /= 2
        dur += add
    return (is_rest, not is_rest, dur)


def meter_of(rhythm: str) -> Fraction | None:
    if not rhythm.startswith("timeSignature_"):
        return None
    sig = rhythm[len("timeSignature_"):]
    if sig in ("common", "cut"):
        return Fraction(1)
    m = re.match(r"^(\d+)/(\d+)$", sig)
    if not m:
        return None
    return Fraction(int(m.group(1)), int(m.group(2)))


def parse_staff(text: str) -> list[dict]:
    """Measures of one token file: dict(tracks {tag: [(is_rest, dur, token)]}, meter, multirest)."""
    measures: list[dict] = []
    state = {"meter": None}

    def new() -> dict:
        return {"tracks": {}, "meter": state["meter"], "multirest": False, "kinds": 0, "lines": 0, "text": []}

    cur = new()
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        seen_track: set[str] = set()
        barline = False
        content_line = False
        for sym in line.split("&"):
            fields = sym.split()
            if not fields:
                continue
            rhythm = fields[0]
            pos = fields[-1]
            if BARLINE.search(rhythm):
                barline = True
                continue
            m = meter_of(rhythm)
            if m is not None:
                state["meter"] = m
                cur["meter"] = m
                continue
            if MULTIREST.match(rhythm):
                cur["multirest"] = True
                cur["kinds"] += 1
                continue
            is_rest, is_note, dur = duration(rhythm)
            if not (is_rest or is_note):
                continue
            cur["kinds"] += 1
            content_line = True
            if dur is None:  # grace
                continue
            if pos in seen_track:  # chord: same duration, count once
                continue
            seen_track.add(pos)
            cur["tracks"].setdefault(pos, []).append((is_rest, dur, rhythm, cur["lines"]))
        if content_line:
            cur["lines"] += 1
        if not barline:
            cur["text"].append(line)
        if barline:
            if cur["kinds"] > 0:
                measures.append(cur)
            cur = new()
    if cur["kinds"] > 0:
        measures.append(cur)
    return measures


def infer_bar(measures: list[dict]) -> Fraction | None:
    totals = []
    for ms in measures:
        if ms["multirest"] or not ms["tracks"]:
            continue
        has_note = any(not r for tr in ms["tracks"].values() for (r, _, _, _) in tr)
        if not has_note:
            continue
        totals.append(max(sum(d for (_, d, _, _) in tr) for tr in ms["tracks"].values()))
    if not totals:
        return None
    val, cnt = Counter(totals).most_common(1)[0]
    if cnt >= 2 or len(set(totals)) == 1:
        return val
    return None


def expected_bar_rest(bar: Fraction) -> str:
    """The token the converter writes for a rest with measure="yes" (_measure_rest_rhythm)."""
    quarters = bar * 4
    for q, tok in ((4, "rest_1"), (3, "rest_2."), (2, "rest_2"), (Fraction(3, 2), "rest_4."),
                   (1, "rest_4"), (Fraction(3, 4), "rest_8."), (Fraction(1, 2), "rest_8")):
        if quarters == q:
            return tok
    return "rest_1"


def _tracks(tracks: dict) -> str:
    return "|".join(t + "=" + "+".join(x[2] for x in tr) for t, tr in sorted(tracks.items()))


def analyse(text: str) -> dict:
    measures = parse_staff(text)
    inferred = infer_bar(measures)
    res = {
        "bars": 0,
        "bars_meter_known": 0,
        "bars_inferred": 0,
        "bars_unknown": 0,
        "susp_bars": 0,        # bars with a bug_rest8 track or a short all-rest bar
        "bug_rest8": 0,        # tracks: primary track = one rest_8, bar longer than an eighth
        "allrest_short": 0,    # bars: every track rest-only and no track fills the bar
        "unknown_rest8": 0,    # tracks: one rest_8 only, bar length unknown (no meter, no notes)
        "other_short": 0,      # tracks: other rest-only primary tracks shorter than the bar
        "over": 0,             # rest-only primary tracks longer than the bar (not a bar rest token)
        "all_rest_bars": 0,
        "examples": [],
        "details": [],         # (bar index, bars in staff, kind, tracks, bar length, basis)
    }
    for idx, ms in enumerate(measures):
        if ms["multirest"] or not ms["tracks"]:
            continue
        res["bars"] += 1
        bar = ms["meter"]
        basis = "meter_known"
        if bar is None:
            bar = inferred
            basis = "inferred"
        if bar is None:
            basis = "unknown"
        res["bars_" + basis] += 1
        tracks = ms["tracks"]
        sums = {t: sum(d for (_, d, _, _) in tr) for t, tr in tracks.items()}
        longest = max(sums.values())
        all_rest = all(all(r for (r, _, _, _) in tr) for tr in tracks.values())
        if all_rest:
            res["all_rest_bars"] += 1
        flagged = False
        for tag in PRIMARY:
            tr = tracks.get(tag)
            if not tr or not all(r for (r, _, _, _) in tr):
                continue
            tot = sums[tag]
            # another voice of the same staff (upper2, lower2) carries notes: a rest of voice 1
            # that starts after the first time step of the bar is a real rest, not a bar rest
            if tr[0][3] != 0 and any(
                t != tag and t.rstrip("0123456789") == tag
                and any(not r for (r, _, _, _) in tracks[t]) for t in tracks
            ):
                continue
            single_rest8 = len(tr) == 1 and tr[0][2] == "rest_8"
            if bar is None:
                if single_rest8:
                    res["unknown_rest8"] += 1
                    if len(res["examples"]) < 3:
                        res["examples"].append(f"bar{idx}:{tag}:unknown_rest8")
                continue
            if tot == bar:
                continue
            if tot > bar:
                res["over"] += 1
                continue
            # shorter than the bar: skip a short measure (pickup, split bar) where this track is
            # as long as the longest track and some track holds a note
            if not all_rest and tot >= longest:
                continue
            if len(tr) == 1 and tr[0][2] == expected_bar_rest(bar):
                continue  # a typed bar rest the converter writes for a bar it has no token for
            if single_rest8:
                res["bug_rest8"] += 1
                flagged = True
                res["details"].append((idx, len(measures), "bug_rest8", _tracks(tracks), str(bar), basis))
                if len(res["examples"]) < 3:
                    res["examples"].append(f"bar{idx}:{tag}:rest_8:bar={bar}({basis})")
            else:
                res["other_short"] += 1
        if all_rest and bar is not None and longest < bar and not flagged:
            if not (len(tracks) and all(len(tr) == 1 and tr[0][2] == expected_bar_rest(bar)
                                        for tr in tracks.values())):
                res["allrest_short"] += 1
                flagged = True
                res["details"].append((idx, len(measures), "allrest_short", _tracks(tracks), str(bar), basis))
                if len(res["examples"]) < 3:
                    res["examples"].append(
                        f"bar{idx}:allrest:{'|'.join(t + '=' + '+'.join(x[2] for x in tr) for t, tr in tracks.items())}:bar={bar}({basis})"
                    )
        if flagged:
            res["susp_bars"] += 1
    return res


COLS = ["bars", "bars_meter_known", "bars_inferred", "bars_unknown", "susp_bars", "bug_rest8",
        "allrest_short", "unknown_rest8", "other_short", "over", "all_rest_bars"]


def source_of(path: str) -> str:
    """Source dataset of a list line (image or token path)."""
    p = path
    for key, name in (
        ("datasets/pdmx/hard/", "pdmx_hard"),
        ("datasets/pdmx/", "pdmx"),
        ("lilypond", "lilypond"),
        ("Lieder-main", "lieder"),
        ("musescore_octave", "musescore_octave"),
        ("grandstaff", "grandstaff"),
        ("/asap/", "asap"),
        ("kern_scriabin", "scriabin"),
        ("meters/", "meter_arm"),
        ("scans/crops", "kern_scans"),
        ("scan_pairs_virtuoso", "scan_pairs"),
    ):
        if key in p:
            return name
    return "other"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("lists", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--source", default=None, help="force the source name")
    ap.add_argument("--details", default=None, help="TSV with one row per flagged bar")
    args = ap.parse_args()
    det = open(args.details, "w") if args.details else None
    if det:
        det.write("source\ttokens\tbar\tbars_in_staff\tkind\ttracks\tbar_length\tbasis\n")
    with open(args.out, "w") as out:
        out.write("list\tsource\ttokens\t" + "\t".join(COLS) + "\texamples\n")
        for lst in args.lists:
            tag = lst.rsplit("/", 1)[-1]
            for line in open(lst):
                line = line.strip()
                if not line:
                    continue
                img, _, tok = line.partition(",")
                tok = tok or img
                try:
                    text = open(tok).read()
                except OSError as e:
                    print("missing", tok, e, file=sys.stderr)
                    continue
                r = analyse(text)
                src = args.source or source_of(img + " " + tok)
                if det:
                    for d in r["details"]:
                        det.write(f"{src}\t{tok}\t" + "\t".join(str(x) for x in d) + "\n")
                out.write(
                    f"{tag}\t{src}\t{tok}\t" + "\t".join(str(r[c]) for c in COLS)
                    + "\t" + ";".join(r["examples"]) + "\n"
                )


if __name__ == "__main__":
    main()
