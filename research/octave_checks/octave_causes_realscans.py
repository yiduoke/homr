"""D32 task 2: note-level attribution of the octave loss (audit category '2 octave') on the real scans, relbrace3_gpu outputs (the audit of
run/eval_run1/brace_models/audit_relbrace3_gpu.md: 3557 octave events = 3.02 micro F1 points on 27 pieces; Petrushka is not in that audit).

READ-ONLY on all outputs. For every octave event of the audit (one reference note, one predicted note, same letter/accidental/staff, octaves differ by 1-2)
the exact octave-shift state of the reference note and of the predicted note is looked up in the MusicXML files (reference: ASAP; Schubert D.899/4: the
edition reference of the audit), with the shift spans (start/stop in the file, bar and onset). The system breaks of the PRINT are taken from the predicted
file (print new-system / new-page of homr's layout, mapped to reference bars through the audit's bar alignment).

Cause of an event (sounding-pitch octave difference d = pred - ref, bracket shift s = +1 for 8va, -1 for 8vb, 0 none):
  bracket-explained: d == s_pred - s_ref  (the written pitch agrees, only the bracket differs)
     ref bracket, pred none -> missed start (a) / read start late (a) / stop early (b); (c) if the reference span crosses a print system break
     pred bracket, ref none -> pred span overlaps a reference span that ended earlier -> stop late (b); else a read-only bracket:
                              spurious start OR reference/edition lacks the print's bracket (cannot be told apart without the print: (a?e) 'read-only bracket')
  both brackets equal (s_pred == s_ref) -> (d) wrong register, no bracket difference (inside = under a bracket)
  everything else -> mixed (register + bracket)
Usage: /Users/yiduoke/Documents/homr/.venv/bin/python -B octave_causes_realscans.py
"""
import json
import os
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

HOME = Path("/Users/yiduoke/Documents/homr/run")
TEST = HOME / "out/testset"
TAG = "relbrace3_gpu"
OUT = HOME / "octave_checks"
LET = "CDEFGAB"
SH = {"8va": 1, "8vb": -1, "15ma": 2, "15mb": -2}


