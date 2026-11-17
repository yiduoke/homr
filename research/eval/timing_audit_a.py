"""Part A: why do run2s7 outputs get pitches but not timing right?

For every reference note that is matched on pitch inventory but not on
pitch+onset+duration, assign one cause per note, per aligned bar.
Read-only: nothing under run/out or run/eval_run1/run2s7 is modified.
Output: eval_run1/timing_audit_a.json (per-note records, sample bars).

Run: /Users/yiduoke/Documents/homr/.venv/bin/python -B timing_audit_a.py
"""
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/octave_wt")
from validation.score_notes import (  # noqa: E402
    DEFAULT_TOLERANCE, Measure, Note, Score, _SEMITONES, _mean_pitches, _nearest, _staff_bars,
    remap_staves,
)

HOME = Path("/Users/yiduoke/Documents/homr/run")
CMP = HOME / "out/compare"
RUN = HOME / "eval_run1/run2s7"
TOL = DEFAULT_TOLERANCE + 1e-9
PIECES = ["mazeppa", "la-campanella", "rachmaninoff-op3-2", "bach-prelude-848", "bach-fugue-848",
          "mozart-kv331-theme", "mozart-kv309-1", "beethoven-pathetry-1".replace("pathetry", "pathetique"),
          "chopin-ballade-4"]
CATS = ["1 tuplet", "2 voice confusion", "3 rest shift", "4 grace/cue", "5 bar length/meter",
        "6 duration only", "7 alignment artefact", "8 other"]


@dataclass(frozen=True)
class XNote(Note):
    voice: str = "1"
    tuplet: bool = False
    cue: bool = False
    dots: int = 0
    tied: bool = False
    ntype: str = ""
    tm: str = ""


@dataclass
class Bar:
    number: str
    notes: tuple
    rests: list  # (staff, voice, onset, dur)
    end: float  # whole bar (all staves of the part) length in quarters
    nominal: float  # nominal length from time signature
    hyp_end: float = 0.0  # bar length if every tuplet were written as plain notated values
    has_tuplet: bool = False


def read_file(path):
    """Mirror of score_notes._read_part, plus voice/tuplet/cue/rest/bar-length info.

    Returns (list of (bars-by-part-staff)), staves per part. bars[abs_staff] = [Bar...]
    """
    root = ET.fromstring(Path(path).read_bytes().decode("utf-8-sig"))
    for el in root.iter():
        el.tag = el.tag.rsplit("}", 1)[-1]
    parts, offset = [], 0
    for part in root.findall("part"):
        staff_count = max([1] + [int(s.text or "1") for s in part.iter("staves")]
                          + [int(n.findtext("staff") or "1") for n in part.findall("measure/note")])
        divisions = Fraction(1)
        nominal = 4.0
        bars = []
        for measure in part.findall("measure"):
            cursor = Fraction(0)
            last_onset = None
            mx = Fraction(0)
            notes, rests = [], []
            for el in measure:
                if el.tag == "attributes":
                    t = el.findtext("divisions")
                    if t is not None:
                        divisions = Fraction(t)
                    if el.find("time") is not None:
                        try:
                            nominal = int(el.findtext("time/beats")) * 4 / int(el.findtext("time/beat-type"))
                        except (TypeError, ValueError):
                            pass
                elif el.tag in ("backup", "forward"):
                    d = Fraction(el.findtext("duration") or "0") / divisions
                    if el.tag == "forward" and d > 0:  # gap: treated as an (implicit) rest
                        rests.append((offset + int(el.findtext("staff") or "1"), el.findtext("voice") or "1",
                                      float(cursor), float(d)))
                    cursor += d if el.tag == "forward" else -d
                    mx = max(mx, cursor)
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
                    mx = max(mx, cursor)
                    staff = int(el.findtext("staff") or "1")
                    voice = el.findtext("voice") or "1"
                    pitch = el.find("pitch")
                    if pitch is None:
                        if el.find("rest") is not None and not chord:
                            rests.append((offset + staff, voice, float(onset), float(dur)))
                        continue
                    midi = (12 * (int(pitch.findtext("octave") or "0") + 1)
                            + _SEMITONES[pitch.findtext("step") or ""] + float(pitch.findtext("alter") or "0"))
                    notes.append(XNote(offset + staff, midi, float(onset or 0), float(dur), grace,
                                       voice=voice, tuplet=el.find("time-modification") is not None,
                                       cue=el.find("cue") is not None,
                                       dots=len(el.findall("dot")),
                                       tied=any(t.get("type") for t in el.findall("tie")),
                                       ntype=el.findtext("type") or "",
                                       tm=(el.findtext("time-modification/actual-notes") or "") + ":" + (el.findtext("time-modification/normal-notes") or "") if el.find("time-modification") is not None else ""))
            vend, vdelta = defaultdict(float), defaultdict(float)
            seen = set()
            for n in notes:
                if n.grace:
                    continue
                k = (n.staff, n.voice)
                vend[k] = max(vend[k], n.onset + n.duration)
                if n.tuplet and (k, n.onset) not in seen:
                    seen.add((k, n.onset))
                    a, _, b = n.tm.partition(":")
                    if a and b and int(b):
                        vdelta[k] += n.duration * (int(a) / int(b) - 1)
            for s_, v_, o_, d_ in rests:
                vend[(s_, v_)] = max(vend[(s_, v_)], o_ + d_)
            hyp = max([float(mx)] + [vend[k] + vdelta[k] for k in vend])
            bars.append(Bar(measure.get("number", ""), tuple(notes), rests, float(mx), nominal, hyp,
                            any(n.tuplet for n in notes)))
        parts.append((bars, offset, staff_count))
        offset += staff_count
    return parts, offset


