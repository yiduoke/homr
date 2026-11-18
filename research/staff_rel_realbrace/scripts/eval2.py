"""eval2.py (D30): evaluation of staff relation models on the held-out sets of the thin-brace collection.
usage: python eval2.py OUT.json LABEL=MODEL.onnx ...        (LABEL 'shipped' = the shipped model; run from run/staff_rel_realbrace)
Sets (argmax decisions; 0 separate, 1 same system, 2 grand staff; miss = true grand not called grand, false grand = other called grand,
false join = true separate not called separate):
  mazeppa    : the reserved Mazeppa pages of the Schott volume (never trained on)
  schott_val : the held-out pieces of the volume (XI, XII, Waldesrauschen, Gnomenreigen) + Concert-Etudes S.144 file (validation, not trained)
  curved_val : curved-brace editions of the held-out works, per edition (never trained)
  curved_train_works : training editions (reference only)
  cappi1802, eder1800, reichardt : transfer tests (never trained; weak scans)
  test_scans : the three Schott test scans, saved crops of extract_eval: pairs inside a system (even chain positions) and between systems; opening pages
"""
import glob, json, os, sys
import numpy as np
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/rel_wt")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from homr import staff_relations as sr
import build_mixture2 as B

BC = B.BC
out = sys.argv[1]
models = {}
for a in sys.argv[2:]:
    n, p = a.split("=", 1)
    models[n] = sr.StaffRelationModel() if p == "shipped" else sr.StaffRelationModel(p)


def pred(m, crops):
    return np.concatenate([m.predict(crops[s:s + 512].astype(np.float32) / 255).argmax(1) for s in range(0, len(crops), 512)]) if len(crops) else np.zeros(0, int)


def counts(y, p):
    return dict(n=int(len(y)), grand=int((y == 2).sum()), miss=int(((y == 2) & (p != 2)).sum()), false_grand=int(((y != 2) & (p == 2)).sum()),
                false_join=int(((y == 0) & (p != 0)).sum()), sep=int((y == 0).sum()), same=int((y == 1).sum()),
                same_wrong=int(((y == 1) & (p != 1)).sum()), acc=float((y == p).mean()) if len(y) else None)


sets = {}   # name -> (crops, labels, groups)
z = np.load(f"{BC}/labels/schott-te-volume.mazeppa(reserved).npz", allow_pickle=True)
sets["mazeppa"] = (z["crops"], z["labels"], np.array(["mazeppa"] * len(z["labels"])))
for nm in ("beethoven-op27-2-cappi1802", "beethoven-op13-eder1800"):
    z = np.load(f"{BC}/labels/{nm}.npz", allow_pickle=True)
    sets[nm.split("-")[-1]] = (z["crops"], z["labels"], np.array([nm] * len(z["labels"])))
b = np.load("mixture_B.npz", allow_pickle=True)
k = b["source"] == "real_thin"
sets["reichardt"] = (b["crops"][k], b["labels"][k], np.array(["reichardt1819"] * int(k.sum())))
# held-out pieces of the volume and Concert-Etudes file
zp = np.load(f"{BC}/labels/schott-te-volume.pool.npz", allow_pickle=True)
pcs = np.array([B.piece_of(p) for p in zp["page"]]); kv = np.isin(pcs, list(B.VAL_PIECES))
zc = np.load(f"{BC}/labels/schott-concert-etudes.npz", allow_pickle=True)
sets["schott_val"] = (np.concatenate([zp["crops"][kv], zc["crops"]]), np.concatenate([zp["labels"][kv], zc["labels"]]),
                      np.concatenate([np.array(["etudes-" + p for p in pcs[kv]]), np.array(["concert-etudes-S144"] * len(zc["labels"]))]))
ktr = ~kv
sets["schott_train_pieces"] = (zp["crops"][ktr], zp["labels"][ktr], np.array(["etudes-" + p for p in pcs[ktr]]))
cv, ct = [], []
for f in sorted(glob.glob(f"{BC}/labels/*.npz")):
    nm = os.path.basename(f)[:-4]
    if nm in B.NOT_CURVED or nm.startswith("schott-"):
        continue
    z = np.load(f, allow_pickle=True)
    (ct if nm in B.CURVED_TRAIN else cv).append((z["crops"], z["labels"], np.array([nm] * len(z["labels"]))))
for key, lst in (("curved_val", cv), ("curved_train_works", ct)):
    sets[key] = tuple(np.concatenate([x[i] for x in lst]) for i in range(3))
res = {}
for mn, m in models.items():
    r = {}
    for sn, (crops, y, g) in sets.items():
        p = pred(m, crops)
        r[sn] = counts(y, p)
        if sn in ("curved_val", "schott_val"):
            r[sn]["per_group"] = {gg: counts(y[g == gg], p[g == gg]) for gg in sorted(set(g))}
    # three Schott test scans (same edition, not transfer): saved crops of every page
    tot = dict(inside=0, grand=0, between=0, between_sep=0, opening_systems=0, opening_grand=0); per = {}
    for piece, opening in (("liszt-te-5", "page-029"), ("liszt-te-10", "page-076"), ("liszt-sonata", "page-02")):
        pc = dict(inside=0, grand=0, between=0, between_sep=0, opening_grand=0, opening_systems=0)
        for f in sorted(glob.glob(f"extract_eval/{piece}__*.npz")):
            zz = np.load(f)
            if "crops" not in zz or len(zz["crops"]) == 0 or len(zz["crops"]) % 2 == 0:
                continue
            pp = pred(m, zz["crops"])
            ins = pp[0::2]; btw = pp[1::2]
            pc["inside"] += len(ins); pc["grand"] += int((ins == 2).sum()); pc["between"] += len(btw); pc["between_sep"] += int((btw == 0).sum())
            if f.endswith(opening + ".npz"):
                pc["opening_systems"] += len(ins); pc["opening_grand"] += int((ins == 2).sum())
        per[piece] = pc
        for kk in tot: tot[kk] += pc[kk]
    r["test_scans"] = dict(total=tot, per_piece=per)
    res[mn] = r
json.dump(res, open(out, "w"), indent=1)
hdr = f"{'model':16s}| " + " | ".join(["mazeppa miss/fg/fj (of grand)", "schott_val", "curved_val", "cappi", "eder", "reichardt", "test scans grand/169 (open/13) sep ok"])
print(hdr)
for mn, r in res.items():
    cells = []
    for sn in ("mazeppa", "schott_val", "curved_val", "cappi1802", "eder1800", "reichardt"):
        c = r[sn]; cells.append(f"{c['miss']}/{c['false_grand']}/{c['false_join']} of {c['grand']}")
    t = r["test_scans"]["total"]
    cells.append(f"{t['grand']}/{t['inside']} ({t['opening_grand']}/{t['opening_systems']}) {t['between_sep']}/{t['between']}")
    print(f"{mn:16s}| " + " | ".join(cells))
