"""Pitch audit on the 28 real-scan test pieces (layout1 outputs): where does the pitch error come from?

Reuses pitch_audit.py (PNote parser with octave-shift state, classify_group with the earlier category definitions)
and the bar alignment stored in out/testset/<piece>/note-scores-layout1.json (tag layout1).
Staff-ignored variant (all notes put on one staff, bars re-aligned with score_notes.align_measures(ignore_staff=True)
from the integration worktree) for every piece whose reference and prediction have different staff counts
(Petrushka, Scriabin Sonata 5, the three Liszt Schott pieces).
Read-only on all outputs. Writes pitch_audit_28.json (records, per-page numbers, features).

Run: /Users/yiduoke/Documents/homr/.venv/bin/python -B pitch_audit_28.py [piece ...]
"""
import os
os.environ["AUDIT_VISIBLE"] = "1"
import importlib.util
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/eval_run1")
import pitch_audit as PA  # noqa: E402  (also sets up timing_audit_a and the octave_wt score_notes)

HOME = Path("/Users/yiduoke/Documents/homr/run")
TEST = HOME / "out/testset"
E1 = HOME / "eval_run1"
import os
TAG = os.environ.get("AUDIT_TAG", "relbrace3_gpu")  # D28: any tag with res-scores-<tag>.json (brace_eval.py)
AUDIT_JSON = E1 / f"brace_audit_{TAG}.json"
from edition_refs import EDITION as EDITION_REF  # noqa: E402  (one shared list of edition-corrected pieces)
CATS = PA.CATS
SCHOTT = ["liszt-sonata", "liszt-te-5", "liszt-te-10"]  # known staff-pairing failure (bars doubled), reported separately

_spec = importlib.util.spec_from_file_location("score_notes_int", HOME / "integration_wt/validation/score_notes.py")
SN = importlib.util.module_from_spec(_spec)
sys.modules["score_notes_int"] = SN
_spec.loader.exec_module(SN)


def pieces():
    return sorted(p.name for p in TEST.iterdir() if (p / f"res-scores-{TAG}.json").exists())


def load_scores(name):
    d = json.load(open(TEST / name / f"res-scores-{TAG}.json"))
    return [r for r in d["results"] if r["name"] == TAG][0]


def combined_bars(parts):
    """list of tuple(notes of all parts) per bar index; all parts must have the same bar count."""
    n = len(parts[0][0])
    assert all(len(p[0]) == n for p in parts), "parts with different bar counts"
    return [tuple(x for bars, _, _ in parts for x in bars[i].notes) for i in range(n)]


def trill_like(bar):
    """Reference notes inside a trill-like run: >= 5 consecutive single notes on one staff (no chord), onsets < 0.2 quarter apart,
    alternating between two pitches at most 2 semitones apart (a playback-expanded trill or tremolo in the reference)."""
    out = set()
    by = defaultdict(list)
    for n in bar:
        if not n.grace:
            by[n.staff].append(n)
    for st, ns in by.items():
        ns.sort(key=lambda n: n.onset)
        on = Counter(round(n.onset, 3) for n in ns)
        ns = [n for n in ns if on[round(n.onset, 3)] == 1]  # singles only
        i = 0
        while i < len(ns) - 1:
            j = i + 1
            while (j < len(ns) and ns[j].onset - ns[j - 1].onset < 0.2 and abs(ns[j].pitch - ns[j - 1].pitch) <= 2 and ns[j].pitch != ns[j - 1].pitch
                   and (j < i + 2 or ns[j].pitch == ns[j - 2].pitch)):
                j += 1
            if j - i >= 5:
                out.update((n.staff, n.name(), round(n.onset, 3)) for n in ns[i:j])
            i = max(j, i + 1)
    return out


def inv(notes, ignore):
    return Counter((0 if ignore else n.staff, n.pitch) for n in notes)


