import json, os, sys, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tokencheck as tc
plans = {}
for p in os.environ["PLAN"].split(","):
    for ln in open(p):
        s = json.loads(ln); plans[s["wid"]] = s
recs = [json.loads(l) for f in sys.argv[1:] for l in open(f)]
errs = collections.Counter((plans[r["wid"]]["renderer"], r["error"][:20]) for r in recs if "error" in r)
infos = tc.staff_infos(recs, plans)
print("staffs", len(infos), "errors", dict(errs))
c = collections.Counter(); b = collections.Counter(); off = collections.Counter()
for d in infos:
    key = (d["renderer"], d["kind"])
    c[key] += 1
    b[key] += d["bad"] > 0
    off[d["renderer"]] += not d["ok_offset"]
for k in sorted(c): print(k, c[k], "bad bar staffs", b[k])
print("offset unknown", dict(off))
sig = sum(1 for d in infos if d["start"] or d["mids"]); print("with sig", sig, "mid", sum(1 for d in infos if d["mids"]), "after change", sum(1 for d in infos if d["sig_after_change"]))
bad = [d for d in infos if d["bad"] > 0][:12]
for d in bad: print(os.path.basename(d["image"]), d["kind"], d["bad_list"][:3], d.get("bar_meters"))
