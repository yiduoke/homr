"""Engrave measures [a, b) (0-based index in the part) of an ASAP MusicXML with Verovio -> PNG (for by-eye checks)."""
import zipfile, copy, io, sys
import xml.etree.ElementTree as ET
import verovio
verovio.enableLog(verovio.LOG_OFF)
ASAP = "/Users/yiduoke/Documents/homr/run/box_scripts/r6_extra/asap_mxl/"

def trimmed_xml(asap, a, b):
    root = ET.fromstring(zipfile.ZipFile(ASAP + asap + ".mxl").read("score.xml"))
    part = root.find("part")
    meas = part.findall("measure")
    state = {}
    for m in meas[:a]:
        for at in m.findall("attributes"):
            for ch in at:
                key = ch.tag + (ch.get("number") or "")
                state[key] = ch
    for m in meas: part.remove(m)
    first = True
    for m in meas[a:b]:
        m = copy.deepcopy(m)
        for p in m.findall("print"): m.remove(p)
        if first and state:
            at = ET.Element("attributes")
            order = ["divisions", "key", "time", "staves", "clef"]
            for tag in order:
                for key, ch in state.items():
                    if ch.tag == tag: at.append(copy.deepcopy(ch))
            m.insert(0, at)
            # attributes of the first measure itself come after and override
        first = False
        part.append(m)
    return ET.tostring(root, encoding="unicode")

def render(asap, a, b, out_png, width=1800):
    import subprocess, tempfile, os
    tk = verovio.toolkit()
    tk.setOptions({"pageWidth": width, "scale": 45, "adjustPageHeight": True, "breaks": "none", "pageMarginTop": 20, "pageMarginBottom": 20,
                   "pageMarginLeft": 20, "pageMarginRight": 20, "header": "none", "footer": "none"})
    tk.loadData(trimmed_xml(asap, a, b))
    svg = tk.renderToSVG(1)
    tmp = tempfile.mktemp(suffix=".svg"); open(tmp, "w").write(svg)
    subprocess.run(["rsvg-convert", "-b", "white", "-w", str(width), "-o", out_png, tmp], check=True); os.remove(tmp)

if __name__ == "__main__":
    render(sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4])
