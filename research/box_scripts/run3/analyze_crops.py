import json, collections, numpy as np, os, random, sys
from multiprocessing import Pool
def load(n): return [json.loads(l) for l in open(f"stats/{n}.jsonl")]
def src(k):
    for s in ["grandstaff","Lieder-main","pdmx/hard","pdmx","musescore_octave","lilypond_round2","lilypond","asap","kern_scriabin"]:
        if f"/{s}/" in k: return s
    return "other"
def ss(png):
    try: return json.load(open(png[:-4]+".json"))["staff_space"]
    except Exception: return None
def table(name, rows, pool):
    n=np.array([r["notes"] for r in rows])
    f=lambda k: 100*np.mean([k(r) for r in rows])
    led=sum(r["ledger"] for r in rows)/max(1,sum(r["notes"] for r in rows))*100
    sps=[x for x in pool.map(ss,[r["key"] for r in rows],chunksize=100) if x]
    sps=np.array(sps)
    print(f"{name:22s} n={len(rows):6d} notes/staff med {np.median(n):4.0f} p90 {np.percentile(n,90):4.0f} | empty(<=2 notes) {f(lambda r:r['notes']<=2):4.1f}% | chord>=4 {f(lambda r:r['maxchord']>=4):4.1f}% (>=6 {f(lambda r:r['maxchord']>=6):4.1f}%) | ledger notes {led:4.1f}% of notes, staffs >=4 ledger notes {f(lambda r:r['ledger']>=4):4.1f}% | 8va/8vb {f(lambda r:r['octshift']>0):4.1f}% | repeated x3 {f(lambda r:r['rep3']):4.1f}% | run>=8 fast notes {f(lambda r:r['max_fast']>=8):4.1f}% | 2nd voice {f(lambda r:r['voices2']):4.1f}% | time sig {f(lambda r:len(r['ts'])>0):4.1f}% | staff space med {np.median(sps):.1f}px, <8px {100*np.mean(sps<8):.1f}%")
if __name__=="__main__":
    with Pool(32) as pool:
        for n in ["pdmx_hard","asap","kern_scriabin"]:
            rows=load("sel_"+n)
            table(n+" (all)", rows, pool)
            random.seed(11)
            sm=[l.split(",")[0] for l in open(f"lists/verify_sample_{n}.txt")]
            ss_=set(sm); table(n+" (150 sample)", [r for r in rows if r["key"] in ss_], pool)
        c=load("control6000")
        table("control mixed (6000)", c, pool)
        by=collections.defaultdict(list)
        for r in c: by[src(r["key"])].append(r)
        for s,v in sorted(by.items()): table("ctl "+s, v, pool)
        table("control hard (3000)", load("control_hard3000"), pool)
