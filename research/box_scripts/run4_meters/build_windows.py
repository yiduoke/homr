"""Build the MusicXML windows of the meter arm (no rendering here).
usage: build_windows.py <round> <n_windows> <pool: train|val> [seed]
Reads mine/src_index_*.jsonl and writes
  xml/<round>/<wid>.musicxml           the window (one part, every bar fills its meter, checked)
  plan/windows_<round>_<pool>.jsonl    one line per window: segments (source, bars, operation), meters, style
Window kinds:
  real       bars of one real score in one meter
  equiv      same bars, other meter of the same duration (3/4 -> 6/8, 2/4 -> 4/8, 4/4 <-> 2/2, ..., C / cut C symbol)
  halve/double  every note value halved/doubled with the beat type (4/4 -> 4/8, 5/8 -> 5/16, 5/16 -> 5/8)
  merge      k consecutive bars joined into one bar (5/4 x2 -> 10/4, 4/4 x2 -> 8/4, 3/4 x3 -> 9/4)
  realchange real bars across a real meter change
  splice     2-4 segments of different scores with different meters one after the other (same staves, clefs)
  merge2     17/16 and 19/16 only: a bar of one meter joined with a bar of another (5/16 + 12/16, 7/16 + 12/16)
Run with nice -n 19; the sources are never modified.
"""
import collections
import glob
import hashlib
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import xml.etree.ElementTree as ET  # noqa: E402

import xmltools as xt  # noqa: E402

ROOT = "/workspace/run4/meters"
COMMON = ["3/4", "4/4", "2/4", "6/8", "3/8", "2/2", "common", "cut"]
NUMERIC = ["1/4", "2/4", "3/4", "4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4", "1/8", "2/8", "3/8", "4/8", "5/8", "6/8",
           "7/8", "9/8", "11/8", "12/8", "13/8", "15/8", "5/16", "7/16", "9/16", "11/16", "12/16", "13/16", "15/16",
           "17/16", "19/16", "2/2", "3/2", "4/2"]
RARE = [m for m in NUMERIC if m not in COMMON]
EQUIV = {"6/8": ["3/4"], "3/4": ["6/8"], "4/8": ["2/4"], "12/16": ["6/8"], "3/2": ["6/4"], "6/4": ["3/2", "12/8"], "12/8": ["6/4"],
         "8/4": ["4/2"], "4/2": ["8/4"], "2/2": ["4/4"], "4/4": ["2/2"], "2/4": ["4/8"]}
HALVE = {"4/8": "4/4", "2/8": "2/4", "1/8": "1/4", "5/8": "5/4", "7/8": "7/4", "9/16": "9/8", "5/16": "5/8", "7/16": "7/8",
         "11/16": "11/8", "13/16": "13/8", "15/16": "15/8", "12/16": "12/8", "3/8": "3/4", "6/8": "6/4", "3/4": "3/2", "2/4": "2/2", "4/4": "4/2",
         "9/8": "9/4", "2/2": None}
DOUBLE = {"1/4": "1/8", "5/4": "5/8", "7/4": "7/8", "11/8": "11/16", "13/8": "13/16", "15/8": "15/16", "4/4": "4/8", "3/4": "3/8",
          "2/4": "2/8", "4/2": "4/4", "9/4": "9/8", "6/4": "6/8", "3/2": "3/4", "2/2": "2/4"}
MERGE = {"10/4": ("5/4", 2), "8/4": ("4/4", 2), "9/4": ("3/4", 3), "12/8": ("6/8", 2), "4/4": ("2/4", 2), "6/4": ("3/4", 2),
         "9/8": ("3/8", 3), "6/8": ("3/8", 2), "3/2": ("3/4", 2), "12/16": ("6/16", 2)}
CROSS = {"17/16": ("5/16", "12/16"), "19/16": ("7/16", "12/16")}
FONTS_VRV = ["Leipzig", "Bravura", "Gootville", "Leland", "Petaluma"]
FONTS_MS = ["Leland", "Bravura", "Petaluma", "MuseJazz", "Gonville"]


def num(m):
    b, d = m.split("/")
    return int(b), int(d)


def dur_q(m):
    b, d = num(m)
    return b * 4 / d


# --------------------------------------------------------------------------- index
def clean(b):
    return bool(b["meter"] and b["ok"] and not b["octave"] and not b["mmrest"] and not b["hidden"] and not b["breve"])


def heldout_hash(stem, pct=8):
    return int(hashlib.sha1(stem.encode()).hexdigest(), 16) % 100 < pct


_SCARCE = None


