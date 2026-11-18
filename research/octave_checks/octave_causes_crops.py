"""D32 task 1: octave errors of the released model on the verified scan-pair crops (pilot + batch 2), classified into five causes.

Read-only on all inputs. For every crop that has a label token file and a read of the released model, the label (ASAP) and the read are
parsed into per-staff note sequences with the octave-shift state at every note, aligned on pitch letters (difflib), and every aligned note
gets (written octave delta wd, sounding octave delta sd = wd + shift_label - shift_read).

Causes (per note, then per crop):
  a  missed / late / early / spurious bracket START inside a crop (bracket does not cross a system edge)
  b  missed / wrong STOP inside a crop (read bracket ends too early or too late, stray stop, bracket does not cross a system edge)
  c  CONTINUATION: the label bracket crosses a system or page break (open at the crop start = continued from the previous system, or open at
     the crop end = continues into the next one) and the read differs
  d  WRONG REGISTER: written octave differs, brackets agree (both none or same state): note read an octave off by ledger lines / clef
  e  EDITION / REFERENCE: written octave and bracket both differ but the SOUNDING pitch agrees (print at pitch vs 8va with lowered notes);
     crops with a by-eye decision of 'edition difference' / 'label wrong, corrected' in the earlier octave reviews are tagged separately
  x  mixed: written octave differs and brackets differ and sounding differs (register error under a bracket error)

Usage: python3 octave_causes_crops.py   -> octave_causes_crops.csv, octave_causes_notes.json (per crop events), prints summary tables.
"""
import csv
import difflib
import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

R = "/Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/"
OUT = "/Users/yiduoke/Documents/homr/run/octave_checks/"
LET = "CDEFGAB"
RELIABLE_Q = ("octave", "trainer", "conversion error", "rhythm", "tuplet", "ledger")  # quarantine reasons that leave the label reliable
UNRELIABLE_Q = ("edition", "alignment", "bar mismatch", "shifted", "label wrong", "not_piece", "crop", "skipped", "by eye")
SHIFT = {"8va": 1, "8vb": -1, "15ma": 2, "15mb": -2}


def parse(tokens):
    """-> per staff: list of notes dict(bar, letter, oct, state, idx), spans [dict(start,stop,sstate,n_start_tok,...)], events [(bar,note_idx_in_staff,type)]"""
    staves = {"upper": [], "lower": []}
    spans = {"upper": [], "lower": []}
    state = {"upper": 0, "lower": 0}
    open_span = {"upper": None, "lower": None}
    events = {"upper": [], "lower": []}
    stray = {"upper": 0, "lower": 0}
    bar = 0
    for ln, line in enumerate(tokens.strip().split("\n")):
        if line.startswith("barline"):
            bar += 1
            continue
        parts = [p.split(" ") for p in line.split("&")]
        # shift events of the line first (the token precedes the note it governs)
        for f in parts:
            t = f[0]
            st = f[-1] if f[-1] in ("upper", "lower") else None
            if t in ("octaveShift_8va", "octaveShift_8vb", "octaveShift_15ma", "octaveShift_15mb"):
                if st is None:
                    continue
                n = len(staves[st])
                if open_span[st] is not None:  # a new start while open: close the old one silently
                    open_span[st]["stop"] = n - 1
                state[st] = SHIFT[t[12:]]
                sp = {"start": n, "stop": None, "dir": state[st], "bar": bar}
                spans[st].append(sp)
                open_span[st] = sp
                events[st].append((bar, n, "start"))
            elif t == "octaveShiftStop":
                if st is None:
                    st = "upper" if open_span["upper"] is not None else ("lower" if open_span["lower"] is not None else None)
                    if st is None:
                        stray["upper"] += 1
                        events["upper"].append((bar, len(staves["upper"]), "stray_stop"))
                        continue
                n = len(staves[st])
                if open_span[st] is None:
                    stray[st] += 1
                    events[st].append((bar, n, "stray_stop"))
                else:
                    open_span[st]["stop"] = n - 1
                    open_span[st]["stop_bar"] = bar
                    open_span[st] = None
                    state[st] = 0
                    events[st].append((bar, n, "stop"))
        for f in parts:
            t = f[0]
            st = f[-1] if f[-1] in ("upper", "lower") else None
            if t.startswith("note") and len(f) > 1 and st and re.match(r"^[A-G]-?\d+$", f[1]):
                staves[st].append({"bar": bar, "letter": f[1][0], "oct": int(f[1][1:]), "state": state[st], "idx": len(staves[st]), "line": ln})
    for st in spans:
        for sp in spans[st]:
            sp["open_end"] = sp["stop"] is None
            if sp["stop"] is None:
                sp["stop"] = len(staves[st]) - 1
    return staves, spans, events, stray