def audit(name, want_json=True):
    res = load_scores(name)
    rparts, rn = PA.read_file(TEST / name / f"{name}-reference{'-edition' if name in EDITION_REF else ''}.musicxml")
    pparts, pn = PA.read_file(TEST / name / f"{name}-{TAG}.musicxml")
    rb, pb = combined_bars(rparts), combined_bars(pparts)
    assert len(rb) == res["reference_measures"] and len(pb) == res["predicted_measures"], (len(rb), len(pb))
    ignore = rn != pn
    if ignore:
        rb = [tuple(replace(n, staff=1) for n in b) for b in rb]
        pb = [tuple(replace(n, staff=1) for n in b) for b in pb]
        mk = lambda bars: SN.Score(tuple(SN.Measure(str(i), tuple(SN.Note(n.staff, n.pitch, n.onset, n.duration, n.grace)
                                                                   for n in b)) for i, b in enumerate(bars)), 1)
        pairs = SN.align_measures(mk(rb), mk(pb), ignore_staff=True)
        if "staff_agnostic" in res:  # cross-check with the stored staff-ignored matches (Petrushka)
            stored = res["staff_agnostic"]["metrics"]["pitch_inventory"]["combined"]["matched"]
            mine = sum(sum((inv(rb[i], True) & inv(pb[j], True)).values()) for i, j in pairs)
            assert mine == stored, (name, mine, stored)
        f1_std = res["metrics"]["pitch_inventory"]["combined"]["f1"]
    else:
        pairs = [(a["reference_index"] - 1, a["prediction_index"] - 1) for a in res["alignment"]]
        f1_std = res["metrics"]["pitch_inventory"]["combined"]["f1"]
    nref = sum(len(b) for b in rb)
    npred = sum(len(b) for b in pb)
    matched = sum(sum((inv(rb[i], ignore) & inv(pb[j], ignore)).values()) for i, j in pairs)
    if not ignore:
        assert matched == res["metrics"]["pitch_inventory"]["combined"]["matched"], (name, matched)
    pc = lambda b: Counter((0 if ignore else n.staff, n.pitch % 12) for n in b)
    matched_pc = sum(sum((pc(rb[i]) & pc(pb[j])).values()) for i, j in pairs)
    recs = []
    for i, j in pairs:
        rs, ps = defaultdict(list), defaultdict(list)
        for n in rb[i]:
            rs[n.staff].append(n)
        for n in pb[j]:
            ps[n.staff].append(n)
        info = {"ref_bar": i + 1, "pred_bar": j + 1}
        r = PA.classify_group(rs, ps, info)
        recs += r
    ai, aj = {i for i, _ in pairs}, {j for _, j in pairs}
    for i in range(len(rb)):
        if i not in ai:
            for n in rb[i]:
                recs.append({"ref_bar": i + 1, "pred_bar": None, "cat": "1 unaligned bar", "label": "ref bar unaligned",
                             "ref": [(n.staff, n.name(), round(n.onset, 3), n.shifted)], "pred": []})
    for j in range(len(pb)):
        if j not in aj:
            for n in pb[j]:
                recs.append({"ref_bar": None, "pred_bar": j + 1, "cat": "1 unaligned bar", "label": "pred bar unaligned",
                             "ref": [], "pred": [(n.staff, n.name(), round(n.onset, 3), n.shifted)]})
    # ---- note level bookkeeping
    refside = Counter()
    predside = Counter()
    for r in recs:
        refside[r["cat"]] += len(r["ref"])
        predside[r["cat"]] += len(r["pred"])
    mc = nref - sum(refside.values())  # matched by the classification (lost bars' few matches count as lost)
    assert mc == npred - sum(predside.values()), (name, mc, npred - sum(predside.values()))
    lostmatch = matched - mc
    assert lostmatch >= 0
    loss_notes = {c: refside[c] + predside[c] for c in CATS}
    loss_notes["1 unaligned bar"] -= 2 * lostmatch  # so that the categories sum to nref+npred-2*matched exactly
    assert sum(loss_notes.values()) == nref + npred - 2 * matched, (name, sum(loss_notes.values()), nref + npred - 2 * matched)
    f1 = 2 * matched / (nref + npred)
    r_ref = nref - refside["1 unaligned bar"]
    r_pred = npred - predside["1 unaligned bar"]
    f1_read = 2 * mc / (r_ref + r_pred) if r_ref + r_pred else float("nan")
    cat1 = Counter(r["label"] for r in recs if r["cat"] == "1 unaligned bar")
    out = {"name": name, "ignore_staff": ignore, "ref_staves": rn, "pred_staves": pn,
           "f1_summary": round(100 * f1_std, 1), "f1_audit": round(100 * f1, 2), "f1_reading_only": round(100 * f1_read, 2),
           "f1_pitch_class": round(100 * 2 * matched_pc / (nref + npred), 2),
           "nref": nref, "npred": npred, "matched": matched, "ref_bars": len(rb), "pred_bars": len(pb),
           "aligned_bars": len(pairs),
           "events": {c: sum(1 for r in recs if r["cat"] == c) for c in CATS},
           "loss_notes": loss_notes, "cat1_labels": dict(cat1),
           "ref_notes_lost": refside["1 unaligned bar"], "pred_notes_lost": predside["1 unaligned bar"],
           "bar_stats": [[i + 1, len(rb[i]), len(pb[j]), sum((inv(rb[i], ignore) & inv(pb[j], ignore)).values())] for i, j in pairs],
           "ref_trill": [[i + 1, st, nm, on] for i, b in enumerate(rb) for st, nm, on in sorted(trill_like(b))],
           "ref_br_bars": [i + 1 for i, b in enumerate(rb) if any(n.shifted for n in b)],
           "pred_br_bars": [j + 1 for j, b in enumerate(pb) if any(n.shifted for n in b)],
           "pairs": [(i, j) for i, j in pairs], "recs": recs if want_json else []}
    return out, rb, pb


