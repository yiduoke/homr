"""Counts per piece/tier, released-model pitch F1 on strong+hard crops by piece, quarantine reasons, content coverage. Reads manifest.csv + work/export."""
import csv, json, collections, re, os, sys
ROOT = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso"
rows = list(csv.DictReader(open(f"{ROOT}/manifest.csv")))
by = collections.defaultdict(lambda: collections.Counter())
f1s = collections.defaultdict(list); wts = collections.defaultdict(list)
qr = collections.defaultdict(collections.Counter)
exp = {}
import glob
for f in glob.glob(f"{ROOT}/work/export/*.json"):
    d = json.load(open(f))
    for r in d["records"]:
        if r.get("crop"): exp[os.path.basename(r["crop"])[:-4] if False else (r["pid"], r["page"], r["sys"])] = r
for r in rows:
    by[r["pid"]][r["tier"]] += 1
    if r["tier"] in ("strong", "hard") and r["pitch_f1"]:
        f1s[r["pid"]].append(float(r["pitch_f1"]))
    if r["tier"] == "quarantine":
        for x in r["reasons"].split(";"):
            qr[r["pid"]][re.sub(r"\(.*|:.*|KeyError.*", "", x).strip()] += 1
print("pid,group,title,strong,hard,quarantine,mean_f1_strong+hard")
pids = []
for r in rows:
    if r["pid"] not in pids: pids.append(r["pid"])
tot = collections.Counter()
for pid in pids:
    r0 = next(r for r in rows if r["pid"] == pid)
    c = by[pid]; m = sum(f1s[pid]) / len(f1s[pid]) if f1s[pid] else float("nan")
    print(f"{pid},{r0['group']},{r0['piece']},{c['strong']},{c['hard']},{c['quarantine']},{m:.3f}")
    for k in ("strong", "hard", "quarantine"): tot[(r0['group'], k)] += c[k]
print(dict(tot))
print("quarantine reasons:")
for pid in pids: print(pid, dict(qr[pid]))
