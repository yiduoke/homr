"""Summary table of one model tag against upstream 566 and the released model: python make_summary.py TAG [OUT.md].
Reads out/testset/<piece>/note-scores-TAG.json (written by eval_all.sh)."""
import glob, json, os, statistics as st, sys
tag = sys.argv[1]
base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "testset")
rows = []
for f in sorted(glob.glob(os.path.join(base, "*", f"note-scores-{tag}.json"))):
    piece = os.path.basename(os.path.dirname(f)); d = json.load(open(f)); e = {}
    if piece.endswith("-rendered") != bool(os.environ.get("RENDERED")): continue
    for r in d["results"]:
        m = r["metrics"]; g = lambda k: m[k]["combined"] if "combined" in m[k] else m[k]
        s = lambda x: x if isinstance(x, int) else x[0]
        e[r["name"]] = dict(p=g("pitch_inventory")["f1"] * 100, po=g("pitch_onset")["f1"] * 100, full=g("pitch_onset_duration")["f1"] * 100,
                            P=g("pitch_inventory")["precision"] * 100, R=g("pitch_inventory")["recall"] * 100, rb=s(r["reference_measures"]), pb=s(r["predicted_measures"]))
    if tag in e: rows.append((piece, e))
names = [n for n in ("run2s7", "566") if n != tag]
L = [f"# Real-scan test set: {tag} vs " + " and ".join(names), "", "F1 in %, pitch / +onset / full match. P, R = pitch precision and recall of " + tag + ". Bars = reference/ours.", "",
     f"| piece | bars | P | R | {tag} pitch | +onset | full | " + " | ".join(f"{n} pitch | +onset | full" for n in names) + " |", "|---|---|---|---|---|---|---|" + "---|---|---|" * len(names)]
for p, e in rows:
    o = e[tag]; cells = " | ".join("%.1f | %.1f | %.1f" % (e[n]["p"], e[n]["po"], e[n]["full"]) if n in e else "- | - | -" for n in names)
    L.append("| %s | %d/%d | %.0f | %.0f | %.1f | %.1f | %.1f | %s |" % (p, o["rb"], o["pb"], o["P"], o["R"], o["p"], o["po"], o["full"], cells))
n = len(rows)
if n:
    mo = [st.mean(e[tag][k] for _, e in rows) for k in ("p", "po", "full")]
    L += ["", "**Mean over %d pieces**: %s %.1f / %.1f / %.1f" % (n, tag, *mo) + "".join(
        ", %s %.1f / %.1f / %.1f" % (nm, *[st.mean(e[nm][k] for _, e in rows if nm in e) for k in ("p", "po", "full")]) for nm in names)]
    for nm in names:
        both = [(e[tag]["full"], e[nm]["full"]) for _, e in rows if nm in e]
        L.append("%s ahead of %s on full match in %d of %d pieces." % (tag, nm, sum(a > b for a, b in both), len(both)))
out = "\n".join(L) + "\n"
if len(sys.argv) > 2: open(sys.argv[2], "w").write(out)
print(out)
