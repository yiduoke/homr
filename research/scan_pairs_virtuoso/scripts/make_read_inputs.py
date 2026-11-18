import json, sys, glob, os
BASE="/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/work"
# usage: make_read_inputs.py <pdf dir> <page list e.g. 5-13 or 5,6,9> <out.jsonl>
pdf, pages, out = sys.argv[1:4]
want=set()
for part in pages.split(","):
    if "-" in part: a,b=part.split("-"); want|=set(range(int(a),int(b)+1))
    else: want.add(int(part))
with open(out,"w") as f:
    for p in sorted(want):
        jf=f"{BASE}/crops/{pdf}/p-{p:02d}.json" if os.path.exists(f"{BASE}/crops/{pdf}/p-{p:02d}.json") else f"{BASE}/crops/{pdf}/p-{p:03d}.json"
        if not os.path.exists(jf): print("missing", jf); continue
        d=json.load(open(jf))
        for s in d["systems"]:
            if s["n_staffs"]==1 and s["crops"] and "file" in s["crops"][0] and s["crops"][0].get("grandstaff"):
                f.write(json.dumps(dict(id=f"{pdf}/{d['page']}/s{s['system']}", image=f"{BASE}/crops/{pdf}/{s['crops'][0]['file']}"))+"\n")
