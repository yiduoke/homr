import json, collections, numpy as np
def load(n): return [json.loads(l) for l in open(f"stats/{n}.jsonl")]
def src(k):
    for s in ["grandstaff","Lieder-main","pdmx/hard","pdmx","musescore_octave","lilypond_round2","lilypond","asap","kern_scriabin"]:
        if f"/{s}/" in k: return s
    return "other"
def rep(name, rows):
    n=len(rows)
    ok=[r for r in rows if r["lab"]>0]
    agree=np.mean([r["nstaffs"]==r["lab"] for r in ok])*100
    extra=np.mean([r["nstaffs"]>r["lab"] for r in ok])*100
    fewer=np.mean([r["nstaffs"]<r["lab"] for r in ok])*100
    border=np.mean([(r["top"]>=20 or r["bot"]>=20) for r in rows])*100
    top=np.mean([r["top"]>=20 for r in rows])*100; bot=np.mean([r["bot"]>=20 for r in rows])*100
    h=np.array([r["H"] for r in rows]); w=np.array([r["W"] for r in rows])
    print(f"{name:24s} n={n:6d} staffs-in-image==label {agree:5.1f}%  image has more {extra:5.1f}%  fewer {fewer:5.1f}% | ink at border top/bottom/any {top:4.1f}/{bot:4.1f}/{border:4.1f}% | H med {np.median(h):.0f} W med {np.median(w):.0f} staff-space? ")
for n in ["pdmx_hard","asap","kern_scriabin"]:
    rows=load("img_"+n)
    rep(n,rows)
    v=[r for r in rows if "-vrv-" in r["key"]]; m=[r for r in rows if "-vrv-" not in r["key"]]
    rep(n+" (MuseScore png)",m); rep(n+" (Verovio png)",v)
    # vrv by part index
    if v:
        byp=collections.defaultdict(list)
        for r in v:
            p=r["key"].rsplit("-",1)[1][:-4]
            byp[p].append(r)
        for p in sorted(byp): rep(f"   vrv part {p}", byp[p])
c=load("img_control6000")
rep("control mixed", c)
by=collections.defaultdict(list)
for r in c: by[src(r["key"])].append(r)
for s,v in sorted(by.items()): rep("ctl "+s, v)
rep("control hard (3000)", load("img_control_hard3000"))