def scarce_stems():
    """Scores that are the only real source of a meter with fewer than 12 train-pool scores (mine/scarce_stems.txt):
    they stay in training even if their hash would hold them out (otherwise 11/8, 11/16, ... lose their examples)."""
    global _SCARCE  # noqa: PLW0603
    if _SCARCE is None:
        fn = f"{ROOT}/mine/scarce_stems.txt"
        _SCARCE = set(open(fn).read().split()) if os.path.exists(fn) else set()
    return _SCARCE


def heldout(stem, pct=8):
    """Score-level hold-out of the meter arm: 8% of the train-pool scores (by hash of the score name) go to validation."""
    return heldout_hash(stem, pct) and stem not in scarce_stems()


def load_pools(pool):
    runs = collections.defaultdict(list)  # meter -> list of run dicts
    stretches = []
    for fn in sorted(glob.glob(f"{ROOT}/mine/src_index_*.jsonl")):
        for ln in open(fn):
            r = json.loads(ln)
            if os.environ.get("HOLDOUT"):
                if pool == "val" and not (r["pool"] == "val" or heldout(r["stem"])):
                    continue
                if pool == "train" and (r["pool"] != "train" or heldout(r["stem"])):
                    continue
            elif r["pool"] != pool:
                continue
            for pi, p in enumerate(r["parts"]):
                if p["staves"] > 2 or p["transpose"] or not p["measures"]:
                    continue
                ms = p["measures"]
                struct = (p["staves"], tuple(tuple(c) if c else None for c in p["clefs"]))
                i = 0
                while i < len(ms):
                    if not clean(ms[i]):
                        i += 1
                        continue
                    j = i
                    while j + 1 < len(ms) and clean(ms[j + 1]):
                        j += 1
                    # a clean stretch i..j; split into meter runs
                    k = i
                    runs_here = []
                    while k <= j:
                        e = k
                        while e + 1 <= j and ms[e + 1]["meter"] == ms[k]["meter"]:
                            e += 1
                            if ms[e]["sym"] != ms[k]["sym"]:
                                pass
                        runs_here.append((k, e - k + 1, ms[k]["meter"], ms[k]["sym"], ms[k]["fifths"]))
                        k = e + 1
                    for (s0, ln_, meter, sym, fif) in runs_here:
                        runs[meter].append(dict(path=r["path"], set=r["set"], stem=r["stem"], part=pi, start=s0, len=ln_,
                                                sym=sym or "", struct=struct, fifths=fif, div=p["divisions"]))
                    if len(runs_here) > 1:
                        stretches.append(dict(path=r["path"], set=r["set"], stem=r["stem"], part=pi, start=i, len=j - i + 1,
                                              struct=struct, runs=runs_here, div=p["divisions"]))
                    i = j + 1
    return runs, stretches


_cache = collections.OrderedDict()


def load_root(path):
    if path in _cache:
        _cache.move_to_end(path)
        return _cache[path]
    root = ET.parse(path).getroot()
    _cache[path] = root
    if len(_cache) > 40:
        _cache.popitem(last=False)
    return root


# --------------------------------------------------------------------------- segments
class Fail(Exception):
    pass


def pick_run(runs, meter, rng, min_len, struct=None, fifths=None):
    cands = [r for r in runs.get(meter, []) if r["len"] >= min_len and (struct is None or r["struct"] == struct)
             and (fifths is None or r["fifths"] == fifths)]
    if not cands:
        raise Fail(f"no run {meter} {min_len} {struct}")
    return rng.choice(cands)


