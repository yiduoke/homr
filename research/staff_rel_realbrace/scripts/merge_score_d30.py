"""merge_score_d30.py (D30, task d): re-merges the saved page XML of the GPU runs (box tags relbrace2_<arm>_s<seed>_gpu, control relbrace2_ctl_gpu) of the three Schott
test scans and the Schott Mazeppa pages with the merger by staff role (run/merge_wt/merge_pages.py, branch merge-by-staff-role), drops minor parts, scores
staff-sensitive and pooled pitch F1 (validation.score_notes, pitch only, run in run/integration_wt) and the hand sync (eval_run1/hand_sync.py).
Mazeppa is scored against run/out/testset/liszt-te-4-schott/liszt-te-4-schott-reference.musicxml = the hand transcription of ANOTHER scan of Mazeppa (Musicaneo, not
the Schott print): its notes are the same piece, the bar layout may differ, so the Mazeppa numbers are provisional.
usage: python merge_score_d30.py TAG [TAG ...]  ->  eval_run1/merge_by_role/d30/<tag>/<piece>/ and results_<tag>.json"""
import json, os, re, subprocess, sys
R = "/Users/yiduoke/Documents/homr/run"; E = f"{R}/eval_run1"; PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"; WT = f"{R}/integration_wt"
OUT = f"{E}/merge_by_role/d30"
PIECES = ["liszt-sonata", "liszt-te-5", "liszt-te-10", "liszt-te-4-schott"]
run = lambda cmd, **kw: subprocess.run(cmd, capture_output=True, text=True, **kw)  # noqa
for tag in sys.argv[1:]:
    res = {}
    for piece in PIECES:
        pages = f"{E}/testset/{tag}/{piece}/page-xml"
        if not os.path.isdir(pages): continue
        ref = f"{R}/out/testset/{piece}/{piece}-reference.musicxml"
        d = f"{OUT}/{tag}/{piece}"; os.makedirs(d, exist_ok=True)
        env = {**os.environ, "HOMR_TRUST_PAGE_TIME": "1", "HOMR_PAGES": pages, "HOMR_OUT": f"{d}/joined"}
        m = run([PY, f"{R}/merge_wt/merge_pages.py"], env=env, cwd="/Users/yiduoke/Documents/homr")
        open(f"{d}/merge.log", "w").write(m.stdout + m.stderr)
        final = f"{d}/final.musicxml"
        dr = run([PY, f"{R}/drop_minor_parts.py", f"{d}/joined.musicxml", final]); open(f"{d}/drop.log", "w").write(dr.stdout + dr.stderr)
        e = {**os.environ, "PYTHONPATH": WT}
        row = {"parts_log": re.findall(r"parts=\d+ measures=\d+", m.stdout)[-1:], "drop": dr.stdout.strip()}
        for kind, extra in (("staff", []), ("pooled", ["--ignore-staff"])):
            js = f"{d}/score-{kind}.json"
            r = run([PY, "-m", "validation.score_notes", ref, f"x={final}", "--json", js, *extra], cwd=WT, env=e)
            try: row[kind] = json.load(open(js))
            except Exception: row[kind] = None; row[kind + "_err"] = (r.stdout + r.stderr)[-300:]
        hs = run([PY, f"{E}/hand_sync.py", final, ref], cwd=WT, env=e); row["hand_sync"] = hs.stdout.strip() or hs.stderr[-200:]
        res[piece] = row
        print(tag, piece, row["parts_log"], row["drop"][:60].replace("\n", " | "), "|", row["hand_sync"][:120], flush=True)
    json.dump(res, open(f"{OUT}/results_{tag}.json", "w"), indent=1)
