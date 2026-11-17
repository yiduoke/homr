"""Meter and per-page evaluation for the run-1 comparison (see README.md).

Reads eval_run1/<model>/<folder>/{<folder>-<model>.musicxml,note-scores.json,page-xml/}
and the references in run/out/compare/<folder>/<folder>-reference.musicxml.
Writes eval_run1/results.json and eval_run1/summary.md.

Definitions
- Printed signature: a <time> of the reference's first part without print-object="no".
- Reference measure i aligns to prediction measure j by score_notes' alignment (joint mode:
  `alignment`; per-staff mode: the pairs of staff 1; indices are positions of <measure>
  elements in the first part). An unaligned reference measure counts as a miss.
- Exact: (symbol as printed: see LILY) predicted signature in effect at j equals the printed one in numerator,
  denominator and symbol (common / cut / none). Numeric: numerator and denominator only.
- Meter in effect: signature of the last <time> at or before the measure in part 1.
- Change: a measure whose numeric meter differs from the previous measure's (the first
  signature of the piece is not a change). A predicted change at prediction measure j
  counts as found when a still unmatched reference change lies within +-1 reference
  measures of the reference measure aligned to j (nearest aligned measure if j is
  unaligned); one-to-one, greedy by distance. Precision = matched / predicted changes,
  recall = matched / reference changes.
- Share: fraction of all reference measures whose aligned prediction measure has the
  same numeric meter in effect as the reference's meter in effect.
- Per page: pitch+onset+duration F1 = 2M/(R+H) over the aligned measure pairs whose
  prediction measure lies on that page (pages by the page files' measure counts of the
  joined first part); R and H are the notes of those pairs only.
"""
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

E = Path(__file__).resolve().parent
CMP = E.parent / "out" / "compare"
MODELS = ["566", "control", "run1", "run2", "run2s7"]
PIECES = ["mazeppa", "la-campanella", "rachmaninoff-op3-2", "bach-prelude-848", "bach-fugue-848",
          "mozart-kv331-theme", "mozart-kv309-1", "beethoven-pathetique-1"]


def meters(path):
    """List per measure of the first part: (printed list [(num, den, symbol)], in_effect)."""
    root = ET.parse(path).getroot()
    part = root.find("part")
    out, cur = [], None
    for m in part.findall("measure"):
        printed = []
        for t in m.iter("time"):
            b, bt = t.findtext("beats"), t.findtext("beat-type")
            if b is None or bt is None:
                continue
            try:
                num, den = int(b), int(bt)
            except ValueError:  # "3+2" and the like
                num, den = b, int(bt)
            sym = t.get("symbol")
            sym = sym if sym in ("common", "cut") else None
            hidden = t.get("print-object") == "no"
            cur = (num, den, sym)
            if not hidden:
                printed.append((num, den, sym))
        out.append((printed, cur))
    return out


def pairs_of(rep):
    if rep["alignment_mode"] == "joint":
        al = rep["alignment"]
    else:
        al = rep["staff_alignment"][0]["pairs"]
    return al


def num(t):
    return None if t is None else (t[0], t[1])


# The KernScores references come from kern via music21 and carry no <time symbol>, but the
# score PDFs are LilyPond engravings, which draw 4/4 as C and 2/2 as cut C (checked on
# Bach fugue, Mozart K. 309 and Beethoven Op. 13 m1 and m11). For these pieces the symbol
# printed in the image replaces the reference file's missing one in the "exact" score.
LILY = {"bach-prelude-848", "bach-fugue-848", "mozart-kv331-theme", "mozart-kv309-1",
        "beethoven-pathetique-1"}


def printed_symbol(t):
    if t[:2] == (4, 4):
        return (4, 4, "common")
    if t[:2] == (2, 2):
        return (2, 2, "cut")
    return (t[0], t[1], None)


