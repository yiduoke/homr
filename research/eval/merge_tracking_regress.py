"""D31 regression check: re-merge EVERY saved page set (all tags x pieces in eval_run1/testset/*/*/page-xml) with the merger of D24
(run/merge_wt, branch merge-by-staff-role) and with the slot tracker (run/merge2_wt, branch merge-staff-slots); both outputs go through
drop_minor_parts.py and are compared with the random part ids normalised (and, as a second column, before drop_minor_parts).
usage: python merge_tracking_regress.py OUTDIR [WORKERS] [TAG,TAG,...]  -> OUTDIR/regress.tsv
columns: tag, piece, SAME/DIFF (after drop), SAME/DIFF (merger output before drop), parts/bars/notes old, parts/bars/notes new"""
import glob
import hashlib
import os
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

R = "/Users/yiduoke/Documents/homr/run"
E = f"{R}/eval_run1"
PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"
OUT = sys.argv[1]
W = int(sys.argv[2]) if len(sys.argv) > 2 else 6
TAGS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
jobs = [j for j in sorted(glob.glob(f"{E}/testset/*/*/page-xml")) if TAGS is None or j.split("/")[-3] in TAGS]
MERGERS = {"old": f"{R}/merge_wt/merge_pages.py", "new": f"{R}/merge2_wt/merge_pages.py"}


def norm(path):
    s = open(path).read()
    ids = {}
    return re.sub(r"P[0-9a-f]{32}", lambda m: ids.setdefault(m.group(0), f"PID{len(ids)}"), s)


def stats(path):
    s = open(path).read()
    parts = re.findall(r"<part id=.*?</part>", s, re.S)
    return len(parts), [p.count("<measure ") for p in parts], sum(p.count("<note") for p in parts)


def one(pages):
    tag, piece = pages.split("/")[-3], pages.split("/")[-2]
    d = f"{OUT}/{tag}/{piece}"
    os.makedirs(d, exist_ok=True)
    res = {}
    for which, script in MERGERS.items():
        env = {**os.environ, "HOMR_TRUST_PAGE_TIME": "0" if tag.startswith("566") else "1", "HOMR_PAGES": pages, "HOMR_OUT": f"{d}/{which}"}
        subprocess.run([PY, script], env=env, cwd="/Users/yiduoke/Documents/homr", capture_output=True)
        subprocess.run([PY, f"{R}/drop_minor_parts.py", f"{d}/{which}.musicxml", f"{d}/{which}-final.musicxml"], capture_output=True)
        try:
            res[which] = (norm(f"{d}/{which}-final.musicxml"), stats(f"{d}/{which}-final.musicxml"), norm(f"{d}/{which}.musicxml"))
        except Exception as e:  # noqa: BLE001
            res[which] = (None, str(e), None)
    same = res["old"][0] is not None and res["old"][0] == res["new"][0]
    same_pre = res["old"][2] is not None and res["old"][2] == res["new"][2]
    line = f"{tag}\t{piece}\t{'SAME' if same else 'DIFF'}\t{'SAME' if same_pre else 'DIFF'}\t{res['old'][1]}\t{res['new'][1]}"
    print(line, flush=True)
    if same and same_pre:
        for which in MERGERS:
            for f in glob.glob(f"{d}/{which}*"):
                os.remove(f)
    else:  # keep the outputs of the sets which differ, for inspection (midi never)
        for f in glob.glob(f"{d}/*.mid"):
            os.remove(f)
    return line


with ThreadPoolExecutor(W) as ex:
    lines = list(ex.map(one, jobs))
open(f"{OUT}/regress.tsv", "w").write("\n".join(lines) + "\n")
print("done", sum("\tSAME\tSAME\t" in line for line in lines), "identical (before and after drop) of", len(lines))
