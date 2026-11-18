"""Shared helpers of the resolution-experiment evaluation (res_*.py): paths, the 28-piece set, metric loading and the
dense-bar recall. Standard library only, so any python3 will do; the scorer itself is imported from the res_wt checkout
(the same validation/score_notes.py as run/integration_wt, byte for byte)."""
import json
import os
import sys

R = "/Users/yiduoke/Documents/homr/run"
E = f"{R}/eval_run1"
OUT = f"{R}/out/testset"
WT = f"{R}/res_wt"
PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"
DENSE_NOTES = 24  # a reference bar with at least this many (visible) notes counts as dense
# Tags are res_<ARM>_s<SEED>[_<MODE>]; the arms of the experiment (see RESOLUTION_EVAL.md)
ARMS = {
    "A7": ("res_A_s7", "run3_ctrl_s7", "1", "direct"),
    "A11": ("res_A_s11", "run3_ctrl_s11", "1", "direct"),
    "B7": ("res_B_s7", "res_B_s7", "1.5", "direct"),
    "B11": ("res_B_s11", "res_B_s11", "1.5", "direct"),
}


def manifest() -> list[tuple[str, str, int, int]]:
    rows = []
    for line in open(f"{E}/testset_manifest.tsv"):
        if line.startswith("#") or not line.strip():
            continue
        piece, pdf, first, last = line.rstrip("\n").split("\t")[:4]
        rows.append((piece, pdf, int(first), int(last)))
    return rows


def pieces28() -> list[str]:
    """The test set of the tables: manifest pieces that have a released-model score (28 of 29; Islamey has none)."""
    return sorted(p for p, *_ in manifest() if os.path.exists(f"{OUT}/{p}/note-scores-layout1.json"))


def score_path(tag: str, piece: str) -> str:
    return f"{OUT}/{piece}/res-scores-{tag}.json"


def dense_path(tag: str, piece: str) -> str:
    return f"{OUT}/{piece}/res-dense-{tag}.json"


def _metrics(m: dict) -> dict:
    def k(name: str) -> dict:
        return m[name]["combined"] if "combined" in m[name] else m[name]

    return {
        "f1": k("pitch_inventory")["f1"] * 100,
        "p": k("pitch_inventory")["precision"] * 100,
        "r": k("pitch_inventory")["recall"] * 100,
        "po": k("pitch_onset")["f1"] * 100,
        "full": k("pitch_onset_duration")["f1"] * 100,
    }


def load_scores(tag: str, piece: str) -> dict | None:
    """{'sens': staff-sensitive metrics, 'pooled': pooled (staff-ignored) metrics, bars...} or None if not scored.
    As in the earlier tables, a piece whose parts have different bar counts (no joint bar index, e.g. Petrushka)
    gets its staff-sensitive per-staff-alignment numbers in the pooled column too (flag pooled_defined=False)."""
    path = score_path(tag, piece)
    if not os.path.exists(path):
        return None
    res = json.load(open(path))["results"][0]
    sens = _metrics(res["metrics"])
    sa = (res.get("staff_agnostic") or {}).get("metrics")
    pooled = _metrics(sa) if sa else sens
    pred, ref = res["predicted_measures"], res["reference_measures"]
    one = lambda v: v if not isinstance(v, list) else max(v)  # noqa: E731
    return {"sens": sens, "pooled": pooled, "pooled_defined": bool(sa), "pred_bars": one(pred), "ref_bars": one(ref),
            "bars_equal": (pred == ref)}


def load_dense(tag: str, piece: str) -> dict | None:
    path = dense_path(tag, piece)
    return json.load(open(path)) if os.path.exists(path) else None


def _score_module():
    if WT not in sys.path:
        sys.path.insert(0, WT)
    from validation import score_notes  # type: ignore

    return score_notes


def dense_stats(ref_path: str, pred_path: str, threshold: int = DENSE_NOTES) -> dict | None:
    """Recall of the reference notes in dense bars (reference bars, all staves together, with >= threshold visible
    notes), using the scorer's own alignment and matching.
    Pooled mode (the prediction has one bar list): bars aligned with the staff of a note ignored, a note counts as found
    if its pitch is in the aligned bar (pitch inventory, the headline metric) -- and, separately, if pitch and onset are.
    Per-staff mode (the parts have different bar counts, e.g. Schott scans before the merger fix, Petrushka): each staff
    aligned on its own, staff-sensitive. None if the reference itself has no shared bar list."""
    sn = _score_module()
    ref = sn.parse_musicxml(open(ref_path, encoding="utf-8-sig").read())
    pred = sn.parse_musicxml(open(pred_path, encoding="utf-8-sig").read())
    if ref.staff_measures:
        return None
    tol = sn.DEFAULT_TOLERANCE
    metrics = ("pitch_inventory", "pitch_onset")
    n = len(ref.measures)
    found = {m: [0] * n for m in metrics}
    aligned = [False] * n
    if not pred.staff_measures:
        mode = "pooled"
        for i, j in sn.align_measures(ref, pred, ignore_staff=True):
            aligned[i] = True
            for m in metrics:
                found[m][i] = sn.count_matches(ref.measures[i].notes, pred.measures[j].notes, m, tol, True)
    else:
        mode = "per_staff"
        if pred.staves != ref.staves:
            pred = sn.remap_staves(ref, pred)
        ref_bars, pred_bars = sn._staff_bars(ref), sn._staff_bars(pred)
        for k in range(ref.staves):
            pairs = sn.align_measures(sn.Score(ref_bars[k], ref.staves), sn.Score(pred_bars[k], ref.staves))
            for i, j in pairs:
                aligned[i] = True
                for m in metrics:
                    found[m][i] += sn.count_matches(ref_bars[k][i].notes, pred_bars[k][j].notes, m, tol)
    dense = [i for i in range(n) if len(ref.measures[i].notes) >= threshold]
    notes = sum(len(ref.measures[i].notes) for i in dense)
    total = sum(len(m.notes) for m in ref.measures)
    out = {"mode": mode, "threshold": threshold, "reference_bars": n, "dense_bars": len(dense),
           "dense_bars_unaligned": sum(not aligned[i] for i in dense), "dense_reference_notes": notes,
           "all_reference_notes": total, "dense_bar_numbers": [ref.measures[i].number for i in dense]}
    for m, short in (("pitch_inventory", "pitch"), ("pitch_onset", "onset")):
        hit = sum(found[m][i] for i in dense)
        out[f"dense_found_{short}"] = hit
        out[f"dense_missed_{short}"] = notes - hit
        out[f"dense_recall_{short}"] = hit / notes if notes else None
        rest_hit = sum(found[m]) - hit
        out[f"other_recall_{short}"] = rest_hit / (total - notes) if total > notes else None
    return out


if __name__ == "__main__":  # python res_lib.py REF.musicxml PRED.musicxml  -> dense stats as JSON
    print(json.dumps(dense_stats(sys.argv[1], sys.argv[2]), indent=1))
