"""Part B step 2 (local): score decoded training-style validation staffs and classify the weak ones.

Input : eval_run1/timing_audit_b_preds.jsonl (copied from the GPU box, made by timing_audit_b_decode.py)
Output: eval_run1/timing_audit_b.json, tables printed to stdout.
Onsets come from summing the kern durations per voice (position token: upper, upper2, lower,
lower2) from each barline; pitch is the sounding pitch after key signature and in-bar accidentals.
The note counting and bar alignment are the ones of validation/score_notes.py.

Run: /Users/yiduoke/Documents/homr/.venv/bin/python -B timing_audit_b.py
"""
import json
import re
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import timing_audit_a as A  # noqa: E402
from timing_audit_a import Bar, XNote  # noqa: E402
from validation.score_notes import Measure, Score, score_notes  # noqa: E402

HERE = Path(__file__).parent
SEM = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}
SHARPS, FLATS = "FCGDAEB", "BEADGCF"
BARLINES = {"barline", "doublebarline", "bolddoublebarline", "repeatEnd", "repeatEndStart"}
LIFT = {"#": 1, "##": 2, "b": -1, "bb": -2, "N": 0}


def kern_quarters(kern):
    """(duration in quarter notes, grace, dots, tuplet 'a:n' or '') of a kern value such as 8., 12, 4G."""
    m = re.fullmatch(r"(\d+)(G?)(\.*)", kern)
    if not m:
        return None
    base, grace, dots = int(m.group(1)), bool(m.group(2)), len(m.group(3))
    if grace:
        return 0.0, True, dots, ""
    if base == 0:
        return 4.0, False, dots, ""
    tm = ""
    if base & (base - 1) == 0:
        d = Fraction(4, base)
    else:
        normal = 1 << (base.bit_length() - 1)
        d = Fraction(4, normal) * Fraction(normal, base)
        tm = f"{base}:{normal}"
    add, tot = d / 2, d
    for _ in range(dots):
        tot += add
        add /= 2
    return float(tot), False, dots, tm


def parse_tokens(text):
    """-> list of Bar (one part, two staves). Notes: XNote, rests: (staff, voice, onset, dur)."""
    bars, key, nominal = [], 0, None
    state = None

    def new():
        return {"cursor": defaultdict(Fraction), "notes": [], "rests": [], "acc": {}, "has": False}

    state = new()

    def close():
        nonlocal state
        if state["has"]:
            vend, vdelta = defaultdict(float), defaultdict(float)
            for n in state["notes"]:
                if not n.grace:
                    k = (n.staff, n.voice)
                    vend[k] = max(vend[k], n.onset + n.duration)
            for s_, v_, o_, d_ in state["rests"]:
                vend[(s_, v_)] = max(vend[(s_, v_)], o_ + d_)
            seen = set()
            for n in state["notes"]:
                k = (n.staff, n.voice)
                if n.tuplet and (k, n.onset) not in seen:
                    seen.add((k, n.onset))
                    a, _, b = n.tm.partition(":")
                    vdelta[k] += n.duration * (int(a) / int(b) - 1)
            end = max([float(c) for c in state["cursor"].values()] + [0.0])
            hyp = max([end] + [vend[k] + vdelta[k] for k in vend])
            bars.append(Bar(str(len(bars) + 1), tuple(state["notes"]), state["rests"], end,
                            nominal if nominal else None, hyp, any(n.tuplet for n in state["notes"])))
        state = new()

    for line in text.splitlines():
        syms = [s.strip().split(" ") for s in line.split("&")]
        groups = defaultdict(list)
        for s in syms:
            r = s[0]
            if r in BARLINES:
                close()
            elif r.startswith("keySignature_"):
                key = int(r.split("_")[1])
            elif r.startswith("timeSignature_"):
                tok = r.split("_")[1]
                if tok == "common":
                    nominal = 4.0
                elif tok == "cut":
                    nominal = 4.0
                else:
                    a, b = tok.split("/")
                    nominal = int(a) * 4 / int(b)
            elif r.startswith(("note_", "rest_")) and len(s) >= 6:
                groups[s[5]].append(s)
        for pos, members in groups.items():
            staff = 2 if pos.startswith("lower") else 1
            durs = []
            for s in members:
                kd = kern_quarters(s[0].split("_", 1)[1])
                if kd is None:
                    continue
                durs.append((s, kd))
            if not durs:
                continue
            onset = state["cursor"][pos]
            advance = Fraction(0)
            for s, (dur, grace, dots, tm) in durs:
                state["has"] = True
                if s[0].startswith("rest_"):
                    state["rests"].append((staff, pos, float(onset), dur))
                else:
                    pm = re.fullmatch(r"([A-G])(\d)", s[1])
                    if not pm:
                        continue
                    letter, octv = pm.group(1), int(pm.group(2))
                    lift = s[2]
                    if lift in LIFT:
                        alter = LIFT[lift]
                        state["acc"][(letter, octv)] = alter
                    elif (letter, octv) in state["acc"]:
                        alter = state["acc"][(letter, octv)]
                    else:
                        alter = (1 if key > 0 and letter in SHARPS[:key] else
                                 -1 if key < 0 and letter in FLATS[:-key] else 0)
                    midi = 12 * (octv + 1) + SEM[letter] + alter
                    state["notes"].append(XNote(staff, float(midi), float(onset), dur, grace, voice=pos,
                                                tuplet=bool(tm), dots=dots, tm=tm))
                if not grace:
                    advance = max(advance, Fraction(dur).limit_denominator(1000))
            state["cursor"][pos] = onset + advance
    close()
    return bars


