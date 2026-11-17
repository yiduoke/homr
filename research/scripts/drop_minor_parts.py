"""Drop parts that cover only a few pages from a joined homr MusicXML.

homr writes an ossia staff or a small extra staff (e.g. Mazeppa's "Piano a 7 octaves") as
a part of its own. Such a part is an alternative to the main staves, not more music, and
when several pages are joined (homr.main with several images, homr/relieur.py) it stays
in the score as a mostly empty part. A part with notes in fewer than half the measures of
the fullest part is removed, together with its entry in the part list.

    python run/drop_minor_parts.py IN.musicxml OUT.musicxml
"""

import sys
import xml.etree.ElementTree as ET


def measures_with_notes(part: ET.Element) -> int:
    return sum(1 for m in part.findall("measure") if m.find("note/pitch") is not None)


def main() -> None:
    tree = ET.parse(sys.argv[1])  # noqa: S314
    root = tree.getroot()
    parts = root.findall("part")
    if len(parts) > 1:
        counts = {p.get("id"): measures_with_notes(p) for p in parts}
        fullest = max(counts.values())
        part_list = root.find("part-list")
        for p in parts:
            if counts[p.get("id")] < 0.5 * fullest:
                root.remove(p)
                if part_list is not None:
                    for sp in part_list.findall("score-part"):
                        if sp.get("id") == p.get("id"):
                            part_list.remove(sp)
                print(f"dropped part {p.get('id')}: notes in {counts[p.get('id')]} of {fullest} measures")
    tree.write(sys.argv[2], encoding="UTF-8", xml_declaration=True)


if __name__ == "__main__":
    main()
