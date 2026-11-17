"""Integrity check of the candidate lists (files exist, no train/val overlap, duplicates only Scriabin x2, counts by source)."""
import collections, os, re, sys
S = "/workspace/run3/"
def src(p, t):
    for s in ["grandstaff","Lieder-main","musescore_octave"]:
        if f"/datasets_meter/{s}/" in t: return s
    if "/datasets_meter/pdmx/hard/" in t: return "pdmx_hard"
    if "/datasets_meter/pdmx/" in t: return "pdmx"
    if "/datasets_meter/asap/" in t: return "asap"
    if "/datasets_meter/kern_scriabin/" in t: return "kern_scriabin"
    return "lilypond_round2" if "lilypond_round2" in p else "lilypond"
def load(f): return [l.strip().split(",") for l in open(S+f) if l.strip()]
L = {n: load(n) for n in ["cand_train.txt","cand_train_nooct.txt","cand_val.txt","cand_val_hard.txt","run2_train_excl.txt","run2_val_excl.txt"]}
for n, rows in L.items():
    c = collections.Counter(src(p,t) for p,t in rows)
    miss = sum(1 for p,t in rows if not (os.path.exists(p) and os.path.exists(t)))
    dup = collections.Counter(p for p,t in rows); d = sum(1 for k,v in dup.items() if v>1)
    print(f"{n:24s} {len(rows):7d} missing files {miss} duplicated images {d} | " + ", ".join(f"{k} {v}" for k,v in sorted(c.items())))
tr = {p for p,t in L["cand_train.txt"]}; va = {p for p,t in L["cand_val.txt"]}
print("train/val image overlap:", len(tr & va))
dups = [p for p,v in collections.Counter(p for p,t in L["cand_train.txt"]).items() if v>1]
print("duplicated images in cand_train are all Scriabin:", all("/kern_scriabin/" in p for p in dups), len(dups))
hv = {p for p,t in L["cand_val_hard.txt"]}
print("cand_val == control val + val_hard:", sorted(L["cand_val.txt"]) == sorted(L["run2_val_excl.txt"]+L["cand_val_hard.txt"]))
print("control train fully contained in cand_train:", {tuple(x) for x in L["run2_train_excl.txt"]} <= {tuple(x) for x in L["cand_train.txt"]})
# score-level: held-out hard scores not in train
sid = lambda p: (re.search(r"/(Qm[A-Za-z0-9]+)-", p) or [None, None])[1]
pid = lambda p: re.match(r"^(.*?)(?:-vrv)?-\d+-\d+$", os.path.basename(p)[:-4])[1]
print("held-out hard PDMX scores in train:", len({sid(p) for p in hv if "/pdmx/hard/" in p} & {sid(p) for p in tr}))
print("held-out ASAP/Scriabin pieces in train:", len({pid(p) for p in hv if "/asap/" in p or "/kern_scriabin/" in p} & {pid(p) for p in tr if "/asap/" in p or "/kern_scriabin/" in p}))
