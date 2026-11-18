"""D24: re-merge the saved page outputs of the three Schott Liszt scans with the merger as it was (run/merge_pages.py) and with
the staff-role merger (run/merge_wt/merge_pages.py, branch merge-by-staff-role); score both, no inference.
usage: python merge_by_role_eval.py [TAG ...]   -> eval_run1/merge_by_role/{old,new}/<tag>/<piece>/..., merge_by_role/results.json"""
import json, os, subprocess, sys, re
R = "/Users/yiduoke/Documents/homr/run"; E = f"{R}/eval_run1"; PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"; WT = f"{R}/integration_wt"
OUT = f"{E}/merge_by_role"
MERGERS = {"old": f"{R}/merge_pages.py", "new": f"{R}/merge_wt/merge_pages.py"}
tags = sys.argv[1:] or ["relctl", "relbrace", "relB0", "relC0"]
res = {}
def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)
for tag in tags:
    for piece in ["liszt-sonata", "liszt-te-5", "liszt-te-10"]:
        pages = f"{E}/testset/{tag}/{piece}/page-xml"
        if not os.path.isdir(pages): continue
        ref = f"{R}/out/testset/{piece}/{piece}-reference.musicxml"
        for which, script in MERGERS.items():
            d = f"{OUT}/{which}/{tag}/{piece}"; os.makedirs(d, exist_ok=True)
            env = {**os.environ, "HOMR_TRUST_PAGE_TIME": "1", "HOMR_PAGES": pages, "HOMR_OUT": f"{d}/joined"}
            m = run([PY, script], env=env, cwd="/Users/yiduoke/Documents/homr")
            open(f"{d}/merge.log", "w").write(m.stdout + m.stderr)
            final = f"{d}/final.musicxml"
            dr = run([PY, f"{R}/drop_minor_parts.py", f"{d}/joined.musicxml", final])
            open(f"{d}/drop.log", "w").write(dr.stdout + dr.stderr)
            e = {**os.environ, "PYTHONPATH": WT}
            row = {"parts_log": re.findall(r"parts=\d+ measures=\d+", m.stdout)[-1:], "drop": dr.stdout.strip()}
            for kind, extra in (("staff", []), ("pooled", ["--ignore-staff"])):
                js = f"{d}/score-{kind}.json"
                r = run([PY, "-m", "validation.score_notes", ref, f"x={final}", "--json", js, *extra], cwd=WT, env=e)
                try:
                    j = json.load(open(js)); row[kind] = j
                except Exception:
                    row[kind] = None; row[kind + "_err"] = (r.stdout + r.stderr)[-300:]
            hs = run([PY, f"{E}/hand_sync.py", final, ref], cwd=WT, env=e)
            row["hand_sync"] = hs.stdout.strip() or hs.stderr[-200:]
            res.setdefault(tag, {}).setdefault(piece, {})[which] = row
            print(tag, piece, which, row["parts_log"], row["drop"][:80].replace("\n", " | "), flush=True)
json.dump(res, open(f"{OUT}/results.json", "w"), indent=1)
