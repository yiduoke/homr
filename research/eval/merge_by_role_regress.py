"""D24 regression check: re-merge EVERY saved page set (all tags x pieces in eval_run1/testset/*/*/page-xml) with the merger as it was
and with the staff-role merger; compare the final MusicXML (after drop_minor_parts) with the part ids normalised.
usage: python merge_by_role_regress.py OUTDIR [WORKERS] [TAG,TAG,...]   -> OUTDIR/regress.tsv (tag, piece, same?, parts old/new, bars old/new, notes old/new)"""
import glob, os, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
R = "/Users/yiduoke/Documents/homr/run"; E = f"{R}/eval_run1"; PY = "/Users/yiduoke/Documents/homr/.venv/bin/python"
OUT = sys.argv[1]; W = int(sys.argv[2]) if len(sys.argv) > 2 else 6
TAGS = sys.argv[3].split(",") if len(sys.argv) > 3 else None
jobs = [j for j in sorted(glob.glob(f"{E}/testset/*/*/page-xml")) if TAGS is None or j.split("/")[-3] in TAGS]
def norm(path):
    s = open(path).read()
    ids = {}
    def sub(m):
        return ids.setdefault(m.group(0), f"PID{len(ids)}")
    return re.sub(r"P[0-9a-f]{32}", sub, s)
def stats(path):
    s = open(path).read()
    parts = re.findall(r"<part id=.*?</part>", s, re.S)
    return len(parts), [p.count("<measure ") for p in parts], sum(p.count("<note") for p in parts)
def one(pages):
    tag, piece = pages.split("/")[-3], pages.split("/")[-2]
    d = f"{OUT}/{tag}/{piece}"; os.makedirs(d, exist_ok=True)
    res = {}
    for which, script in (("old", f"{R}/merge_pages.py"), ("new", f"{R}/merge_wt/merge_pages.py")):
        env = {**os.environ, "HOMR_TRUST_PAGE_TIME": "0" if tag.startswith("566") else "1", "HOMR_PAGES": pages, "HOMR_OUT": f"{d}/{which}"}
        if which == "old" and os.path.exists(f"{d}/old-final.musicxml") and os.path.getsize(f"{d}/old-final.musicxml") > 0:
            pass   # the merger as it was does not change: reuse the earlier result of the same page set
        else:
            subprocess.run([PY, script], env=env, cwd="/Users/yiduoke/Documents/homr", capture_output=True)
            subprocess.run([PY, f"{R}/drop_minor_parts.py", f"{d}/{which}.musicxml", f"{d}/{which}-final.musicxml"], capture_output=True)
        try: res[which] = (norm(f"{d}/{which}-final.musicxml"), stats(f"{d}/{which}-final.musicxml"))
        except Exception as e: res[which] = (None, str(e))
    same = res["old"][0] is not None and res["old"][0] == res["new"][0]
    line = f"{tag}\t{piece}\t{'SAME' if same else 'DIFF'}\t{res['old'][1]}\t{res['new'][1]}"
    print(line, flush=True)
    for w in ("old", "new"):
        for ext in ("musicxml", "mid"):
            for f in glob.glob(f"{d}/{w}.{ext}"): os.remove(f)
    return line
with ThreadPoolExecutor(W) as ex:
    lines = list(ex.map(one, jobs))
open(f"{OUT}/regress.tsv", "w").write("\n".join(lines) + "\n")
print("done", sum("\tSAME\t" in l for l in lines), "same of", len(lines))