# ------------------------------------------------------------------ page mapping and per-page F1
def page_of_pred_bars(name, npred):
    """pred bar index (0-based) -> page number (the number in page-xml/page-NN.musicxml), from the bar counts of the per-page
    outputs; exact when the pages' bar counts add up to the bars of the final output (or a prefix of the pages does: the pages
    after it are then lost in the joiner). Returns (list, lost_pages) or (None, None) when it does not add up."""
    pages = sorted(((int(re.search(r"page-(\d+)", f.name).group(1)), f) for f in (E1 / "testset" / TAG / name / "page-xml").glob("page-*.musicxml")))
    counts = []
    for num, f in pages:
        r = ET.parse(f).getroot()
        counts.append((num, max(len(p.findall("measure")) for p in r.findall("part"))))
    cum, pg = 0, []
    for k, (num, c) in enumerate(counts):
        if cum == npred:
            return pg, [n for n, _ in counts[k:]]
        pg += [num] * c
        cum += c
    return (pg, []) if cum == npred else (None, None)


def page_stats(name, a, rb, pb):
    pg, lost_pages = page_of_pred_bars(name, len(pb))
    if pg is None:
        return None
    pairs = a["pairs"]
    ignore = a["ignore_staff"]
    ref_page = {i: pg[j] for i, j in pairs}
    last = None
    aligned = sorted(ref_page)
    for i in range(len(rb)):
        if i in ref_page:
            last = ref_page[i]
        elif last is not None:
            ref_page[i] = last
    if lost_pages and aligned:  # trailing reference bars belong to the first lost page
        for i in range(aligned[-1] + 1, len(rb)):
            ref_page[i] = lost_pages[0]
    for i in range(len(rb)):
        ref_page.setdefault(i, pg[0])
    st = defaultdict(Counter)
    for i in range(len(rb)):
        st[ref_page[i]]["ref"] += len(rb[i])
    for j in range(len(pb)):
        st[pg[j]]["pred"] += len(pb[j])
        st[pg[j]]["bars"] += 1
    for i, j in pairs:
        st[pg[j]]["matched"] += sum((inv(rb[i], ignore) & inv(pb[j], ignore)).values())
    for r in a["recs"]:
        pgn = pg[r["pred_bar"] - 1] if r["pred_bar"] is not None else ref_page[r["ref_bar"] - 1]
        st[pgn]["ev " + r["cat"]] += 1
    return {str(p): dict(v) for p, v in sorted(st.items())}