def meter_scores(ref, pred, pairs, lily=False):
    r2p = {p["reference_index"]: p["prediction_index"] for p in pairs}
    p2r = {p["prediction_index"]: p["reference_index"] for p in pairs}
    ref_idx = sorted(p2r.values())
    printed = [(i + 1, t) for i, (pr, _) in enumerate(ref) for t in pr[:1]]
    exact = exact_file = numeric = 0
    for i, t0 in printed:
        t = printed_symbol(t0) if lily else t0
        j = r2p.get(i)
        if j is None or j > len(pred):
            continue
        pt = pred[j - 1][1]
        if pt is None:
            continue
        numeric += num(pt) == num(t)
        exact += pt == t
        exact_file += pt == t0
    # meter in effect share
    same = 0
    for i in range(1, len(ref) + 1):
        j = r2p.get(i)
        if j is not None and j <= len(pred):
            same += num(pred[j - 1][1]) == num(ref[i - 1][1])

    def changes(seq):
        ch, prev = [], None
        for k, (_, cur) in enumerate(seq, start=1):
            if prev is not None and cur is not None and num(cur) != num(prev):
                ch.append(k)
            if cur is not None:
                prev = cur
        return ch

    rc, pc = changes(ref), changes(pred)

    def to_ref(j):
        if j in p2r:
            return p2r[j]
        if not p2r:
            return None
        near = min(p2r, key=lambda q: abs(q - j))
        return p2r[near]

    cands = sorted(((abs(to_ref(j) - r), j, r) for j in pc for r in rc
                    if to_ref(j) is not None and abs(to_ref(j) - r) <= 1))
    used_j, used_r, hit = set(), set(), 0
    for _, j, r in cands:
        if j in used_j or r in used_r:
            continue
        used_j.add(j), used_r.add(r)
        hit += 1
    return {
        "printed": len(printed), "exact": exact, "exact_ref_file_symbols": exact_file, "numeric": numeric,
        "ref_measures": len(ref), "meter_in_effect_match": same,
        "ref_changes": len(rc), "pred_changes": len(pc), "changes_matched": hit,
        "change_precision": hit / len(pc) if pc else None,
        "change_recall": hit / len(rc) if rc else None,
        "ref_change_measures": rc, "pred_change_measures": pc,
        "printed_list": [(i, f"{t[0]}/{t[1]}" + (f" {t[2]}" if t[2] else "")) for i, t in printed],
    }


def page_f1(model, piece, pairs):
    pages = sorted((p for p in (E / model / piece / "page-xml").glob("page-*.musicxml")),
                   key=lambda p: int(re.search(r"page-(\d+)", p.name).group(1)))
    # merge_pages pairs a page's parts with the joined parts by music21's part id (staves of a
    # piano part are "P1-Staff1", "P1-Staff2"; an extra staff is e.g. "Voice"). Only pages
    # with a part of the first page's first id add measures to the joined first part; a page
    # whose main staves carry another id (Mazeppa page 11: "P2-Staff1") adds none and is
    # lost in the join for every model alike.
    from music21 import converter

    ids = []
    for p in pages:
        sc = converter.parse(str(p), forceSource=True)
        ids.append({q.id: len(q.getElementsByClass("Measure")) for q in sc.parts})
    first = next(iter(ids[0]))
    counts = [(p.name, c.get(first, 0)) for p, c in zip(pages, ids)]
    res, start = [], 0
    for name, n in counts:
        sel = [q for q in pairs if start < q["prediction_index"] <= start + n]
        mt = sum(q["matches"]["pitch_onset_duration"] for q in sel)
        R = sum(q["reference_notes"] for q in sel)
        H = sum(q["predicted_notes"] for q in sel)
        res.append({"page": name, "pred_measures": [start + 1, start + n], "pairs": len(sel),
                    "ref_notes": R, "pred_notes": H, "matched": mt,
                    "f1": 2 * mt / (R + H) if R + H else None})
        start += n
    return res


