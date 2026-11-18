#!/usr/bin/env python3
"""
Read-only. For flagged token files (detail TSV rows, kind bug_rest8) find in the source MusicXML a
measure where one (staff, voice) holds a single rest of type eighth, no measure attribute is
involved, and print what the XML says: typed or measure="yes", the type element, the measure's
time signature. This shows whether a flagged bar comes from a typeless rest (the bug) or from a
real eighth rest (typed).
usage: xml_find_bar.py DETAILS_TSV N_PER_SOURCE
"""
import collections
import random
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, "/workspace/audit_barrest")
import xml_scan as X  # noqa: E402


def first_single_eighth(path):
    root = ET.parse(path).getroot()
    for part in root.findall("part"):
        beats = beat_type = None
        for meas in part.findall("measure"):
            for a in meas.findall("attributes"):
                t = a.find("time")
                if t is not None:
                    beats, beat_type = t.findtext("beats"), t.findtext("beat-type")
            tracks = collections.defaultdict(list)
            for n in meas.findall("note"):
                if n.find("chord") is None:
                    tracks[(n.findtext("staff", "1"), n.findtext("voice", "1"))].append(n)
            for key, notes in tracks.items():
                if len(notes) == 1 and notes[0].find("rest") is not None:
                    n = notes[0]
                    if n.findtext("type") == "eighth":
                        s = re.sub(r"\s+", " ", ET.tostring(n, encoding="unicode"))[:200]
                        return f"part {part.get('id')} m{meas.get('number')} time {beats}/{beat_type}: {s}"
    return ""


def main():
    rows = [l.rstrip("\n").split("\t") for l in open(sys.argv[1])][1:]
    n = int(sys.argv[2])
    random.seed(20261120)
    by = collections.defaultdict(set)
    for r in rows:
        if r[4] == "bug_rest8":
            by[r[0]].add(r[1])
    for src, toks in sorted(by.items()):
        for t in random.sample(sorted(toks), min(n, len(toks))):
            s, ident = X.source_id(t)
            xml = X.find_xml(s, ident)
            if xml is None:
                print(src, t.split("/")[-1], "XML_NOT_FOUND")
                continue
            print(src, t.split("/")[-1], xml.split("/")[-1], first_single_eighth(xml)[:260] or "no measure with a single typed eighth rest found")


if __name__ == "__main__":
    main()