def make_segment(runs, T, rng, nbars, struct=None, op=None, fifths=None):
    """Segment (measures, start_state, info) for target meter T (string 'n/d' or 'common'/'cut')."""
    sym = ""
    base = T
    if T == "common":
        base, sym = "4/4", "common"
    elif T == "cut":
        base, sym = ("2/2", "cut") if rng.random() < 0.85 else ("4/4", "cut")
    # recipes available
    recs = []
    if runs.get(base):
        recs.append(("real", base, 3.0))
    if T in ("common", "cut", "4/4", "2/2"):
        recs.append(("sym", base, 2.0))
    for s in EQUIV.get(base, []):
        recs.append(("equiv", s, 1.5))
    if base in HALVE and HALVE[base]:
        recs.append(("halve", HALVE[base], 2.0))
    if base in DOUBLE:
        recs.append(("double", DOUBLE[base], 1.5))
    if base in MERGE:
        recs.append(("merge", MERGE[base][0], 1.5))
    if base in RARE and base not in ("17/16", "19/16"):
        # for rare meters the real bars are scarce: derived recipes get more weight, real bars stay
        pass
    rng.shuffle(recs)
    if op:
        recs = [x for x in recs if x[0] == op]
    # weighted order
    order = []
    pool_ = list(recs)
    while pool_:
        w = [x[2] for x in pool_]
        pick = rng.choices(range(len(pool_)), w)[0]
        order.append(pool_.pop(pick))
    for kind, S, _w in order:
        try:
            k = MERGE[base][1] if kind == "merge" else 1
            need = nbars * k
            r = pick_run(runs, S, rng, max(2 if nbars > 1 else 1, k), struct, fifths)
            m = min(r["len"], need)
            n_src = m - (m % k)
            if n_src < k:
                continue
            off = rng.randint(0, r["len"] - n_src)
            root = load_root(r["path"])
            measures, state, _end = xt.segment(root, r["part"], r["start"] + off, r["start"] + off + n_src)
            b, d = num(base)
            ok = True
            if kind == "real":
                if sym:
                    xt.set_meter(measures, state, b, d, sym)
                elif T in ("4/4", "2/2"):
                    xt.set_meter(measures, state, b, d, "")  # numeric version of a score that may print C
            elif kind == "sym":
                xt.set_meter(measures, state, b, d, sym)
            elif kind == "equiv":
                xt.set_meter(measures, state, b, d, sym)
            elif kind == "halve":
                ok = xt.retime(measures, state, 0.5)
            elif kind == "double":
                ok = xt.retime_double(measures, state)
            elif kind == "merge":
                measures = xt.merge_k(measures, state, k, b, d, sym)
            if not ok:
                continue
            info = dict(src=r["stem"], set=r["set"], part=r["part"], start=r["start"] + off, bars=len(measures), op=kind,
                        from_meter=S, meter=T)
            return measures, state, info, r["struct"]
        except Fail:
            continue
        except ValueError:
            continue
    raise Fail(f"no recipe for {T}")


def lcm_divisions(segs):
    ds = [int(st["divisions"].text) for _m, st, _i in segs]
    L = 1
    for d in ds:
        L = L * d // math.gcd(L, d)
    return L


def normalise_divisions(segs):
    L = lcm_divisions(segs)
    if L > 20000:
        raise Fail("divisions")
    for m, st, _i in segs:
        f = L // int(st["divisions"].text)
        if f != 1:
            xt.scale_divisions(m, st, f)


# --------------------------------------------------------------------------- chains
def meter_weights(rng, rare_boost):
    pass


def sample_chain(runs, rng, target_rare, k):
    """Meters of a splice window: an anchor (rare with prob rare_boost) and others; same-denominator 50%."""
    seq = []
    anchor = target_rare
    seq.append(anchor)
    cur = anchor
    for _ in range(k - 1):
        dens = {"4": ["1/4", "2/4", "3/4", "4/4", "5/4", "6/4", "7/4"], "8": ["3/8", "6/8", "9/8", "12/8", "5/8", "7/8", "4/8"],
                "2": ["2/2", "3/2", "4/2", "cut"]}
        key = cur.split("/")[1] if "/" in cur else ("4" if cur == "common" else "2")
        if rng.random() < 0.5 and key in dens:
            nxt = rng.choice(dens[key])
        else:
            nxt = rng.choice(COMMON) if rng.random() < 0.7 else rng.choice(RARE)
        if os.environ.get("COMMON_ONLY") and nxt not in COMMON:
            nxt = rng.choice(COMMON)
        if nxt == cur:
            nxt = rng.choice([m for m in COMMON if m != cur])
        seq.append(nxt)
        cur = nxt
    if rng.random() < 0.5:
        seq.reverse()
    return seq


