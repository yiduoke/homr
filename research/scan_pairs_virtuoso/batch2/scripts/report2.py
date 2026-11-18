"""Batch-2 report: counts per piece and tier, released-model pitch and pitch+onset F1 on the kept crops (against the FINAL tokens), quarantine reasons, octave roles,
eye-check error rates. Writes report.json and prints markdown tables. Run with run/tuplet_wt on the path (rhythm_tools)."""
import sys, os, csv, json, re, glob, collections, statistics
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rhythm_tools as rt
from pieces2 import P, BY
B = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2/"
rows = list(csv.DictReader(open(B + "manifest.csv")))
reads = {}
for f in glob.glob(B + "work/reads/*.jsonl"):
    for l in open(f):
        d = json.loads(l); reads[d["id"]] = d
exp = {}
for f in glob.glob(B + "work/export/*.json"):
    for r in json.load(open(f))["records"]:
        if r.get("name"): exp[r["name"]] = r
KEPT = ("strong", "hard", "octave_verified")
KEEP_ROLE = {  # corrected crops that open/continue the printed bracket (decided by eye)
 "N19_p-25_s3": (True, True), "N19_p-25_s4": (True, True), "N19_p-26_s0": (True, True), "N19_p-26_s1": (True, False)}
def roles(name, toks):
    has = bool(re.search("octaveShift", toks))
    starts = len(re.findall(r"octaveShift_8v[ab]", toks)); stops = toks.count("octaveShiftStop")
    lines = toks.strip().split("\n"); first_note = next((i for i, l in enumerate(lines) if l.startswith("note")), 10 ** 9)
    first_shift = next((i for i, l in enumerate(lines) if l.startswith("octaveShift_8v")), 10 ** 9)
    rec = exp.get(name, {})
    inside_start = (first_shift < first_note) and bool(rec.get("oct_start_inside"))
    open_end = starts > stops or (stops > starts and False)
    stop_in_crop = stops > 0
    if name in KEEP_ROLE: inside_start, open_end = KEEP_ROLE[name]; stop_in_crop = not open_end
    return dict(has=has, start_inside=inside_start, open_end=open_end, stop_in_crop=stop_in_crop, ends_inside=(inside_start and stop_in_crop))
out = dict(pieces={}, groups={}, quarantine={}, roles={}, eye={})
per = collections.OrderedDict()
for r in rows:
    pid = r["pid"]; d = per.setdefault(pid, dict(title=r["piece"], group=r["group"], strong=0, hard=0, octave_verified=0, quarantine=0, f1p=[], f1o=[]))
    t = r["tier"]; d[t if t in ("strong", "hard", "octave_verified") else "quarantine"] += 1
    if t in KEPT:
        name = os.path.basename(r["crop"])[:-4]; pdf = r["page_image"].split("/")[1]; pg = r["page_image"].split("/")[2][:-4]
        rd = reads.get(f"{pdf}/{pg}/s{r['system_index']}")
        if rd and rd.get("tokens"):
            m = rt.agreement(open(B + f"tokens/{name}.tokens").read(), rd["tokens"]); d["f1p"].append(m["pitch_f1"]); d["f1o"].append(m["onset_f1"])
tot = collections.defaultdict(lambda: collections.Counter())
print("| pid | piece | group | strong | hard | octave-verified | quarantined | pitch F1 | pitch+onset F1 |\n|---|---|---|---|---|---|---|---|---|")
G = {"T": "train", "V": "val", "D": "demets"}
agg = collections.defaultdict(lambda: dict(n=0, p=[], o=[]))
for pid, d in per.items():
    mp = statistics.mean(d["f1p"]) if d["f1p"] else float("nan"); mo = statistics.mean(d["f1o"]) if d["f1o"] else float("nan")
    print(f"| {pid} | {d['title']} | {G[d['group']]} | {d['strong']} | {d['hard']} | {d['octave_verified']} | {d['quarantine']} | {mp:.3f} | {mo:.3f} |")
    for k in ("strong", "hard", "octave_verified", "quarantine"): tot[G[d['group']]][k] += d[k]
    agg[G[d['group']]]["p"] += d["f1p"]; agg[G[d['group']]]["o"] += d["f1o"]
    out["pieces"][pid] = dict(title=d["title"], group=G[d["group"]], strong=d["strong"], hard=d["hard"], octave_verified=d["octave_verified"], quarantine=d["quarantine"], pitch_f1=mp, onset_f1=mo)
