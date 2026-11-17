"""Per-source statistics and manifest of the scan lists. usage: python stats.py (on the box, after build_pairs.py)."""
import collections, hashlib, json, os, re, statistics
BASE = "/workspace/run4/scans"
P = [json.loads(l) for l in open(f"{BASE}/pairs.jsonl")]
val_pieces = {tuple(x) for x in json.load(open(f"{BASE}/scan_val_pieces.json"))}
pieces = {(p["repo"], p["piece"]): p for p in json.load(open(f"{BASE}/pieces.json"))}
st = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
notes = collections.defaultdict(lambda: collections.defaultdict(list))
meters = collections.defaultdict(lambda: collections.defaultdict(collections.Counter))
keys = collections.defaultdict(collections.Counter)
quar = collections.defaultdict(collections.Counter)
for r in P:
    repo = r["repo"].split("-")[0]
    if r["reasons"]:
        for x in r["reasons"]:
            quar[repo][x] += 1
        quar[repo]["_any"] += 1
        continue
    split = "val" if (r["repo"], r["piece"]) in val_pieces else "train"
    st[repo][split]["staffs"] += 1
    notes[repo][split].append(r["n_notes"])
    txt = open(r["tokens"]).read()
    for m in re.findall(r"timeSignature_[\w/]+", txt):
        meters[repo][split][m] += 1
    for m in re.findall(r"keySignature_-?\d+", txt):
        keys[repo][m] += 1
    st[repo][split]["pieces"] += 0
    st[repo][split]["verified_by_" + r["checks"].get("verified_by", "?")] += 1
out = {}
for repo in st:
    out[repo] = {}
    for split in ("train", "val"):
        n = notes[repo][split]
        pcs = {(r["repo"], r["piece"]) for r in P if r["repo"].startswith(repo) and not r["reasons"] and (((r["repo"], r["piece"]) in val_pieces) == (split == "val"))}
        out[repo][split] = dict(staffs=st[repo][split]["staffs"], pieces=len(pcs),
                                notes_per_staff=dict(mean=round(statistics.mean(n), 1) if n else 0, median=statistics.median(n) if n else 0,
                                                     p10=sorted(n)[len(n) // 10] if n else 0, p90=sorted(n)[9 * len(n) // 10] if n else 0),
                                time_signature_tokens=dict(meters[repo][split]),
                                verified_by={k[12:]: v for k, v in st[repo][split].items() if k.startswith("verified_by_")})
    out[repo]["key_signatures"] = dict(keys[repo])
    out[repo]["quarantine"] = dict(quar[repo])
pc = collections.Counter(p["status"] for p in pieces.values())
out["pieces"] = dict(pc)
out["pieces_quarantined"] = sorted(f"{k[0]}/{k[1]}" for k, p in pieces.items() if p["status"] != "ok")
out["val_pieces"] = sorted(f"{a}/{b}" for a, b in val_pieces)
scripts = {}
for f in sorted(os.listdir(f"{BASE}/scripts")):
    if f.endswith((".py",)) and not f.startswith("t"):
        scripts[f] = hashlib.sha256(open(f"{BASE}/scripts/{f}", "rb").read()).hexdigest()[:16]
out["script_sha256_16"] = scripts
ps = json.load(open(f"{BASE}/piece_status.json"))
out["piece_level_status"] = {k: v for k, v in sorted(collections.Counter(f"{r[0].split('-')[0]}:{r[2]}" for r in ps).items())}
out["piece_status_note"] = "match = total system count of the homr detection equals the .krn line breaks and all systems are single grand staffs; excluded_test = composition in test_set_exclusions.txt"
out["seeds"] = dict(validation_pieces=20261118, eye_sample=31, image_stats=11)
for f in ("scan_train.txt", "scan_val.txt", "scan_quarantine.txt"):
    out["lines_" + f] = sum(1 for _ in open(f"{BASE}/{f}") if _.strip())
json.dump(out, open(f"{BASE}/manifest.json", "w"), indent=1)
print(json.dumps(out, indent=1)[:6000])