def build_one(runs, stretches, rng, kind, T, wid):
    """Returns (root, info) or raises Fail."""
    segs = []
    structs = []
    if kind in ("real", "equiv", "halve", "double", "merge", "sym"):
        nbars = rng.randint(8, 16)
        op = {"real": "real", "equiv": "equiv", "halve": "halve", "double": "double", "merge": "merge", "sym": "sym"}[kind]
        nb = nbars if op != "merge" else rng.randint(5, 10)
        m, st, info, struct = make_segment(runs, T, rng, nb, op=op)
        segs.append((m, st, info))
        structs.append(struct)
    elif kind == "realchange":
        cands = [s for s in stretches]
        if not cands:
            raise Fail("no stretches")
        s = rng.choice(cands)
        r0 = rng.randrange(len(s["runs"]) - 1)
        # window from some bars before the change to some after
        a = s["runs"][r0]
        b = s["runs"][r0 + 1]
        before = min(a[1], rng.randint(2, 6))
        after = min(b[1] + (s["runs"][r0 + 2][1] if r0 + 2 < len(s["runs"]) and rng.random() < 0.5 else 0), rng.randint(3, 8))
        m0 = a[0] + a[1] - before
        m1 = b[0] + after
        root = load_root(s["path"])
        measures, state, _e = xt.segment(root, s["part"], m0, m1)
        segs.append((measures, state, dict(src=s["stem"], set=s["set"], part=s["part"], start=m0, bars=m1 - m0, op="realchange", meter="mixed")))
    elif kind == "splice":
        k = rng.choices([2, 3, 4], [0.5, 0.35, 0.15])[0]
        seq = sample_chain(runs, rng, T, k)
        struct = None
        # anchor first for structure (rare ones are scarce): build the rarest first
        order = sorted(range(k), key=lambda i: 0 if seq[i] in RARE else 1)
        built = {}
        for i in order:
            nb = rng.randint(2, 5)
            m, st, info, s_ = make_segment(runs, seq[i], rng, nb, struct=struct)
            struct = s_ if struct is None else struct
            built[i] = (m, st, info)
        segs = [built[i] for i in range(k)]
    elif kind == "alt":
        # the rare meter again and again between other meters: T X T Y T ...
        k = rng.randint(3, 6)
        seq = []
        for i in range(k):
            seq.append(T if i % 2 == 0 else (rng.choice(COMMON) if (rng.random() < 0.7 or os.environ.get("COMMON_ONLY")) else rng.choice(RARE)))
        struct = None
        built = {}
        for i in sorted(range(k), key=lambda i: 0 if seq[i] == T else 1):
            m, st, info, s_ = make_segment(runs, seq[i], rng, rng.randint(2, 3), struct=struct)
            struct = s_ if struct is None else struct
            built[i] = (m, st, info)
        segs = [built[i] for i in range(k)]
    elif kind == "merge2":
        a_m, b_m = CROSS[T]
        nb = rng.randint(1, 3)
        pieces = []
        struct = None
        fifths = rng.choice([0, 0, 1, -1, 2, -2, 3, -3])
        for _ in range(nb):
            ma, sa, ia, s1 = make_segment(runs, a_m, rng, 1, struct=struct, fifths=fifths)
            struct = s1
            mb, sb, ib, _s2 = make_segment(runs, b_m, rng, 1, struct=struct, fifths=fifths)
            pieces.append(((ma, sa, ia), (mb, sb, ib)))
        # normalise divisions across everything
        allsegs = [x for p in pieces for x in p]
        normalise_divisions(allsegs)
        bars = []
        b, d = num(T)
        for (ma, sa, ia), (mb, sb, ib) in pieces:
            order = [ma[0], mb[0]] if rng.random() < 0.5 else [mb[0], ma[0]]
            # the later bar must not restate the time signature (removed in merge) and the first bar carries none (state does)
            merged, _ = xt.merge_measures(order, b, d)
            bars.append(merged)
        st0 = pieces[0][0][1]
        xt.set_meter(bars, st0, b, d, "")
        info = dict(src="+".join(sorted({p[0][2]["src"] for p in pieces} | {p[1][2]["src"] for p in pieces})), set="mixed", part=0, start=0,
                    bars=len(bars), op="merge2", meter=T)
        # filler: a few bars of an equivalent plain meter before and after? keep just the merged bars + one bar of 4/4 neighbours is not needed
        segs = [(bars, st0, info)]
        # follow with bars of a common meter to give the system some context
        mm, ss, ii, _s3 = make_segment(runs, rng.choice(["3/4", "4/4", "2/4"]), rng, rng.randint(2, 4), struct=struct, fifths=fifths)
        segs.append((mm, ss, ii))
        # the first part (bars of the cross meter) must fill the front: add context in front as well
        segs = [segs[1]] + segs if rng.random() < 0.3 else segs
    else:
        raise Fail("kind")
    normalise_divisions(segs)
    root = xt.assemble([(m, st) for m, st, _i in segs])
    ok, problems = xt.check_bars(root)
    if not ok:
        raise Fail(f"bars {problems[:3]}")
    ok, problems = xt.check_types(root)
    if not ok:
        raise Fail(f"types {problems[:3]}")
    return root, [i for _m, _s, i in segs]


