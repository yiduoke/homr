"""D31: tables of the slot tracker against the D24 merger on the 28 real scans, for the shipped control, realbrace-2 and realbrace-3.
usage: python merge_tracking_table.py  -> merge_tracking/table.md, merge_tracking/results.json
Column sets (same page XML, same scorer, only the merger differs):
  d24      = tags shipped_merge_role_gpu / relbrace2_gpu / relbrace3_gpu  (D24 merger + drop_minor_parts.py)
  slots    = ctl_slots / rb2_slots / rb3_slots                           (slot tracker + drop_minor_parts.py)
  nodrop   = ..._nodrop                                                  (slot tracker only; its own minor-slot rule)"""
import json
import os
import statistics as st
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import res_lib as L  # noqa: E402

SETS = {
    "d24": {"ctl": "shipped_merge_role_gpu", "rb2": "relbrace2_gpu", "rb3": "relbrace3_gpu"},
    "slots": {"ctl": "ctl_slots", "rb2": "rb2_slots", "rb3": "rb3_slots"},
    "nodrop": {"ctl": "ctl_slots_nodrop", "rb2": "rb2_slots_nodrop", "rb3": "rb3_slots_nodrop"},
}
SCHOTT = {"liszt-sonata", "liszt-te-5", "liszt-te-10"}
OUTD = f"{L.E}/merge_tracking"
os.makedirs(OUTD, exist_ok=True)


def part_bars(path):
    root = ET.fromstring(open(path, "rb").read().decode("utf-8-sig"))
    return [len(p.findall("measure")) for p in root.findall("part")]


def load(tag, piece):
    s = L.load_scores(tag, piece)
    if s is None:
        return None
    pred, ref = f"{L.OUT}/{piece}/{piece}-{tag}.musicxml", f"{L.OUT}/{piece}/{piece}-reference.musicxml"
    pb, rb = part_bars(pred), part_bars(ref)
    hp = f"{L.OUT}/{piece}/hand-sync-{tag}.json"
    hs = json.load(open(hp)) if os.path.exists(hp) else None
    return {"sens": s["sens"], "pooled": s["pooled"], "pooled_defined": s["pooled_defined"], "pred_parts": pb, "ref_parts": rb,
            "bars_equal": s["bars_equal"], "hand": hs}


def fmt_bars(d):
    pb = d["pred_parts"]
    return "/".join(map(str, pb)) if len(set(pb)) > 1 else f"{pb[0]}" + (f"x{len(pb)}" if len(pb) > 1 else "")


def hand_pct(d):
    h = d["hand"]
    return None if not h or "pct" not in h else h["pct"]


