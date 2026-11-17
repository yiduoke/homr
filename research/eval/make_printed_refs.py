"""Write <folder>-reference-printed.musicxml next to each reference (see printed/README in README.md).

Step 1 (rule): `<accidental>` of every pitched note from homr/accidentals.py
AccidentalState.printed_sign (run/acc_wt, branch accidentals-run2): sounding <alter> -> printed sign,
per staff, step+octave carry to the barline, key from <key><fifths>, tie across a barline = no sign.
Notes are processed in onset order within a measure (all voices of a staff share the carried signs).
Step 2 (corrections): eval_run1/printed/<folder>.corrections.json, entries
  {"measure": n (1-based position in the part), "staff": s, "onset": divisions, "pitch": "C#4"-like
   step+octave e.g. "C4", "sign": "#|b|N|##|bb|_", "why": text}
override the rule's sign for what the PDF actually prints. Sounding <alter> is never changed.
Usage: python make_printed_refs.py [folder ...]
"""
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/acc_wt")
from homr.accidentals import ALTER_TO_SIGN, SIGN_TO_MUSIC_XML, AccidentalState, key_alteration  # noqa: E402

E = Path(__file__).resolve().parent
CMP = E.parent / "out" / "compare"
KERN = ["bach-prelude-848", "bach-fugue-848", "mozart-kv331-theme", "mozart-kv309-1", "beethoven-pathetique-1"]
LABELS_OK = {"bach-prelude-848", "bach-fugue-848"}  # bar labels = measure index (not KV309, Beethoven: shifted)
LILYPOND = True  # all five KernScores-based test PDFs are LilyPond engravings
EXTRA_XML = {"N#": "natural-sharp", "Nb": "natural-flat"}
AFTER = ("type", "dot")  # <accidental> goes after the last of these, before the rest


def sign_of(note):
    a = note.find("accidental")
    return None if a is None else a.text


def notes_by_measure(root):
    """Yield (measure_index, measure, [(onset, order, note)]) for the first part."""
    part = root.find("part")
    for mi, m in enumerate(part.findall("measure"), start=1):
        pos, out, order = 0, [], 0
        for el in m:
            if el.tag == "note":
                dur = el.findtext("duration")
                if el.find("chord") is not None:
                    onset = last_onset
                else:
                    onset = pos
                    last_onset = pos
                    if el.find("grace") is None and dur is not None:
                        pos += int(dur)
                out.append((onset, order, el))
                order += 1
            elif el.tag == "backup":
                pos -= int(el.findtext("duration"))
            elif el.tag == "forward":
                pos += int(el.findtext("duration"))
        yield mi, m, out


def set_accidental(note, sign):
    old = note.find("accidental")
    if old is not None:
        note.remove(old)
    if sign in (None, "_"):
        return
    idx = 0
    for i, ch in enumerate(list(note)):
        if ch.tag in AFTER or ch.tag in ("pitch", "duration", "tie", "instrument", "voice", "cue", "grace", "chord"):
            idx = i + 1
    el = ET.Element("accidental")
    el.text = SIGN_TO_MUSIC_XML.get(sign) or EXTRA_XML.get(sign) or sign
    note.insert(idx, el)


REPEAT_GAP = {"bach-prelude-848": 1.0, "bach-fugue-848": 1.0}


