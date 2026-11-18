"""Pitch audit: classify pitch-inventory errors (misses / extras) of run2s7 per aligned bar.

Reuses timing_audit_a (bar alignment from note-scores.json, staff remap, bar lists) but swaps in a
parser that keeps step/alter/octave, chord info and octave-shift state.
Read-only. Output: pitch_audit.json (all error records) + stdout summary.
Run: /Users/yiduoke/Documents/homr/.venv/bin/python -B pitch_audit.py
"""
import os
import json
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/eval_run1")
import timing_audit_a as TA  # noqa: E402
from timing_audit_a import Bar, TOL, inventory_partners  # noqa: E402

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/octave_wt")
from validation.score_notes import Note, _SEMITONES  # noqa: E402

LET = "CDEFGAB"
PIECES = ["mazeppa", "la-campanella", "rachmaninoff-op3-2", "chopin-ballade-4", "bach-fugue-848",
          "bach-prelude-848", "mozart-kv331-theme", "mozart-kv309-1", "beethoven-pathetique-1"]
CATS = ["1 unaligned bar", "2 octave", "3 accidental", "4 step", "5 clef", "6 staff assignment",
        "7a chord member missing", "7b whole event missing", "8 extra", "9 other"]


@dataclass(frozen=True)
class PNote(Note):
    step: str = "C"
    alter: float = 0.0
    octave: int = 4
    onset_key: float = 0.0
    shifted: str = ""  # active octave-shift on this staff in this bar ("" / "8va" / "8vb" ...)

    @property
    def dp(self):
        return self.octave * 7 + LET.index(self.step)

    def name(self):
        a = {0.0: "", 1.0: "#", -1.0: "b", 2.0: "##", -2.0: "bb"}.get(self.alter, f"({self.alter})")
        return f"{self.step}{a}{self.octave}"


def read_file(path):
    """Same as timing_audit_a.read_file (bars, staves) but with PNote and octave-shift tracking."""
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
        active = {}  # staff -> shift type
        for measure in part.findall("measure"):
            cursor = Fraction(0)
            last_onset = None
            mx = Fraction(0)
            notes, rests = [], []
            bar_shift = dict(active)
            for el in measure:
                if el.tag == "direction":
                    for osh in el.iter("octave-shift"):
                        st = int(el.findtext("staff") or "1")
                        t = osh.get("type")
                        sz = osh.get("size", "8")
                        if t in ("up", "down"):
                            active[st] = ("8vb" if t == "up" else "8va") if sz == "8" else (
                                "15mb" if t == "up" else "15ma")
                            bar_shift[st] = active[st]
                        elif t == "stop":
                            active.pop(st, None)
                elif el.tag == "attributes":
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
                    if el.tag == "forward" and d > 0:
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
                    pitch = el.find("pitch")
                    if pitch is None:
                        continue
                    if os.environ.get("AUDIT_VISIBLE") == "1" and (el.get("print-object") == "no" or any(
                            (h.text or "").strip() == "none" for h in el.findall("notehead"))):
                        continue  # hidden notes are not counted by the scorer since D10 (the cursor has advanced already)
                    step = pitch.findtext("step")
                    alter = float(pitch.findtext("alter") or "0")
                    octv = int(pitch.findtext("octave") or "0")
                    midi = 12 * (octv + 1) + _SEMITONES[step] + alter
                    notes.append(PNote(offset + staff, midi, float(onset or 0), float(dur), grace,
                                       step=step, alter=alter, octave=octv, shifted=bar_shift.get(staff, "")))
            bars.append(Bar(measure.get("number", ""), tuple(notes), rests, float(mx), nominal, float(mx), False))
        parts.append((bars, offset, staff_count))
        offset += staff_count
    return parts, offset


TA.read_file = read_file  # make build_units use the spelled parser
# Bar rebuilt by TA.staff_bar_lists keeps note objects, so PNote survives.