# --------------------------------------------------------------------------- main
def plan_kinds(n, rng):
    kinds = ["real", "equiv", "halve", "double", "merge", "sym", "realchange", "splice"]
    weights = [0.10, 0.07, 0.14, 0.04, 0.04, 0.03, 0.08, 0.50]
    if os.environ.get("COMMON_ONLY"):
        kinds = ["real", "equiv", "sym", "realchange", "splice", "alt"]
        weights = [0.15, 0.10, 0.05, 0.10, 0.50, 0.10]
    elif os.environ.get("RARE_FOCUS"):
        kinds = ["real", "halve", "double", "merge", "splice", "alt"]
        weights = [0.10, 0.15, 0.05, 0.05, 0.35, 0.30]
    return rng.choices(kinds, weights, k=n)


def main():
    rnd, n, pool = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    seed = int(sys.argv[4]) if len(sys.argv) > 4 else 1
    rng = random.Random(f"{rnd}-{pool}-{seed}")
    runs, stretches = load_pools(pool)
    print("pool", pool, "runs for", len(runs), "meters; stretches with changes", len(stretches), flush=True)
    os.makedirs(f"{ROOT}/xml/{rnd}", exist_ok=True)
    os.makedirs(f"{ROOT}/plan", exist_ok=True)
    out = open(f"{ROOT}/plan/windows_{rnd}_{pool}.jsonl", "w")
    made = fails = 0
    cnt = collections.Counter()
    tries = 0
    while made < n and tries < n * 6:
        tries += 1
        kind = plan_kinds(1, rng)[0]
        # target meter: rare with prob .55 (deficit weighting is done in the lists step), common otherwise
        if kind in ("halve", "double", "merge") and os.environ.get("RARE_FOCUS"):
            tab = {"halve": HALVE, "double": DOUBLE, "merge": MERGE}[kind]
            foc = [m for m in os.environ["RARE_FOCUS"].split(",") if m in tab and (tab[m] if kind != "halve" else True)]
            T = rng.choice(foc) if foc else rng.choice(os.environ["RARE_FOCUS"].split(","))
        elif kind in ("halve", "double", "merge"):
            T = rng.choice(sorted({"halve": HALVE, "double": DOUBLE, "merge": MERGE}[kind].keys()))
        elif kind == "equiv":
            T = rng.choice(sorted(EQUIV))
        elif kind == "sym":
            T = rng.choice(["common", "cut", "4/4", "2/2"])
        elif os.environ.get("RARE_FOCUS"):
            foc = os.environ["RARE_FOCUS"].split(",")
            T = rng.choice(foc)
        else:
            T = rng.choice(RARE) if rng.random() < 0.55 else rng.choice(COMMON)
        if kind == "merge2" or (kind == "splice" and rng.random() < 0.03):
            kind, T = "merge2", rng.choice(sorted(CROSS))
        wid = f"w{rnd}{pool[0]}{made:05d}"
        try:
            root, infos = build_one(runs, stretches, rng, kind, T, wid)
        except Fail as e:
            fails += 1
            cnt["fail_" + kind] += 1
            continue
        except Exception as e:  # noqa: BLE001
            fails += 1
            cnt["err_" + kind] += 1
            continue
        meters = xt.meters_of(root)
        if os.environ.get("COMMON_ONLY"):
            ok_c = True
            for mm in meters:
                base = (mm or "").split(":")[0]
                sym = (mm or "").split(":")[1] if ":" in (mm or "") else ""
                key = sym if sym in ("common", "cut") else base
                if key not in COMMON:
                    ok_c = False
            if not ok_c:
                continue
        nb = len(meters)
        if nb > 26:
            continue
        # style
        renderer = "vrv" if rng.random() < 0.6 else "ms"
        tsclass = rng.choices(["small", "normal", "large"], [0.42, 0.45, 0.13])[0]
        tsscale = {"small": rng.choice([0.5, 0.58, 0.66, 0.74]), "normal": 1.0, "large": rng.choice([1.2, 1.3, 1.4])}[tsclass]
        spec = dict(wid=wid, round=rnd, pool=pool, kind=kind, target=T, bars=nb, meters=meters, segments=infos, renderer=renderer,
                    font=rng.choice(FONTS_VRV if renderer == "vrv" else FONTS_MS), tsclass=tsclass, tsscale=tsscale,
                    vrv_scale=rng.choice([30, 35, 40, 40, 45]) if renderer == "vrv" else None)
        with open(f"{ROOT}/xml/{rnd}/{wid}.musicxml", "w") as f:
            f.write(xt.to_string(root))
        out.write(json.dumps(spec) + "\n")
        out.flush()
        made += 1
        cnt[kind] += 1
        if made % 100 == 0:
            print(made, dict(cnt), flush=True)
    print("done", made, "fails", fails, dict(cnt))


if __name__ == "__main__":
    main()