# ------------------------------------------------------------------ reference features (visible-difficulty proxies)
def ref_features(name):
    root = ET.fromstring((TEST / name / f"{name}-reference.musicxml").read_bytes().decode("utf-8-sig"))
    for el in root.iter():
        el.tag = el.tag.rsplit("}", 1)[-1]
    LET = "CDEFGAB"
    feat = Counter()
    for pi, part in enumerate(root.findall("part")):
        clef = {}
        for m in part.findall("measure"):
            if pi == 0:
                feat["bars"] += 1
            for el in m:
                if el.tag == "attributes":
                    for c in el.findall("clef"):
                        clef[int(c.get("number", "1"))] = (c.findtext("sign"), int(c.findtext("line") or 0))
                elif el.tag == "direction":
                    for o in el.iter("octave-shift"):
                        if o.get("type") in ("up", "down"):
                            feat["octave_shift_dirs"] += 1
                elif el.tag == "note":
                    if el.find("grace") is not None:
                        feat["grace"] += 1
                    if el.find("tremolo") is not None or el.find(".//tremolo") is not None:
                        feat["tremolo"] += 1
                    if el.find("time-modification") is not None:
                        feat["tuplet_notes"] += 1
                    if el.find("cue") is not None:
                        feat["cue"] += 1
                    p = el.find("pitch")
                    if p is None:
                        continue
                    feat["notes"] += 1
                    staff = int(el.findtext("staff") or "1")
                    sign, line = clef.get(staff, ("G", 2) if staff == 1 else ("F", 4))
                    step, octv = p.findtext("step"), int(p.findtext("octave"))
                    dp = octv * 7 + LET.index(step)
                    # diatonic position of the bottom staff line
                    bottom = {("G", 2): 4 * 7 + 2, ("F", 4): 2 * 7 + 4, ("C", 3): 3 * 7 + 5, ("C", 4): 3 * 7 + 3}.get((sign, line), 4 * 7 + 2)
                    rel = dp - bottom  # 0 = bottom line, 8 = top line
                    ledger = (-rel) // 2 if rel < 0 else (rel - 8) // 2 if rel > 8 else 0
                    if ledger >= 3:
                        feat["ledger3"] += 1
                    if ledger >= 1:
                        feat["ledger1"] += 1
    return dict(feat)


EDITION = {  # from scores/testset/*.pdf and testset_manifest.tsv
    "bach-fugue-873": "Bach-Gesellschaft (engraved)", "bach-prelude-873": "Bach-Gesellschaft (engraved)",
    "bach-italian-concerto-2": "Universal Edition",
    "beethoven-appassionata-1": "Universal Edition (Schenker)", "beethoven-hammerklavier-4": "Peters",
    "beethoven-waldstein-1": "Peters", "chopin-etude-op10-4": "Breitkopf", "chopin-etude-op25-10": "Peters",
    "chopin-etude-op25-11": "Peters", "chopin-polonaise-op53": "Breitkopf", "chopin-scherzo3": "Breitkopf",
    "debussy-pour-le-piano-1": "Fromont", "debussy-reflets": "Durand", "haydn-hob16-49-1": "Breitkopf 1799",
    "liszt-hr-6": "Paderewski", "liszt-paganini-6": "Breitkopf 1851", "liszt-sonata": "Schott",
    "liszt-te-5": "Schott", "liszt-te-10": "Schott", "mozart-k475": "Schirmer", "prokofiev-toccata": "Dover (Sarcasms/Visions)",
    "ravel-alborada": "Demets", "schubert-impromptu-d899-4": "Breitkopf", "schubert-wanderer-3-4": "Peters",
    "schumann-kreisleriana-1": "Schirmer", "schumann-toccata": "Peters", "scriabin-sonata-5": "Muzgiz",
    "stravinsky-petrushka": "(piano score, file x.pdf)",
}


