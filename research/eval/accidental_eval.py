"""Printed-accidental scorer for run 2 (see README.md).

Usage: python accidental_eval.py [--models 566 run1 ...] [--pieces ...] [--pred-dir-name NAME]
Works on any model whose joined output eval_run1/<model>/<folder>/<folder>-<model>.musicxml and
note-scores.json exist (same layout as the run-1 models).

References: run/out/compare/<folder>/<folder>-reference-printed.musicxml for the five KernScores pieces
(make_printed_refs.py); for mazeppa, la-campanella, rachmaninoff-op3-2 the plain reference file, whose
<accidental> elements are the transcription's own.

Notes: measures are paired by the alignment score_notes wrote to note-scores.json (joint `alignment`, or
the per-staff `staff_alignment` pairs), on the same note lists score_notes builds: all parts and staves of
the file, read by validation/score_notes.py's own parser (octave_wt), with its staff remap when the staff
counts differ. (An earlier version read only the first part, so a piano score lost the left hand.)
Inside a pair, reference and predicted notes are matched one-to-one by sounding letter name + octave +
onset (within score_notes' tolerance), staff ignored. That is the pitch+onset match of score_notes, except
that an error in <alter> still counts as a match, so the sounding-pitch error is visible; the matches with
equal sounding pitch are about score_notes' pitch+onset matches (greedy matching and staff ignored, so
they can differ by a few notes). Without a note-scores.json (Ballade) score_notes is run live.
- Printed sign: <accidental> value mapped by homr.accidentals.MUSIC_XML_TO_SIGN
  (sharp #, flat b, natural N, double-sharp ##, flat-flat bb, natural-sharp -> #, natural-flat -> b),
  "none" if absent.
- Per class (#, b, N, ##, bb, none): precision = matched notes predicted as class that the reference has as
  that class / matched notes predicted as class; recall likewise over reference classes; F1.
  Reported over all matched notes and over the matched notes whose sounding pitch is right.
- Sounding pitch correct: <alter> equal (alter missing = 0), share of matched notes.
- Reference notes without a match are not counted (they are the note-recognition errors of score_notes).
Writes accidental_results.json and accidental_summary.md.
"""
import argparse
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/acc_wt")
from homr.accidentals import MUSIC_XML_TO_SIGN  # noqa: E402

from meter_eval import CMP, E, MODELS, PIECES, pairs_of  # noqa: E402

KERN = ["bach-prelude-848", "bach-fugue-848", "mozart-kv331-theme", "mozart-kv309-1", "beethoven-pathetique-1"]
BALLADE = "chopin-ballade-4"
CLASSES = ["#", "b", "N", "##", "bb", "none"]
STEP = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}


def reference_path(piece):
    p = CMP / piece / f"{piece}-reference-printed.musicxml"
    return p if p.exists() else CMP / piece / f"{piece}-reference.musicxml"


SN_DIR = "/Users/yiduoke/Documents/homr/run/octave_wt"
sys.path.insert(0, SN_DIR)
from dataclasses import dataclass  # noqa: E402
import inspect  # noqa: E402
from validation import score_notes as sn  # noqa: E402


@dataclass(frozen=True)
class XNote(sn.Note):
    diat: int = 0
    alter: int = 0
    sign: str = "none"


_src = inspect.getsource(sn._read_part).replace(
    "Note(staff_offset + staff, midi, float(onset or 0), float(duration), grace)",
    "XNote(staff_offset + staff, midi, float(onset or 0), float(duration), grace,"
    " int(pitch.findtext('octave')) * 7 + STEP[pitch.findtext('step')], int(float(pitch.findtext('alter') or 0)),"
    " MUSIC_XML_TO_SIGN.get(element.findtext('accidental'), 'none') if element.findtext('accidental') else 'none')")
assert "XNote(" in _src
sn.__dict__.update(XNote=XNote, STEP=STEP, MUSIC_XML_TO_SIGN=MUSIC_XML_TO_SIGN)
exec(_src, sn.__dict__)  # noqa: S102 - score_notes' own reader plus diatonic step, alter and printed sign


def read_score(path):
    return sn.parse_musicxml(Path(path).read_bytes().decode("utf-8-sig"))


def bar_pairs(ref, pred, rep):
    """Yield (reference notes, prediction notes) per aligned bar, as score_notes pairs them."""
    if ref.staves != pred.staves:
        pred = sn.remap_staves(ref, pred)
    if rep["alignment_mode"] == "joint":
        for pr in rep["alignment"]:
            yield (ref.measures[pr["reference_index"] - 1].notes, pred.measures[pr["prediction_index"] - 1].notes)
    else:
        rb, pb = sn._staff_bars(ref), sn._staff_bars(pred)
        for k, st in enumerate(rep["staff_alignment"]):
            for pr in st["pairs"]:
                yield rb[k][pr["reference_index"] - 1].notes, pb[k][pr["prediction_index"] - 1].notes


def match(ref_notes, pred_notes, tol=sn.DEFAULT_TOLERANCE):
    """One-to-one by (diatonic, onset); greedy in onset order within equal keys."""
    buckets = defaultdict(list)
    for k, n in enumerate(pred_notes):
        buckets[n.diat].append(k)
    used, pairs = set(), []
    for r in sorted(ref_notes, key=lambda n: (n.onset, n.diat)):
        for k in buckets.get(r.diat, []):
            if k not in used and abs(pred_notes[k].onset - r.onset) <= tol + 1e-9:
                used.add(k)
                pairs.append((r, pred_notes[k]))
                break
    return pairs


