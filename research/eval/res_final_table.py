"""FINAL comparison table of the input-resolution experiment (arm A 256x1280 vs arm B 384x1920, seeds 7 and 11, GPU harness).

Written 2026-11-17 (Pacific) to the advisor's specification: the same GPU pipeline for every arm (res_eval.py: same layout, merger,
scorer, loop guard), EDITION-CORRECTED references for every arm (Schubert D. 899/4 against
out/testset/schubert-impromptu-d899-4/schubert-impromptu-d899-4-reference-edition.musicxml; every other piece its normal reference,
the Scriabin one is already the version without the stray part), target metric 97 % POOLED sounding-pitch F1 on every held-out piece
(visible notes, correct octave and bar), judged on music: paired B - A per seed, missed notes in dense bars, bar counts, cost.

usage: python res_final_table.py [--a7 res_A_s7_gpu --a11 res_A_s11_gpu --b7 res_B_s7_gpu --b11 res_B_s11_gpu] [--baseline layout1 | --no-baseline]
                                 [--label-a A --label-b B] [--name SUFFIX] [--date YYYY-MM-DD] [--force-rescore] [--no-baseline-dense]
The four defaults are the GPU runs of the experiment. "A" and "B" are the two sides of a pair per seed (B - A); to compare other runs
give their tags, e.g. B enlarged against B direct: --a7 res_B_s7_gpu --a11 res_B_s11_gpu --b7 res_B_s7_gpu_enl --b11 res_B_s11_gpu_enl
--label-a "B direct" --label-b "B enlarged" --name enlarge --no-baseline. A tag whose outputs are missing
(no <piece>-<tag>.musicxml, or output present but not yet scored by res_eval.py) is reported as missing for that piece and left
out of every mean and of every pair that needs it; nothing is guessed. Means of a partial tag are over the pieces present and
are marked "partial n of 28"; paired differences use only pieces where both runs of the pair exist.

Step 1, re-scoring (Schubert only, saved outputs, no inference): for every tag, score_notes (validation/score_notes.py of res_wt, the same file
as integration_wt) against the edition reference, visible notes, written as
  out/testset/<piece>/note-scores-<tag>-edition.json   (staff-sensitive, as after_merger_tables_octave.py reads it)
  out/pooled/<piece>/<tag>-edition.json                (--ignore-staff: staff-sensitive metrics + the staff_agnostic block = pooled)
  out/testset/<piece>/res-dense-<tag>-edition.json     (dense-bar recall against the edition reference)
Existing files are kept (use --force-rescore to redo). Every other piece reads the files res_eval.py wrote
(res-scores-<tag>.json, res-dense-<tag>.json, produced with the normal reference, which is what the other 27 pieces use).
The released baseline (layout1) is read exactly as after_merger_tables_octave.py reads it (note-scores-layout1[_am].json,
out/pooled/<piece>/layout1[_am].json; Schubert the -edition files; the three Schott scans from the after-merger outputs T_am);
its dense-bar recall is computed here once from the saved layout1 outputs (res-dense-layout1[_am][-edition].json).

Output: out/testset/RES-FINAL-table-<date>[-<name>].md
  1 tags and status, 2 summary lines per tag, 3 per-piece tables (pooled, staff-sensitive, +onset, full, bars), 4 paired B - A per seed
  (mean and spread over the seeds, wins / losses), 5 dense-bar recall and missed notes, 6 what moved, 7 cost (wall per page from the
  saved per-piece wall times of the runs, with the caveat that they are only comparable if the box was not shared).
"""
import argparse
import datetime
import json
import math
import os
import re
import statistics as st
import subprocess
import sys
import zoneinfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import res_lib as L  # noqa: E402

T, P = L.OUT, f"{L.R}/out/pooled"
from edition_refs import EDITION  # noqa: E402  (one shared list of edition-corrected pieces)
SCHOTT = {"liszt-sonata", "liszt-te-5", "liszt-te-10"}
PETRUSHKA = "stravinsky-petrushka"
TIE = 0.1  # points: a piece is a tie when |mean d| <= TIE (as res_paired.py)


def edition_ref(piece: str) -> str:
    return f"{T}/{piece}/{piece}-reference{'-edition' if piece in EDITION else ''}.musicxml"


def es(piece: str) -> str:
    return "-edition" if piece in EDITION else ""


