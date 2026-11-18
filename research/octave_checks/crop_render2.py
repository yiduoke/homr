"""crop_render2.py IN.musicxml LO HI OUT.png [by_index]: engraves bars LO..HI of every part with Verovio. LO/HI are measure indices (1-based, position in the file) if by_index is
given (default), else measure numbers. Unlike crop_render.py the first kept bar gets the merged attributes (divisions, staves, the latest key/time/clef before it), so two-staff references render as grand staffs.
Octave-shift directions inside the range are drawn by Verovio (bracket and lowered notes); an orphan stop is dropped."""
import sys, copy, os, subprocess
import xml.etree.ElementTree as ET
import verovio
from PIL import Image

def render(inp, lo, hi, out, by_index=True, width=2100, scale=55):
    tree = ET.parse(inp); root = tree.getroot()
    for part in root.findall("part"):
        ms = part.findall("measure")
        att = ET.Element("attributes")
        first = ms[0].find("attributes")
        if first is not None: att = copy.deepcopy(first)
        def sel(i, m):
            if by_index: return lo <= i + 1 <= hi
            try: return lo <= int(m.get("number")) <= hi
            except ValueError: return False
        keep = [m for i, m in enumerate(ms) if sel(i, m)]
        firstkept = next(i for i, m in enumerate(ms) if sel(i, m))
        for m in ms[:firstkept]:
            a = m.find("attributes")
            if a is None: continue
            for ch in a:
                if ch.tag in ("key", "time"):
                    for old in att.findall(ch.tag): att.remove(old)
                    att.append(copy.deepcopy(ch))
                elif ch.tag == "clef":
                    for old in att.findall("clef"):
                        if old.get("number") == ch.get("number"): att.remove(old)
                    att.append(copy.deepcopy(ch))
        # order children as the schema wants
        order = ["divisions", "key", "time", "staves", "clef", "transpose"]
        kids = sorted(list(att), key=lambda e: order.index(e.tag) if e.tag in order else 99)
        for k in list(att): att.remove(k)
        for k in kids: att.append(k)
        if keep[0].find("attributes") is not None: keep[0].remove(keep[0].find("attributes"))
        keep[0].insert(0, att)
        for m in ms:
            if m not in keep: part.remove(m)
    tmp = out + ".tmp.musicxml"; tree.write(tmp, encoding="UTF-8", xml_declaration=True)
    tk = verovio.toolkit()
    tk.setOptions({"pageWidth": width, "pageHeight": 900, "scale": scale, "breaks": "none", "header": "none", "footer": "none", "adjustPageHeight": True, "mnumInterval": 1})
    tk.loadFile(tmp)
    svg = tk.renderToSVG(1)
    open(out + ".svg", "w").write(svg); subprocess.run(["rsvg-convert", "-b", "white", "-o", out, out + ".svg"], check=True, capture_output=True); os.remove(out + ".svg"); os.remove(tmp)
    return out

if __name__ == "__main__":
    inp, lo, hi, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    render(inp, lo, hi, out, by_index=(sys.argv[5] != "number") if len(sys.argv) > 5 else True)
