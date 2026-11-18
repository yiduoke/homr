"""D28: per-piece, per-model tables of the pairing-model comparison on the 28 real scans (needs the tags pulled from the box).
usage: python brace_table.py  ->  eval_run1/brace_models/table.md, results.json
Columns: pooled pitch (sounding pitch in the aligned bar on either staff), staff-sensitive pitch, pooled +onset, pooled full, bars per part
(output / reference), parts, bar counts equal to the reference, hands in the same reference bar (hand_sync.py), delta of pooled pitch to the
shipped control. Regression rule (task 4): pooled pitch lower by >= 0.5 points than the control, or bar counts differ from the reference where
the control's equal / differ by more bars, or the hand-sync share lower by >= 3 points."""
import json
import os
import statistics as st
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import res_lib as L  # noqa: E402

TAGS = {"ctl": "shipped_merge_role_gpu", "rb2": "relbrace2_gpu", "rb3": "relbrace3_gpu"}
SCHOTT = {"liszt-sonata", "liszt-te-5", "liszt-te-10"}
OUTD = f"{L.E}/brace_models"
os.makedirs(OUTD, exist_ok=True)


def part_bars(path):
    root = ET.fromstring(open(path, "rb").read().decode("utf-8-sig"))
    return [len(p.findall("measure")) for p in root.findall("part")]


def load(tag, piece):
    s = L.load_scores(tag, piece)
    if s is None:
        return None
    pred = f"{L.OUT}/{piece}/{piece}-{tag}.musicxml"
    ref = f"{L.OUT}/{piece}/{piece}-reference.musicxml"
    pb, rb = part_bars(pred), part_bars(ref)
    hs = None
    hp = f"{L.OUT}/{piece}/hand-sync-{tag}.json"
    if os.path.exists(hp):
        hs = json.load(open(hp))
    wall = None
    wp = f"{L.E}/testset/{tag}/{piece}/wall_seconds.txt"
    if os.path.exists(wp):
        wall = float(open(wp).read())
    return {"sens": s["sens"], "pooled": s["pooled"], "pooled_defined": s["pooled_defined"], "pred_parts": pb, "ref_parts": rb,
            "bars_equal": s["bars_equal"] and pb == rb if len(rb) == len(pb) else s["bars_equal"], "pred_bars": s["pred_bars"],
            "ref_bars": s["ref_bars"], "hand": hs, "wall": wall}


def fmt_bars(d):
    pb = d["pred_parts"]
    b = "/".join(map(str, pb)) if len(set(pb)) > 1 else f"{pb[0]}" + (f"x{len(pb)}" if len(pb) > 1 else "")
    return b


def hand_pct(d):
    h = d["hand"]
    return None if not h or "pct" not in h else h["pct"]