def run_scorer(ref: str, tag: str, pred: str, out: str, ignore_staff: bool) -> None:
    os.makedirs(os.path.dirname(out), exist_ok=True)
    cmd = [L.PY, "-m", "validation.score_notes", ref, f"{tag}={pred}", "--json", out] + (["--ignore-staff"] if ignore_staff else [])
    r = subprocess.run(cmd, cwd=L.WT, env={**os.environ, "PYTHONPATH": L.WT}, capture_output=True, text=True)
    if r.returncode:
        sys.exit(f"scorer failed for {tag} {pred}\n{r.stderr[-500:]}")


def result_to_row(res: dict, dense: dict | None) -> dict:
    """Same reading of a score_notes result as res_lib.load_scores (pooled = staff_agnostic block, else the staff-sensitive one)."""
    sens = L._metrics(res["metrics"])
    sa = (res.get("staff_agnostic") or {}).get("metrics")
    pred, ref = res["predicted_measures"], res["reference_measures"]
    one = lambda v: v if not isinstance(v, list) else max(v)  # noqa: E731
    return {"sens": sens, "pooled": L._metrics(sa) if sa else sens, "pooled_defined": bool(sa), "pred_bars": one(pred), "ref_bars": one(ref),
            "bars_equal": pred == ref, "pred_raw": pred, "ref_raw": ref, "dense": dense}


def first_result(path: str) -> dict | None:
    return json.load(open(path))["results"][0] if os.path.exists(path) else None


def rescore_edition_piece(piece: str, tag: str, force: bool) -> str:
    """Re-score one saved tag of one edition-corrected piece against its -reference-edition file (same scorer as the other pieces)."""
    pred = f"{T}/{piece}/{piece}-{tag}.musicxml"
    if not os.path.exists(pred):
        return "no output"
    ref = edition_ref(piece)
    f_sens, f_pool, f_dense = f"{T}/{piece}/note-scores-{tag}-edition.json", f"{P}/{piece}/{tag}-edition.json", f"{T}/{piece}/res-dense-{tag}-edition.json"
    did = []
    if force or not os.path.exists(f_sens):
        run_scorer(ref, tag, pred, f_sens, False)
        did.append("note-scores")
    if force or not os.path.exists(f_pool):
        run_scorer(ref, tag, pred, f_pool, True)
        did.append("pooled")
    if force or not os.path.exists(f_dense):
        json.dump(L.dense_stats(ref, pred), open(f_dense, "w"), indent=1)
        did.append("dense")
    a, b = first_result(f_sens)["metrics"], first_result(f_pool)["metrics"]
    assert L._metrics(a) == L._metrics(b), "staff-sensitive numbers differ between the two scorer runs"
    return "rescored " + "+".join(did) if did else "kept (already rescored)"


def load_res_tag(tag: str, piece: str) -> dict | None:
    """One piece of one GPU-harness tag; None if not scored. Schubert from the edition rescoring."""
    pred = f"{T}/{piece}/{piece}-{tag}.musicxml"
    if not os.path.exists(pred):
        return None
    if piece in EDITION:
        res = first_result(f"{P}/{piece}/{tag}-edition.json")
        dpath = f"{T}/{piece}/res-dense-{tag}-edition.json"
        return result_to_row(res, json.load(open(dpath)) if os.path.exists(dpath) else None) if res else None
    s = L.load_scores(tag, piece)
    if not s:
        return None
    res = first_result(L.score_path(tag, piece))
    return result_to_row(res, L.load_dense(tag, piece))


def load_baseline(tag: str, piece: str, with_dense: bool) -> dict | None:
    """Released baseline read as after_merger_tables_octave.py does (Schott scans from T_am, Schubert -edition files)."""
    t = tag + "_am" if piece in SCHOTT and os.path.exists(f"{T}/{piece}/note-scores-{tag}_am.json") else tag
    sres = first_result(f"{T}/{piece}/note-scores-{t}{es(piece)}.json")
    pres = first_result(f"{P}/{piece}/{t}{es(piece)}.json")
    if sres is None or pres is None:
        return None
    merged = dict(sres)
    # the octave script reads staff_agnostic.metrics if present, else the pooled file's own metrics
    sa = (pres.get("staff_agnostic") or {}).get("metrics")
    merged["staff_agnostic"] = {"metrics": sa if sa else pres["metrics"]}
    dense = None
    if with_dense:
        dpath = f"{T}/{piece}/res-dense-{t}{es(piece)}.json"
        if not os.path.exists(dpath):
            pred = f"{T}/{piece}/{piece}-{t}.musicxml"
            if os.path.exists(pred):
                json.dump(L.dense_stats(edition_ref(piece), pred), open(dpath, "w"), indent=1)
        dense = json.load(open(dpath)) if os.path.exists(dpath) else None
    row = result_to_row(merged, dense)
    row["pooled_defined"] = True  # the octave tables show the pooled column as such
    return row


