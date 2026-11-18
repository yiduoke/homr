"""Re-score every saved prediction of every edition-corrected piece (eval_run1/edition_refs.py: EDITION) against its -reference-edition file, staff-sensitive and pooled
(validation/score_notes.py of res_wt = integration_wt, `--ignore-staff` for the pooled/staff_agnostic block), plus the dense-bar file. Existing -edition files are kept; later tags
(e.g. the pilot_* ones the pilot automation adds) are picked up by running this again:  python octave_checks/rescore_edition.py [--force] [--piece P ...]
Also scores the ORIGINAL reference once per tag into octave_checks/edition_scores/<piece>/<tag>-orig(.pooled).json (so before/after use the same scorer, same day) and writes
octave_checks/edition_scores/before_after.json and EDITION_RESCORE.md (per piece and tag: staff-sensitive and pooled pitch F1 / +onset, before and after)."""
import argparse, json, os, subprocess, sys
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/eval_run1")
import edition_refs as E
import res_lib as L
import res_final_table as F

OUTD = "/Users/yiduoke/Documents/homr/run/octave_checks/edition_scores"

def score_orig(piece, tag, force):
    pred = f"{E.OUT}/{piece}/{piece}-{tag}.musicxml"
    ref = f"{E.OUT}/{piece}/{piece}-reference.musicxml"
    d = f"{OUTD}/{piece}"; os.makedirs(d, exist_ok=True)
    fs, fp = f"{d}/{tag}-orig.json", f"{d}/{tag}-orig.pooled.json"
    if force or not os.path.exists(fs): F.run_scorer(ref, tag, pred, fs, False)
    if force or not os.path.exists(fp): F.run_scorer(ref, tag, pred, fp, True)
    return fs, fp

def row(res):
    m = L._metrics(res["metrics"]); return {k: round(m[k], 2) for k in ("f1", "po", "full")}

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--force", action="store_true"); ap.add_argument("--piece", nargs="*"); a = ap.parse_args()
    pieces = a.piece or sorted(E.EDITION)
    res = {}
    for p in pieces:
        for tag in E.tags_with_outputs(p):
            st = F.rescore_edition_piece(p, tag, a.force)
            fs, fp = score_orig(p, tag, a.force)
            T, P = E.OUT, f"{E.R}/out/pooled"
            es = F.first_result(f"{T}/{p}/note-scores-{tag}-edition.json"); ep = F.first_result(f"{P}/{p}/{tag}-edition.json")
            os_ = F.first_result(fs); op = F.first_result(fp)
            sa = lambda r: row({"metrics": (r.get("staff_agnostic") or {}).get("metrics") or r["metrics"]})
            res.setdefault(p, {})[tag] = {"status": st, "sens_before": row(os_), "sens_after": row(es), "pooled_before": sa(op), "pooled_after": sa(ep)}
            print(p, tag, st, res[p][tag]["sens_before"]["f1"], "->", res[p][tag]["sens_after"]["f1"], "pooled", res[p][tag]["pooled_before"]["f1"], "->", res[p][tag]["pooled_after"]["f1"], flush=True)
    os.makedirs(OUTD, exist_ok=True)
    json.dump(res, open(f"{OUTD}/before_after.json", "w"), indent=1)
    L_ = ["# Edition-reference rescoring, all saved tags (D33)", "", "Pitch inventory F1 %, +onset in brackets. Same scorer for both columns, run on the same day; staff-sensitive and pooled (staff_agnostic block). Visible notes only.", ""]
    for p, tags in res.items():
        L_ += [f"## {p}", "", "| tag | staff-sens before | staff-sens after | pooled before | pooled after |", "|---|---|---|---|---|"]
        c = lambda r: f"{r['f1']:.1f} ({r['po']:.1f})"
        for t, r in tags.items(): L_.append(f"| {t} | {c(r['sens_before'])} | {c(r['sens_after'])} | {c(r['pooled_before'])} | {c(r['pooled_after'])} |")
        L_.append("")
    open(f"{OUTD}/EDITION_RESCORE.md", "w").write("\n".join(L_))

if __name__ == "__main__": main()
