"""Compose meter_train.txt / meter_val.txt from the rendered staffs of the meter arm.
usage: compose_lists.py <train|val> <target size> <out dir> staffs1.jsonl [...]      (plans: PLAN env, comma separated)
Filters: trainer filters (vocabulary, length, ledger lines), bar offset known, automatic bar check clean,
no staff of a rejected style. Then quotas: ~20% without signature, every meter >= MIN staffs (as far as the candidates allow),
common meters in the shares of the real data, small-print ~30% of all staffs, >= 25% change staffs.
Writes <out>/meter_<pool>.txt, <out>/manifest_<pool>.json (per meter, per style, per kind, held-out sources).
"""
import collections
import json
import os
import random
import sys

sys.path.insert(0, "/workspace/run4/meters/code")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
import tokencheck as tc  # noqa: E402
from homr.transformer.configs import Config  # noqa: E402
from training.transformer.data_loader import MAX_ALLOWED_LEDGER_LINES  # noqa: E402
from training.transformer.training_vocabulary import check_token_lines, max_ledger_lines, read_tokens  # noqa: E402

pool, target, outdir = sys.argv[1], int(sys.argv[2]), sys.argv[3]
files = sys.argv[4:]
REJECT_STYLES = set(filter(None, os.environ.get("REJECT_STYLES", "").split(",")))  # "renderer/tsclass"
MIN = int(os.environ.get("MIN_PER_METER", "150" if pool == "train" else "12"))
rng = random.Random(20261118 if pool == "train" else 20261119)
MAXLEN = Config().max_seq_len - 2
COMMON = {"3/4": 7919, "4/4": 7658, "2/4": 4745, "6/8": 2795, "common": 2117, "3/8": 1905, "2/2": 1225, "cut": 368}
ALLM = ["1/4", "2/4", "3/4", "4/4", "5/4", "6/4", "7/4", "8/4", "9/4", "10/4", "1/8", "2/8", "3/8", "4/8", "5/8", "6/8", "7/8", "9/8",
        "11/8", "12/8", "13/8", "15/8", "5/16", "7/16", "9/16", "11/16", "12/16", "13/16", "15/16", "17/16", "19/16", "2/2", "3/2", "4/2",
        "common", "cut"]
RARE = [m for m in ALLM if m not in COMMON]

plans = {}
for p in os.environ["PLAN"].split(","):
    for ln in open(p):
        s = json.loads(ln)
        plans[s["wid"]] = s
recs = [json.loads(ln) for f in files for ln in open(f)]
infos = tc.staff_infos(recs, plans)
print("staffs rendered", len(infos), flush=True)


def trainable(d):
    try:
        t = read_tokens(d["tokens"])
        check_token_lines(t)
    except Exception:  # noqa: BLE001
        return "vocab"
    if len(t) > MAXLEN:
        return "long"
    if max_ledger_lines(t) > MAX_ALLOWED_LEDGER_LINES:
        return "ledger"
    return "ok"


sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_windows import heldout, heldout_hash, scarce_stems  # noqa: E402

rej = collections.Counter()
cands = []
for d in infos:
    r = trainable(d)
    if r != "ok":
        rej[r] += 1
        continue
    if not d["ok_offset"]:
        rej["offset"] += 1
        continue
    if d["bad"] > 0:
        rej["barcheck"] += 1
        continue
    if f"{d['renderer']}/{d['tsclass']}" in REJECT_STYLES:
        rej["style"] += 1
        continue
    spec = plans[d["spec"]]
    if pool == "train" and any(heldout(x) for g in spec["segments"] for x in g["src"].split("+")):
        rej["heldout_source"] += 1
        continue
    if pool == "val" and any(x in scarce_stems() and heldout_hash(x) for g in spec["segments"] for x in g["src"].split("+")):
        rej["scarce_source_kept_in_train"] += 1
        continue
    d["srcs"] = sorted({s for g in spec["segments"] for s in g["src"].split("+")})
    d["seg_by_meter"] = collections.defaultdict(set)
    for g in spec["segments"]:
        for s in g["src"].split("+"):
            d["seg_by_meter"][g["meter"]].add(s)
    d["has_sig"] = bool(d["start"] or d["mids"])
    d["change"] = bool(d["mids"]) or d["sig_after_change"]
    # printed meters in the vocabulary names (the token text is 'n/d', 'common', 'cut')
    cands.append(d)
print("candidates", len(cands), "rejected", dict(rej), flush=True)

nosig = [d for d in cands if not d["has_sig"]]
sig = [d for d in cands if d["has_sig"]]
n_nosig = int(0.20 * target)
n_sig = target - n_nosig
cls_share = {"small": 0.375, "normal": 0.50, "large": 0.125}  # of the staffs with a signature (small = 30% of all staffs)
sel = {}


def cls_count():
    return collections.Counter(sel[k]["tsclass"] for k in sel if sel[k]["has_sig"])


def add(d):
    sel[d["image"]] = d


def deficit_class(d):
    c = cls_count()
    n = max(1, sum(c.values()))
    return cls_share[d["tsclass"]] - c[d["tsclass"]] / n