def main():
    pieces = L.pieces28()
    R = {k: {p: load(t, p) for p in pieces} for k, t in TAGS.items()}
    json.dump(R, open(f"{OUTD}/results.json", "w"), indent=1)
    out = []
    w = out.append
    w("# Pairing models on the 28 real scans: same GPU pipeline, same merger, same scorer (D28)\n")
    w("Pooled = pitch counted in the aligned bar on either staff (a piece whose parts have different bar counts, e.g. Petrushka, has no joint bar list and carries "
      "its per-staff numbers, marked `*`). Bars = bars per output part (reference in the second column; `x2` = two parts with that count). Hands = share of output bars "
      "where both hands point to the same reference bar (`hand_sync.py`, two-staff pieces only). Delta = pooled pitch of the model minus the shipped control (same box, GPU, merger by staff role).\n")
    for metric, label in (("pooled", "pooled pitch F1"), ("sens", "staff-sensitive pitch F1")):
        w(f"## {label}\n")
        w("| piece | control | rb2 | rb3 | rb2 - ctl | rb3 - ctl |")
        w("|---|---|---|---|---|---|")
        for p in pieces:
            c, a, b = R["ctl"][p], R["rb2"][p], R["rb3"][p]
            def f(d):
                if d is None:
                    return "n/a"
                m = d[metric]["f1"]
                star = "*" if metric == "pooled" and not d["pooled_defined"] else ""
                return f"{m:.1f}{star}"
            def dl(d):
                return "n/a" if d is None or c is None else f"{d[metric]['f1'] - c[metric]['f1']:+.1f}"
            w(f"| {p}{' (Schott)' if p in SCHOTT else ''} | {f(c)} | {f(a)} | {f(b)} | {dl(a)} | {dl(b)} |")
        for k in ("ctl", "rb2", "rb3"):
            pass
        means = {k: st.mean(R[k][p][metric]["f1"] for p in pieces if R[k][p]) for k in R}
        means25 = {k: st.mean(R[k][p][metric]["f1"] for p in pieces if R[k][p] and p not in SCHOTT) for k in R}
        w(f"| **mean of 28** | {means['ctl']:.2f} | {means['rb2']:.2f} | {means['rb3']:.2f} | {means['rb2']-means['ctl']:+.2f} | {means['rb3']-means['ctl']:+.2f} |")
        w(f"| **mean of the 25 non-Schott** | {means25['ctl']:.2f} | {means25['rb2']:.2f} | {means25['rb3']:.2f} | {means25['rb2']-means25['ctl']:+.2f} | {means25['rb3']-means25['ctl']:+.2f} |\n")
    w("## pooled +onset and pooled full note F1\n")
    w("| piece | ctl +onset | rb2 | rb3 | ctl full | rb2 | rb3 |")
    w("|---|---|---|---|---|---|---|")
    for p in pieces:
        c, a, b = R["ctl"][p], R["rb2"][p], R["rb3"][p]
        g = lambda d, k: "n/a" if d is None else f"{d['pooled'][k]:.1f}"  # noqa: E731
        w(f"| {p} | {g(c,'po')} | {g(a,'po')} | {g(b,'po')} | {g(c,'full')} | {g(a,'full')} | {g(b,'full')} |")
    for k2, lab in (("po", "+onset"), ("full", "full")):
        pass
    mm = {(k, m): st.mean(R[k][p]["pooled"][m] for p in pieces if R[k][p]) for k in R for m in ("po", "full")}
    w(f"| **mean of 28** | {mm['ctl','po']:.2f} | {mm['rb2','po']:.2f} | {mm['rb3','po']:.2f} | {mm['ctl','full']:.2f} | {mm['rb2','full']:.2f} | {mm['rb3','full']:.2f} |\n")
    w("## Bars per part, equality with the reference, hands in the same bar\n")
    w("| piece | ref bars | ctl bars | eq | hands % | rb2 bars | eq | hands % | rb3 bars | eq | hands % |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for p in pieces:
        row = [p]
        rr = R["ctl"][p]
        row.append("/".join(map(str, rr["ref_parts"])) if rr else "n/a")
        for k in ("ctl", "rb2", "rb3"):
            d = R[k][p]
            if d is None:
                row += ["n/a"] * 3
                continue
            hp = hand_pct(d)
            row += [fmt_bars(d), "yes" if d["bars_equal"] else "NO", "n/a" if hp is None else f"{hp:.0f}"]
        w("| " + " | ".join(row) + " |")
    for k in R:
        n_eq = sum(1 for p in pieces if R[k][p] and R[k][p]["bars_equal"])
        hs = [hand_pct(R[k][p]) for p in pieces if R[k][p] and hand_pct(R[k][p]) is not None]
        w(f"\n{TAGS[k]}: bar counts equal to the reference on {n_eq} of {len(pieces)} pieces; hands in the same bar, mean {st.mean(hs):.1f} % over {len(hs)} pieces, "
          f"below 100 on {sum(1 for h in hs if h < 99.95)}.")
    w("\n## Regressions against the shipped control (task 4)\n")
    for k in ("rb2", "rb3"):
        w(f"### {TAGS[k]}\n")
        rows = []
        for p in pieces:
            c, d = R["ctl"][p], R[k][p]
            if c is None or d is None:
                continue
            dpool = d["pooled"]["f1"] - c["pooled"]["f1"]
            why = []
            if dpool <= -0.5:
                why.append(f"pooled pitch {dpool:+.1f}")
            bc = max(abs(x - y) for x, y in zip(d["pred_parts"], d["ref_parts"])) if len(d["pred_parts"]) == len(d["ref_parts"]) else 999
            bc0 = max(abs(x - y) for x, y in zip(c["pred_parts"], c["ref_parts"])) if len(c["pred_parts"]) == len(c["ref_parts"]) else 999
            if (c["bars_equal"] and not d["bars_equal"]) or bc > bc0:
                why.append(f"bars {fmt_bars(d)} vs control {fmt_bars(c)} (reference {'/'.join(map(str, c['ref_parts']))})")
            hc, hd = hand_pct(c), hand_pct(d)
            if hc is not None and hd is not None and hd <= hc - 3:
                why.append(f"hands {hd:.0f} % vs {hc:.0f} %")
            if why:
                rows.append(f"* {p}: " + "; ".join(why))
        w("\n".join(rows) if rows else "None.")
        w("")
        gains = [(p, R[k][p]["pooled"]["f1"] - R["ctl"][p]["pooled"]["f1"]) for p in pieces if R[k][p] and R["ctl"][p]]
        w("Pooled change, all 28: " + ", ".join(f"{p} {x:+.1f}" for p, x in sorted(gains, key=lambda t: t[1]) if abs(x) >= 0.05) + "\n")
    open(f"{OUTD}/table.md", "w").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