def to_score(parts, nstaves):
    """Same combination rules as score_notes.parse_musicxml."""
    if any(len(p[0]) != len(parts[0][0]) for p in parts):
        per = tuple(
            tuple(Measure(b.number, tuple(n for n in b.notes if n.staff == s)) for b in bars)
            for bars, off, cnt in parts for s in range(off + 1, off + cnt + 1))
        return Score((), nstaves, per)
    comb = tuple(Measure(parts[0][0][i].number, tuple(n for bars, _, _ in parts for n in bars[i].notes))
                 for i in range(len(parts[0][0])))
    return Score(comb, nstaves)


def staff_bar_lists(parts):
    """abs staff -> list[Bar] (with only that staff's notes/rests; end = part bar end)."""
    out = {}
    for bars, off, cnt in parts:
        for s in range(off + 1, off + cnt + 1):
            out[s] = [Bar(b.number, tuple(n for n in b.notes if n.staff == s),
                          [r for r in b.rests if r[0] == s], b.end, b.nominal, b.hyp_end, b.has_tuplet) for b in bars]
    return out


# ---------------------------------------------------------------- matching
def max_matching(edges, n_right):
    assigned = {}

    def aug(i, seen):
        for j in edges[i]:
            if j in seen:
                continue
            seen.add(j)
            if j not in assigned or aug(assigned[j], seen):
                assigned[j] = i
                return True
        return False

    for i in sorted(range(len(edges)), key=lambda k: len(edges[k])):
        aug(i, set())
    return {i: j for j, i in assigned.items()}


def full_match(R, P):
    edges = [[j for j, p in enumerate(P) if r.staff == p.staff and r.pitch == p.pitch and r.grace == p.grace
              and abs(r.onset - p.onset) <= TOL and abs(r.duration - p.duration) <= TOL]
             for r in R]
    return max_matching(edges, len(P))