# step A: rare meters first (scarcest first)
avail = {m: [d for d in sig if m in d["printed"]] for m in ALLM}
order = sorted(ALLM, key=lambda m: len(avail[m]))
quota_rare = int(os.environ.get("RARE_TARGET", "165" if pool == "train" else "15"))
for m in order:
    if m in COMMON:
        continue
    have = sum(1 for d in sel.values() if m in d["printed"])
    pool_m = [d for d in avail[m] if d["image"] not in sel]
    rng.shuffle(pool_m)
    # diversify by source: round robin over scores
    by_src = collections.defaultdict(list)
    for d in pool_m:
        by_src[tuple(sorted(d["seg_by_meter"].get(m, d["srcs"])))[:1]].append(d)
    keys = list(by_src)
    rng.shuffle(keys)
    i = 0
    while have < quota_rare and keys:
        k = keys[i % len(keys)]
        if by_src[k]:
            # prefer the class that is most under its share
            lst = by_src[k]
            lst.sort(key=lambda d: len(set(d["printed"]) & set(RARE)) + rng.random() * 0.5 - 0.5 * deficit_class(d))
            add(lst.pop(0))
            have += 1
        else:
            keys.remove(k)
            continue
        i += 1
# step B: common meters by real share
total_w = sum(COMMON.values())
rem = n_sig - sum(1 for d in sel.values() if d["has_sig"])
want = {m: COMMON[m] / total_w * (rem + sum(1 for d in sel.values() if d["has_sig"] and any(x in COMMON for x in d["printed"]))) for m in COMMON}
for m in sorted(COMMON, key=lambda m: len(avail[m])):
    have = sum(1 for d in sel.values() if m in d["printed"])
    pool_m = [d for d in avail[m] if d["image"] not in sel]
    rng.shuffle(pool_m)
    pool_m.sort(key=lambda d: -deficit_class(d) + rng.random() * 0.05)
    k = 0
    while have < want[m] and k < len(pool_m) and sum(1 for d in sel.values() if d["has_sig"]) < n_sig:
        add(pool_m[k])
        have += 1
        k += 1
# step C: change share
n_all = lambda: len(sel)  # noqa: E731
ch_have = sum(1 for d in sel.values() if d["change"])
def n_rare(d):
    return sum(1 for m in set(d["printed"]) if m in RARE)


ch_pool = [d for d in sig if d["change"] and d["image"] not in sel]
rng.shuffle(ch_pool)
ch_pool.sort(key=lambda d: 5 * n_rare(d) + rng.random(), reverse=True)  # pop() takes the staffs with the fewest rare meters first
while ch_have < 0.30 * target and ch_pool and sum(1 for d in sel.values() if d["has_sig"]) < n_sig:
    add(ch_pool.pop())
    ch_have += 1
# step D: fill the signature staffs to n_sig
rest = [d for d in sig if d["image"] not in sel]
rng.shuffle(rest)
rest.sort(key=lambda d: -deficit_class(d) + rng.random() * 0.1 + 5 * n_rare(d))
for d in rest:
    if sum(1 for x in sel.values() if x["has_sig"]) >= n_sig:
        break
    add(d)
# step E: no-signature staffs, preferably from windows of selected staffs (the same music, continuation systems)
wsel = {d["spec"] for d in sel.values()}
ns = [d for d in nosig if d["spec"] in wsel] + [d for d in nosig if d["spec"] not in wsel]
rng.shuffle(ns)
ns = sorted(ns, key=lambda d: d["spec"] not in wsel)
for d in ns[:n_nosig]:
    add(d)

final = list(sel.values())
rng.shuffle(final)
os.makedirs(outdir, exist_ok=True)
with open(f"{outdir}/meter_{pool}.txt", "w") as f:
    for d in final:
        f.write(f"{d['image']},{d['tokens']}\n")

man = {"pool": pool, "target": target, "n": len(final), "rejected": dict(rej), "candidates": len(cands)}
man["no_signature"] = sum(1 for d in final if not d["has_sig"])
man["with_signature"] = sum(1 for d in final if d["has_sig"])
man["change_staffs"] = sum(1 for d in final if d["change"])
man["mid_staff_change"] = sum(1 for d in final if d["mids"])
man["system_start_after_change"] = sum(1 for d in final if d["sig_after_change"])
man["by_tsclass"] = dict(collections.Counter(d["tsclass"] if d["has_sig"] else "nosig" for d in final))
man["per_meter"] = {}
for m in ALLM:
    ds = [d for d in final if m in d["printed"]]
    scores = set()
    for d in ds:
        scores |= d["seg_by_meter"].get(m, set())
    man["per_meter"][m] = dict(staffs=len(ds), start=sum(1 for d in ds if d["start"] == m), mid=sum(1 for d in ds if any(x == m for _b, x in d["mids"])),
                               scores=len(scores), small=sum(1 for d in ds if d["tsclass"] == "small"))
man["per_style"] = dict(collections.Counter(f"{d['renderer']}/{d['font']}/{d['tsclass']}" for d in final))
man["per_renderer_tsclass"] = dict(collections.Counter(f"{d['renderer']}/{d['tsclass']}" for d in final))
man["per_kind"] = dict(collections.Counter(d["kind"] for d in final))
man["source_scores"] = sorted({s for d in final for s in d["srcs"]})
man["n_source_scores"] = len(man["source_scores"])
json.dump(man, open(f"{outdir}/manifest_{pool}.json", "w"), indent=1)
print(json.dumps({k: v for k, v in man.items() if k not in ("per_meter", "source_scores", "per_style")}, indent=1))
for m in ALLM:
    print(m, man["per_meter"][m])
