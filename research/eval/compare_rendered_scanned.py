"""Paired read: each virtuoso piece rendered from its reference vs the real scan, same code and weights.
usage: python compare_rendered_scanned.py TAG [OUT.md]  (reads out/testset/<piece>[-rendered]/note-scores-TAG.json)"""
import json, os, sys, statistics as st
tag = sys.argv[1]; base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "testset")
def get(piece):
    f = os.path.join(base, piece, f"note-scores-{tag}.json")
    if not os.path.exists(f): return None
    for r in json.load(open(f))["results"]:
        if r["name"] == tag:
            m = r["metrics"]; g = lambda k: m[k]["combined"] if "combined" in m[k] else m[k]
            return [g(k)["f1"] * 100 for k in ("pitch_inventory", "pitch_onset", "pitch_onset_duration")]
rows = []
for d in sorted(os.listdir(base)):
    if d.endswith("-rendered"):
        a, b = get(d), get(d[:-9])
        if a and b: rows.append((d[:-9], a, b))
L = [f"# Rendered vs real scan, tag {tag}", "", "F1 in %. Rendered = pages engraved from the reference; scan = the real edition.", "",
     "| piece | rendered pitch | scan pitch | gap | rendered +onset | scan +onset |", "|---|---|---|---|---|---|"]
for p, a, b in rows: L.append("| %s | %.1f | %.1f | %+.1f | %.1f | %.1f |" % (p, a[0], b[0], a[0] - b[0], a[1], b[1]))
if rows:
    L += ["", "**Mean over %d pieces**: rendered pitch %.1f, scan pitch %.1f; rendered +onset %.1f, scan +onset %.1f" % (len(rows),
          st.mean(r[1][0] for r in rows), st.mean(r[2][0] for r in rows), st.mean(r[1][1] for r in rows), st.mean(r[2][1] for r in rows)),
          "Rendered pieces at or above 97 pitch: %d of %d." % (sum(r[1][0] >= 97 for r in rows), len(rows))]
out = "\n".join(L) + "\n"
if len(sys.argv) > 2: open(sys.argv[2], "w").write(out)
print(out)