def inventory_partners(R, P, used_r, used_p):
    """Pair leftover notes of equal (staff,pitch), preferring nearest onset."""
    cand = []
    for i, r in enumerate(R):
        if i in used_r:
            continue
        for j, p in enumerate(P):
            if j in used_p or (r.staff, r.pitch) != (p.staff, p.pitch):
                continue
            cand.append((abs(r.onset - p.onset), i, j))
    cand.sort()
    out = {}
    ur, up = set(), set()
    for _, i, j in cand:
        if i in ur or j in up:
            continue
        ur.add(i)
        up.add(j)
        out[i] = j
    return out


# ---------------------------------------------------------------- classification
def rest_before(bar, voice, staff, onset):
    return sum(d for s, v, o, d in bar.rests if s == staff and v == voice and o < onset - TOL)


def classify(r, p, R, P, rb, pb, ref_full_missing_tuplet_voice, overlap_ratio):
    """Return (category, detail) for ref note r with pitch-partner p (pred note)."""
    if rb.end > 1.5 * rb.nominal + 1e-6 or pb.end > 2 * pb.nominal + 1e-6:
        return "5 bar length/meter", (f"cadenza-like bar: ref len {rb.end:.2f} (nominal {rb.nominal:g}), "
                                      f"pred len {pb.end:.2f} (nominal {pb.nominal:g})")
    if overlap_ratio < 0.5:
        return "7 alignment artefact", "low pitch overlap in aligned bar"
    if r.tuplet:
        return "1 tuplet", f"ref {r.tm} / pred " + (p.tm if p.tuplet else "plain")
    if p.tuplet:
        return "1 tuplet", "spurious tuplet in prediction (ref note is plain)"
    if any(q.tuplet and q.voice == p.voice and q.onset < p.onset - TOL for q in P):
        return "1 tuplet", "cascade after spurious tuplet in pred voice"
    if (r.voice, r.staff) in ref_full_missing_tuplet_voice and any(
            q.tuplet and q.voice == r.voice and q.onset < r.onset - TOL for q in R):
        return "1 tuplet", "cascade after tuplet in same voice"
    ng_ref, ng_pred = sum(n.grace for n in R), sum(n.grace for n in P)
    if r.grace or p.grace or r.cue or p.cue:
        return "4 grace/cue", "grace" if (r.grace or p.grace) else "cue"
    if ng_ref != ng_pred:
        return "4 grace/cue", f"bar has {ng_ref} ref grace notes vs {ng_pred} in pred (written as regular notes or dropped)"
    len_diff = pb.end - rb.end
    if abs(len_diff) > 1 / 24 and rb.has_tuplet and abs(pb.end - rb.hyp_end) <= 1 / 24 \
            and abs(pb.nominal - rb.nominal) < 1e-6:
        return "1 tuplet", f"bar length explained by tuplet(s) written plain ({len_diff:+.3f} q)"
    rvoices = {n.voice for n in R}
    pvoices = {n.voice for n in P}
    if abs(pb.nominal - rb.nominal) > 1e-6:
        return "5 bar length/meter", f"time signature differs (ref {rb.nominal:g}, pred {pb.nominal:g} q)"
    if abs(len_diff) > 1 / 24:
        nt_ref, nt_pred = sum(n.tuplet for n in R), sum(n.tuplet for n in P)
        if len_diff > 0 and nt_ref and nt_pred < nt_ref:
            return "1 tuplet", (f"bar longer {len_diff:+.3f} q; ref bar has {nt_ref} tuplet notes, pred {nt_pred} "
                                "(not exactly explained)")
        d_bar_rest = sum(x[3] for x in pb.rests) - sum(x[3] for x in rb.rests)
        if abs(d_bar_rest) > TOL and abs(len_diff - d_bar_rest) <= 2 * TOL and len(rvoices) == len(pvoices):
            return "3 rest shift", f"pred bar has {d_bar_rest:+.3f} q of rests/gaps vs ref; bar length {len_diff:+.3f} q"
        if len(rvoices) != len(pvoices):
            return "2 voice confusion", f"voices ref {len(rvoices)} vs pred {len(pvoices)}; bar length {len_diff:+.3f} q"
        if {x[1] for x in pb.rests} - pvoices and not ({x[1] for x in rb.rests} - rvoices):
            return "2 voice confusion", f"pred rests sit in a voice without notes; bar length {len_diff:+.3f} q"
        nr, npd = sum(not n.grace for n in R), sum(not n.grace for n in P)
        if nr != npd:
            return "8 other", f"extra/missing notes in bar (ref {nr}, pred {npd}); bar length {len_diff:+.3f} q"
        return "5 bar length/meter", f"same meter, pred bar {len_diff:+.3f} q (ref bar {rb.end:g})"
    if abs(r.onset - p.onset) <= TOL:
        ratio = p.duration / r.duration if r.duration else 0
        return "6 duration only", f"dur ratio {ratio:.2f}" + (" ref dotted" if r.dots else "") + (
            " ref tied" if r.tied else "")
    delta = p.onset - r.onset
    d_rest = rest_before(pb, p.voice, p.staff, p.onset) - rest_before(rb, r.voice, r.staff, r.onset)
    if abs(d_rest) > TOL and abs(delta - d_rest) <= 2 * TOL:
        return "3 rest shift", f"{'extra' if d_rest > 0 else 'missing'} rest {abs(d_rest):.3g} q before"
    other_voice_onset = any(q.voice != r.voice and abs(q.onset - p.onset) <= TOL for q in R)
    if len(rvoices) != len(pvoices):
        return "2 voice confusion", f"voices ref {len(rvoices)} vs pred {len(pvoices)}"
    if other_voice_onset:
        return "2 voice confusion", "pred onset equals another ref voice's onset"
    nr, npd = sum(not n.grace for n in R), sum(not n.grace for n in P)
    if nr != npd:
        return "8 other", f"extra/missing notes in bar (ref {nr}, pred {npd}); onset delta {delta:+.3f} q"
    return "8 other", f"delta {delta:+.3f} q, d_rest {d_rest:+.3f}"