def pair_pass(M, E, test, min_count=1, key=None):
    """Greedy pairing of misses M and extras E (lists of notes) under predicate/label `test(m, e)`.
    Returns list of (m, e, label) and shrinks M, E in place. If key is given, only labels with
    >= min_count pairs per (key-label) survive."""
    cand = []
    for i, m in enumerate(M):
        for j, e in enumerate(E):
            lab = test(m, e)
            if lab is not None:
                cand.append((abs(m.onset - e.onset), i, j, lab))
    cand.sort(key=lambda c: c[:3])
    um, ue, out = set(), set(), []
    for _, i, j, lab in cand:
        if i in um or j in ue:
            continue
        um.add(i)
        ue.add(j)
        out.append((M[i], E[j], lab))
    if min_count > 1:
        cnt = Counter(l for _, _, l in out)
        keep = [t for t in out if cnt[t[2]] >= min_count]
        dropped = {id(t[0]) for t in out} - {id(t[0]) for t in keep}
        um = {i for i, m in enumerate(M) if id(m) not in dropped and i in um}
        ue_ids = {id(t[1]) for t in keep}
        ue = {j for j, e in enumerate(E) if id(e) in ue_ids}
        out = keep
    M[:] = [m for i, m in enumerate(M) if i not in um]
    E[:] = [e for j, e in enumerate(E) if j not in ue]
    return out


def classify_group(ref_by_staff, pred_by_staff, info):
    """ref_by_staff / pred_by_staff: staff -> list of notes of one aligned bar pair (all staves of the unit).
    Returns list of records."""
    recs = []
    M, E = [], []
    ref_by_staff = {s: list(v) for s, v in ref_by_staff.items()}
    pred_by_staff = {s: list(v) for s, v in pred_by_staff.items()}
    # (1b) aligned pair whose content is unrelated (bar overlap < 10 %, >= 4 notes both sides) or a staff-bar
    # that is empty on one side with >= 4 notes on the other: counted as "bar not aligned / lost".
    allR = [n for s in ref_by_staff for n in ref_by_staff[s]]
    allP = [n for s in pred_by_staff for n in pred_by_staff[s]]
    ov = sum((Counter((n.staff, n.pitch) for n in allR) & Counter((n.staff, n.pitch) for n in allP)).values())
    lost = {}
    if len(allR) >= 4 and len(allP) >= 4 and ov < 0.1 * max(len(allR), len(allP)):
        lost = {s: "aligned bar unrelated (overlap<10%)" for s in set(ref_by_staff) | set(pred_by_staff)}
    else:
        for s in set(ref_by_staff) | set(pred_by_staff):
            nr, np_ = len(ref_by_staff.get(s, [])), len(pred_by_staff.get(s, []))
            if nr >= 4 and np_ == 0:
                lost[s] = "staff-bar empty in prediction"
            elif np_ >= 4 and nr == 0:
                lost[s] = "staff-bar empty in reference"
    for s, why in lost.items():
        for n in ref_by_staff.pop(s, []):
            recs.append({**info, "cat": "1 unaligned bar", "label": why, "ref": [(n.staff, n.name(), round(n.onset, 3), n.shifted)], "pred": []})
        for n in pred_by_staff.pop(s, []):
            recs.append({**info, "cat": "1 unaligned bar", "label": why, "ref": [], "pred": [(n.staff, n.name(), round(n.onset, 3), n.shifted)]})
    for s in sorted(set(ref_by_staff) | set(pred_by_staff)):
        R, P = ref_by_staff.get(s, []), pred_by_staff.get(s, [])
        inv = inventory_partners(R, P, set(), set())
        M += [r for i, r in enumerate(R) if i not in inv]
        used = set(inv.values())
        E += [p for j, p in enumerate(P) if j not in used]

    def rec(cat, ms, es, label=""):
        for m in ms:
            pass
        recs.append({**info, "cat": cat, "label": label,
                     "ref": [(m.staff, m.name(), round(m.onset, 3), m.shifted) for m in ms],
                     "pred": [(e.staff, e.name(), round(e.onset, 3), e.shifted) for e in es]})

    # (6) staff assignment: same pitch, different staff (exact equality, done first because unambiguous)
    for m, e, _ in pair_pass(M, E, lambda m, e: "x" if m.pitch == e.pitch and m.staff != e.staff else None):
        rec("6 staff assignment", [m], [e])
    # (2) octave
    for m, e, l in pair_pass(M, E, lambda m, e: (e.octave - m.octave) if (
            m.step == e.step and m.alter == e.alter and m.staff == e.staff and 1 <= abs(e.octave - m.octave) <= 2) else None):
        rec("2 octave", [m], [e], f"{l:+d}")
    # (3) accidental
    for m, e, l in pair_pass(M, E, lambda m, e: f"{m.alter:+g}->{e.alter:+g}" if (
            m.step == e.step and m.octave == e.octave and m.alter != e.alter) else None):
        rec("3 accidental", [m], [e], l)
    # (4) step
    for m, e, l in pair_pass(M, E, lambda m, e: (e.dp - m.dp) if abs(e.dp - m.dp) == 1 and m.staff == e.staff else None):
        rec("4 step", [m], [e], f"{l:+d}")
    # (5) clef: >=3 pairs with the same diatonic shift (3rd or 6th) in the same staff
    for m, e, l in pair_pass(M, E, lambda m, e: (m.staff, e.dp - m.dp) if (
            m.staff == e.staff and abs(e.dp - m.dp) in (2, 5)) else None, min_count=3):
        rec("5 clef", [m], [e], f"staff{l[0]} {l[1]:+d} steps")
    # (9) other: leftover miss and extra at the same staff/onset (a substitution)
    for m, e, l in pair_pass(M, E, lambda m, e: "sub" if m.staff == e.staff and abs(m.onset - e.onset) <= TOL else None):
        rec("9 other", [m], [e], f"{m.name()}->{e.name()} ({e.pitch - m.pitch:+g} st)")
    # (7) leftover misses: chord member vs whole event; (8) leftover extras
    inv_pred = Counter((e.staff, e.pitch) for s in pred_by_staff for e in pred_by_staff[s])
    for m in M:
        chord = [n for n in ref_by_staff.get(m.staff, []) if abs(n.onset - m.onset) <= TOL and n.grace == m.grace]
        others_present = any(inv_pred[(c.staff, c.pitch)] > 0 for c in chord if c is not m)
        cat = "7a chord member missing" if others_present else "7b whole event missing"
        recs.append({**info, "cat": cat, "label": f"chord size {len(chord)}", "chord": len(chord),
                     "ref": [(m.staff, m.name(), round(m.onset, 3), m.shifted)], "pred": []})
    for e in E:
        recs.append({**info, "cat": "8 extra", "label": "", "ref": [], "pred": [(e.staff, e.name(), round(e.onset, 3), e.shifted)]})
    return recs


