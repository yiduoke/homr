"""Label checks for the run-3 token files (written by relabel_run3.py), no images.
usage: verify_run3.py <tokens list file: lines 'image,run1_token' (selected_<set>.txt)> <set> <out.json> [root]
root = directory with the new tokens (default /workspace/run3/tokens; /workspace/run2/tokens for a control).
(a) the new file equals the run-1 file apart from the lift field;
(b) lift distribution old (sounding alteration of run 1) vs new (printed sign);
(c) consistency (a sign printed on one of several same-pitch notes of a line counts for all; mismatches in the first bar of a staff and old-label ##/bb rewrites are counted apart): the sounding alteration computed from the new printed signs (key signature, signs carried in the
    bar per staff and octave, ties) equals the run-1 lift. A mismatch means a missing, spurious or wrong printed
    sign (or a tie across the staff start, counted apart).
"""
import collections, json, os, sys
from multiprocessing import Pool

sys.path.insert(0, "/workspace/homr_acc")
from homr.accidentals import AccidentalState, SIGN_TO_ALTER  # noqa: E402

ROOT = "/workspace/run3/tokens"
OLD = {"_": 0, "N": 0, "#": 1, "b": -1, "##": 2, "bb": -2}


def newpath(t):
    return ROOT + "/" + t[len("/workspace/"):]


def one(t):
    a = open(t).read().split("\n")
    p = newpath(t)
    if not os.path.exists(p):
        return None
    b = open(p).read().split("\n")
    res = dict(bad=None, old=collections.Counter(), new=collections.Counter(), notes=0, mism=0, mism_tie_start=0,
               mism_kinds=collections.Counter(), staff_mism=0)
    if len(a) != len(b):
        res["bad"] = "line count"
        return res
    state = AccidentalState(0)
    last_pitch_slur = {}
    seen_bar = False
    mism_any = False
    for i, (x, y) in enumerate(zip(a, b)):
        px, py = x.split("&"), y.split("&")
        if len(px) != len(py):
            res["bad"] = f"line {i} parts"
            return res
        notes_line = []
        for pp, qq in zip(px, py):
            f, g = pp.strip().split(" "), qq.strip().split(" ")
            if len(f) != len(g):
                res["bad"] = f"line {i} fields"
                return res
            if len(f) != 6:
                if pp != qq:
                    res["bad"] = f"line {i}: {pp} | {qq}"
                    return res
                continue
            f2, g2 = list(f), list(g)
            f2[2] = g2[2] = ""
            if f2 != g2:
                res["bad"] = f"line {i}: {pp} | {qq}"
                return res
            if f[0] == "barline" or f[0].startswith("repeat"):
                state.new_bar(); seen_bar = True
                continue
            if f[0].startswith("keySignature_"):
                state.set_key(int(f[0].split("_")[1]))
                continue
            if f[0].startswith("note"):
                notes_line.append((f, g))
        # a sign printed on one of several notes of the same step and octave in the line counts for all of them
        line_sign = {}
        for f, g in notes_line:
            if g[2] in SIGN_TO_ALTER:
                line_sign[(f[5].rstrip("2"), f[1][0], int(f[1][1:]))] = g[2]
        for f, g in notes_line:
            old, new = f[2], g[2]
            res["old"][old] += 1
            res["new"][new] += 1
            step, octave = f[1][0], int(f[1][1:])
            staff = f[5].rstrip("2")
            slur_stop = "slurStop" in f[4]
            slur_start = "slurStart" in f[4]
            key = (staff, step, octave)
            tie_alter = None
            if slur_stop and key in last_pitch_slur:
                tie_alter = last_pitch_slur[key][0]
            shared = False
            if new not in SIGN_TO_ALTER and key in line_sign:
                new = line_sign[key]
                shared = True
            sounding = state.sounding_alter(staff, step, octave, new, tie_alter)
            expect = OLD[old]
            res["notes"] += 1
            if sounding != expect:
                if old == "_" and g[2] in ("##", "bb"):
                    res["mism_old_bug"] = res.get("mism_old_bug", 0) + 1
                elif not seen_bar:
                    res["mism_first_bar"] = res.get("mism_first_bar", 0) + 1
                    res["mism_tie_start"] += 1
                else:
                    res["mism"] += 1
                    res["mism_kinds"][f"{old}->{g[2]}(got {sounding})"] += 1
                    mism_any = True
                    if "first" not in res:
                        res["first"] = (t, i, f"{old}->{g[2]} got {sounding}")
            if slur_start:
                last_pitch_slur[key] = (expect, True)
    res["staff_mism"] = int(mism_any)
    return res


def main():
    global ROOT
    lst, name, out = sys.argv[1:4]
    if len(sys.argv) > 4:
        ROOT = sys.argv[4]
    toks = sorted({l.strip().split(",")[-1] for l in open(lst) if l.strip()})
    tot = dict(files=0, missing=0, bad=0, notes=0, mism=0, mism_tie_start=0, staff_mism=0,
               old=collections.Counter(), new=collections.Counter(), kinds=collections.Counter())
    bads = []
    firsts = []
    with Pool(50) as p:
        for t, r in zip(toks, p.imap(one, toks, chunksize=64)):
            if r is None:
                tot["missing"] += 1
                continue
            tot["files"] += 1
            if r["bad"]:
                tot["bad"] += 1
                bads.append((t, r["bad"]))
                continue
            for k in ("notes", "mism", "mism_tie_start", "staff_mism"):
                tot[k] += r[k]
            tot["mism_old_bug"] = tot.get("mism_old_bug", 0) + r.get("mism_old_bug", 0)
            tot["old"].update(r["old"]); tot["new"].update(r["new"]); tot["kinds"].update(r["mism_kinds"])
            if "first" in r:
                firsts.append(r["first"])
    print(name, "files", tot["files"], "missing(dropped)", tot["missing"], "other-field diffs", tot["bad"], "notes", tot["notes"],
          "mismatch notes", tot["mism"], f"({100*tot['mism']/max(1,tot['notes']):.3f}%)",
          "staffs with mismatch", tot["staff_mism"], f"({100*tot['staff_mism']/max(1,tot['files']):.2f}%)",
          "first-bar (tie/carry from before the staff, not judged)", tot["mism_tie_start"], "old-label ##/bb bug", tot.get("mism_old_bug", 0))
    print("  old", {k: tot["old"][k] for k in ("_", "#", "b", "N", "##", "bb")})
    print("  new", {k: tot["new"][k] for k in ("_", "#", "b", "N", "##", "bb")})
    print("  top mismatch kinds", tot["kinds"].most_common(8))
    print("  BAD", bads[:3])
    json.dump({k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in tot.items()} | {"bads": bads[:20]}, open(out, "w"), indent=1)
    json.dump(firsts, open(out.replace(".json", "_first.json"), "w"))


if __name__ == "__main__":
    main()