def parse(path):
    """-> bars: list (combined over parts) of dict(notes=[(gstaff, name, onset, shift_str, span_id)], sysstart=bool); spans: list of dict"""
    root = ET.fromstring(Path(path).read_bytes().decode("utf-8-sig"))
    for el in root.iter():
        el.tag = el.tag.rsplit("}", 1)[-1]
    parts = root.findall("part")
    offset = 0
    nb = None
    bars = None
    spans = []
    for pi, part in enumerate(parts):
        staff_count = max([1] + [int(s.text or "1") for s in part.iter("staves")] + [int(n.findtext("staff") or "1") for n in part.findall("measure/note")])
        divisions = Fraction(1)
        active = {}  # gstaff -> span index
        measures = part.findall("measure")
        if bars is None:
            bars = [{"notes": [], "sysstart": False} for _ in measures]
        for mi, m in enumerate(measures):
            if pi == 0 and m.find("print") is not None and (m.find("print").get("new-system") == "yes" or m.find("print").get("new-page") == "yes"):
                bars[mi]["sysstart"] = True
            cursor = Fraction(0)
            last_onset = None
            events = []  # (time, gstaff, kind, dirtype, size)
            notes = []
            for el in m:
                if el.tag == "attributes":
                    t = el.findtext("divisions")
                    if t is not None:
                        divisions = Fraction(t)
                elif el.tag == "direction":
                    for osh in el.iter("octave-shift"):
                        st = offset + int(el.findtext("staff") or "1")
                        events.append((cursor, st, osh.get("type"), osh.get("size", "8")))
                elif el.tag in ("backup", "forward"):
                    d = Fraction(el.findtext("duration") or "0") / divisions
                    cursor += d if el.tag == "forward" else -d
                    last_onset = None
                elif el.tag == "note":
                    chord = el.find("chord") is not None
                    grace = el.find("grace") is not None
                    dur = Fraction(el.findtext("duration") or "0") / divisions
                    onset = last_onset if chord else cursor
                    if not chord:
                        last_onset = cursor
                        if not grace:
                            cursor += dur
                    pitch = el.find("pitch")
                    if pitch is None:
                        continue
                    if el.get("print-object") == "no" or any((h.text or "").strip() == "none" for h in el.findall("notehead")):
                        continue
                    step = pitch.findtext("step")
                    alter = float(pitch.findtext("alter") or "0")
                    octv = int(pitch.findtext("octave") or "0")
                    a = {0.0: "", 1.0: "#", -1.0: "b", 2.0: "##", -2.0: "bb"}.get(alter, f"({alter})")
                    st = offset + int(el.findtext("staff") or "1")
                    notes.append((st, f"{step}{a}{octv}", float(onset or 0), onset))
            # states: process events in time order (stable) against notes sorted by onset
            ev_sorted = sorted(enumerate(events), key=lambda x: (x[1][0], x[0]))
            for st, name, onset_f, onset in sorted(notes, key=lambda n: n[3] if n[3] is not None else 0):
                pass
            # apply events up to each note's onset
            active_local = dict(active)
            order = sorted(notes, key=lambda n: (n[3] if n[3] is not None else Fraction(0)))
            ei = 0
            for st, name, onset_f, onset in order:
                t = onset if onset is not None else Fraction(0)
                while ei < len(ev_sorted) and ev_sorted[ei][1][0] <= t:
                    _, (tm, est, kind, size) = ev_sorted[ei]
                    if kind in ("up", "down"):
                        typ = ("8vb" if kind == "up" else "8va") if size == "8" else ("15mb" if kind == "up" else "15ma")
                        spans.append({"staff": est, "type": typ, "sbar": mi, "sonset": round(float(tm), 3), "ebar": None, "eonset": None})
                        active_local[est] = len(spans) - 1
                    elif kind == "stop" and est in active_local:
                        sp = spans[active_local.pop(est)]
                        sp["ebar"], sp["eonset"] = mi, round(float(tm), 3)
                    ei += 1
                sid = active_local.get(st)
                bars[mi]["notes"].append((st, name, round(onset_f, 3), spans[sid]["type"] if sid is not None else "", sid))
            while ei < len(ev_sorted):  # events after the last note of the measure
                _, (tm, est, kind, size) = ev_sorted[ei]
                if kind in ("up", "down"):
                    typ = ("8vb" if kind == "up" else "8va") if size == "8" else ("15mb" if kind == "up" else "15ma")
                    spans.append({"staff": est, "type": typ, "sbar": mi, "sonset": round(float(tm), 3), "ebar": None, "eonset": None})
                    active_local[est] = len(spans) - 1
                elif kind == "stop" and est in active_local:
                    sp = spans[active_local.pop(est)]
                    sp["ebar"], sp["eonset"] = mi, round(float(tm), 3)
                ei += 1
            active = active_local
        offset += staff_count
    for sp in spans:
        if sp["ebar"] is None:
            sp["ebar"], sp["eonset"] = len(bars) - 1, 1e9  # never closed
            sp["open"] = True
    return bars, spans