def analyse_unit(ref_bar, pred_bar, staff, ref_i, pred_j):
    R, P = list(ref_bar.notes), list(pred_bar.notes)
    full = full_match(R, P)
    used_p = set(full.values())
    inv = inventory_partners(R, P, set(full), used_p)
    overlap = (len(full) + len(inv)) / max(len(R), len(P), 1)
    # voices of ref where a tuplet note is unmatched
    bad_tuplet_voices = {(r.voice, r.staff) for i, r in enumerate(R) if r.tuplet and i not in full}
    recs = []
    for i, j in inv.items():
        cat, det = classify(R[i], P[j], R, P, ref_bar, pred_bar, bad_tuplet_voices, overlap)
        recs.append({"staff": staff, "ref_bar": ref_i + 1, "pred_bar": pred_j + 1,
                     "ref_number": ref_bar.number, "cat": cat, "detail": det,
                     "len_mismatch": bool(abs(pred_bar.end - ref_bar.end) > 1 / 24 or abs(pred_bar.nominal - ref_bar.nominal) > 1e-6),
                     "ref_len": round(ref_bar.end, 3), "pred_len": round(pred_bar.end, 3),
                     "ref_nom": ref_bar.nominal, "pred_nom": pred_bar.nominal,
                     "overlap": round(overlap, 2),
                     "pitch": R[i].pitch, "ref_onset": round(R[i].onset, 4), "pred_onset": round(P[j].onset, 4),
                     "ref_dur": round(R[i].duration, 4), "pred_dur": round(P[j].duration, 4)})
    return len(full), len(inv), len(R), len(P), recs


