"""D32 task 3 numbers: (1) verified training examples we hold for each bracket role (starts, stops, continuations, none), pilot + batch 2;
(2) the released model's per-span success on label brackets of each role (all analysed crops, original ASAP labels).
Read-only. Prints markdown tables, writes octave_causes_gap.json."""
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/octave_checks")
import octave_causes_crops as O  # noqa: E402

RUN = "/Users/yiduoke/Documents/homr/run/"
crops = O.load_all()
byname = {c["name"]: c for c in crops}
res = {r["name"]: r for r in json.load(open(O.OUT + "octave_causes_notes.json"))}


def read_list(p):
    out = []
    for l in open(p):
        l = l.strip()
        if not l:
            continue
        img, tok = l.split(",")[:2]
        out.append((os.path.basename(img)[:-4], RUN + tok if not tok.startswith("/") else tok))
    return out


P = O.R + "lists/"
B = O.R + "batch2/lists/"
SETS = {
    "pilot train (A+B: strong)": [P + "train_strong.txt"],
    "pilot train (hard + octave-verified)": [P + "train_hard.txt", P + "train_octave_verified.txt"],
    "pilot val (C)": [P + "val_strong.txt"],
    "batch2 train (strong+hard+octave-verified)": [B + "batch2_train_all.txt"],
    "batch2 Demets (Une barque)": [B + "batch2_train_demets_unebarque.txt"],
    "batch2 val": [B + "batch2_val.txt"],
}
# chosen label per crop: admitted token file (may be corrected) else the original
chosen = {}
members = {}
for k, fl in SETS.items():
    mem = []
    for f in fl:
        for n, tp in read_list(f):
            if os.path.exists(tp):
                chosen[n] = open(tp).read()
                mem.append(n)
    members[k] = mem

# neighbours (same pid, manifest order)
order = defaultdict(list)
for c in crops:
    order[(c["set"], c["row"]["pid"])].append(c["name"])


def label_text(n):
    return chosen.get(n) or byname[n]["label"]


def mrange(c):
    s = c["row"]["asap_measure_range"]
    if not s:
        return None
    a = s.split("-")
    return int(a[0]), int(a[-1])


def roles(n):
    c = byname[n]
    txt = label_text(n)
    if txt is None:
        return None
    st, sp, ev, stray = O.parse(txt)
    key = (c["set"], c["row"]["pid"])
    lst = order[key]
    k = lst.index(n)
    prev_open = False
    if k > 0:
        p = byname[lst[k - 1]]
        pt = label_text(p["name"])
        a, b = mrange(p), mrange(c)
        contig = (a and b and (b[0] == a[1] + 1 or b[0] == a[1])) or not (a and b)
        if pt and contig:
            pst, psp, _, _ = O.parse(pt)
            prev_open = any(s["open_end"] for x in psp.values() for s in x)
    r = Counter()
    nsp = 0
    for s in ("upper", "lower"):
        for x in sp[s]:
            nsp += 1
            cont_in = x["start"] == 0 and prev_open
            if cont_in:
                r["cont_in"] += 1
            else:
                r["start"] += 1
            if x["open_end"]:
                r["cont_out"] += 1
            else:
                r["stop"] += 1
    return r, nsp


out = {}
print("### Verified examples already available (admitted lists; crops with at least one such span, spans in brackets)\n")
print("| list | crops | no bracket | with a start inside (spans) | with a stop inside (spans) | continuing from the previous system (spans) | continuing into the next system (spans) | 8vb (lower or 8vb) spans |")
print("|---|---|---|---|---|---|---|---|")
tot = Counter()
for k, mem in members.items():
    c_none = c_start = c_stop = c_in = c_out = 0
    s_start = s_stop = s_in = s_out = 0
    for n in mem:
        rr = roles(n)
        if rr is None:
            continue
        r, nsp = rr
        if nsp == 0:
            c_none += 1
        c_start += r["start"] > 0
        c_stop += r["stop"] > 0
        c_in += r["cont_in"] > 0
        c_out += r["cont_out"] > 0
        s_start += r["start"]
        s_stop += r["stop"]
        s_in += r["cont_in"]
        s_out += r["cont_out"]
    print(f"| {k} | {len(mem)} | {c_none} | {c_start} ({s_start}) | {c_stop} ({s_stop}) | {c_in} ({s_in}) | {c_out} ({s_out}) | |")
    out[k] = dict(crops=len(mem), none=c_none, start=[c_start, s_start], stop=[c_stop, s_stop], cont_in=[c_in, s_in], cont_out=[c_out, s_out])
    tot["crops"] += len(mem)
    tot["none"] += c_none
    tot["start"] += c_start
    tot["stop"] += c_stop
    tot["cont_in"] += c_in
    tot["cont_out"] += c_out
    tot["s_start"] += s_start
    tot["s_stop"] += s_stop
    tot["s_in"] += s_in
    tot["s_out"] += s_out