def prf(conf, sub):
    rows = {}
    for c in CLASSES:
        tp = conf.get((c, c), 0)
        pred = sum(v for (r, p), v in conf.items() if p == c)
        ref = sum(v for (r, p), v in conf.items() if r == c)
        P = tp / pred if pred else None
        R = tp / ref if ref else None
        F = 2 * P * R / (P + R) if P and R else (0.0 if (pred and ref) else None)
        rows[c] = {"tp": tp, "predicted": pred, "reference": ref, "precision": P, "recall": R, "f1": F}
    return rows


def score(piece, model, pred_path=None, rep=None):
    d = E / model / piece
    ref = read_score(reference_path(piece))
    pred = read_score(pred_path or d / f"{piece}-{model}.musicxml")
    if rep is None:
        rep = json.load(open(d / "note-scores.json"))["results"][0]
    elif rep == "live":
        rep = sn.score_notes(ref, pred)
    tol = rep["tolerance_quarters"]
    sn_po = rep["metrics"]["pitch_onset"]["combined"]["matched"]
    conf, conf_ok = Counter(), Counter()
    matched = sound_ok = 0
    for rn, pn in bar_pairs(ref, pred, rep):
        for r, p in match(rn, pn, tol):
            matched += 1
            conf[(r.sign, p.sign)] += 1
            if r.alter == p.alter:
                sound_ok += 1
                conf_ok[(r.sign, p.sign)] += 1
    notes = lambda sc: [n for m in (sc.measures or [b for st in sc.staff_measures for b in st]) for n in m.notes]
    rn_all, pn_all = notes(ref), notes(pred)
    ref_total = len(rn_all)
    return {"reference_file": reference_path(piece).name, "ref_notes": ref_total, "matched": matched, "score_notes_pitch_onset_matched": sn_po,
            "sounding_correct": sound_ok, "sounding_correct_share": sound_ok / matched if matched else None,
            "pred_notes_with_accidental": sum(1 for n in pn_all if n.sign != "none"),
            "ref_notes_with_accidental": sum(1 for n in rn_all if n.sign != "none"),
            "classes_all_matched": prf(conf, None), "classes_sounding_correct": prf(conf_ok, None),
            "confusion_all_matched": {f"{r}->{p}": v for (r, p), v in sorted(conf.items())}}


def f(x):
    return "-" if x is None else f"{100 * x:.1f}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="*", default=["566", "run1"])
    ap.add_argument("--pieces", nargs="*", default=PIECES)
    ap.add_argument("--ballade", nargs="*", default=["566", "run2s7"], help="models scored on the Ballade (live score_notes)")
    a = ap.parse_args()
    res = {}
    for m in a.models:
        for p in a.pieces:
            if (E / m / p / "note-scores.json").exists():
                res.setdefault(m, {})[p] = score(p, m)
    for m in a.ballade:
        pp = CMP / BALLADE / f"{BALLADE}-{m}.musicxml"
        if m in a.models and pp.exists():
            res.setdefault(m, {})[BALLADE] = score(BALLADE, m, pp, "live")
    json.dump(res, open(E / "accidental_results.json", "w"), indent=1)
    L = ["# Printed-accidental scorer", "", "Definitions: docstring of accidental_eval.py. Percent.", ""]
    for m, v in res.items():
        L += [f"## {m}", "", "| Piece | ref file | matched (score_notes pitch+onset) | sounding pitch correct | ref signs | pred signs | " +
              " | ".join(f"{c} P/R/F1" for c in CLASSES) + " |", "|---|---|---|---|---|---|" + "---|" * len(CLASSES)]
        tot, pooled = Counter(), Counter()
        for p, s in v.items():
            cells = []
            for c in CLASSES:
                r = s["classes_all_matched"][c]
                cells.append(f"{f(r['precision'])}/{f(r['recall'])}/{f(r['f1'])} ({r['reference']})")
            L.append(f"| {p} | {s['reference_file'].replace(p + '-', '')} | {s['matched']} ({s['score_notes_pitch_onset_matched']}) | {f(s['sounding_correct_share'])} | "
                     f"{s['ref_notes_with_accidental']} | {s['pred_notes_with_accidental']} | " + " | ".join(cells) + " |")
            for k, x in s["confusion_all_matched"].items():
                tot[k] += x
                if p != BALLADE:
                    pooled[tuple(k.split("->"))] += x
            tot["_m"] += s["matched"]; tot["_s"] += s["sounding_correct"]
        L += ["", f"Sounding pitch correct over all pieces: {f(tot['_s'] / tot['_m'])} of {tot['_m']} matched notes. "
              "Confusion (reference->predicted, counts, all pieces): " +
              ", ".join(f"{k}: {x}" for k, x in sorted(tot.items(), key=lambda t: -t[1]) if not k.startswith("_") and k.split("->")[0] != k.split("->")[1] or k in ()) , ""]
        pm = sum(pooled.values())
        L += [f"Pooled over the {len(v) - (BALLADE in v)} non-Ballade pieces: {pm} matched notes, printed sign right among matched notes "
              f"{f(sum(x for (r, q), x in pooled.items() if r == q) / pm)}.", "",
              "| class | P | R | F1 | reference |", "|---|---|---|---|---|"]
        for c, r in prf(pooled, None).items():
            L.append(f"| {c} | {f(r['precision'])} | {f(r['recall'])} | {f(r['f1'])} | {r['reference']} |")
        L += [""]
        L += ["Correct pairs (diagonal): " + ", ".join(f"{k}: {x}" for k, x in sorted(tot.items(), key=lambda t: -t[1])
                                                     if not k.startswith("_") and k.split("->")[0] == k.split("->")[1]), ""]
    open(E / "accidental_summary.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
