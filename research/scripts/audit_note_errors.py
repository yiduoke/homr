"""Error taxonomy for homr upstream-566 MusicXML output vs reference.

Run: /Users/yiduoke/Documents/homr/.venv/bin/python -B audit_homr.py
Writes audit_results.json next to this script and prints tables.
Reads only; writes run/out/compare/note-error-audit.json.
"""
import glob
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

SCORER_DIR = "/Users/yiduoke/Documents/homr/run/octave_wt"
sys.path.insert(0, SCORER_DIR)
from validation.score_notes import Measure, Note, Score, align_measures  # noqa: E402

OUT_DIR = Path("/Users/yiduoke/Documents/homr/run/out/compare")
TOL = 1 / 96
SEM = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
LETTERS = "CDEFGAB"
UP = "/private/tmp/claude-501/upstream"
REF = "/Users/yiduoke/Documents/homr/run/out/compare"
PIECES = {
    "mazeppa": {
        "ref": f"{REF}/mazeppa/mazeppa-reference.musicxml",
        "merged": f"{REF}/mazeppa/mazeppa-upstream566.musicxml",
        "pages": sorted(p for p in glob.glob(f"{REF}/mazeppa/pages-upstream566/page-*.musicxml") if "teaser" not in p),
        "saved": f"{REF}/mazeppa/note-scores.json",
    },
    "la-campanella": {
        "ref": f"{REF}/la-campanella/la-campanella-reference.musicxml",
        "merged": f"{REF}/la-campanella/la-campanella-upstream566.musicxml",
        "pages": sorted(p for p in glob.glob(f"{REF}/la-campanella/pages-upstream566/page-*.musicxml") if "teaser" not in p),
        "saved": f"{REF}/la-campanella/note-scores.json",
    },
}


def parse_file(path):
    """Return (parts_measures, staves). Each part: list of measures dict(number, notes, end)."""
    root = ET.parse(path).getroot()
    for el in root.iter():
        el.tag = el.tag.rsplit("}", 1)[-1]
    parts, offset = [], 0
    for part in root.findall("part"):
        divisions = 1
        staves = 1
        measures = []
        for m in part.findall("measure"):
            cursor = 0.0
            end = 0.0
            last_start = 0.0
            notes = []
            for el in m:
                if el.tag == "attributes":
                    if el.findtext("divisions"):
                        divisions = float(el.findtext("divisions"))
                    if el.findtext("staves"):
                        staves = int(el.findtext("staves"))
                elif el.tag == "backup":
                    cursor -= float(el.findtext("duration"))
                elif el.tag == "forward":
                    cursor += float(el.findtext("duration"))
                elif el.tag == "note":
                    dur = float(el.findtext("duration") or 0) / divisions
                    is_chord = el.find("chord") is not None
                    is_grace = el.find("grace") is not None
                    if el.find("rest") is not None:
                        if not is_chord and not is_grace:
                            cursor += dur * divisions
                        end = max(end, cursor)
                        continue
                    if el.find("unpitched") is not None:
                        continue
                    pitch = el.find("pitch")
                    if pitch is None:
                        continue
                    step = pitch.findtext("step")
                    alter = int(round(float(pitch.findtext("alter") or 0)))
                    octave = int(pitch.findtext("octave"))
                    midi = 12 * (octave + 1) + SEM[step] + alter
                    staff = int(el.findtext("staff") or 1)
                    if is_chord:
                        start = last_start
                    else:
                        start = cursor / divisions
                        last_start = start
                        if not is_grace:
                            cursor += dur * divisions
                    end = max(end, cursor)
                    notes.append({
                        "staff": offset + staff,
                        "midi": midi,
                        "letter": step,
                        "onset": start,
                        "dur": 0.0 if is_grace else dur,
                        "grace": is_grace,
                        "tuplet": el.find("time-modification") is not None,
                    })
            measures.append({"number": m.get("number"), "notes": notes, "end": end / divisions})
        parts.append(measures)
        offset += staves
    return parts, offset