def main():
    results = {}
    for piece in PIECES:
        ref = meters(CMP / piece / f"{piece}-reference.musicxml")
        for model in MODELS:
            d = E / model / piece
            sc, xml = d / "note-scores.json", d / f"{piece}-{model}.musicxml"
            if not sc.exists():
                continue
            rep = json.load(open(sc))["results"][0]
            pairs = pairs_of(rep)
            pred = meters(xml)
            m = rep["metrics"]
            notes = {k: {x: m[k]["combined"][x] for x in ("precision", "recall", "f1")} for k in m}
            results.setdefault(piece, {})[model] = {
                "notes": notes,
                "alignment_mode": rep["alignment_mode"],
                "reference_measures": rep["reference_measures"],
                "predicted_measures": rep["predicted_measures"],
                "meter": meter_scores(ref, pred, pairs, piece in LILY),
                "pages": page_f1(model, piece, pairs),
                "page_measures_sum_vs_final_part1": [
                    sum(p["pred_measures"][1] - p["pred_measures"][0] + 1 for p in page_f1(model, piece, pairs)),
                    len(pred)],
            }
    json.dump(results, open(E / "results.json", "w"), indent=1)
    write_summary(results)


def pct(x):
    return "n/a" if x is None else f"{100 * x:.1f}"


def write_summary(res):
    models = [m for m in MODELS if any(m in v for v in res.values())]
    L = ["# Run 1 evaluation: complete time signatures", "",
         "Pipeline and commands: README.md. Per-note scores in percent (F1; P and R in results.json).", ""]
    for key, title in (("pitch_inventory", "Pitch inventory F1"), ("pitch_onset", "Pitch+onset F1"),
                       ("pitch_onset_duration", "Pitch+onset+duration F1 (P / R in brackets)")):
        L += [f"## {title}", "", "| Piece | " + " | ".join(models) + " |", "|---|" + "---|" * len(models)]
        for piece, v in res.items():
            cells = []
            for mo in models:
                if mo in v:
                    n = v[mo]["notes"][key]
                    s = pct(n["f1"])
                    if key == "pitch_onset_duration":
                        s += f" ({pct(n['precision'])} / {pct(n['recall'])})"
                    cells.append(s)
                else:
                    cells.append("-")
            L.append(f"| {piece} | " + " | ".join(cells) + " |")
        L.append("")
    L += ["## Meter", "",
          "Exact = number, denominator and symbol; numeric = number and denominator. "
          "Counts are printed signatures matched / printed in the reference. Change P/R: "
          "matched changes within +-1 aligned measure / predicted, / reference changes. "
          "Share = reference measures whose meter in effect matches.", "",
          "| Piece | Model | printed | exact (symbol as printed) | exact (ref file symbol) | numeric | changes (ref / pred / hit) | change P | change R | share |",
          "|---|---|---|---|---|---|---|---|---|---|"]
    for piece, v in res.items():
        for mo in models:
            if mo not in v:
                continue
            m = v[mo]["meter"]
            L.append(f"| {piece} | {mo} | {m['printed']} | {m['exact']} | {m['exact_ref_file_symbols']} | {m['numeric']} | "
                     f"{m['ref_changes']} / {m['pred_changes']} / {m['changes_matched']} | "
                     f"{pct(m['change_precision'])} | {pct(m['change_recall'])} | "
                     f"{pct(m['meter_in_effect_match'] / m['ref_measures'])} |")
    L += ["", "Printed signatures per reference: " + "; ".join(
        f"{p}: " + ", ".join(f"m{i} {t}" for i, t in next(iter(v.values()))["meter"]["printed_list"])
        for p, v in res.items()), ""]
    L += ["## Page regressions (pitch+onset+duration F1; flagged when run1 is more than 2 points below 566 or control)", "",
          "| Piece | Page | " + " | ".join(models) + " | flag |", "|---|---|" + "---|" * len(models) + "---|"]
    for piece, v in res.items():
        if "run1" not in v:
            continue
        for k, pg in enumerate(v["run1"]["pages"]):
            vals, flag = [], []
            for mo in models:
                pgs = v.get(mo, {}).get("pages", [])
                f = pgs[k]["f1"] if k < len(pgs) else None
                vals.append(f)
            r1 = pg["f1"]
            for mo, f in zip(models, vals):
                if mo != "run1" and f is not None and r1 is not None and r1 < f - 0.02:
                    flag.append(f"below {mo}")
            L.append(f"| {piece} | {pg['page']} | " + " | ".join(pct(f) for f in vals) + f" | {', '.join(flag)} |")
    open(E / "summary.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