def align(A, B):
    """pairs (i,j) of notes with the same letter. Notes are grouped into time slices (token lines) per staff; slices are aligned on their
    sorted letter tuples (difflib); inside matched slices notes are paired after sorting by (letter, octave) so that the order of chord members
    does not matter; inside replaced blocks notes are paired per letter in order of octave."""
    def slices(N):
        out = []
        for n in N:
            if out and out[-1][0]["line"] == n["line"]:
                out[-1].append(n)
            else:
                out.append([n])
        return out
    SA, SB = slices(A), slices(B)
    key = lambda sl: tuple(sorted(n["letter"] for n in sl))
    sm = difflib.SequenceMatcher(None, [key(x) for x in SA], [key(x) for x in SB], autojunk=False)
    out = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            for k in range(i2 - i1):
                a = sorted(SA[i1 + k], key=lambda n: (n["letter"], n["oct"]))
                b = sorted(SB[j1 + k], key=lambda n: (n["letter"], n["oct"]))
                out += [(x["idx"], y["idx"]) for x, y in zip(a, b)]
        elif tag == "replace":
            fa = [n for sl in SA[i1:i2] for n in sl]
            fb = [n for sl in SB[j1:j2] for n in sl]
            by = defaultdict(list)
            for n in fb:
                by[n["letter"]].append(n)
            # pair in order of appearance per letter (greedy)
            used = defaultdict(int)
            for n in fa:
                lst = by[n["letter"]]
                if used[n["letter"]] < len(lst):
                    out.append((n["idx"], lst[used[n["letter"]]]["idx"]))
                    used[n["letter"]] += 1
    return out


def letters_f1(A, B):
    ca, cb = Counter(n["letter"] for n in A), Counter(n["letter"] for n in B)
    m = sum((ca & cb).values())
    return 2 * m / (len(A) + len(B)) if (A or B) else 1.0


def load_all():
    """crop dict list (pilot + batch 2) with label tokens (original), read tokens, manifest fields, set name."""
    crops = []
    for base, mf, tokd, group_set in [(R, R + "manifest.csv", R + "tokens/", "pilot"), (R + "batch2/", R + "batch2/manifest.csv", R + "batch2/tokens/", "batch2")]:
        recs = {}
        for f in glob.glob(base + "work/export/*.json"):
            for r in json.load(open(f))["records"]:
                recs[f"{r['pid']}_{r['page']}_s{r['sys']}"] = r
        reads = {}
        for f in glob.glob(base + "work/reads/*.jsonl"):
            for l in open(f):
                d = json.loads(l)
                reads[d["id"]] = d
        unc = base + "tokens_uncorrected/"
        for row in csv.DictReader(open(mf)):
            name = os.path.basename(row["crop"])[:-4]
            rec = recs.get(name)
            tp = unc + name + ".tokens" if os.path.exists(unc + name + ".tokens") else tokd + name + ".tokens"
            if not os.path.exists(tp):
                crops.append({"name": name, "set": group_set, "row": row, "label": None, "read": None, "base": base})
                continue
            rd = reads.get(rec["id"]) if rec else None
            crops.append({"name": name, "set": group_set, "row": row, "label": open(tp).read(), "read": rd["tokens"] if rd else None, "base": base,
                          "corrected": os.path.exists(base + ("octave_review/tokens_corrected/" + name + ".tokens"))})
    return crops