def to_score(parts, staves):
    """Combine parts into one Score (scorer-style), for alignment with score_notes."""
    if len({len(p) for p in parts}) != 1:
        raise ValueError("parts have different measure counts")
    measures = []
    for i in range(len(parts[0])):
        notes = tuple(
            Note(n["staff"], float(n["midi"]), n["onset"], n["dur"], n["grace"])
            for p in parts for n in p[i]["notes"]
        )
        measures.append(Measure(parts[0][i]["number"], notes))
    return Score(tuple(measures), staves)


def bar_notes(parts, i):
    out = []
    for p in parts:
        out.extend(p[i]["notes"])
    return out


def max_match(rs, os_, pred):
    adj = [[j for j, o in enumerate(os_) if pred(r, o)] for r in rs]
    match_o = [-1] * len(os_)

    def try_(i, seen):
        for j in adj[i]:
            if not seen[j]:
                seen[j] = True
                if match_o[j] == -1 or try_(match_o[j], seen):
                    match_o[j] = i
                    return True
        return False

    for i in range(len(rs)):
        try_(i, [False] * len(os_))
    return [(match_o[j], j) for j in range(len(os_)) if match_o[j] != -1]


def interval_class(r, o):
    d = abs(r["midi"] - o["midi"])
    if d == 0:
        return "other"
    if d % 12 == 0:
        return "octave"
    li, lo = LETTERS.index(r["letter"]), LETTERS.index(o["letter"])
    if r["letter"] == o["letter"] and d <= 2:
        return "accidental"
    if (li - lo) % 7 in (1, 6):
        return "staff_step"
    return "other"


def new_stats():
    return Counter()


def cascade(R, O, st):
    """Classify reference notes R and output notes O of one aligned bar pair into st."""
    ri, oi = list(range(len(R))), list(range(len(O)))

    def same_staff_pitch(r, o):
        return r["staff"] == o["staff"] and r["midi"] == o["midi"]

    def close_onset(r, o):
        return abs(r["onset"] - o["onset"]) <= TOL

    def run(pred, ri, oi, label):
        pairs = max_match([R[i] for i in ri], [O[j] for j in oi], pred)
        used_r = {ri[a] for a, _ in pairs}
        used_o = {oi[b] for _, b in pairs}
        for a, b in pairs:
            r = R[ri[a]]
            st[label] += 1
            if r["tuplet"]:
                st[label + "_tuplet"] += 1
        return [x for x in ri if x not in used_r], [x for x in oi if x not in used_o]

    ri, oi = run(lambda r, o: same_staff_pitch(r, o) and close_onset(r, o)
                 and abs(r["dur"] - o["dur"]) <= TOL, ri, oi, "c1")
    ri, oi = run(lambda r, o: same_staff_pitch(r, o) and close_onset(r, o), ri, oi, "c2")
    ri, oi = run(same_staff_pitch, ri, oi, "c3")

    # Category 4: wrong pitch at the same onset, greedy by smallest pitch distance.
    cands = []
    for i in ri:
        for j in oi:
            if close_onset(R[i], O[j]):
                diff = abs(R[i]["midi"] - O[j]["midi"])
                cands.append((R[i]["staff"] != O[j]["staff"], diff, i, j))
    cands.sort()
    used_r, used_o = set(), set()
    for _, _, i, j in cands:
        if i in used_r or j in used_o:
            continue
        used_r.add(i)
        used_o.add(j)
        st["c4"] += 1
        st["c4_" + interval_class(R[i], O[j])] += 1
        if R[i]["tuplet"]:
            st["c4_tuplet"] += 1
    ri = [i for i in ri if i not in used_r]
    oi = [j for j in oi if j not in used_o]

    # Missing: reference notes left with no output note to pair with.
    for i in ri:
        r = R[i]
        chord = sum(1 for x in R if x["staff"] == r["staff"] and not x["grace"]
                    and abs(x["onset"] - r["onset"]) <= TOL)
        st["missing"] += 1
        st["missing_chord3plus" if chord >= 3 else "missing_single_or_pair"] += 1
    st["extra"] += len(oi)


