"""Run-3 candidate selection (step 1 of the list build). Needs stats/*.jsonl from staff_stats3.py.
Writes lists/selected_<set>.txt (image,run-1 token path), lists/selection.json (role train|val per staff,
selection details). Seeds: SEED below.
Only staffs which pass the training-time filters (sequence length, at most 5 ledger lines, vocabulary; Scriabin
Verovio crops of part >= 1 left out) take part: lists/valid_<set>.txt from valid_staffs.py.
Hard PDMX: pool = index_excl_v2 staffs that are in none of the control lists (train, val, holdout_real,
holdout_inserted); sampled by score (all pool staffs of a score together), weight (density/median)^2 with
density = mean notes per pool staff (Efraimidis-Spirakis keys), scores with more than MAX_SCORE_STAFFS pool
staffs and density below MIN_DENSITY are not eligible; meter quota: every meter that is not one of the
common ones gets up to RARE_QUOTA staffs first. Then about HOLD_HARD staffs of whole scores that never
occur in any control list are moved to the held-out list.
ASAP and Scriabin: all staffs; whole pieces (by name without -vrv) are moved to the held-out list until
about HOLD_ASAP / HOLD_SCR staffs.
"""
import collections, json, random, re
import numpy as np

SEED = 20261117
TARGET_TOTAL = 21000      # hard PDMX staffs before the held-out split (20,000 train + ~1,000 held out)
HOLD_HARD, HOLD_ASAP, HOLD_SCR = 1000, 300, 100
MAX_SCORE_STAFFS = 100
MIN_DENSITY = 15.0
RARE_QUOTA = 400
COMMON = {"timeSignature_4/4", "timeSignature_3/4", "timeSignature_2/4", "timeSignature_6/8",
          "timeSignature_common", "timeSignature_cut", "none"}
S = "/workspace/run3/"
rng = random.Random(SEED)


VALID = {}


def load(n):
    """Staff statistics of a set, only staffs which pass the training filters (lists/valid_<set>.txt, valid_staffs.py)."""
    if n not in VALID:
        VALID[n] = {l.strip() for l in open(f"{S}lists/valid_{n}.txt")}
    return [r for r in (json.loads(l) for l in open(f"{S}stats/{n}.jsonl")) if r["key"] in VALID[n]]


sid_re = re.compile(r"/(Qm[A-Za-z0-9]{44})-(?:vrv-)?\d+-\d+\.png$")
ord_re = re.compile(r"-(vrv-)?(\d+)-(\d+)\.png$")

control_keys = set()
for f in ["run2_train_excl.txt", "run2_val_excl.txt", "holdout_real_excl.txt", "holdout_inserted_excl.txt"]:
    control_keys |= {l.split(",")[0] for l in open(S + f) if l.strip()}

# the octave sets (musescore_octave, lilypond) are made from PDMX scores too, with other image paths: a score counts as
# "in control" when its hash (Qm + 44 characters) occurs in any control line, whatever the set
hash_re = re.compile(r"(Qm[A-Za-z0-9]{44})")
control_scores = set()
for f in ["run2_train_excl.txt", "run2_val_excl.txt", "holdout_real_excl.txt", "holdout_inserted_excl.txt"]:
    for l in open(S + f):
        m = hash_re.search(l.split(",")[0])
        if m:
            control_scores.add(m[1])
hp = load("pdmx_hard")
by_score = collections.defaultdict(list)
for r in hp:
    by_score[sid_re.search(r["key"])[1]].append(r)


def staff_order(r):
    m = ord_re.search(r["key"])
    return (1 if m[1] else 0, int(m[2]), int(m[3]))


def score_meters(rows):
    """All time signature tokens of the score (any staff), in staff order, first = opening meter."""
    out = []
    for r in sorted(rows, key=staff_order):
        for t in r["ts"]:
            if t not in out:
                out.append(t)
    return out or ["none"]


def score_meter(rows):
    for r in sorted(rows, key=staff_order):
        if r["ts"]:
            return r["ts"][0]
    return "none"


in_control = {s for s, rows in by_score.items() if s in control_scores or any(r["key"] in control_keys for r in rows)}
info = {}
for s, rows in by_score.items():
    pool = [r for r in rows if r["key"] not in control_keys]
    if not pool:
        continue
    info[s] = dict(pool=pool, n=len(pool), dens=float(np.mean([r["notes"] for r in pool])),
                   meter=score_meter(rows), meters=score_meters(rows), ctl=s in in_control)
med = float(np.median([v["dens"] for v in info.values()]))
elig = {s: v for s, v in info.items() if v["n"] <= MAX_SCORE_STAFFS and v["dens"] >= MIN_DENSITY}
print("pool scores", len(info), "staffs", sum(v["n"] for v in info.values()), "| eligible", len(elig),
      "staffs", sum(v["n"] for v in elig.values()), "| median density", round(med, 1))


def es_order(ids):
    keys = {s: rng.random() ** (1.0 / max((elig[s]["dens"] / med) ** 2, 1e-6)) for s in ids}
    return sorted(ids, key=lambda s: -keys[s])