def audit(name):
    res, rbars, pbars, units, unal, pparts = TA.build_units(name)
    groups = defaultdict(lambda: ([], []))  # (i,j) -> staves
    ref_by, pred_by = {}, {}
    for s, i, j in units:
        ref_by.setdefault((i, j), {})[s] = list(rbars[s][i].notes)
        pred_by.setdefault((i, j), {})[s] = list(pbars[s][j].notes)
    recs, nref, npred = [], 0, 0
    for (i, j), rs in ref_by.items():
        info = {"ref_bar": i + 1, "pred_bar": j + 1, "overlap": None}
        recs += classify_group(rs, pred_by[(i, j)], info)
    # (1) unaligned bars
    unal_pred = []
    if res["alignment_mode"] == "joint":
        up = [k - 1 for k in res["unmatched_prediction_measures"]]
        unal_pred = [(s, k) for s in pbars for k in up if k < len(pbars[s])]
    else:
        for sa in res["staff_alignment"]:
            unal_pred += [(sa["staff"], k - 1) for k in sa["unmatched_prediction_measures"]]
    for s, i in unal:
        for n in rbars[s][i].notes:
            recs.append({"ref_bar": i + 1, "pred_bar": None, "cat": "1 unaligned bar", "label": "ref",
                         "ref": [(n.staff, n.name(), round(n.onset, 3), n.shifted)], "pred": []})
    for s, k in unal_pred:
        for n in pbars[s][k].notes:
            recs.append({"ref_bar": None, "pred_bar": k + 1, "cat": "1 unaligned bar", "label": "pred",
                         "ref": [], "pred": [(n.staff, n.name(), round(n.onset, 3), n.shifted)]})
    nref = sum(len(b.notes) for s in rbars for b in rbars[s])
    # chord-size baseline for all ref notes
    base = Counter()
    for s in rbars:
        for b in rbars[s]:
            c = Counter(round(n.onset, 3) for n in b.notes if not n.grace)
            for k in c.values():
                base[k] += k
    m = res["metrics"]["pitch_inventory"]["combined"]
    return {"name": name, "pitch_f1": round(100 * m["f1"], 1), "ref_notes": m["reference"], "pred_notes": m["predicted"],
            "recs": recs, "ref_chord_baseline": dict(base), "alignment_mode": res["alignment_mode"]}


def main():
    out = {}
    for name in PIECES:
        a = audit(name)
        out[name] = a
        c = Counter(r["cat"] for r in a["recs"])
        print(name, a["pitch_f1"], len(a["recs"]), dict(sorted(c.items())))
    Path("/Users/yiduoke/Documents/homr/run/eval_run1/pitch_audit.json").write_text(json.dumps(out))


if __name__ == "__main__":
    main()