def audit_piece(name, cfg):
    ref_parts, ref_staves = parse_file(cfg["ref"])
    out_parts, out_staves = parse_file(cfg["merged"])
    ref_score = to_score(ref_parts, ref_staves)
    out_score = to_score(out_parts, out_staves)
    pairs = align_measures(ref_score, out_score)

    # Cross-check against the saved scorer report when it has the same prediction file.
    saved_check = "no saved report"
    try:
        saved = json.load(open(cfg["saved"]))
        for r in saved["results"]:
            if r["input"]["path"] == cfg["merged"]:
                saved_pairs = sorted((a["reference_index"] - 1, a["prediction_index"] - 1)
                                     for a in r["alignment"])
                saved_check = "identical" if saved_pairs == sorted(pairs) else "DIFFERENT"
    except (OSError, KeyError):
        pass

    ref_al = {i for i, _ in pairs}
    out_al = {j for _, j in pairs}
    res = {"measures_ref": len(ref_parts[0]), "measures_out": len(out_parts[0]),
           "aligned_pairs": len(pairs), "alignment_vs_saved_report": saved_check}
    st = new_stats()
    gst = new_stats()
    for i, j in pairs:
        R = bar_notes(ref_parts, i)
        O = bar_notes(out_parts, j)
        cascade([n for n in R if not n["grace"]], [n for n in O if not n["grace"]], st)
        cascade([n for n in R if n["grace"]], [n for n in O if n["grace"]], gst)
    # Bars without partner.
    for i in range(len(ref_parts[0])):
        if i not in ref_al:
            for n in bar_notes(ref_parts, i):
                (gst if n["grace"] else st)["cat7_ref"] += 1
    for j in range(len(out_parts[0])):
        if j not in out_al:
            for n in bar_notes(out_parts, j):
                (gst if n["grace"] else st)["cat7_out"] += 1

    total_ref = sum(1 for p in ref_parts for m in p for n in m["notes"] if not n["grace"])
    total_ref_grace = sum(1 for p in ref_parts for m in p for n in m["notes"] if n["grace"])
    total_out = sum(1 for p in out_parts for m in p for n in m["notes"] if not n["grace"])
    accounted = st["c1"] + st["c2"] + st["c3"] + st["c4"] + st["missing"]
    unal_ref = st["cat7_ref"]
    assert accounted + unal_ref == total_ref, (accounted, unal_ref, total_ref)
    res.update({"total_ref_notes": total_ref, "total_out_notes": total_out,
                "total_ref_grace": total_ref_grace,
                "main": dict(st), "grace": dict(gst)})
    return res


def join_stats(name, cfg):
    """Raw per-page outputs concatenated vs merged output."""
    def summarize(paths_or_one):
        notes_seq, n_notes, n_rests, dur = [], 0, 0, 0.0
        files = paths_or_one
        for f in files:
            parts, _ = parse_file(f)
            for i in range(len(parts[0])):
                dur += max(p[i]["end"] for p in parts)
                for p in parts:
                    for n in p[i]["notes"]:
                        n_notes += 1
                        if not n["grace"]:
                            notes_seq.append((n["staff"], n["midi"], n["dur"]))
            # rests: count via raw XML
            root = ET.parse(f).getroot()
            for el in root.iter():
                if el.tag.rsplit("}", 1)[-1] == "rest":
                    n_rests += 1
        return notes_seq, n_notes, n_rests, dur

    raw_seq, raw_notes, raw_rests, raw_dur = summarize(cfg["pages"])
    mer_seq, mer_notes, mer_rests, mer_dur = summarize([cfg["merged"]])
    sm = SequenceMatcher(None, [(s, m) for s, m, _ in raw_seq],
                         [(s, m) for s, m, _ in mer_seq], autojunk=False)
    matched = dur_changed = 0
    for op, a0, a1, b0, b1 in sm.get_opcodes():
        if op == "equal":
            for k in range(a1 - a0):
                matched += 1
                if abs(raw_seq[a0 + k][2] - mer_seq[b0 + k][2]) > TOL:
                    dur_changed += 1
    return {
        "raw_pages": len(cfg["pages"]),
        "raw_notes_incl_grace": raw_notes, "merged_notes_incl_grace": mer_notes,
        "raw_duration_quarters": round(raw_dur, 2), "merged_duration_quarters": round(mer_dur, 2),
        "raw_rest_elements": raw_rests, "merged_rest_elements": mer_rests,
        "padding_rests_inserted": mer_rests - raw_rests,
        "notes_matched_by_sequence": matched,
        "notes_with_changed_duration": dur_changed,
        "pct_matched_duration_changed": round(100 * dur_changed / max(matched, 1), 2),
        "raw_only_notes_unmatched": len(raw_seq) - matched,
        "merged_only_notes_unmatched": len(mer_seq) - matched,
    }


