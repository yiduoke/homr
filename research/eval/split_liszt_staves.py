"""Split the Liszt HR6 reference (4 declared staves) into the printed main system and the printed ossia.

The scan prints two staves per system. Old staves 3 and 4 are the main staves. Old staves 1 and 2
hold a whole-bar rest in every bar except bars 58-61 and 66-69, where they hold the "Ossia"
staves printed above the main system (page 3 of the scan). So:

  main file  : old staves 3, 4 -> staves 1, 2 (clefs, <staves>, staff-layout renumbered);
               tempo words that were attached to old staff 1 go to staff 1; Ossia words and the
               ossia octave-shift are left out.
  ossia file : old staves 1, 2 unchanged (notes, rests, Ossia words, octave-shift), so that
               main + ossia hold every note of the original.

Backups/forwards are rebuilt from the original onsets after the removal.

usage: split_liszt_staves.py ORIGINAL MAIN_OUT OSSIA_OUT
"""

from __future__ import annotations

import copy
import sys
import xml.etree.ElementTree as ET


def is_ossia_direction(d: ET.Element) -> bool:
    for dt in d.findall("direction-type"):
        for ch in dt:
            if ch.tag == "octave-shift":
                return True
            if ch.tag == "words" and (ch.text or "").strip() == "Ossia":
                return True
    return False


def rebuild(measure: ET.Element, keep) -> None:
    """keep(child) -> None to drop the child, else the new staff number (or True to leave it)."""
    children = list(measure)
    # original onsets
    cursor = 0
    last_start = 0
    starts = {}
    for c in children:
        if c.tag == "note":
            chord = c.find("chord") is not None
            starts[id(c)] = last_start if chord else cursor
            if not chord:
                last_start = cursor
                cursor += int(c.findtext("duration") or 0)
        elif c.tag == "backup":
            cursor -= int(c.findtext("duration"))
        elif c.tag == "forward":
            cursor += int(c.findtext("duration"))
        else:
            starts[id(c)] = cursor
    template_tail = None
    for c in children:
        if c.tag == "backup":
            template_tail = (c.text, c.tail, copy.deepcopy(c))
            break
    for c in children:
        measure.remove(c)
    cur = 0
    out = []
    for c in children:
        if c.tag in ("backup", "forward"):
            continue
        new_staff = keep(c)
        if new_staff is None:
            continue
        if new_staff is not True:
            c.find("staff").text = str(new_staff)
        if c.tag in ("note", "direction", "harmony") and not (
            c.tag == "note" and c.find("chord") is not None
        ):
            start = starts[id(c)]
            if start != cur:
                tag = "backup" if start < cur else "forward"
                el = ET.Element(tag)
                dur = ET.SubElement(el, "duration")
                dur.text = str(abs(cur - start))
                el.text = c.tail and "\n" + " " * 10  # indentation of children
                el.tail = c.tail
                if template_tail is not None:
                    el.text = template_tail[2].text
                    el.tail = template_tail[2].tail
                    dur.tail = template_tail[2][0].tail
                    dur.text = str(abs(cur - start))
                out.append(el)
                cur = start
            if c.tag == "note":
                cur += int(c.findtext("duration") or 0)
        out.append(c)
    for c in out:
        measure.append(c)


def convert(src: str, dst: str, mode: str) -> None:
    raw = open(src, encoding="utf-8").read()
    header = raw[: raw.index("<score-partwise")]
    tree = ET.parse(src)
    root = tree.getroot()
    main = mode == "main"
    old_to_new = {"3": 1, "4": 2} if main else {"1": 1, "2": 2}
    for m in root.iter("measure"):
        # attributes
        for a in m.findall("attributes"):
            for st in a.findall("staves"):
                st.text = "2"
            for clef in a.findall("clef"):
                n = clef.get("number")
                if n in old_to_new:
                    clef.set("number", str(old_to_new[n]))
                else:
                    tail = clef.tail
                    idx = list(a).index(clef)
                    a.remove(clef)
                    if idx > 0:
                        prev = list(a)[idx - 1]
                        prev.tail = tail
        for p in m.findall("print"):
            for sl in p.findall("staff-layout"):
                n = sl.get("number")
                if n in old_to_new and old_to_new[n] != 1:
                    sl.set("number", str(old_to_new[n]))
                else:  # distances above old staff 1/2/3 belong to staves that are gone or now first
                    idx = list(p).index(sl)
                    tail = sl.tail
                    p.remove(sl)
                    if idx > 0:
                        list(p)[idx - 1].tail = tail

        def keep(c: ET.Element):
            if c.tag == "note":
                s = c.findtext("staff")
                return old_to_new[s] if s in old_to_new else None
            if c.tag == "direction":
                s = c.findtext("staff")
                if main:
                    if s in ("3", "4"):
                        return old_to_new[s]
                    if s == "1" and not is_ossia_direction(c):
                        return 1  # tempo words printed above the top staff
                    return None
                return old_to_new[s] if s in old_to_new and is_ossia_direction(c) else None
            return True

        rebuild(m, keep)
    out = ET.tostring(root, encoding="unicode")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(header + out + "\n")


if __name__ == "__main__":
    src, main_out, ossia_out = sys.argv[1:4]
    convert(src, main_out, "main")
    convert(src, ossia_out, "ossia")
