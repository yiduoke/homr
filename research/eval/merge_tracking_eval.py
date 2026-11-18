"""D31: re-merge the saved page XML of a run with a merger (default run/merge2_wt/merge_pages.py, the slot tracker) and score it.
No transcription: the pages are those of `--src` (eval_run1/testset/<src>/<piece>/page-xml). Per piece it writes two outputs, scored the
way brace_eval.py scores (rel_wt validation/score_notes.py --ignore-staff, edition-corrected reference, hand_sync.py):
  out/testset/<piece>/<piece>-<tag>.musicxml         merger + drop_minor_parts.py (the harness default)
  out/testset/<piece>/<piece>-<tag>_nodrop.musicxml  merger only (its own rule: a slot with real staves on fewer than half the bars is dropped)
usage: python merge_tracking_eval.py --src SRC_TAG --tag NEW_TAG [--merger PATH] [--pieces P ...] [--workers 6] [--score-only]"""
import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import res_lib as L  # noqa: E402

L.WT = f"{L.R}/rel_wt"
from edition_refs import EDITION  # noqa: E402  (one shared list of edition-corrected pieces)
HOME = "/Users/yiduoke/Documents/homr"


def ref_of(piece):
    return f"{L.OUT}/{piece}/{piece}-reference{'-edition' if piece in EDITION else ''}.musicxml"


def sh(cmd, env=None, cwd=None, log=None):
    f = open(log, "w") if log else subprocess.DEVNULL
    return subprocess.run(cmd, env=env, cwd=cwd, stdout=f, stderr=subprocess.STDOUT).returncode


def score(pred, ref, tag, piece):
    env = {**os.environ, "PYTHONPATH": L.WT}
    if sh([L.PY, "-m", "validation.score_notes", ref, f"{tag}={pred}", "--json", L.score_path(tag, piece), "--ignore-staff"], env=env, cwd=L.WT,
          log=f"{L.OUT}/{piece}/res-score-{tag}.log"):
        return "scoring failed"
    r = subprocess.run([L.PY, f"{L.E}/hand_sync.py", pred, ref], cwd=L.WT, env=env, capture_output=True, text=True)
    try:
        hs = eval(r.stdout.strip().splitlines()[-1])  # a dict literal
    except Exception:
        hs = {"error": (r.stdout + r.stderr)[-200:]}
    json.dump(hs, open(f"{L.OUT}/{piece}/hand-sync-{tag}.json", "w"))
    return "scored"


def one(a, piece):
    pages = f"{L.E}/testset/{a.src}/{piece}/page-xml"
    D = f"{L.E}/merge_tracking/{a.tag}/{piece}"
    os.makedirs(D, exist_ok=True)
    out, out_nd = f"{L.OUT}/{piece}/{piece}-{a.tag}.musicxml", f"{L.OUT}/{piece}/{piece}-{a.tag}_nodrop.musicxml"
    t0 = time.time()
    if not a.score_only:
        env = {**os.environ, "HOMR_TRUST_PAGE_TIME": "1", "HOMR_PAGES": pages, "HOMR_OUT": f"{D}/joined"}
        if sh([L.PY, a.merger], env=env, cwd=HOME, log=f"{D}/merge.log"):
            return f"{piece}: FAILED merge"
        if sh([L.PY, f"{L.R}/drop_minor_parts.py", f"{D}/joined.musicxml", out], log=f"{D}/drop.log"):
            return f"{piece}: FAILED drop"
        subprocess.run(["cp", f"{D}/joined.musicxml", out_nd])
    r1 = score(out, ref_of(piece), a.tag, piece)
    r2 = score(out_nd, ref_of(piece), a.tag + "_nodrop", piece)
    return f"{piece}: {r1}/{r2} in {time.time() - t0:.0f} s"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--src", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--merger", default=f"{L.R}/merge2_wt/merge_pages.py")
    ap.add_argument("--pieces", nargs="*")
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args()
    pieces = a.pieces or L.pieces28()
    sha = hashlib.sha256(open(a.merger, "rb").read()).hexdigest()[:16]
    json.dump({"src": a.src, "tag": a.tag, "merger": a.merger, "merger_sha256_16": sha}, open(f"{L.OUT}/MERGETRACK-{a.tag}-settings.json", "w"))
    with ThreadPoolExecutor(a.workers) as ex:
        for line in ex.map(lambda p: one(a, p), pieces):
            print(time.strftime("%H:%M:%S"), a.tag, line, flush=True)


if __name__ == "__main__":
    main()