def main():
    audit = json.load(open(HOME / "eval_run1/brace_audit_relbrace3_gpu.json"))["audit"]
    ev_all = []
    per_piece = {}
    for piece, a in audit.items():
        refp = TEST / piece / f"{piece}-reference{'-edition' if piece == 'schubert-impromptu-d899-4' else ''}.musicxml"
        prp = TEST / piece / f"{piece}-{TAG}.musicxml"
        rb, rspans = parse(refp)
        pb, pspans = parse(prp)
        pairs = {i: j for i, j in a["pairs"]}  # ref bar idx -> pred bar idx (0-based)
        pairs_inv = {j: i for i, j in pairs.items()}
        pred_sysstart = {j for j, b in enumerate(pb) if b["sysstart"]}
        # reference bars that start a print system (through the alignment)
        ref_sysstart = {i for i, j in pairs.items() if j in pred_sysstart}
        # also page-level: number of pred systems
        ign = a["ignore_staff"]
        nref, npred = a["nref"], a["npred"]
        lut_r = defaultdict(list)
        for bi, b in enumerate(rb):
            for n in b["notes"]:
                lut_r[(bi, n[1], n[2])].append(n)
        lut_p = defaultdict(list)
        for bi, b in enumerate(pb):
            for n in b["notes"]:
                lut_p[(bi, n[1], n[2])].append(n)

        def span_cross(spans, sid, sysstart):
            """does the span contain a system start strictly after its start bar (<= end bar)"""
            sp = spans[sid]
            return any(sp["sbar"] < b <= sp["ebar"] for b in sysstart)

        evs = []
        for r in a["recs"]:
            if r["cat"] != "2 octave":
                continue
            (rs, rname, ronset, _), (ps, pname, ponset, _) = r["ref"][0], r["pred"][0]
            ri, pj = r["ref_bar"] - 1, r["pred_bar"] - 1
            rc = lut_r.get((ri, rname, ronset), [])
            pc = lut_p.get((pj, pname, ponset), [])
            if not ign:
                rc = [n for n in rc if n[0] == rs] or rc
                pc = [n for n in pc if n[0] == ps] or pc
            rn = rc[0] if rc else None
            pn = pc[0] if pc else None
            sr = SH.get(rn[3], 0) if rn else None
            sp_ = SH.get(pn[3], 0) if pn else None
            d = int(r["label"])
            ev = {"piece": piece, "ref_bar": ri + 1, "pred_bar": pj + 1, "staff": rs, "ref": rname, "pred": pname, "d": d, "sr": sr, "sp": sp_,
                  "ref_span": None, "pred_span": None}
            if rn is None or pn is None:
                ev["cause"] = "unlocated"
                evs.append(ev)
                continue
            rsid, psid = rn[4], pn[4]
            if rsid is not None:
                s = rspans[rsid]
                ev["ref_span"] = [s["sbar"] + 1, s["sonset"], s["ebar"] + 1, None if s.get("open") else s["eonset"], span_cross(rspans, rsid, ref_sysstart)]
            if psid is not None:
                s = pspans[psid]
                ev["pred_span"] = [s["sbar"] + 1, s["sonset"], s["ebar"] + 1, None if s.get("open") else s["eonset"], span_cross(pspans, psid, pred_sysstart)]
            # classification
            if sr == sp_:
                # same exact state at the two notes: look at the bracket profile of the two bars on that staff (dense bars: the audit pairs a
                # missed note with an extra one of the same letter, so a bracket that starts/stops at a different place shows up here)
                def prof(bars, bi, staff, spans, ignore):
                    return [(n[2], n[3], n[4]) for n in bars[bi]["notes"] if n[3] and (ignore or n[0] == staff)]
                R = prof(rb, ri, rs, rspans, ign)
                P = prof(pb, pj, ps, pspans, ign)
                prev_R = prof(rb, ri - 1, rs, rspans, ign) if ri > 0 else []
                crossflag = any(span_cross(rspans, x[2], ref_sysstart) for x in R) or any(span_cross(pspans, x[2], pred_sysstart) for x in P)
                crossflag = crossflag or (not R and bool(prev_R) and any(span_cross(rspans, x[2], ref_sysstart) for x in prev_R))
                ev["bar_profile"] = [len(R), len(P)]
                if not R and not P:
                    ev["cause"], ev["sub"] = "d", "no bracket in either bar (register / ledger lines / clef)"
                elif R and not P:
                    ev["cause"], ev["sub"] = ("c" if crossflag else "a"), "bar: reference has a bracket, read none on this staff"
                elif P and not R:
                    if prev_R and any(x[0] >= 0 for x in prev_R):
                        ev["cause"], ev["sub"] = ("c" if crossflag else "b"), "bar: read bracket runs on where the reference bracket ended in the previous bar"
                    else:
                        ev["cause"], ev["sub"] = "ae", "bar: read-only bracket (spurious or reference lacks the print's bracket)"
                else:
                    r0, r1 = min(x[0] for x in R), max(x[0] for x in R)
                    p0, p1 = min(x[0] for x in P), max(x[0] for x in P)
                    if abs(r0 - p0) > 0.2:
                        ev["cause"], ev["sub"] = ("c" if crossflag else "a"), "bar: bracket starts at a different note"
                    elif abs(r1 - p1) > 0.2:
                        ev["cause"], ev["sub"] = ("c" if crossflag else "b"), "bar: bracket stops at a different note"
                    else:
                        ev["cause"], ev["sub"] = "d", "bracket extent equal in both bars, note read an octave off"
            elif d == sp_ - sr:
                if sr != 0 and sp_ == 0:
                    # reference bracket, pred none: does a pred span overlap the reference span?
                    s = rspans[rsid]
                    cross = ev["ref_span"][4]
                    overlap = None
                    for qi, q in enumerate(pspans):
                        if q["staff"] == (pn[0] if not ign else q["staff"]) and q["type"] == s["type"]:
                            pass
                    # map the reference span to pred bar coordinates and look for any predicted span of the same direction overlapping its bar range
                    ps_bars = [pairs.get(b) for b in range(s["sbar"], s["ebar"] + 1)]
                    ps_bars = [b for b in ps_bars if b is not None]
                    if ps_bars:
                        lo, hi = min(ps_bars), max(ps_bars)
                        overlap = [q for q in pspans if q["sbar"] <= hi and q["ebar"] >= lo and q["type"] == s["type"]]
                    if cross:
                        ev["cause"], ev["sub"] = "c", "reference bracket crosses a print system break; read has none here"
                    elif overlap:
                        q = overlap[0]
                        # after the pred span end -> stopped early; before its start -> started late
                        pb_, po_ = pj, ponset
                        if (pb_, po_) >= (q["ebar"], q["eonset"]) and not q.get("open"):
                            ev["cause"], ev["sub"] = "b", "read stops early"
                        else:
                            ev["cause"], ev["sub"] = "a", "read starts late"
                    else:
                        ev["cause"], ev["sub"] = "a", "missed bracket"
                elif sr == 0 and sp_ != 0:
                    q = pspans[psid]
                    ref_overlap = None
                    pr_bars = [pairs_inv.get(b) for b in range(q["sbar"], q["ebar"] + 1)]
                    pr_bars = [b for b in pr_bars if b is not None]
                    if pr_bars:
                        lo, hi = min(pr_bars), max(pr_bars)
                        ref_overlap = [x for x in rspans if x["sbar"] <= hi and x["ebar"] >= lo and x["type"] == q["type"]]
                    if ref_overlap:
                        x = ref_overlap[0]
                        if ri >= x["ebar"]:
                            cross = any(x["sbar"] < b <= x["ebar"] for b in ref_sysstart) or ev["pred_span"][4]
                            ev["cause"], ev["sub"] = ("c" if cross else "b"), "read stops late (reference bracket ended before this note)"
                        else:
                            ev["cause"], ev["sub"] = "a", "read starts early"
                    else:
                        ev["cause"], ev["sub"] = "ae", "read-only bracket (spurious or reference lacks the print's bracket)"
                else:
                    ev["cause"], ev["sub"] = "a", "different bracket direction"
            else:
                ev["cause"], ev["sub"] = "x", "register + bracket"
            evs.append(ev)
        ev_all += evs
        per_piece[piece] = {"nref": nref, "npred": npred, "events": len(evs), "f1_audit": a["f1_audit"],
                            "causes": dict(Counter(e["cause"] for e in evs))}
    json.dump({"events": ev_all, "per_piece": per_piece}, open(OUT / "octave_causes_realscans.json", "w"))
    return ev_all, per_piece


if __name__ == "__main__":
    ev, pp = main()
    tot_notes = sum(p["nref"] + p["npred"] for p in pp.values())
    print("pieces", len(pp), "events", len(ev), "points", round(100 * 2 * len(ev) / tot_notes, 3))
    print(Counter(e["cause"] for e in ev))
