"""Cut a MusicXML reference to bars FIRST..LAST (1-based positions in the part, not printed numbers).

The first kept bar gets the attributes in force at that point (divisions, key, time, clefs,
staves), so it reads the same as in the full score. Inputs are never changed.

    python cut_reference.py IN.musicxml OUT.musicxml FIRST LAST
"""
import copy
import sys
from xml.etree import ElementTree as ET

src, dst, first, last = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
tree = ET.parse(src)
root = tree.getroot()
ORDER = ["divisions", "key", "time", "staves", "clef"]
for part in root.findall("part"):
    measures = part.findall("measure")
    state = {}  # tag -> element (clef keyed by number)
    for m in measures[: first - 1]:
        for att in m.findall("attributes"):
            for e in att:
                key = e.tag if e.tag != "clef" else "clef" + e.get("number", "1")
                state[key] = e
    for m in measures[: first - 1] + measures[last:]:
        part.remove(m)
    head = part.find("measure")
    att = head.find("attributes")
    if att is None:
        att = ET.Element("attributes")
        head.insert(0, att)
    have = {e.tag if e.tag != "clef" else "clef" + e.get("number", "1") for e in att}
    for tag in ORDER:
        for key in sorted(k for k in state if k == tag or (tag == "clef" and k.startswith("clef"))):
            if key not in have:
                att.append(copy.deepcopy(state[key]))
    # keep MusicXML element order inside attributes
    els = list(att)
    for e in els:
        att.remove(e)
    rank = {t: i for i, t in enumerate(ORDER)}
    for e in sorted(els, key=lambda e: rank.get(e.tag, 99)):
        att.append(e)
tree.write(dst, xml_declaration=True, encoding="UTF-8")
print(f"kept bars {first}..{last} of {len(measures)}", file=sys.stderr)