def pct(x, d):
    return f"{x} ({100 * x / d:.1f}%)" if d else f"{x}"


def main():
    results = {}
    for name, cfg in PIECES.items():
        results[name] = {"bars": audit_piece(name, cfg), "joining": join_stats(name, cfg)}
    (OUT_DIR / "note-error-audit.json").write_text(json.dumps(results, indent=2))
    for name, r in results.items():
        b = r["bars"]
        m = b["main"]
        T = b["total_ref_notes"]
        print(f"== {name}: ref nongrace notes {T}, out nongrace {b['total_out_notes']}, "
              f"aligned bar pairs {b['aligned_pairs']} (ref bars {b['measures_ref']}, "
              f"out bars {b['measures_out']}), alignment vs saved report: {b['alignment_vs_saved_report']}")
        rows = [
            ("1 full match", m.get("c1", 0)),
            ("2 duration wrong", m.get("c2", 0)),
            ("3 onset wrong, pitch present", m.get("c3", 0)),
            ("4 wrong pitch, same onset", m.get("c4", 0)),
            ("   4a octave", m.get("c4_octave", 0)),
            ("   4b accidental only", m.get("c4_accidental", 0)),
            ("   4c one staff step", m.get("c4_staff_step", 0)),
            ("   4d other", m.get("c4_other", 0)),
            ("5 missing (total)", m.get("missing", 0)),
            ("   5a in chord of 3+", m.get("missing_chord3plus", 0)),
            ("   5b single/pair", m.get("missing_single_or_pair", 0)),
            ("6 extra (output notes, aligned bars)", m.get("extra", 0)),
            ("7 ref notes in unaligned bars", m.get("cat7_ref", 0)),
            ("7 output notes in unaligned bars", m.get("cat7_out", 0)),
        ]
        for label, v in rows:
            if label.startswith("6") or label.startswith("7 output"):
                print(f"  {label}: {v}")
            else:
                print(f"  {label}: {pct(v, T)}")
        print(f"  tuplet in 1/2/3/4: {m.get('c1_tuplet',0)}/{m.get('c2_tuplet',0)}/"
              f"{m.get('c3_tuplet',0)}/{m.get('c4_tuplet',0)} of {m.get('c1',0)}/{m.get('c2',0)}/"
              f"{m.get('c3',0)}/{m.get('c4',0)}; tuplet notes in ref total: "
              f"{sum(1 for p in parse_file(PIECES[name]['ref'])[0] for mm in p for n in mm['notes'] if n['tuplet'] and not n['grace'])}")
        g = b["grace"]
        print(f"  grace (ref {b['total_ref_grace']}): c1 {g.get('c1',0)}, c2 {g.get('c2',0)}, "
              f"c3 {g.get('c3',0)}, c4 {g.get('c4',0)}, missing {g.get('missing',0)}, "
              f"extra {g.get('extra',0)}, unaligned {g.get('cat7_ref',0)}")
        j = r["joining"]
        print("  joining: " + json.dumps(j))


if __name__ == "__main__":
    main()
