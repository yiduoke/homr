"""analyze.py EDITION[:k] ... : labels the extracted pages of every edition from the page structure (label_pairs.py rules: pairs 0, 2, 4 ... of a
page with exactly k = 2 staffs per system are grand staffs, the others separate; k = 3 = voice + piano (same system, grand, separate), k = 4 = two pianos with a brace each: grand, same system,
grand, separate; a page is kept only if barlines cross the gap of every same-system pair and of no separate pair) and counts the pages, systems,
grand pairs and the decisions of the SHIPPED relation model (argmax; 0 separate, 1 same system, 2 grand staff).
Writes labels/<edition>.npz (crops, labels, page, shipped prediction) for the kept pages; prints one row per edition."""
import sys, os, glob, json, numpy as np
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/rel_wt")
from homr import staff_relations as sr
assert not os.environ.get("HOMR_STAFF_RELATION_MODEL")
SEP, SAME, GRAND = 0, 1, 2
PATTERN = {2: [GRAND, SEP], 3: [SAME, GRAND, SEP], 4: [GRAND, SAME, GRAND, SEP]}
model = sr.StaffRelationModel()
os.makedirs("labels", exist_ok=True)
def label_page(d, k):
    if "crops" not in d or len(d["crops"]) == 0: return None, "nopairs"
    pairs, top = d["pairs"], d["top"]; n = len(top)
    order = list(np.argsort(top)); chain = [(order[i], order[i + 1]) for i in range(n - 1)]
    if sorted(map(tuple, pairs)) != sorted(chain): return None, "chain"
    by = {tuple(p): i for i, p in enumerate(pairs)}; idx = [by[c] for c in chain]
    if n % k: return None, f"n%{k}"
    lab = np.array([PATTERN[k][i % k] for i in range(len(chain))])
    conn = d["connectors"][idx]
    if (conn[lab == SEP] > 0).any(): return None, "separate-has-connector"
    if (conn[lab != SEP] < 1).any():
        # second independent signal (no barline across some gap): the gaps of the paired staffs are all smaller than the gaps between systems
        gap = d["gap"][idx]
        if (lab == SEP).any() and (lab != SEP).any() and gap[lab != SEP].max() < 0.8 * gap[lab == SEP].min():
            out = np.empty(len(pairs), int)
            for c, l in zip(idx, lab): out[c] = l
            return out, "ok"
        return None, "same-without-connector"
    out = np.empty(len(pairs), int)
    for c, l in zip(idx, lab): out[c] = l
    return out, "ok"
rows = []
GROUPS = {"schott-te-volume": lambda p: "schott-te-volume.mazeppa(reserved)" if 16 <= p <= 28 else "schott-te-volume.pool"}
def run_group(name, k, files):
    stats = {}; C, L, P = [], [], []; nsys = 0
    for f in files:
        d = np.load(f); lab, why = label_page(d, k); stats[why] = stats.get(why, 0) + 1
        if lab is None: continue
        C.append(d["crops"]); L.append(lab); P += [os.path.basename(f)[:-4]] * len(lab); nsys += len(d["top"]) // k
    if not C: return (name, len(files), 0, 0, 0, 0, 0, 0, stats)
    crops, y = np.concatenate(C), np.concatenate(L)
    pr = np.concatenate([model.predict(crops[s:s + 256].astype(np.float32) / 255).argmax(1) for s in range(0, len(crops), 256)])
    np.savez_compressed(f"labels/{name}.npz", crops=crops, labels=y, page=np.array(P), shipped=pr)
    miss = int(((y == GRAND) & (pr != GRAND)).sum()); fg = int(((y != GRAND) & (pr == GRAND)).sum()); fj = int(((y == SEP) & (pr != SEP)).sum())
    return (name, len(files), stats.get("ok", 0), nsys, int((y == GRAND).sum()), miss, fg, fj, stats)
for arg in sys.argv[1:]:
    ed, k = (arg.split(":") + ["2"])[:2]; k = int(k)
    files = sorted(glob.glob(f"extract/{ed}__*.npz"))
    if ed in GROUPS:
        byg = {}
        for f in files:
            p = int(f.rsplit("page-", 1)[1][:-4]); byg.setdefault(GROUPS[ed](p), []).append(f)
        for g, fs in sorted(byg.items()): rows.append(run_group(g, k, fs))
    else:
        rows.append(run_group(ed, k, files))
print(f"{'edition':42s} pages kept systems grand missed falsegrand falsejoin  (skip reasons)")
for r in rows:
    print(f"{r[0]:42s} {r[1]:4d} {r[2]:4d} {r[3]:5d} {r[4]:5d} {r[5]:5d} {r[6]:5d} {r[7]:5d}   {({a:b for a,b in r[8].items() if a!='ok'})}")