def mean(xs):
    xs = list(xs)
    return st.mean(xs) if xs else float("nan")


def sd2(a, b):
    return abs(a - b) / math.sqrt(2)


def sign_test(wins: int, losses: int) -> float:
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) / 2**n)


def f1(x, nd=1):
    return "n/a" if x is None or (isinstance(x, float) and math.isnan(x)) else f"{x:.{nd}f}"


def bars_str(r: dict) -> str:
    v, w = r["pred_raw"], r["ref_raw"]
    a = f"{v[0]}/{v[1]}" if isinstance(v, list) else str(v)
    b = str(w[0]) if isinstance(w, list) else str(w)
    return f"{a}/{b}"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--a7", default="res_A_s7_gpu")
    ap.add_argument("--a11", default="res_A_s11_gpu")
    ap.add_argument("--b7", default="res_B_s7_gpu")
    ap.add_argument("--b11", default="res_B_s11_gpu")
    ap.add_argument("--label-a", default="A")
    ap.add_argument("--label-b", default="B")
    ap.add_argument("--name", default="")
    ap.add_argument("--baseline", default="layout1")
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--no-baseline-dense", action="store_true")
    ap.add_argument("--date", default=datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d"))
    ap.add_argument("--force-rescore", action="store_true")
    ap.add_argument("--pieces", nargs="*")
    a = ap.parse_args()
    pieces = a.pieces or L.pieces28()
    n_all = len(pieces)
    tags = [a.a7, a.a11, a.b7, a.b11]
    ROLE = {a.a7: ("A", 7), a.a11: ("A", 11), a.b7: ("B", 7), a.b11: ("B", 11)}
    assert len(ROLE) == 4, "the four tags must differ"

    # ---- step 1: re-score Schubert against the edition reference
    status = {}
    for t in tags:
        for ep in sorted(EDITION & set(pieces)):
            status[t] = status.get(t, "") + ("; " if t in status else "") + f"{ep}: {rescore_edition_piece(ep, t, a.force_rescore)}"
            print(f"{t}: {ep} {status[t]}", flush=True)

    # ---- load
    cols = ([] if a.no_baseline else [a.baseline]) + tags
    data = {t: {p: load_res_tag(t, p) for p in pieces} for t in tags}
    if not a.no_baseline:
        data[a.baseline] = {p: load_baseline(a.baseline, p, not a.no_baseline_dense) for p in pieces}
    present = {c: [p for p in pieces if data[c][p]] for c in cols}
    missing = {c: [p for p in pieces if not data[c][p]] for c in cols}
    label = {a.baseline: "released"}
    for t in tags:
        ar, sd = ROLE[t]
        label[t] = f"{a.label_a if ar == 'A' else a.label_b} s{sd}"

    pacific = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles")).strftime("%Y-%m-%d %H:%M %Z")
    out = [f"# Resolution experiment, final comparison (arm A 256x1280 vs arm B 384x1920), {a.date}", "",
           f"Generated {pacific} by `eval_run1/res_final_table.py`. Same GPU pipeline for every arm (`res_eval.py`: same layout, merger, scorer, loop guard), "
           "visible notes only, **edition-corrected references for every column** (Schubert D. 899/4 against `schubert-impromptu-d899-4-reference-edition.musicxml`; the Scriabin reference is the one without "
           "the stray part). Pooled = a pitch counts if it is in the aligned bar on either staff (sounding pitch, correct octave and bar). Target: 97 % pooled pitch on every piece. "
           "The released column is the laptop CPU run of the released model after the merger fixes (not the same hardware as the GPU arms; reference only).", ""]

    # ---- 1 status
    out += ["## 1. Runs", "", "| column | tag | pieces scored | Schubert re-score | missing |", "|---|---|---|---|---|"]
    for c in cols:
        miss = ", ".join(missing[c]) if missing[c] else "none"
        out.append(f"| {label[c]} | `{c}` | {len(present[c])} of {n_all}{' (partial)' if len(present[c]) < n_all else ''} | {status.get(c, 'existing -edition files')} | {miss} |")
    out.append("")

    # ---- 2 summary
    def summ(c):
        rows = {p: data[c][p] for p in present[c]}
        n = len(rows)
        if not n:
            return None
        sens, pool, po, full = (mean(r["sens"]["f1"] for r in rows.values()), mean(r["pooled"]["f1"] for r in rows.values()),
                                mean(r["pooled"]["po"] for r in rows.values()), mean(r["pooled"]["full"] for r in rows.values()))
        worst = min(rows, key=lambda p: rows[p]["pooled"]["f1"])
        nopet = [p for p in rows if p != PETRUSHKA]
        worst2 = min(nopet, key=lambda p: rows[p]["pooled"]["f1"]) if nopet else None
        ds = [r["dense"] for r in rows.values() if r["dense"]]
        notes = sum(d["dense_reference_notes"] for d in ds)
        missed = sum(d["dense_missed_pitch"] for d in ds)
        return dict(n=n, sens=sens, pool=pool, po=po, full=full, worst=worst, worstv=rows[worst]["pooled"]["f1"], worst2=worst2,
                    worst2v=rows[worst2]["pooled"]["f1"] if worst2 else None, at97=sum(r["pooled"]["f1"] >= 97 for r in rows.values()),
                    at97s=sum(r["sens"]["f1"] >= 97 for r in rows.values()), beq=sum(r["bars_equal"] for r in rows.values()),
                    dn=len(ds), notes=notes, missed=missed, recall=100 * (notes - missed) / notes if notes else None)

    S = {c: summ(c) for c in cols}
    out += ["## 2. Summary per run (means over the pieces scored; macro mean over pieces)", "",
            "| run | pieces | staff-sens pitch | pooled pitch | pooled +onset | pooled full | worst piece (pooled) | worst without Petrushka | pieces at 97+ pooled | at 97+ staff-sens | bar count = reference |",
            "|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in cols:
        s = S[c]
        if not s:
            out.append(f"| {label[c]} | 0 | missing | | | | | | | | |")
            continue
        part = "" if s["n"] == n_all else f" (partial {s['n']} of {n_all})"
        out.append(f"| {label[c]}{part} | {s['n']} | {s['sens']:.2f} | {s['pool']:.2f} | {s['po']:.2f} | {s['full']:.2f} | {s['worst']} {s['worstv']:.1f} | "
                   f"{s['worst2']} {s['worst2v']:.1f} | {s['at97']} of {s['n']} | {s['at97s']} | {s['beq']} of {s['n']} |")
    out += ["", "Petrushka is provisional (three reference staves against two of ours; its pooled column uses one joint alignment, not verified). Bar count = reference means "
           "equal bar counts per part (a pair of counts for a piece whose hands differ).", ""]

    # ---- 3 per-piece tables
    def piece_table(title, fn, note=""):
        out.extend([f"### {title}", ""] + ([note, ""] if note else []))
        out.append("| piece | " + " | ".join(label[c] for c in cols) + " |")
        out.append("|---" * (1 + len(cols)) + "|")
        for p in pieces:
            mark = " *" if p in SCHOTT else (" (provisional)" if p == PETRUSHKA else "")
            cells = []
            for c in cols:
                r = data[c][p]
                cells.append("**missing**" if not r else fn(r))
            out.append(f"| {p}{mark} | " + " | ".join(cells) + " |")
        out.append("")

    out += ["## 3. Per piece", "", "Percent F1. Bold figures in the pooled table are below 97. `*` = Schott scan, released column re-merged (`_am`); the GPU runs always use the current merger."]
    out.append("")
    piece_table("3a. Pooled sounding-pitch F1 (the target metric, 97)", lambda r: f"{r['pooled']['f1']:.1f}" if r["pooled"]["f1"] >= 97 else f"**{r['pooled']['f1']:.1f}**")
    piece_table("3b. Staff-sensitive pitch F1", lambda r: f"{r['sens']['f1']:.1f}")
    piece_table("3c. Pooled pitch + onset F1", lambda r: f"{r['pooled']['po']:.1f}")
    piece_table("3d. Pooled full (pitch + onset + duration) F1", lambda r: f"{r['pooled']['full']:.1f}")
    piece_table("3e. Bars: ours / reference", bars_str, "A pair `x/y/z` means our two hands have x and y bars against z in the reference.")

    # ---- 4 paired
    seeds = sorted({ROLE[t][1] for t in tags})
    arm_tag = {(ROLE[t][0], ROLE[t][1]): t for t in tags}
    pairs = [(s, arm_tag.get(("A", s)), arm_tag.get(("B", s))) for s in seeds]
    pairs = [(s, ta, tb) for s, ta, tb in pairs if ta and tb and any(data[ta][p] and data[tb][p] for p in pieces)]
    METRICS = [("pooled pitch F1", lambda r: r["pooled"]["f1"]), ("staff-sensitive pitch F1", lambda r: r["sens"]["f1"]),
               ("pooled pitch+onset F1", lambda r: r["pooled"]["po"]), ("pooled full F1", lambda r: r["pooled"]["full"]),
               ("dense-bar recall of pitches", lambda r: None if not r["dense"] or r["dense"]["dense_recall_pitch"] is None else 100 * r["dense"]["dense_recall_pitch"])]
    out += ["## 4. Paired differences, B minus A (same seed = same start weights, list, steps and data order; only the input size differs)", ""]
    paired = {}  # metric -> piece -> {seed: d}
    usable_by_seed = {}
    for s, ta, tb in pairs:
        usable_by_seed[s] = [p for p in pieces if data[ta][p] and data[tb][p]]
        out.append(f"* seed {s}: A = `{ta}`, B = `{tb}`, {len(usable_by_seed[s])} of {n_all} pieces in both"
                   + ("" if len(usable_by_seed[s]) == n_all else " (left out: " + ", ".join(p for p in pieces if p not in usable_by_seed[s]) + ")"))
    for s in seeds:
        if s not in usable_by_seed:
            out.append(f"* seed {s}: no piece scored in both runs (A `{arm_tag.get(('A', s))}`, B `{arm_tag.get(('B', s))}`), not compared yet")
    out.append("")
    if not pairs:
        out += ["No complete A/B pair yet.", ""]
    for title, fn in METRICS:
        per_piece = {}
        for s, ta, tb in pairs:
            for p in usable_by_seed[s]:
                x, y = fn(data[ta][p]), fn(data[tb][p])
                if x is not None and y is not None:
                    per_piece.setdefault(p, {})[s] = (x, y)
        if not per_piece:
            continue
        paired[title] = per_piece
        two = len(pairs) == 2
        hdr = ["piece"] + [f"A s{s}" for s, _, _ in pairs] + [f"B s{s}" for s, _, _ in pairs] + [f"d s{s}" for s, _, _ in pairs] + ["mean d" + (" +- sd" if two else ""), "verdict"]
        out += [f"### {title}", "", "| " + " | ".join(hdr) + " |", "|" + "---|" * len(hdr)]
        win = loss = tie = both = 0
        per_seed_d = {s: [] for s, _, _ in pairs}
        for p in pieces:
            if p not in per_piece:
                continue
            pp = per_piece[p]
            ds = {s: pp[s][1] - pp[s][0] for s in pp}
            m = mean(ds.values())
            sdv = sd2(*ds.values()) if len(ds) == 2 else None
            v = "B wins" if m > TIE else "B loses" if m < -TIE else "tie"
            ag = len(ds) == 2 and (all(d > TIE for d in ds.values()) or all(d < -TIE for d in ds.values()))
            win, loss, tie, both = win + (v == "B wins"), loss + (v == "B loses"), tie + (v == "tie"), both + ag
            for s in ds:
                per_seed_d[s].append(ds[s])
            row = [p] + [f"{pp[s][0]:.1f}" if s in pp else "n/a" for s, _, _ in pairs] + [f"{pp[s][1]:.1f}" if s in pp else "n/a" for s, _, _ in pairs]
            row += [f"{ds[s]:+.2f}" if s in ds else "n/a" for s, _, _ in pairs] + [f"{m:+.2f}" + (f" +- {sdv:.2f}" if sdv is not None else ""), v + (" (both seeds)" if ag else "")]
            out.append("| " + " | ".join(row) + " |")
        D = {s: mean(v) for s, v in per_seed_d.items()}
        out += ["", f"Mean B - A per seed: " + ", ".join(f"s{s} {D[s]:+.2f} ({len(per_seed_d[s])} pieces)" for s in D)
                + (f"; mean {mean(D.values()):+.2f} +- {sd2(*D.values()):.2f} (range of the two seeds, n = 2, not a confidence interval)" if len(D) == 2 else "")
                + f". B wins {win}, loses {loss}, ties {tie} (tie band {TIE}); both seeds agree beyond the band on {both}; sign test over the {win + loss} decided pieces p = {sign_test(win, loss):.3f}.", ""]
    # seed noise yardstick
    for ar in ("A", "B"):  # the two runs of one side, different seeds
        t7, t11 = arm_tag.get((ar, 7)), arm_tag.get((ar, 11))
        if t7 and t11:
            both_p = [p for p in pieces if data[t7][p] and data[t11][p]]
            if both_p:
                d = [data[t11][p]["pooled"]["f1"] - data[t7][p]["pooled"]["f1"] for p in both_p]
                out.append(f"Seed noise, arm {ar}: s11 - s7 pooled pitch over {len(both_p)} pieces: mean {mean(d):+.2f}, mean absolute difference {mean(abs(x) for x in d):.2f}, "
                           f"largest {max(d, key=abs):+.2f}, pieces with |diff| >= 1 point: {sum(abs(x) >= 1 for x in d)}.")
    out.append("")

    # ---- 5 dense
    out += ["## 5. Missed notes in dense passages", "", "Dense = reference bars (all staves together, visible notes) with at least "
            f"{L.DENSE_NOTES} notes. Recall = share of the reference pitches found in the aligned bar (pooled alignment; Petrushka is per staff). Missed = number of reference notes not found.", "",
            "| run | pieces | dense bars | dense reference notes | dense pitches missed | dense recall % |", "|---|---|---|---|---|---|"]
    for c in cols:
        rows = [data[c][p] for p in present[c] if data[c][p]["dense"]]
        if not rows:
            out.append(f"| {label[c]} | 0 | | | | |")
            continue
        nb = sum(r["dense"]["dense_bars"] for r in rows)
        notes = sum(r["dense"]["dense_reference_notes"] for r in rows)
        miss = sum(r["dense"]["dense_missed_pitch"] for r in rows)
        out.append(f"| {label[c]} | {len(rows)} | {nb} | {notes} | {miss} | {100 * (notes - miss) / notes:.2f} |")
    out += ["", "Per piece dense-bar recall % (pitches missed in brackets):", "", "| piece | dense bars / notes | " + " | ".join(label[c] for c in cols) + " |", "|---" * (2 + len(cols)) + "|"]
    for p in pieces:
        ref_d = next((data[c][p]["dense"] for c in cols if data[c][p] and data[c][p]["dense"]), None)
        head = f"{ref_d['dense_bars']} / {ref_d['dense_reference_notes']}" if ref_d else "n/a"
        cells = []
        for c in cols:
            r = data[c][p]
            if not r:
                cells.append("**missing**")
            elif not r["dense"] or r["dense"]["dense_recall_pitch"] is None:
                cells.append("n/a")
            else:
                cells.append(f"{100 * r['dense']['dense_recall_pitch']:.1f} ({r['dense']['dense_missed_pitch']})")
        out.append(f"| {p} | {head} | " + " | ".join(cells) + " |")
    out.append("")

    # ---- 6 what moved
    out += ["## 6. What moved", ""]
    pp = paired.get("pooled pitch F1", {})
    two = len(pairs) == 2
    moved = []
    for p in pieces:
        if p not in pp:
            continue
        ds = {s: pp[p][s][1] - pp[p][s][0] for s in pp[p]}
        if two and len(ds) == 2:
            if all(d >= 1 for d in ds.values()) or all(d <= -1 for d in ds.values()):
                moved.append((p, ds))
        elif not two and len(ds) == 1:
            if abs(next(iter(ds.values()))) >= 1:
                moved.append((p, ds))
    if not pairs:
        out.append("No complete pair yet.")
    else:
        rule = ("pieces where the pooled pitch F1 changes by at least 1 point in the same direction in both seeds" if two else
                f"SINGLE SEED ({pairs[0][0]}) only, provisional: pieces where the pooled pitch F1 changes by at least 1 point (a one-seed change is not yet distinguishable from seed noise, see the seed-noise line in section 4)")
        out += [f"Rule: {rule}.", ""]
        if moved:
            out += ["| piece | direction | " + " | ".join(f"d s{s}" for s, _, _ in pairs) + " | A pooled (mean) | B pooled (mean) |", "|---" * (3 + len(pairs) + 1) + "|"]
            for p, ds in sorted(moved, key=lambda x: -abs(mean(x[1].values()))):
                am = mean(pp[p][s][0] for s in pp[p]); bm = mean(pp[p][s][1] for s in pp[p])
                out.append(f"| {p} | {'B better' if mean(ds.values()) > 0 else 'B worse'} | " + " | ".join(f"{ds[s]:+.2f}" if s in ds else "n/a" for s, _, _ in pairs) + f" | {am:.1f} | {bm:.1f} |")
        else:
            out.append("No piece moves by 1 point under this rule.")
    out.append("")

    # ---- 7 cost
    out += ["## 7. Inference cost on the box (wall time per page from the saved per-piece times)", "",
            "From `eval_run1/testset/<tag>/<piece>/wall_seconds.txt` (the `run_homr.py` call of the piece: segmentation, staff detection, transformer; merge and scoring not included) divided by the page "
            "count. Pieces are run one after the other by `res_eval.py`, but **the box is shared** with other agents' jobs, so these times are only indicative; a clean comparison needs a quiet box "
            "(`res_timing.py` on 5 pages, see `RESOLUTION_EVAL.md`, 'Final comparison').", ""]
    walls = {}
    for t in tags:
        w = {}
        for p in pieces:
            f = f"{L.E}/testset/{t}/{p}/wall_seconds.txt"
            npg = len([x for x in os.listdir(f"{L.E}/pages/{p}") if re.fullmatch(r"page-\d+\.png", x)]) if os.path.isdir(f"{L.E}/pages/{p}") else 0
            if os.path.exists(f) and npg:
                w[p] = (float(open(f).read().strip()), npg)
        walls[t] = w
    out += ["| run | pieces with a time | pages | wall s per page (total / pages) | median of per-piece s/page |", "|---|---|---|---|---|"]
    for t in tags:
        w = walls[t]
        if not w:
            out.append(f"| {label[t]} | 0 | | missing (per-piece times not pulled) | |")
            continue
        tot, pg = sum(x[0] for x in w.values()), sum(x[1] for x in w.values())
        out.append(f"| {label[t]} | {len(w)} | {pg} | {tot / pg:.2f} | {st.median(x[0] / x[1] for x in w.values()):.2f} |")
    for s, ta, tb in pairs:
        common = [p for p in pieces if p in walls[ta] and p in walls[tb]]
        if common:
            ta_s, tb_s = sum(walls[ta][p][0] for p in common), sum(walls[tb][p][0] for p in common)
            ratios = [(walls[tb][p][0] / walls[tb][p][1]) / (walls[ta][p][0] / walls[ta][p][1]) for p in common]
            out += ["", f"Seed {s}, {len(common)} common pieces: B/A wall ratio {tb_s / ta_s:.2f} (summed), per-piece median {st.median(ratios):.2f}, range {min(ratios):.2f}-{max(ratios):.2f}. "
                    f"Spread of the same measure between A s7 and A s11 (same model size, different run) gives the noise of this timing."]
    ta7, ta11 = arm_tag.get(("A", 7)), arm_tag.get(("A", 11))
    if ta7 and ta11:
        common = [p for p in pieces if p in walls[ta7] and p in walls[ta11]]
        if common:
            r = [(walls[ta11][p][0]) / (walls[ta7][p][0]) for p in common]
            out.append(f"Noise yardstick: A s11 / A s7 wall ratio per piece, median {st.median(r):.2f}, range {min(r):.2f}-{max(r):.2f} over {len(common)} pieces (the same architecture, so the ratio would be 1.0 on a quiet box).")
    out.append("")

    path = f"{T}/RES-FINAL-table-{a.date}{'-' + a.name if a.name else ''}.md"
    open(path, "w").write("\n".join(out) + "\n")
    print("\n".join(out[: out.index("## 3. Per piece")]))
    print("wrote", path)


if __name__ == "__main__":
    main()