def split_name(row):
    g = row["group"]
    return {"A": "pilot-train", "B": "pilot-train(rendered)", "C": "pilot-val", "T": "b2-train", "V": "b2-val", "D": "b2-train(Demets)"}[g]


def eye_decisions():
    d = {}
    for r in csv.DictReader(open(R + "octave_review.csv")):
        d[os.path.basename(r["crop"])[:-4]] = ("pilot", r["decision"], r["evidence"])
    for r in csv.DictReader(open(R + "batch2/octave_review.csv")):
        d[r["crop"]] = ("batch2", r["decision"], r["note"])
    return d


def main():
    crops = load_all()
    eyed = eye_decisions()
    # label open-at-end per crop (for continuation detection), ordered by manifest order within (piece pid)
    for c in crops:
        c["usable"] = None
        row = c["row"]
        if c["label"] is None:
            c["usable"] = "no label tokens (conversion error / not piece music)"
            continue
        if c["read"] is None:
            c["usable"] = "no read"
            continue
        if row["pid"] == "A1" or c["name"] in ("A4_p-20_s2", "A10_p-12_s5"):
            c["usable"] = "label known wrong (Liszt TE1 shifted by one measure; two Ballade crops misaligned, see octave_review.md)"
            continue
        if row["tier"] == "quarantine":
            rs = row["reasons"].split(";")
            if any(any(u in r for u in UNRELIABLE_Q) for r in rs):
                c["usable"] = "quarantined, label unreliable: " + re.sub(r"\(.*", "", rs[0])[:50]
    # parse
    for c in crops:
        if c["usable"]:
            continue
        c["L"] = parse(c["label"])
        c["Rd"] = parse(c["read"])
    # neighbour map: previous crop (same pid, manifest order) with label
    order = defaultdict(list)
    for i, c in enumerate(crops):
        order[(c["set"], c["row"]["pid"])].append(i)
    for key, idxs in order.items():
        for k, i in enumerate(idxs):
            c = crops[i]
            c["prev"] = crops[idxs[k - 1]] if k > 0 else None
            c["next"] = crops[idxs[k + 1]] if k + 1 < len(idxs) else None

    def mrange(c):
        s = c["row"]["asap_measure_range"]
        if not s:
            return None
        a = s.split("-")
        return int(a[0]), int(a[-1])

    def contiguous(p, c):
        """previous crop p precedes c directly"""
        if p is None or p["label"] is None:
            return False
        a, b = mrange(p), mrange(c)
        if a and b:
            return b[0] == a[1] + 1 or b[0] == a[1]
        return True  # unknown ranges: manifest order only

    results = []
    for c in crops:
        row = c["row"]
        rec = {"name": c["name"], "set": c["set"], "group": split_name(row), "pid": row["pid"], "piece": row["piece"], "tier": row["tier"],
               "edition": row["edition"], "page_image": row["page_image"], "system_index": row["system_index"],
               "measures": row["asap_measure_range"], "usable": c["usable"] or "yes"}
        if c["usable"]:
            results.append(rec)
            continue
        Ls, Ss, Ev, St = c["L"]
        Rs, Rss, Rev, Rst = c["Rd"]
        # continuation flags of label spans
        notes_label = sum(len(v) for v in Ls.values())
        notes_read = sum(len(v) for v in Rs.values())
        allL = Ls["upper"] + Ls["lower"]
        allR = Rs["upper"] + Rs["lower"]
        pcf1 = letters_f1(allL, allR)
        rec.update({"n_label_notes": notes_label, "n_read_notes": notes_read, "pc_f1": round(pcf1, 3)})
        # label brackets
        lab_spans = {st: [dict(s) for s in Ss[st]] for st in Ss}
        prev_open = False
        p = c["prev"]
        if contiguous(p, c) and "L" in p:
            prev_open = any(s["open_end"] for st in p["L"][1] for s in p["L"][1][st])
        nxt_ok = c["next"] is not None and c["next"]["label"] is not None
        for st in lab_spans:
            for s in lab_spans[st]:
                s["cont_in"] = bool(s["start"] == 0 and prev_open)
                s["start_at_first"] = s["start"] == 0
                s["cont_out"] = bool(s["open_end"])
        rd_spans = {st: [dict(s) for s in Rss[st]] for st in Rss}
        rec["label_spans"] = sum(len(v) for v in lab_spans.values())
        rec["read_spans"] = sum(len(v) for v in rd_spans.values())
        rec["label_starts"] = sum(1 for st in Ev for e in Ev[st] if e[2] == "start")
        rec["read_starts"] = sum(1 for st in Rev for e in Rev[st] if e[2] == "start")
        rec["label_stops"] = sum(1 for st in Ev for e in Ev[st] if e[2] in ("stop", "stray_stop"))
        rec["read_stops"] = sum(1 for st in Rev for e in Rev[st] if e[2] in ("stop", "stray_stop"))
        rec["label_cont_in"] = sum(1 for st in lab_spans for s in lab_spans[st] if s["cont_in"])
        rec["label_cont_out"] = sum(1 for st in lab_spans for s in lab_spans[st] if s["cont_out"])
        rec["read_stray_stops"] = sum(Rst.values())
        rec["label_start_at_first_note"] = sum(1 for st in lab_spans for s in lab_spans[st] if s["start_at_first"])
        # per-note
        ev = []  # per affected note: dict(staff, i, j, wd, sd, cls)
        n_aligned = 0
        for st in ("upper", "lower"):
            A, B = Ls[st], Rs[st]
            pairs = align(A, B)
            n_aligned += len(pairs)
            Rsp = rd_spans[st]
            Lsp = lab_spans[st]
            for i, j in pairs:
                a, b = A[i], B[j]
                wd = a["oct"] - b["oct"]
                sL, sR = a["state"], b["state"]
                sd = wd + sL - sR
                if abs(wd) > 2:
                    continue
                if wd == 0 and sL == sR:
                    continue
                # span context
                cls, sub = None, ""
                if wd != 0 and sL == sR:
                    cls = "d"
                    sub = "inside-bracket" if sL else "no-bracket"
                elif wd != 0 and sd == 0:
                    cls = "e"
                    sub = "label-bracket,read-at-pitch" if sL and not sR else ("label-at-pitch,read-bracket" if sR and not sL else "bracket-direction")
                elif wd != 0:
                    cls = "x"
                    sub = "register+bracket"
                else:  # wd == 0, sL != sR: bracket only
                    if sL:  # label has bracket at this note
                        sp = next((s for s in Lsp if s["start"] <= i <= s["stop"] and s["dir"] == sL), None)
                        crosses = sp and (sp["cont_in"] or sp["cont_out"])
                        # read span overlapping the label span?
                        ov = None
                        if sp:
                            for r in Rsp:
                                # read span covers aligned notes inside the label span?
                                if any(r["start"] <= jj <= r["stop"] for ii, jj in pairs if sp["start"] <= ii <= sp["stop"]):
                                    ov = r
                                    break
                        if ov is None:
                            kind = "missed bracket"
                            cls = "c" if crosses else "a"
                        elif j < ov["start"]:
                            kind = "read starts late"
                            cls = "c" if crosses else "a"
                        elif j > ov["stop"]:
                            kind = "read stops early"
                            cls = "c" if crosses else "b"
                        else:
                            kind = "direction/size differs"
                            cls = "c" if crosses else "a"
                        sub = kind + ("; cont_in" if sp and sp["cont_in"] else "") + ("; cont_out" if sp and sp["cont_out"] else "")
                    else:  # read has bracket, label none
                        r = next((s for s in Rsp if s["start"] <= j <= s["stop"] and s["dir"] == sR), None)
                        ov = None
                        if r:
                            for s in Lsp:
                                if any(s["start"] <= ii <= s["stop"] for ii, jj in pairs if r["start"] <= jj <= r["stop"]):
                                    ov = s
                                    break
                        if ov is None:
                            cls, sub = "a", "spurious bracket (label none)"
                        elif i > ov["stop"]:
                            cls, sub = "b", "read stops late"
                            if ov["cont_out"] or ov["cont_in"]:
                                cls = "c"
                        else:
                            cls, sub = "a", "read starts early"
                ev.append({"staff": st, "bar": a["bar"], "i": i, "wd": wd, "sd": sd, "sL": sL, "sR": sR, "cls": cls, "sub": sub})
        rec["n_aligned"] = n_aligned
        # token-level differences without affected notes
        tok = []
        if rec["read_stray_stops"] or any(e[2] == "stray_stop" for st in Rev for e in Rev[st]):
            tok.append("b:stray stop in read")
        if rec["label_cont_out"] and not any(s["open_end"] for st in rd_spans for s in rd_spans[st]) and any(
                s["open_end"] is False and s["stop"] == len(Rs[st]) - 1 for st in rd_spans for s in rd_spans[st]):
            tok.append("c:read closes bracket at system end, label continues")
        # bracket token count differences without any aligned-note evidence
        if not ev:
            if rec["read_starts"] > rec["label_starts"]:
                tok.append("a:read has extra start token(s), no note affected")
            elif rec["read_starts"] < rec["label_starts"]:
                tok.append("a:read lacks a start token, no note affected")
            if rec["read_stops"] < rec["label_stops"]:
                tok.append("b:read lacks a stop token (label stops at the crop end), no note affected")
            elif rec["read_stops"] > rec["label_stops"] and not any(t.startswith("b:stray") for t in tok):
                tok.append("b:read has an extra stop token, no note affected")
        rec["events"] = ev
        rec["tok_diffs"] = tok
        cnt = Counter(e["cls"] for e in ev)
        rec["n_events"] = len(ev)
        rec["n_events_by_cls"] = dict(cnt)
        rec["n_sound_diff_notes"] = sum(1 for e in ev if e["sd"] != 0)
        rec["n_written_diff_notes"] = sum(1 for e in ev if e["wd"] != 0)
        # crop flag and primary class
        flagged = bool(ev) or bool(tok)
        rec["flagged"] = flagged
        prim = None
        if flagged:
            if cnt:
                # primary class = class with most affected notes; ties by priority c a b e d x
                pr = {"c": 0, "a": 1, "b": 2, "e": 3, "d": 4, "x": 5}
                prim = sorted(cnt.items(), key=lambda kv: (-kv[1], pr[kv[0]]))[0][0]
            else:
                prim = "c" if any(t.startswith("c:") for t in tok) else ("b" if any(t.startswith("b:") for t in tok) else "a")
        rec["auto_primary"] = prim
        rec["auto_classes_present"] = "".join(sorted(set(cnt) | {t[0] for t in tok if t[1] == ":"}))
        rec["eye_review"] = eyed.get(c["name"], ("", "", ""))[1]
        results.append(rec)
    json.dump(results, open(OUT + "octave_causes_notes.json", "w"), indent=0)
    cols = ["name", "set", "group", "pid", "piece", "tier", "edition", "measures", "usable", "n_label_notes", "n_read_notes", "pc_f1", "n_aligned",
            "label_spans", "read_spans", "label_starts", "read_starts", "label_stops", "read_stops", "label_cont_in", "label_cont_out", "n_events",
            "n_written_diff_notes", "n_sound_diff_notes", "n_events_by_cls", "tok_diffs", "flagged", "auto_primary", "auto_classes_present", "eye_review"]
    with open(OUT + "octave_causes_crops.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in results:
            w.writerow([json.dumps(r.get(k)) if isinstance(r.get(k), (dict, list)) else r.get(k, "") for k in cols])
    return results


if __name__ == "__main__":
    res = main()
    print(len(res), "crops;", Counter(r["usable"] if r["usable"] == "yes" else "excluded" for r in res))
    print(Counter(r["usable"] for r in res if r["usable"] != "yes").most_common())