def rule_signs(root, system_starts=(), repeat_gap=None):
    """{(measure, staff, onset, step+octave, voice): sign} by the rule; also returns alter map."""
    state = AccidentalState(0)
    pend, last_print, last_voice = {}, {}, {}
    divisions = 1
    res = {}
    for mi, m, notes in notes_by_measure(root):
        for dv in m.iter("divisions"):
            divisions = int(dv.text)
        for k in m.iter("key"):
            f = k.findtext("fifths")
            if f is not None:
                state.set_key(int(f))
        state.new_bar()
        last_print.clear()
        last_voice.clear()
        new_pend = {}
        for onset, order, n in sorted(notes, key=lambda t: (t[0], t[1])):
            p = n.find("pitch")
            if p is None:
                continue
            step, octv = p.findtext("step"), int(p.findtext("octave"))
            alter = int(float(p.findtext("alter") or 0))
            staff = n.findtext("staff") or "1"
            voice = n.findtext("voice") or "1"
            ties = {t.get("type") for t in n.findall("tie")}
            key = (staff, voice, step, octv)
            tie_alter = pend.pop(key, None) if "stop" in ties else None
            prev = state._carried.get((staff, step, octv))
            # LilyPond repeats the accidental of a note tied over a system break (seen on the
            # prelude, m45-46); not when the alteration is the key's own
            brk = (tie_alter is not None and mi in system_starts
                   and tie_alter != key_alteration(state.fifths, step))
            sign = state.printed_sign(staff, step, octv, alter, tie_alter=tie_alter, force=brk)
            # LilyPond cancels a double sign with natural + single sign (natural-sharp / natural-flat)
            if LILYPOND and sign in ("#", "b") and prev in (2, -2):
                sign = "N" + sign
            q = onset / divisions
            pk = (staff, step, octv)
            if (sign == "_" and repeat_gap is not None and "stop" not in ties
                    and alter != key_alteration(state.fifths, step) and pk in last_print
                    and (q - last_print[pk] > repeat_gap or last_voice.get(pk) not in (None, voice))):
                sign = ALTER_TO_SIGN[alter]  # courtesy repeat
            last_voice[pk] = voice
            if sign != "_":
                last_print[pk] = q
            if "start" in ties:
                new_pend[key] = alter
            res[(mi, staff, onset, f"{step}{octv}", voice, order)] = sign
        pend = new_pend
    return res


def build(folder, apply_corrections=True):
    src = CMP / folder / f"{folder}-reference.musicxml"
    root = ET.parse(src).getroot()
    sysf = E / 'printed' / f'{folder}.systems.json'
    starts = set(json.load(open(sysf))['starts']) if sysf.exists() and folder in LABELS_OK else set()
    signs = rule_signs(root, starts, REPEAT_GAP.get(folder))
    corr = []
    cf = E / "printed" / f"{folder}.corrections.json"
    if apply_corrections and cf.exists():
        corr = json.load(open(cf))
    cmap = {}
    for c in corr:
        cmap[(c["measure"], str(c["staff"]), c["onset"], c["pitch"])] = c["sign"]
    stats = {"notes": 0, "rule_signs": 0, "corrected": 0, "music21_signs": 0, "rule_vs_music21_diff": []}
    for mi, m, notes in notes_by_measure(root):
        for onset, order, n in notes:
            p = n.find("pitch")
            if p is None:
                continue
            step, octv = p.findtext("step"), int(p.findtext("octave"))
            staff = n.findtext("staff") or "1"
            voice = n.findtext("voice") or "1"
            rule = signs[(mi, staff, onset, f"{step}{octv}", voice, order)]
            old = sign_of(n)
            stats["notes"] += 1
            stats["rule_signs"] += rule != "_"
            stats["music21_signs"] += old is not None
            from homr.accidentals import MUSIC_XML_TO_SIGN
            oldsign = MUSIC_XML_TO_SIGN.get(old, old) if old else "_"
            if oldsign != rule:
                stats["rule_vs_music21_diff"].append([mi, staff, onset, f"{step}{octv}", oldsign, rule])
            final = rule
            k = (mi, staff, onset, f"{step}{octv}")
            if k in cmap:
                final = cmap[k]
                stats["corrected"] += final != rule
            set_accidental(n, final)
    out = CMP / folder / f"{folder}-reference-printed.musicxml"
    ET.indent(root)
    body = ET.tostring(root, encoding="unicode")
    head = ('<?xml version="1.0" encoding="utf-8"?>\n'
            '<!DOCTYPE score-partwise PUBLIC "-//Recordare//DTD MusicXML 4.0 Partwise//EN" '
            '"http://www.musicxml.org/dtds/partwise.dtd">\n')
    out.write_text(head + body + "\n", encoding="utf-8")
    json.dump(stats, open(E / "printed" / f"{folder}.stats.json", "w"), indent=0)
    return stats


if __name__ == "__main__":
    for f in sys.argv[1:] or KERN:
        s = build(f)
        print(f, {k: (v if k != "rule_vs_music21_diff" else len(v)) for k, v in s.items()})