def main():
    pieces = L.pieces28()
    R = {s: {m: {p: load(t, p) for p in pieces} for m, t in tags.items()} for s, tags in SETS.items()}
    json.dump(R, open(f"{OUTD}/results.json", "w"), indent=1)
    out = []
    w = out.append
    w("# Slot tracker against the D24 merger on the 28 real scans (D31)\n")
    w("Same saved page XML of the three runs of D28 (shipped control, realbrace-2, realbrace-3); `d24` = D24 merger + drop_minor_parts.py (the numbers of D28), `slots` = slot tracker + "
      "drop_minor_parts.py, `nodrop` = slot tracker alone. `*` = per-staff numbers (parts of different lengths, no joint bar list).\n")
    for metric, label in (("pooled", "pooled pitch F1"), ("sens", "staff-sensitive pitch F1"), ("po", "pooled pitch + onset F1"), ("full", "pooled full note F1")):
        w(f"## {label}\n")
        w("| piece | ctl d24 | ctl slots | rb2 d24 | rb2 slots | rb3 d24 | rb3 slots | ctl nodrop | rb2 nodrop | rb3 nodrop |")
        w("|---|---|---|---|---|---|---|---|---|---|")

        def val(d):
            if d is None:
                return None
            src = d["sens"] if metric == "sens" else d["pooled"]
            return src[{"pooled": "f1", "sens": "f1", "po": "po", "full": "full"}[metric]]

        for p in pieces:
            row = [p + (" (Schott)" if p in SCHOTT else "")]
            for s, m in (("d24", "ctl"), ("slots", "ctl"), ("d24", "rb2"), ("slots", "rb2"), ("d24", "rb3"), ("slots", "rb3"), ("nodrop", "ctl"), ("nodrop", "rb2"), ("nodrop", "rb3")):
                d = R[s][m][p]
                v = val(d)
                star = "*" if v is not None and metric != "sens" and not d["pooled_defined"] else ""
                row.append("n/a" if v is None else f"{v:.1f}{star}")
            w("| " + " | ".join(row) + " |")
        mean = lambda s, m, ps: st.mean(val(R[s][m][p]) for p in ps if R[s][m][p])  # noqa: E731
        non = [p for p in pieces if p != "stravinsky-petrushka"]
        for lab, ps in (("mean of 28", pieces), ("mean of 27 without Petrushka", non)):
            w(f"| **{lab}** | " + " | ".join(f"{mean(s, m, ps):.2f}" for s, m in (("d24", "ctl"), ("slots", "ctl"), ("d24", "rb2"), ("slots", "rb2"), ("d24", "rb3"), ("slots", "rb3"), ("nodrop", "ctl"), ("nodrop", "rb2"), ("nodrop", "rb3"))) + " |")
        w("")
    w("## Bars per part (reference), hands in the same reference bar\n")
    w("| piece | ref | ctl d24 | ctl slots | rb2 d24 | rb2 slots | rb3 d24 | rb3 slots | hands ctl d24/slots | rb2 d24/slots | rb3 d24/slots |")
    w("|---|---|---|---|---|---|---|---|---|---|---|")
    for p in pieces:
        row = [p, "/".join(map(str, R["d24"]["ctl"][p]["ref_parts"]))]
        for m in ("ctl", "rb2", "rb3"):
            for s in ("d24", "slots"):
                d = R[s][m][p]
                row.append("n/a" if d is None else fmt_bars(d) + ("" if d["bars_equal"] else " NO"))
        for m in ("ctl", "rb2", "rb3"):
            hs = [hand_pct(R[s][m][p]) for s in ("d24", "slots")]
            row.append(" / ".join("n/a" if h is None else f"{h:.0f}" for h in hs))
        w("| " + " | ".join(row) + " |")
    for s in SETS:
        for m in ("ctl", "rb2", "rb3"):
            eq = sum(1 for p in pieces if R[s][m][p] and R[s][m][p]["bars_equal"])
            hs = [hand_pct(R[s][m][p]) for p in pieces if R[s][m][p] and hand_pct(R[s][m][p]) is not None]
            w(f"\n{s}/{m}: bars equal to the reference on {eq} of {len(pieces)}; hands in the same bar, mean {st.mean(hs):.1f} % over {len(hs)} pieces.")
    w("\n## Piece by piece: slot tracker minus D24 merger (pooled pitch; changes of 0.05 or more), both with drop_minor_parts.py\n")
    for m in ("ctl", "rb2", "rb3"):
        ch = [(p, R["slots"][m][p]["pooled"]["f1"] - R["d24"][m][p]["pooled"]["f1"]) for p in pieces if R["slots"][m][p] and R["d24"][m][p]]
        w(f"* {m}: " + (", ".join(f"{p} {x:+.2f}" for p, x in ch if abs(x) >= 0.05) or "no change"))
    w("\n## Adoption criteria on the slot tracker (task 4): rb2 / rb3 against the shipped control, same merger (with drop_minor_parts.py and without)\n")
    for s in ("slots", "nodrop"):
        for k in ("rb2", "rb3"):
            rows = []
            for p in pieces:
                c, d = R[s]["ctl"][p], R[s][k][p]
                if c is None or d is None:
                    continue
                why = []
                dp = d["pooled"]["f1"] - c["pooled"]["f1"]
                if dp <= -0.5:
                    why.append(f"pooled {dp:+.1f}")
                bc = max(abs(x - y) for x, y in zip(d["pred_parts"], d["ref_parts"])) if len(d["pred_parts"]) == len(d["ref_parts"]) else 999
                bc0 = max(abs(x - y) for x, y in zip(c["pred_parts"], c["ref_parts"])) if len(c["pred_parts"]) == len(c["ref_parts"]) else 999
                if (c["bars_equal"] and not d["bars_equal"]) or bc > bc0:
                    why.append(f"bars {fmt_bars(d)} vs {fmt_bars(c)} (reference {'/'.join(map(str, c['ref_parts']))})")
                hc, hd = hand_pct(c), hand_pct(d)
                if hc is not None and hd is not None and hd <= hc - 3:
                    why.append(f"hands {hd:.0f} % vs {hc:.0f} %")
                if why:
                    rows.append(f"  * {p}: " + "; ".join(why))
            w(f"* {k} vs ctl, merger {s}: " + ("none" if not rows else ""))
            out.extend(rows)
    open(f"{OUTD}/table.md", "w").write("\n".join(out))
    print("\n".join(out))


if __name__ == "__main__":
    main()
