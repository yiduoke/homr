"""Compare model tags piece by piece: python compare_tags.py BASE TAG [TAG...] -> table (pitch / +onset / full for each, difference to BASE),
pitch against the 97% target. Reads out/testset/<piece>/note-scores-<tag>.json (the model named <tag> inside each file)."""
import glob, json, os, statistics as st, sys
base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", "testset")
tags = sys.argv[1:]
def load(tag):
    out = {}
    files = glob.glob(os.path.join(base_dir, "*", f"note-scores-{tag}.json")) + glob.glob(os.path.join(base_dir, "*", "note-scores.json")) + glob.glob(os.path.join(base_dir, "*", "note-scores-layout1.json"))
    for f in files:
        piece = os.path.basename(os.path.dirname(f)); d = json.load(open(f))
        for r in d["results"]:
            if r["name"] == tag and piece not in out:
                m = r["metrics"]; g = lambda k: m[k]["combined"] if "combined" in m[k] else m[k]
                out[piece] = tuple(g(k)["f1"] * 100 for k in ("pitch_inventory", "pitch_onset", "pitch_onset_duration"))
    return out
data = {t: load(t) for t in tags}
pieces = sorted(set.intersection(*[set(d) for d in data.values()]))
print("piece | " + " | ".join(f"{t} pitch/+on/full" for t in tags) + " | d pitch vs " + tags[0] + " | below 97 pitch")
rows = []
for p in pieces:
    cells = [" ".join("%5.1f" % x for x in data[t][p]) for t in tags]
    d = [data[t][p][0] - data[tags[0]][p][0] for t in tags[1:]]
    print("%-26s | %s | %s | %s" % (p, " | ".join(cells), " ".join("%+5.1f" % x for x in d), "" if all(data[t][p][0] >= 97 for t in tags) else ""))
print("\nmean over %d pieces:" % len(pieces))
for t in tags:
    print("  %-12s pitch %.1f  +onset %.1f  full %.1f   pieces with pitch >= 97: %d" % (t, *[st.mean(data[t][p][i] for p in pieces) for i in range(3)], sum(data[t][p][0] >= 97 for p in pieces)))
for t in tags[1:]:
    dd = [data[t][p][0] - data[tags[0]][p][0] for p in pieces]
    print("  %s - %s pitch: mean %+.2f, better in %d, worse in %d, equal %d" % (t, tags[0], st.mean(dd), sum(x > 0.05 for x in dd), sum(x < -0.05 for x in dd), sum(abs(x) <= 0.05 for x in dd)))