def build_units(name):
    ref_path = CMP / name / f"{name}-reference.musicxml"
    pred_path = (CMP / name / f"{name}-run2s7.musicxml") if name == "chopin-ballade-4" \
        else (RUN / name / f"{name}-run2s7.musicxml")
    score_path = (CMP / name / "note-scores.json") if name == "chopin-ballade-4" else (RUN / name / "note-scores.json")
    res = json.load(open(score_path))["results"]
    res = [r for r in res if r["input"]["path"].endswith(f"{name}-run2s7.musicxml")][0]
    rparts, rn = read_file(ref_path)
    pparts, pn = read_file(pred_path)
    rbars = staff_bar_lists(rparts)
    pbars = staff_bar_lists(pparts)
    ref_score, pred_score = to_score(rparts, rn), to_score(pparts, pn)
    if rn != pn:  # replicate staff remap for bar lists
        means = _mean_pitches(_staff_bars(ref_score))
        merged = {s: [] for s in range(1, rn + 1)}
        for k in range(1, pn + 1):
            bars = pbars[k]
            mean = _mean_pitches([tuple(Measure(b.number, b.notes) for b in bars)])[0]
            tgt = _nearest(mean, means, k) if mean is not None else min(k, rn)
            slot = merged[tgt]
            for i, b in enumerate(bars):
                nb = Bar(b.number, tuple(replace(n, staff=tgt) for n in b.notes),
                         [(tgt,) + r[1:] for r in b.rests], b.end, b.nominal)
                if i < len(slot):
                    o = slot[i]
                    slot[i] = Bar(o.number, o.notes + nb.notes, o.rests + nb.rests, max(o.end, nb.end), o.nominal)
                else:
                    slot.append(nb)
        pbars = merged
    units, unmatched_ref = [], []
    if res["alignment_mode"] == "joint":
        pairs = [(a["reference_index"] - 1, a["prediction_index"] - 1) for a in res["alignment"]]
        for s in range(1, rn + 1):
            for i, j in pairs:
                units.append((s, i, j))
        ref_unal = [i - 1 for i in res["unmatched_reference_measures"]]
        unal = [(s, i) for s in range(1, rn + 1) for i in ref_unal]
    else:
        unal = []
        for sa in res["staff_alignment"]:
            s = sa["staff"]
            for pr in sa["pairs"]:
                units.append((s, pr["reference_index"] - 1, pr["prediction_index"] - 1))
            unal += [(s, i - 1) for i in sa["unmatched_reference_measures"]]
    return res, rbars, pbars, units, unal, pparts


def audit(name):
    res, rbars, pbars, units, unal, pparts = build_units(name)
    recs, tot = [], Counter()
    for s, i, j in units:
        f, inv, nr, npd, rr = analyse_unit(rbars[s][i], pbars[s][j], s, i, j)
        tot["full"] += f
        tot["inv"] += inv
        tot["ref"] += nr
        recs += rr
    ref_unal = sum(len(rbars[s][i].notes) for s, i in unal)
    m = res["metrics"]
    chk_full = m["pitch_onset_duration"]["combined"]["matched"]
    chk_inv = m["pitch_inventory"]["combined"]["matched"]
    # joint-mode inventory is computed per staff inside count_matches' multiset => same as mine
    ok = (tot["full"] == chk_full) and (tot["full"] + len(recs) == chk_inv)
    return {"name": name, "full": tot["full"], "inv_matched": chk_inv, "ref_notes": m["pitch_inventory"]["combined"]["reference"],
            "pred_notes": m["pitch_inventory"]["combined"]["predicted"],
            "targets": len(recs), "ref_notes_in_unmatched_bars": ref_unal, "check_ok": ok,
            "check": [tot["full"], chk_full, tot["full"] + len(recs), chk_inv],
            "f1": [round(100 * m[k]["combined"]["f1"], 1) for k in m],
            "recs": recs}


def main():
    out = {}
    for name in PIECES:
        out[name] = audit(name)
        a = out[name]
        c = Counter(r["cat"] for r in a["recs"])
        print(name, "targets", a["targets"], "check", a["check_ok"], a["check"], dict(sorted(c.items())))
    Path("/Users/yiduoke/Documents/homr/run/eval_run1/timing_audit_a.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
