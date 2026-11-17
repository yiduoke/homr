"""Pitches right per bar against a reference MusicXML, per staff.

    python score_vs_ref.py REFERENCE.musicxml NAME=HYP.musicxml [NAME=HYP.musicxml ...]

Bars are aligned by dynamic programming on per-bar pitch F1 (so a missing or extra bar
doesn't shift everything after it). Reported: mean F1 over matched bars, the same
ignoring octave, and the mean over all reference bars (unmatched bars count 0).
"""
import sys
from collections import Counter

from music21 import converter


def bars(part):
    return [
        Counter(p.midi for n in m.flatten().notes for p in n.pitches)
        for m in part.getElementsByClass("Measure")
    ]


def f1(a, b):
    i = sum((a & b).values())
    if not a and not b:
        return 1.0
    p = i / max(1, sum(b.values()))
    r = i / max(1, sum(a.values()))
    return 0 if p + r == 0 else 2 * p * r / (p + r)


def pc(c):
    o = Counter()
    for k, v in c.items():
        o[k % 12] += v
    return o


def score(ref, hyp):
    out = []
    for si in (0, 1):
        R, H = bars(ref.parts[si]), bars(hyp.parts[si])
        n, m = len(R), len(H)
        D = [[0.0] * (m + 1) for _ in range(n + 1)]
        for i in range(1, n + 1):
            for j in range(1, m + 1):
                D[i][j] = max(D[i - 1][j], D[i][j - 1], D[i - 1][j - 1] + f1(R[i - 1], H[j - 1]))
        i, j, pairs = n, m, []
        while i > 0 and j > 0:
            if abs(D[i][j] - (D[i - 1][j - 1] + f1(R[i - 1], H[j - 1]))) < 1e-9:
                pairs.append((i - 1, j - 1))
                i -= 1
                j -= 1
            elif D[i][j] == D[i - 1][j]:
                i -= 1
            else:
                j -= 1
        ex = [f1(R[a], H[b]) for a, b in pairs]
        po = [f1(pc(R[a]), pc(H[b])) for a, b in pairs]
        out.append(
            {
                "bars": n,
                "matched": len(pairs),
                "f1": sum(ex) / max(1, len(ex)),
                "f1_octave_free": sum(po) / max(1, len(po)),
                "over_all": sum(ex) / n,
                "good": sum(x >= 0.9 for x in ex),
                "bad": sum(x < 0.5 for x in ex),
            }
        )
    return out


ref = converter.parse(sys.argv[1])
print(f"reference: {len(ref.parts)} parts, {len(ref.parts[0].getElementsByClass('Measure'))} bars")
for arg in sys.argv[2:]:
    name, path = arg.split("=", 1)
    s = score(ref, converter.parse(path))
    print(
        f"{name:22s} "
        + " | ".join(
            f"staff {k + 1}: all-bars {x['over_all']:.3f}, matched {x['f1']:.3f} "
            f"(octave-free {x['f1_octave_free']:.3f}), >=90% {x['good']}, <50% {x['bad']}"
            for k, x in enumerate(s)
        )
    )
