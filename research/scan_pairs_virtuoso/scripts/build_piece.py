"""Stage 1 for one piece: collect its systems, align them to the ASAP measures, write work/assign/<pid>.json.
usage: HOMR_FIXED_MARGIN=1 PYTHONPATH=integration_wt python build_piece.py <pid> [skip_first_systems]"""
import sys, os, json, collections, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import labels, align
from pieces import BY
BASE = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/work"

def page_json(pdf, p):
    for pat in (f"{BASE}/crops/{pdf}/p-{p:02d}.json", f"{BASE}/crops/{pdf}/p-{p:03d}.json"):
        if os.path.exists(pat): return pat

def collect(cfg, skip_first=0):
    systems = []
    for p in cfg["pages"]:
        jf = page_json(cfg["pdf"], p)
        if not jf: systems.append(dict(page=p, missing=True)); continue
        d = json.load(open(jf))
        for s in d["systems"]:
            c = s["crops"][0] if s["crops"] else None
            ok = s["n_staffs"] == 1 and c and "file" in c and c.get("grandstaff")
            rec = dict(page=d["page"], page_no=p, sys=s["system"], page_shape=d.get("page_shape"), mode=d.get("mode"), eligible=bool(ok))
            if c and "file" in c:
                rec.update(crop=f"{BASE}/crops/{cfg['pdf']}/{c['file']}", bbox=c["page_bbox"], shape=c["shape"],
                           groups=c["n_bar_groups"], first_x=c["bar_first_x"], unit=c["bar_unit"])
            rec["id"] = f"{cfg['pdf']}/{d['page']}/s{s['system']}"
            systems.append(rec)
    return systems

def main():
    pid = sys.argv[1]; cfg = BY[pid]; skip = int(sys.argv[2]) if len(sys.argv) > 2 else cfg.get('skip', 0)
    systems = collect(cfg)
    reads = {}
    rf = f"{BASE}/reads/{cfg['pdf']}.jsonl"
    if os.path.exists(rf):
        for l in open(rf):
            r = json.loads(l); reads[r["id"]] = r
    elig = [s for s in systems if s.get("eligible")]
    if skip: 
        for s in elig[:skip]: s["eligible"] = False; s["skipped"] = "before piece start"
        elig = elig[skip:]
    voices = labels.load(cfg["asap"]); v = voices[0]
    meas_notes = [collections.Counter(sym.pitch for sym in m if sym.rhythm.startswith("note")) for m in v]
    dps = []
    for s in elig:
        r = reads.get(s["id"])
        k = align.bar_k(s.get("groups"), s.get("first_x"), s.get("unit"))
        dps.append(dict(k=k, model_notes=(r["notes"] if r and "notes" in r else None),
                        pitch_counter=collections.Counter(p for b, p in r["notes"]) if r and "notes" in r else None,
                        model_bars=align.bar_counters(r["notes"]) if r and "notes" in r else None))
        s["k"] = k; s["read"] = r is not None
    res, score, end = align.align(dps, meas_notes)
    out = dict(pid=pid, n_measures=len(v), n_systems=len(systems), n_eligible=len(elig), score=score, end=end, systems=systems)
    if res:
        for s, a, d in zip(elig, res, dps):
            s["start"], s["L"], s["gap"] = a["start"], a["L"], a["gap"]
            if d["model_notes"] is not None and a["L"] > 0:
                c = collections.Counter()
                for m in range(a["start"], a["start"] + a["L"]): c.update(meas_notes[m])
                s["f1"] = align.f1(c, d["pitch_counter"])
                # pitch-class F1 (octave-insensitive)
                strip = lambda cc: collections.Counter({k[:-1]: n for k, n in cc.items()}) if False else collections.Counter(x[:-1] for x in cc.elements())
                s["f1_pc"] = align.f1(strip(c), strip(d["pitch_counter"]))
                s["label_notes"] = sum(c.values()); s["model_notes_n"] = len(d["model_notes"])
    os.makedirs(f"{BASE}/assign", exist_ok=True)
    json.dump(out, open(f"{BASE}/assign/{pid}.json", "w"))
    el = [s for s in elig if "L" in s]
    asg = [s for s in el if s["L"] > 0]
    print(pid, cfg["title"], "measures", len(v), "systems", len(systems), "eligible", len(elig), "assigned", len(asg), "end", end,
          "gaps", sum(1 for s in asg if s["gap"]), "score %.1f" % score,
          "F1>=0.8: %d" % sum(1 for s in asg if s.get("f1", 0) >= 0.8), "reads %d/%d" % (sum(1 for s in elig if s["read"]), len(elig)))

if __name__ == "__main__":
    main()
