"""D28: run one staff-pairing model through the full page pipeline on the 28 real scans, GPU, common merger, common scorer.

Like res_eval.py (same layout of folders, loop guard, fixed margin, trust page time, drop_minor_parts, scorer with --ignore-staff), but
  * code: run/rel_wt (branch staff-relations-real = integration + HOMR_STAFF_RELATION_MODEL), released transcription weights (default),
  * merger: run/merge_wt/merge_pages.py (branch merge-by-staff-role: parts named by staff role); run/merge_pages.py is not used,
  * references: edition-corrected (Schubert D. 899/4 against its -reference-edition file; Scriabin's reference has no stray part),
  * hand_sync.py per piece (hands in the same reference bar).
usage: python brace_eval.py --tag TAG [--relation PATH_TO_ONNX|shipped] [--pieces P ...] [--force] [--score-only]
GPU unless HOMR_FORCE_CPU=1 is set in the environment (then say so in the tag). Run it under nice, one evaluation at a time.
Output: eval_run1/testset/<TAG>/<piece>/ (pages, page-xml, homr.log, merge.log, drop.log, wall_seconds.txt),
out/testset/<piece>/<piece>-<TAG>.musicxml, res-scores-<TAG>.json (staff-sensitive + staff_agnostic = pooled), hand-sync-<TAG>.json,
out/testset/BRACE-<TAG>-settings.json."""
import argparse
import datetime
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import zoneinfo

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import res_lib as L  # noqa: E402

L.WT = f"{L.R}/rel_wt"
MERGER = f"{L.R}/merge_wt/merge_pages.py"
from edition_refs import EDITION  # noqa: E402  (one shared list of edition-corrected pieces)


def sh(cmd, env=None, cwd=None, log=None):
    f = open(log, "w") if log else subprocess.DEVNULL
    return subprocess.run(cmd, env=env, cwd=cwd, stdout=f, stderr=subprocess.STDOUT).returncode