def to_parts(bars):
    return [(bars, 0, 2)]


def dataset_of(path):
    p = path.lower()
    for k in ("musescore_octave", "grandstaff", "lieder", "pdmx", "lilypond", "musescore"):
        if k in p:
            return k
    return "other"


def evaluate(rec):
    rb, pb = parse_tokens(rec["label"]), parse_tokens(rec["pred"])
    if not rb or not any(b.notes for b in rb):
        return None
    if not pb:
        pb = [Bar("1", (), [], 0.0, None)]
    rs = Score(tuple(Measure(b.number, b.notes) for b in rb), 2)
    ps = Score(tuple(Measure(b.number, b.notes) for b in pb), 2)
    res = score_notes(rs, ps)
    f1 = [res["metrics"][m]["combined"]["f1"] for m in ("pitch_inventory", "pitch_onset", "pitch_onset_duration")]
    rbars, pbars = A.staff_bar_lists(to_parts(rb)), A.staff_bar_lists(to_parts(pb))
    cats = Counter()
    for al in res["alignment"]:
        i, j = al["reference_index"] - 1, al["prediction_index"] - 1
        for s in (1, 2):
            a, b = rbars[s][i], pbars[s][j]
            if a.nominal is None:
                a.nominal = a.end
            if b.nominal is None:
                b.nominal = a.nominal
            _, _, _, _, recs = A.analyse_unit(a, b, s, i, j)
            for r in recs:
                cats[r["cat"]] += 1
    unal = sum(len(b.notes) for k, b in enumerate(rb) if (k + 1) in res["unmatched_reference_measures"])
    return {"f1": f1, "cats": dict(cats), "ref_notes": res["metrics"]["pitch_inventory"]["combined"]["reference"],
            "pred_notes": res["metrics"]["pitch_inventory"]["combined"]["predicted"],
            "unaligned_ref_notes": unal, "ref_bars": len(rb), "pred_bars": len(pb)}


def main():
    rows = [json.loads(l) for l in open(HERE / "timing_audit_b_preds.jsonl")]
    out = []
    for r in rows:
        e = evaluate(r)
        if e is None:
            continue
        e.update({"i": r["i"], "png": r["png"], "dataset": dataset_of(r["png"]), "exact": r["label"].strip() == r["pred"].strip()})
        out.append(e)
    (HERE / "timing_audit_b.json").write_text(json.dumps(out))
    n = len(out)

    def mean(k):
        return sum(e["f1"][k] for e in out) / n

    print(f"staffs scored: {n} of {len(rows)}; identical token strings: {sum(e['exact'] for e in out)}")
    print("mean F1 pitch / pitch+onset / pitch+onset+duration:", [round(100 * mean(k), 1) for k in range(3)])
    low = [e for e in out if e["f1"][2] < 0.8]
    print(f"staffs with full-match F1 < 80%: {len(low)} ({100 * len(low) / n:.1f}%)")
    ds = defaultdict(list)
    for e in out:
        ds[e["dataset"]].append(e)
    print("dataset n  meanP  meanPO  meanPOD  lowshare")
    for d, v in sorted(ds.items()):
        print(d, len(v), *[round(100 * sum(e["f1"][k] for e in v) / len(v), 1) for k in range(3)],
              f"{100 * sum(e['f1'][2] < 0.8 for e in v) / len(v):.1f}%")
    # sample-level cause of low staffs
    print("\nlow staffs: dominant cause (pitch F1 < 80% => 'pitch errors')")
    tab = defaultdict(Counter)
    notes_tab = defaultdict(Counter)
    for e in low:
        if e["f1"][0] < 0.8:
            cause = "pitch/symbol errors (pitch F1<80%)"
        elif e["cats"]:
            cause = Counter(e["cats"]).most_common(1)[0][0] if False else max(e["cats"].items(), key=lambda kv: kv[1])[0]
        else:
            cause = "none found"
        tab[e["dataset"]][cause] += 1
        for c, v in e["cats"].items():
            notes_tab[e["dataset"]][c] += v
    for d, c in sorted(tab.items()):
        print(d, dict(c))
    print("\nlow staffs: note counts by category (pitch-matched, not fully matched)")
    for d, c in sorted(notes_tab.items()):
        print(d, dict(sorted(c.items())))
    print("\nall staffs: pitch-matched but not fully matched notes by category, per dataset")
    allc = defaultdict(Counter)
    for e in out:
        for c, v in e["cats"].items():
            allc[e["dataset"]][c] += v
    for d, c in sorted(allc.items()):
        print(d, dict(sorted(c.items())))
    imperfect = [e for e in out if e["f1"][2] < 0.999]
    print(f"staffs with any full-match loss: {len(imperfect)}; <95%: {sum(e['f1'][2] < 0.95 for e in out)}; "
          f"timing loss (full F1 < pitch F1): {sum(e['f1'][2] < e['f1'][0] - 1e-9 for e in out)}")
    print("low staffs detail:")
    for e in low:
        print(" ", e["dataset"], e["png"].split("/")[-1], [round(100 * x, 1) for x in e["f1"]], e["cats"],
              "ref notes", e["ref_notes"], "bars ref/pred", e["ref_bars"], e["pred_bars"])
    json.dump({"all_notes": {d: dict(c) for d, c in allc.items()}}, open(HERE / "timing_audit_b_all.json", "w"))
    json.dump({"tab": {d: dict(c) for d, c in tab.items()}, "notes": {d: dict(c) for d, c in notes_tab.items()}},
              open(HERE / "timing_audit_b_summary.json", "w"))


if __name__ == "__main__":
    main()
