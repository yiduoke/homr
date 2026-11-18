#!/usr/bin/env python3
"""
Bar rests in final MusicXML outputs (the writer's joined.musicxml of the saved page outputs):
per part / measure / (staff, voice) track that holds only rests, compare the track's total
duration with the length of the bar from the time signature in force.

  measure_yes_ok     <rest measure="yes"/> with duration == bar
  measure_yes_wrong  <rest measure="yes"/> with another duration
  typed_full         typed rests that add up to the bar
  typed_under        typed rests shorter than the bar (a rest_8 for a bar)
  typed_over         typed rests longer than the bar (rest_1 in a 3/4 bar)
usage: musicxml_barrests.py ROOT [--glob 'testset/layout1/*/joined.musicxml']
"""
import glob
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from fractions import Fraction


def analyse(path):
    root = ET.parse(path).getroot()
    res = Counter()
    ex = []
    for part in root.findall("part"):
        divisions = 1
        beats, beat_type = None, None
        for meas in part.findall("measure"):
            res["measures"] += 1
            for a in meas.findall("attributes"):
                d = a.find("divisions")
                if d is not None and d.text:
                    divisions = int(d.text)
                t = a.find("time")
                if t is not None:
                    b, bt = t.findtext("beats"), t.findtext("beat-type")
                    try:
                        beats, beat_type = int(b), int(bt)
                    except (TypeError, ValueError):
                        beats, beat_type = None, None
            tracks = defaultdict(lambda: {"dur": 0, "rest": True, "measure_yes": False, "n": 0})
            for note in meas.findall("note"):
                if note.find("grace") is not None or note.find("chord") is not None:
                    if note.find("rest") is None:
                        tracks[(note.findtext("staff", "1"), note.findtext("voice", "1"))]["rest"] = False
                    continue
                key = (note.findtext("staff", "1"), note.findtext("voice", "1"))
                tr = tracks[key]
                tr["dur"] += int(note.findtext("duration", "0") or 0)
                tr["n"] += 1
                rest = note.find("rest")
                if rest is None:
                    tr["rest"] = False
                elif rest.get("measure") == "yes":
                    tr["measure_yes"] = True
            if beats is None:
                res["measures_no_meter"] += 1
                continue
            bar = Fraction(divisions * 4 * beats, beat_type)
            staffs = defaultdict(list)
            for key, tr in tracks.items():
                if tr["n"]:
                    staffs[key[0]].append(tr)
            for st, trs in staffs.items():
                if not all(t["rest"] for t in trs):
                    continue
                d = Fraction(max(t["dur"] for t in trs))
                my = any(t["measure_yes"] for t in trs)
                res["staff_rest_only"] += 1
                if d == bar:
                    res["staff_full"] += 1
                elif my:
                    res["staff_measure_yes_wrong"] += 1
                elif d < bar:
                    res["staff_typed_under"] += 1
                else:
                    res["staff_typed_over"] += 1
            for key, tr in tracks.items():
                if not tr["rest"] or tr["n"] == 0:
                    continue
                res["rest_only_tracks"] += 1
                d = Fraction(tr["dur"])
                if tr["measure_yes"]:
                    kind = "measure_yes_ok" if d == bar else "measure_yes_wrong"
                else:
                    kind = "typed_full" if d == bar else ("typed_under" if d < bar else "typed_over")
                res[kind] += 1
                if kind in ("measure_yes_wrong", "typed_under", "typed_over") and len(ex) < 5:
                    ex.append(f"{part.get('id')} m{meas.get('number')} voice{key[1]} {kind} dur={float(d/divisions):.3g}q bar={float(bar/divisions):.3g}q")
    return res, ex


def main():
    pattern = sys.argv[1]
    tot = Counter()
    rows = []
    for p in sorted(glob.glob(pattern)):
        try:
            r, ex = analyse(p)
        except Exception as e:  # noqa: BLE001
            print("ERR", p, e, file=sys.stderr)
            continue
        tot.update(r)
        rows.append((p, r, ex))
        print(p.split("/")[-2], dict(r), ex[:2])
    print("TOTAL", dict(tot))


if __name__ == "__main__":
    main()