train = [k for k in members if "val" not in k]
t = Counter()
for k in train:
    for kk in ("crops", "none"):
        t[kk] += out[k][kk]
    for kk in ("start", "stop", "cont_in", "cont_out"):
        t[kk] += out[k][kk][0]
        t["s_" + kk] += out[k][kk][1]
print(f"| **training lists together (no validation)** | {t['crops']} | {t['none']} | {t['start']} ({t['s_start']}) | {t['stop']} ({t['s_stop']}) | {t['cont_in']} ({t['s_cont_in']}) | {t['cont_out']} ({t['s_cont_out']}) | |")
out["train_total"] = dict(t)

# (2) per-span success of the released model
print("\n### Released model: per label-bracket-span outcome (all analysed crops, original labels)\n")
stat = defaultdict(Counter)
for c in crops:
    r = res.get(c["name"])
    if not r or r["usable"] != "yes" or r["pc_f1"] < 0.8:
        continue
    L = O.parse(c["label"])
    Rd = O.parse(c["read"])
    # continuation flags from the stored record (computed with neighbour check)
    prev_open_flags = None
    st, sp, ev, stray = L
    rst, rsp, rev, rstray = Rd
    # recompute prev_open as in roles()
    key = (c["set"], c["row"]["pid"])
    lst = order[key]
    k = lst.index(c["name"])
    prev_open = False
    if k > 0:
        p = byname[lst[k - 1]]
        a, b = mrange(p), mrange(c)
        contig = (a and b and (b[0] == a[1] + 1 or b[0] == a[1])) or not (a and b)
        if p["label"] and contig:
            _, psp, _, _ = O.parse(p["label"])
            prev_open = any(s["open_end"] for x in psp.values() for s in x)
    group = "val" if r["group"] in ("pilot-val", "b2-val") else "train"
    for s in ("upper", "lower"):
        pairs = O.align(st[s], rst[s])
        pm = dict(pairs)
        for x in sp[s]:
            cont_in = x["start"] == 0 and prev_open
            cont_out = x["open_end"]
            role = "continuation from previous system" if cont_in else ("starts inside, runs into next system" if cont_out else "starts and stops inside")
            idx = [i for i in range(x["start"], x["stop"] + 1) if i in pm]
            if not idx:
                continue
            ok_all = all(rst[s][pm[i]]["state"] == st[s][i]["state"] for i in idx)
            first_ok = rst[s][pm[idx[0]]]["state"] == st[s][idx[0]]["state"]
            # stop: the first aligned note after the span must have read state 0 (when the label stops inside the crop)
            after = [i for i in range(x["stop"] + 1, len(st[s])) if i in pm]
            stop_ok = None
            if not cont_out and after:
                stop_ok = rst[s][pm[after[0]]]["state"] == 0 and st[s][after[0]]["state"] == 0
            if not cont_out and after and not stop_ok:
                nxt = rst[s][pm[after[0]]]["state"]
                # read span covering that note
                rs_cov = next((q for q in rsp[s] if q["start"] <= pm[after[0]] <= q["stop"]), None)
                kind = "stop missing: read bracket never closes in the crop" if rs_cov and rs_cov["open_end"] else ("read closes later than the label" if nxt else "label state not 0 after span")
                stat[role]["stopfail: " + kind] += 1
            stat[role]["spans"] += 1
            stat[role]["all notes right"] += ok_all
            stat[role]["first note right (start)"] += first_ok
            if stop_ok is not None:
                stat[role]["stops evaluable"] += 1
                stat[role]["stop right"] += stop_ok
            stat[role]["_" + group] += 1
            stat[role]["all notes right " + group] += ok_all
print("| label bracket role | spans | all notes under it read with the right shift | start right (first note) | stops evaluable | stop right | train spans | all right (train) | val spans | all right (val) |")
print("|---|---|---|---|---|---|---|---|---|---|")
for role, c in stat.items():
    n = c["spans"]
    print(f"| {role} | {n} | {c['all notes right']} ({100 * c['all notes right'] / n:.0f} %) | {c['first note right (start)']} ({100 * c['first note right (start)'] / n:.0f} %) | {c['stops evaluable']} | "
          f"{c['stop right']} ({100 * c['stop right'] / c['stops evaluable']:.0f} %) | {c['_train']} | {c['all notes right train']} | {c['_val']} | {c['all notes right val']} |" if c["stops evaluable"] else
          f"| {role} | {n} | {c['all notes right']} ({100 * c['all notes right'] / n:.0f} %) | {c['first note right (start)']} ({100 * c['first note right (start)'] / n:.0f} %) | 0 | - | {c['_train']} | {c['all notes right train']} | {c['_val']} | {c['all notes right val']} |")
print()
for role, c in stat.items():
    print(role, {k: v for k, v in c.items() if k.startswith("stopfail")})
out["span_stats"] = {k: dict(v) for k, v in stat.items()}
json.dump(out, open(O.OUT + "octave_causes_gap.json", "w"), indent=1)