def sha(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def ref_of(piece: str) -> str:
    return f"{L.OUT}/{piece}/{piece}-reference{'-edition' if piece in EDITION else ''}.musicxml"


def pages_of(piece: str) -> list[str]:
    return sorted(p for p in glob.glob(f"{L.E}/pages/{piece}/page-*.png") if re.fullmatch(r"page-\d+\.png", os.path.basename(p)))


def run_piece(tag, piece, env, force) -> str:
    out = f"{L.OUT}/{piece}/{piece}-{tag}.musicxml"
    if os.path.exists(out) and not force:
        return "kept"
    pages = pages_of(piece)
    if not pages:
        return "no page images"
    D = f"{L.E}/testset/{tag}/{piece}"
    os.makedirs(f"{D}/pages", exist_ok=True)
    for p in pages:
        dst = f"{D}/pages/{os.path.basename(p)}"
        if os.path.lexists(dst):
            os.remove(dst)
        os.symlink(p, dst)
    for stale in glob.glob(f"{D}/page-xml/*") + glob.glob(f"{D}/pages/*.musicxml"):
        os.remove(stale)
    t0 = time.time()
    rc = sh([L.PY, f"{L.E}/run_homr.py", f"{D}/page-xml"] + sorted(glob.glob(f"{D}/pages/page-[0-9]*.png")), env=env, cwd=L.WT, log=f"{D}/homr.log")
    open(f"{D}/wall_seconds.txt", "w").write(f"{time.time() - t0:.1f}\n")
    if rc:
        return f"FAILED homr (see {D}/homr.log)"
    menv = {**os.environ, "HOMR_TRUST_PAGE_TIME": "1", "HOMR_PAGES": f"{D}/page-xml", "HOMR_OUT": f"{D}/joined"}
    if sh([L.PY, MERGER], env=menv, cwd="/Users/yiduoke/Documents/homr", log=f"{D}/merge.log"):
        return f"FAILED merge (see {D}/merge.log)"
    if sh([L.PY, f"{L.R}/drop_minor_parts.py", f"{D}/joined.musicxml", out], log=f"{D}/drop.log"):
        return f"FAILED drop_minor_parts (see {D}/drop.log)"
    return f"done in {time.time() - t0:.0f} s"


def score_piece(tag: str, piece: str) -> str:
    ref, pred = ref_of(piece), f"{L.OUT}/{piece}/{piece}-{tag}.musicxml"
    if not os.path.exists(pred):
        return "no output"
    env = {**os.environ, "PYTHONPATH": L.WT}
    if sh([L.PY, "-m", "validation.score_notes", ref, f"{tag}={pred}", "--json", L.score_path(tag, piece), "--ignore-staff"],
          env=env, cwd=L.WT, log=f"{L.OUT}/{piece}/res-score-{tag}.log"):
        return "scoring failed"
    r = subprocess.run([L.PY, f"{L.E}/hand_sync.py", pred, ref], cwd=L.WT, env=env, capture_output=True, text=True)
    try:
        hs = eval(r.stdout.strip().splitlines()[-1])  # a dict literal printed by hand_sync.py
    except Exception:
        hs = {"error": (r.stdout + r.stderr)[-200:]}
    json.dump(hs, open(f"{L.OUT}/{piece}/hand-sync-{tag}.json", "w"))
    return "scored"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--relation", default="shipped")
    ap.add_argument("--pieces", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args()
    env = {**os.environ, "PYTHONPATH": L.WT, "HOMR_FIXED_MARGIN": "1", "HOMR_LOOP_GUARD": "1"}
    for k in ("HOMR_STAFF_RELATION_MODEL", "HOMR_MODEL_NAME", "HOMR_INPUT_SCALE", "HOMR_ENLARGE_BASE_CROP", "HOMR_HIRES_DIR"):
        env.pop(k, None)
    if a.relation != "shipped":
        env["HOMR_STAFF_RELATION_MODEL"] = a.relation
    la = datetime.datetime.now(zoneinfo.ZoneInfo("America/Los_Angeles"))
    commit = subprocess.run(["git", "-C", L.WT, "describe", "--always", "--dirty"], capture_output=True, text=True).stdout.strip()
    settings = {"tag": a.tag, "relation_model": a.relation, "relation_sha256_16": sha(a.relation) if a.relation != "shipped" else "shipped (pdmx2)",
                "transcription": "released pytorch_model_meteracc-r2s7-afae0e3", "HOMR_FORCE_CPU": os.environ.get("HOMR_FORCE_CPU"),
                "HOMR_LOOP_GUARD": "1", "HOMR_FIXED_MARGIN": "1", "HOMR_TRUST_PAGE_TIME": "1", "code": "rel_wt", "rel_wt_commit": commit,
                "merger": MERGER, "merger_sha256_16": sha(MERGER), "scorer_sha256_16": sha(f"{L.WT}/validation/score_notes.py"),
                "decoder_sha256_16": sha(f"{L.WT}/homr/transformer/decoder_inference.py"),
                "onnx_sha256_16": {os.path.basename(f): sha(f) for f in sorted(glob.glob(f"{L.WT}/homr/transformer/*_pytorch_model_meteracc-r2s7-afae0e3*.onnx"))},
                "started_pacific": la.strftime("%Y-%m-%d %H:%M %Z")}
    json.dump(settings, open(f"{L.OUT}/BRACE-{a.tag}-settings.json", "w"), indent=1)
    print(json.dumps(settings, indent=1), flush=True)
    pieces = a.pieces or L.pieces28()
    t_all = time.time()
    for piece, *_ in L.manifest():
        if piece not in pieces:
            continue
        status = "scoring only" if a.score_only else run_piece(a.tag, piece, env, a.force)
        if status.startswith(("done", "kept")) or a.score_only:
            status += ", " + score_piece(a.tag, piece)
        print(f"{time.strftime('%H:%M:%S')} {a.tag} {piece}: {status}", flush=True)
    print(f"all pieces {time.time() - t_all:.0f} s", flush=True)


if __name__ == "__main__":
    main()