def report():
    d = json.load(open(AUDIT_JSON))
    A, P, F = d["audit"], d["pages"], d["features"]
    names = sorted(A)
    main_ = [n for n in names if n not in SCHOTT]
    short = [c.split()[0] for c in CATS]
    print("### per piece: F1 and events")
    print("| piece | edition | F1 (SUMMARY) | F1 audited | reading-only F1 | lost-bar share of loss | events | " + " | ".join(CATS) + " |")
    print("|" + "---|" * (7 + len(CATS)))
    for n in names:
        a = A[n]
        ev = a["events"]
        T = sum(ev.values())
        loss = sum(a["loss_notes"].values())
        sh = a["loss_notes"]["1 unaligned bar"] / loss if loss else 0
        mark = "*" if a["ignore_staff"] else ""
        print(f"| {n}{mark} | {EDITION[n]} | {a['f1_summary']} | {a['f1_audit']} | {a['f1_reading_only']} | {100*sh:.0f}% | {T} | "
              + " | ".join(f"{ev[c]} ({100*ev[c]/T:.0f}%)" for c in CATS) + " |")
    for title, group in (("25 pieces without the Liszt Schott three", main_), ("Liszt Schott three", SCHOTT)):
        tot = Counter()
        for n in group:
            tot.update(A[n]["events"])
        T = sum(tot.values())
        print(f"| **{title}** | | | | | | {T} | " + " | ".join(f"{tot[c]} ({100*tot[c]/T:.0f}%)" for c in CATS) + " |")
    print()
    print("### F1 points lost per category (note level: missed reference notes + extra predicted notes, divided by ref+pred notes; "
          "sums to 100 - audited F1)")
    print("| piece | loss | " + " | ".join(short) + " |")
    print("|" + "---|" * (2 + len(CATS)))
    for group, label in ((main_, "mean over 25"), (SCHOTT, "mean over 3 Schott")):
        if group is main_:
            for n in group:
                a = A[n]
                den = a["nref"] + a["npred"]
                print(f"| {n} | {100*sum(a['loss_notes'].values())/den:.1f} | " + " | ".join(f"{100*a['loss_notes'][c]/den:.1f}" for c in CATS) + " |")
        mean = {c: sum(100 * A[n]["loss_notes"][c] / (A[n]["nref"] + A[n]["npred"]) for n in group) / len(group) for c in CATS}
        print(f"| **{label}** | {sum(mean.values()):.1f} | " + " | ".join(f"{mean[c]:.1f}" for c in CATS) + " |")
    print()
    # means of the F1 numbers
    print("octave-blind F1 (pitch class, same alignment), mean over 25: "
          f"{sum(A[n]['f1_pitch_class'] for n in main_)/len(main_):.1f} vs audited {sum(A[n]['f1_audit'] for n in main_)/len(main_):.1f}")
    for group, label in ((main_, "25"), (SCHOTT, "3 Schott"), (names, "28")):
        print(f"mean over {label}: SUMMARY {sum(A[n]['f1_summary'] for n in group)/len(group):.1f}, audited {sum(A[n]['f1_audit'] for n in group)/len(group):.1f}, "
              f"reading-only {sum(A[n]['f1_reading_only'] for n in group)/len(group):.1f}")
    pool_loss = Counter()
    for n in main_:
        for c in CATS:
            pool_loss[c] += A[n]["loss_notes"][c]
    T = sum(pool_loss.values())
    print("pooled over 25 (notes, ref+pred):", {c.split()[0]: f"{100*pool_loss[c]/T:.0f}%" for c in CATS}, "total", T)
    print()
    print("### octave events by bracket context (bar level, any staff): ref has a bracket in the bar / only the prediction has one / neither; and direction")
    tot = Counter()
    for n in names:
        o = [r for r in A[n]["recs"] if r["cat"] == "2 octave"]
        if not o:
            continue
        rbs, pbs = set(A[n]["ref_br_bars"]), set(A[n]["pred_br_bars"])
        ctx = Counter("ref" if r["ref_bar"] in rbs else "pred only" if r["pred_bar"] in pbs else "neither" for r in o)
        dr = Counter("pred lower" if int(r["label"]) < 0 else "pred higher" for r in o)
        if n not in SCHOTT:
            tot.update(ctx)
        print(f"{n}: {len(o)} | ref bracket {ctx['ref']} | only pred bracket {ctx['pred only']} | neither {ctx['neither']} | {dict(dr)}")
    print("25 pieces:", dict(tot))
    print()
    print("### lost-bar breakdown (notes)")
    for n in names:
        a = A[n]
        if a["cat1_labels"]:
            print(n, a["cat1_labels"], f"bars ref/pred/aligned {a['ref_bars']}/{a['pred_bars']}/{a['aligned_bars']}")
    print()
    print("### aligned bars that are not lost: pitch F1 by reference notes per bar (25 pieces pooled; bars with a lost staff excluded)")
    bk = [(0, 12), (12, 24), (24, 36), (36, 60), (60, 1000)]
    acc = {b: Counter() for b in bk}
    for n in main_:
        a = A[n]
        lostb = {r["ref_bar"] for r in a["recs"] if r["cat"] == "1 unaligned bar" and r["ref_bar"] is not None and r["pred_bar"] is not None}
        for rbar, nr, np_, m in a["bar_stats"]:
            if rbar in lostb:
                continue
            for b in bk:
                if b[0] <= nr < b[1]:
                    acc[b]["bars"] += 1
                    acc[b]["m"] += m
                    acc[b]["den"] += nr + np_
    for b in bk:
        c = acc[b]
        print(f"ref notes/bar {b[0]}-{b[1]-1 if b[1]<1000 else '+'}: {c['bars']} bars, F1 {100*2*c['m']/max(c['den'],1):.1f}")
    print()
    print("### features of the reference")
    print("| piece | notes/bar | ledger>=3 | octave-shift marks | grace | tremolo | tuplet notes |")
    print("|---|---|---|---|---|---|---|")
    for n in names:
        f = F[n]
        nb = f.get("notes", 0)
        print(f"| {n} | {nb/max(f.get('bars',1),1):.1f} | {100*f.get('ledger3',0)/max(nb,1):.1f}% | {f.get('octave_shift_dirs',0)} | {f.get('grace',0)} | {f.get('tremolo',0)} | {100*f.get('tuplet_notes',0)/max(nb,1):.0f}% |")


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "--report":
    report()
    sys.exit(0)


def main():
    names = sys.argv[1:] or pieces()
    out, pagesd, feats = {}, {}, {}
    for name in names:
        try:
            a, rb, pb = audit(name)
        except Exception as e:  # e.g. parts with different bar counts: no joint bar list
            print(f"{name:28s} NOT AUDITED: {type(e).__name__} {str(e)[:100]}", flush=True)
            continue
        out[name] = a
        pagesd[name] = page_stats(name, a, rb, pb)
        feats[name] = ref_features(name)
        c = a["events"]
        print(f"{name:28s} full {a['f1_summary']:5.1f} audit {a['f1_audit']:5.1f} reading-only {a['f1_reading_only']:5.1f} "
              f"events {sum(c.values()):5d} " + " ".join(f"{k.split()[0]}:{v}" for k, v in c.items() if v), flush=True)
    AUDIT_JSON.write_text(json.dumps({"audit": out, "pages": pagesd, "features": feats}))


if __name__ == "__main__":
    main()