print("\n| group | strong | hard | octave-verified | quarantined | kept | pitch F1 | pitch+onset F1 |\n|---|---|---|---|---|---|---|---|")
for g, c in tot.items():
    kept = c["strong"] + c["hard"] + c["octave_verified"]
    print(f"| {g} | {c['strong']} | {c['hard']} | {c['octave_verified']} | {c['quarantine']} | {kept} | {statistics.mean(agg[g]['p']):.3f} | {statistics.mean(agg[g]['o']):.3f} |")
    out["groups"][g] = dict(c, kept=kept, pitch_f1=statistics.mean(agg[g]["p"]), onset_f1=statistics.mean(agg[g]["o"]))
allp = [x for a in agg.values() for x in a["p"]]; allo = [x for a in agg.values() for x in a["o"]]
print(f"\nall kept crops {len(allp)}: pitch F1 {statistics.mean(allp):.3f} (median {statistics.median(allp):.3f}), pitch+onset F1 {statistics.mean(allo):.3f} (median {statistics.median(allo):.3f})")
out["all"] = dict(n=len(allp), pitch=statistics.mean(allp), onset=statistics.mean(allo))
# quarantine reasons
qc = collections.Counter(); qpiece = collections.defaultdict(collections.Counter)
def cls(x):
    x = x.strip()
    if x.startswith("conversion error"): return "duration/tuplet not representable (no token)"
    if x.startswith("tuplet not representable"): return "duration/tuplet not representable (no token)"
    if x.startswith("rhythm: MusicXML bar longer"): return "rhythm: MusicXML bar longer than the meter"
    if x.startswith("rhythm: token duration"): return "rhythm: token sum differs from MusicXML (volta/repeat split, cadenza)"
    if x.startswith("trainer:ledger"): return "ledger lines > 5 (trainer filter)"
    if x.startswith("trainer"): return "trainer filter (vocabulary/length)"
    if x.startswith("octave-bracket disagreement") or x.startswith("octave shift (pitch") or x.startswith("octave review"): return "octave review: not admitted (label wrong / edition difference / partial)"
    if x.startswith("by eye"): return "wrong by eye"
    if x.startswith("alignment ambiguous"): return "alignment ambiguous"
    if x.startswith("bar mismatch"): return "bar mismatch"
    if x.startswith("edition mismatch"): return "edition/key mismatch"
    if x.startswith("not_piece_music"): return "not music of the piece (before start / after end)"
    if x.startswith("crop:not_one_grand_staff"): return "crop not one grand staff"
    return x[:50]
for r in rows:
    if r["tier"] == "quarantine":
        cs = {cls(x) for x in r["reasons"].split(";")}
        for c in cs: qc[c] += 1; qpiece[r["pid"]][c] += 1
        qc["_total"] += 1
print("\nquarantine reasons (a crop can have several; total %d):" % qc.pop("_total"))
for k, v in qc.most_common(): print(f"- {k}: {v}")
out["quarantine"] = dict(qc)
# octave roles over kept crops
rc = collections.Counter(); rpiece = collections.defaultdict(collections.Counter)
for r in rows:
    if r["tier"] not in KEPT: continue
    name = os.path.basename(r["crop"])[:-4]; ro = roles(name, open(B + f"tokens/{name}.tokens").read()); grp = G[r["group"]]
    for key, cond in (("kept", True), ("has_8va_token", ro["has"]), ("start_inside_8va", ro["start_inside"]), ("continue_through_8va (starts inside, no stop)", ro["start_inside"] and not ro["stop_in_crop"]),
                      ("end_an_8va (starts inside, stop in crop)", ro["ends_inside"]), ("open_at_end (continues into next system)", ro["open_end"]), ("bracket starts and stops in the crop", ro["has"] and not ro["start_inside"] and ro["stop_in_crop"] and not ro["open_end"])):
        if cond: rc[(grp, key)] += 1; rc[("ALL", key)] += 1
print("\noctave roles of kept crops:")
for g in ("train", "val", "demets", "ALL"):
    print(g, {k: rc[(g, k)] for k in ("kept", "has_8va_token", "start_inside_8va", "continue_through_8va (starts inside, no stop)", "end_an_8va (starts inside, stop in crop)", "open_at_end (continues into next system)", "bracket starts and stops in the crop")})
out["roles"] = {f"{g}|{k}": v for (g, k), v in rc.items()}
# eye check
ev = [r for r in rows if r["eye"]]
sn = [r for r in ev if r["tier"] == "strong" or (r["tier"] == "quarantine" and r["eye"].startswith("wrong") and r["verification"] == "")]
print("\neye check rows:", len(ev))
json.dump(out, open(B + "report.json", "w"), indent=1, default=str)
