"""Per-staff statistics from token files (run 3 candidate audit and selection).
usage: staff_stats3.py <out.jsonl> <list file>   (list: lines 'image,tokens' or 'tokens')
Fields: key (image path or token path), tok, notes, rests, lines, measures, maxchord (max notes with the
same position in one line), chord4 (bool), ledger (count of notes needing a ledger line), octshift (count
of octaveShift lines), ts (list of timeSignature tokens), keysig.
"""
import json, multiprocessing as mp, re, sys

NOTE = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}
ANCH = {"G2": ("B", 4), "G1": ("D", 5), "F4": ("D", 3), "F3": ("F", 3), "F5": ("B", 2), "C1": ("G", 4),
        "C2": ("E", 4), "C3": ("C", 4), "C4": ("A", 3), "C5": ("F", 3)}
PITCH = re.compile(r"^([A-G])(\d)$")


def dia(p):
    m = PITCH.match(p)
    return int(m[2]) * 7 + NOTE[m[1]] if m else None


def anchor(clef):
    base = clef.replace("clef_", "").split("_")[0]
    a = ANCH.get(base)
    return a[1] * 7 + NOTE[a[0]] if a else None


def work(item):
    key, tok = item
    try:
        lines = open(tok).read().split("\n")
    except Exception:
        return None
    notes = rests = meas = ledger = octs = 0
    voices2 = False
    lastp = {}
    rep_run = {}
    rep3 = False
    fast_run = {}
    max_fast = 0
    maxchord = 0
    clefs = {}
    ts = []
    keysig = None
    for ln in lines:
        if not ln:
            continue
        syms = [s.split(" ") for s in ln.split("&")]
        per = {}
        for f in syms:
            t = f[0]
            pos = f[5] if len(f) == 6 else ""
            grp = "lower" if pos.startswith("lower") else "upper"
            if pos.endswith("2"):
                voices2 = True
            if t.startswith("clef_"):
                clefs[grp] = t
            elif t.startswith("keySignature") and keysig is None:
                keysig = t
            elif t.startswith("timeSignature"):
                ts.append(t)
            elif t.startswith("note"):
                notes += 1
                if len(f) > 1:
                    if lastp.get(pos) == f[1] and pos not in per:
                        rep_run[pos] = rep_run.get(pos, 1) + 1
                    elif pos not in per:
                        rep_run[pos] = 1
                    if pos not in per:
                        lastp[pos] = f[1]
                    if rep_run.get(pos, 1) >= 3:
                        rep3 = True
                if t.split("_")[1].rstrip(".") in ("8", "16", "32", "64", "8G") and pos not in per:
                    fast_run[pos] = fast_run.get(pos, 0) + 1
                    max_fast = max(max_fast, fast_run[pos])
                elif pos not in per:
                    fast_run[pos] = 0
                per[pos] = per.get(pos, 0) + 1
                d = dia(f[1]) if len(f) > 1 else None
                a = anchor(clefs.get(grp, "clef_G2" if grp == "upper" else "clef_F4"))
                if d is not None and a is not None and abs(d - a) >= 6:
                    ledger += 1
            elif t.startswith("rest"):
                rests += 1
            elif t.startswith("octaveShift"):
                octs += 1
            elif t == "barline":
                meas += 1
                fast_run = {}
        if per:
            maxchord = max(maxchord, max(per.values()))
    return dict(key=key, tok=tok, notes=notes, rests=rests, measures=meas, maxchord=maxchord,
                chord4=maxchord >= 4, voices2=voices2, rep3=rep3, max_fast=max_fast, ledger=ledger, octshift=octs, ts=ts, keysig=keysig,
                lines=len([l for l in lines if l]))


def main():
    out, lst = sys.argv[1], sys.argv[2]
    items = []
    for ln in open(lst):
        ln = ln.strip()
        if not ln:
            continue
        p = ln.split(",")
        items.append((p[0], p[-1]))
    with mp.Pool(int(__import__("os").environ.get("NP", "50"))) as pool, open(out, "w") as fo:
        n = 0
        for r in pool.imap(work, items, chunksize=200):
            if r is None:
                continue
            fo.write(json.dumps(r) + "\n")
            n += 1
    print("wrote", n, "of", len(items))


if __name__ == "__main__":
    main()
