"""Key-signature check for the run-1/run-2 comparison (extends meter_eval.py, which stays unchanged).

Reads the same inputs as meter_eval.py (references run/out/compare/<folder>/<folder>-reference.musicxml,
eval_run1/<model>/<folder>/<folder>-<model>.musicxml and note-scores.json) and writes
eval_run1/key_results.json and eval_run1/key_summary.md.

Definitions (measure alignment from score_notes as in meter_eval.pairs_of)
- Key in effect: fifths of the last <key> at or before the measure in part 1 (None before the first).
- Printed key change: a measure whose key in effect differs from the previous measure's
  (the first key of the piece is not a change).
- Share: reference measures whose aligned prediction measure has the same fifths in effect.
  An unaligned reference measure counts as a miss.
- Change precision / recall: as for meter changes, a predicted change at prediction measure j matches
  a still unmatched reference change within +-1 reference measures of the measure aligned to j
  (one-to-one, greedy by distance).
- first key: fifths of the piece's first key, ref vs prediction.
"""
import json
import xml.etree.ElementTree as ET

from meter_eval import CMP, E, MODELS, PIECES, pairs_of, pct


def keys(path):
    part = ET.parse(path).getroot().find("part")
    out, cur = [], None
    for m in part.findall("measure"):
        for k in m.iter("key"):
            f = k.findtext("fifths")
            if f is not None:
                cur = int(f)
        out.append(cur)
    return out


def changes(seq):
    ch, prev = [], None
    for i, c in enumerate(seq, start=1):
        if prev is not None and c is not None and c != prev:
            ch.append(i)
        if c is not None:
            prev = c
    return ch


def key_scores(ref, pred, pairs):
    r2p = {p["reference_index"]: p["prediction_index"] for p in pairs}
    p2r = {p["prediction_index"]: p["reference_index"] for p in pairs}
    same = aligned = 0
    for i in range(1, len(ref) + 1):
        j = r2p.get(i)
        if j is not None and j <= len(pred):
            aligned += 1
            same += pred[j - 1] == ref[i - 1]
    rc, pc = changes(ref), changes(pred)

    def to_ref(j):
        if j in p2r:
            return p2r[j]
        return p2r[min(p2r, key=lambda q: abs(q - j))] if p2r else None

    cands = sorted((abs(to_ref(j) - r), j, r) for j in pc for r in rc
                   if to_ref(j) is not None and abs(to_ref(j) - r) <= 1)
    uj, ur, hit = set(), set(), 0
    for _, j, r in cands:
        if j in uj or r in ur:
            continue
        uj.add(j), ur.add(r)
        hit += 1
    return {"ref_measures": len(ref), "aligned": aligned, "match_of_aligned": same,
            "share_of_ref_measures": same / len(ref), "match_share_of_aligned": same / aligned if aligned else None,
            "first_key_ref": ref[0] if ref else None, "first_key_pred": pred[0] if pred else None,
            "ref_changes": len(rc), "pred_changes": len(pc), "changes_matched": hit,
            "change_precision": hit / len(pc) if pc else None, "change_recall": hit / len(rc) if rc else None,
            "ref_change_measures": rc, "ref_change_fifths": [ref[i - 1] for i in rc],
            "pred_change_measures": pc}


def main():
    res = {}
    for piece in PIECES:
        ref = keys(CMP / piece / f"{piece}-reference.musicxml")
        for model in MODELS:
            d = E / model / piece
            sc, xml = d / "note-scores.json", d / f"{piece}-{model}.musicxml"
            if not sc.exists():
                continue
            rep = json.load(open(sc))["results"][0]
            res.setdefault(piece, {})[model] = key_scores(ref, keys(xml), pairs_of(rep))
    json.dump(res, open(E / "key_results.json", "w"), indent=1)
    L = ["# Key-signature check", "", "Definitions: docstring of key_eval.py. Share = reference measures whose aligned "
         "prediction measure has the same key (fifths) in effect; share of aligned = same, over aligned measures only. "
         "Changes: ref / pred / matched within +-1 measure.", "",
         "| Piece | Model | first key ref / pred | share of ref measures | share of aligned | key changes (ref / pred / hit) | change P | change R |",
         "|---|---|---|---|---|---|---|---|"]
    for piece, v in res.items():
        for mo in MODELS:
            if mo in v:
                s = v[mo]
                L.append(f"| {piece} | {mo} | {s['first_key_ref']} / {s['first_key_pred']} | {pct(s['share_of_ref_measures'])} | "
                         f"{pct(s['match_share_of_aligned'])} | {s['ref_changes']} / {s['pred_changes']} / {s['changes_matched']} | "
                         f"{pct(s['change_precision'])} | {pct(s['change_recall'])} |")
    L += ["", "Reference key changes (measure: fifths after the change): " + "; ".join(
        f"{p}: " + (", ".join(f"m{m} -> {f}" for m, f in zip(next(iter(v.values()))["ref_change_measures"],
                                                            next(iter(v.values()))["ref_change_fifths"])) or "none")
        for p, v in res.items()), ""]
    open(E / "key_summary.md", "w").write("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