chosen, total = [], 0
chosen_set = set()
# 1. rare meters
# a score belongs to every rare class (a meter outside COMMON) that occurs anywhere in it, also as a
# meter change; the quota counts the staffs of the chosen scores that contain the class
cls = collections.defaultdict(list)
for s, v in elig.items():
    for m in v["meters"]:
        if m not in COMMON:
            cls[m].append(s)
for m in sorted(cls, key=lambda m: len(cls[m])):
    got = sum(elig[s]["n"] for s in chosen_set if m in elig[s]["meters"])
    for s in es_order([s for s in cls[m] if s not in chosen_set]):
        if got >= RARE_QUOTA:
            break
        chosen.append(s); chosen_set.add(s); got += elig[s]["n"]
total = sum(elig[s]["n"] for s in chosen)
print("rare meter classes", len(cls), "scores", len(chosen), "staffs", total)
# 2. fill by weight
for s in es_order([s for s in elig if s not in chosen_set]):
    if total >= TARGET_TOTAL:
        break
    if total + elig[s]["n"] > TARGET_TOTAL + 150:
        continue
    chosen.append(s); chosen_set.add(s); total += elig[s]["n"]
print("chosen scores", len(chosen), "staffs", total)

# held-out hard: whole scores never in a control list
cand = [s for s in chosen if not elig[s]["ctl"]]
rng.shuffle(cand)
held, hn = [], 0
for s in cand:
    if hn >= HOLD_HARD:
        break
    if hn + elig[s]["n"] > HOLD_HARD + 60:
        continue
    held.append(s); hn += elig[s]["n"]
held_set = set(held)
print("held-out hard scores", len(held), "staffs", hn)

role = {}
sel_hard = []
for s in chosen:
    for r in elig[s]["pool"]:
        role[r["key"]] = "val" if s in held_set else "train"
        sel_hard.append(r)


def groups(n, hold):
    rows = load(n)
    g = collections.defaultdict(list)
    for r in rows:
        g[re.sub(r"-vrv$", "", re.match(r"^(.*)-(?:\d+)-(?:\d+)\.png$", r["key"].split("/")[-1])[1]
                 .replace("-vrv-", "-vrv-")).rstrip("-")].append(r)
    return rows, g


def split_pieces(name, hold):
    rows = load(name)
    g = collections.defaultdict(list)
    for r in rows:
        base = r["key"].split("/")[-1][:-4]
        m = re.match(r"^(.*?)(?:-vrv)?-\d+-\d+$", base)
        g[m[1]].append(r)
    names = sorted(g)
    rng.shuffle(names)
    held, n = [], 0
    for p in names:
        if n >= hold:
            break
        if n + len(g[p]) > hold + 60:
            continue
        held.append(p); n += len(g[p])
    for p, rs in g.items():
        for r in rs:
            role[r["key"]] = "val" if p in held else "train"
    return rows, held, n, len(g)


asap_rows, asap_held, asap_n, asap_pieces = split_pieces("asap", HOLD_ASAP)
scr_rows, scr_held, scr_n, scr_pieces = split_pieces("kern_scriabin", HOLD_SCR)
print("ASAP pieces", asap_pieces, "held-out", asap_held, asap_n)
print("Scriabin pieces", scr_pieces, "held-out", scr_held, scr_n)

for name, rows in [("pdmx_hard", sel_hard), ("asap", asap_rows), ("kern_scriabin", scr_rows)]:
    with open(f"{S}lists/selected_{name}.txt", "w") as f:
        for r in rows:
            f.write(f"{r['key']},{r['tok']}\n")
meters_pool = collections.Counter(m for v in elig.values() for m in v["meters"])
meters_sel = collections.Counter(m for s in chosen for m in elig[s]["meters"])
meters_sel_staffs = collections.Counter()
for s in chosen:
    for m in elig[s]["meters"]:
        meters_sel_staffs[m] += elig[s]["n"]
meters_sel_train_staffs = collections.Counter()
for s in chosen:
    if s not in held_set:
        for m in elig[s]["meters"]:
            meters_sel_train_staffs[m] += elig[s]["n"]
json.dump(dict(
    role=role, seed=SEED, target_total=TARGET_TOTAL, hold=dict(hard=HOLD_HARD, asap=HOLD_ASAP, scriabin=HOLD_SCR),
    max_score_staffs=MAX_SCORE_STAFFS, min_density=MIN_DENSITY, rare_quota=RARE_QUOTA, common_meters=sorted(COMMON),
    median_density=med, pool_scores=len(info), eligible_scores=len(elig),
    chosen_scores=len(chosen), heldout_hard_scores=held, asap_heldout_pieces=asap_held,
    scriabin_heldout_pieces=scr_held, meters_eligible_scores=meters_pool, meters_selected_scores=meters_sel,
    meters_selected_staffs=meters_sel_staffs, meters_train_staffs=meters_sel_train_staffs,
    meter_note="a score counts for every meter token occurring in it (also meter changes)",
    chosen_score_ids=chosen,
), open(f"{S}lists/selection.json", "w"), indent=1)
print("meters selected (staffs of scores containing it):", meters_sel_staffs.most_common(50))
print("meters eligible (scores containing it):", meters_pool.most_common(50))
print("meters selected (scores containing it):", meters_sel.most_common(50))
