"""Engrave the Claude-made reference MusicXML files with Verovio (bar numbers on every bar) so the time signatures can be
checked against the printed scores. Writes out/meter_check/<piece>.pdf and out/meter_check/meters.md (meter per bar)."""
import os, subprocess, sys, tempfile
import xml.etree.ElementTree as ET
import verovio
from PIL import Image
R = "/Users/yiduoke/Documents/homr/run/out/"
PIECES = {
    "mazeppa": R + "compare/mazeppa/mazeppa-reference.musicxml",
    "la-campanella": R + "compare/la-campanella/la-campanella-reference.musicxml",
    "rachmaninoff-op3-2": R + "compare/rachmaninoff-op3-2/rachmaninoff-op3-2-reference.musicxml",
    "chopin-ballade-4": R + "compare/chopin-ballade-4/chopin-ballade-4-reference.musicxml",
    "stravinsky-petrushka": R + "testset/stravinsky-petrushka/stravinsky-petrushka-reference.musicxml",
}
out = R + "meter_check/"; lines = ["# Meters in the Claude references (bar number: meter)", ""]
for name, path in PIECES.items():
    if not os.path.exists(path): print("missing", path); continue
    root = ET.parse(path).getroot(); ts = []
    for m in root.find("part").findall("measure"):
        b = m.findtext("attributes/time/beats")
        if b: ts.append(f"{m.get('number')}: {b}/{m.findtext('attributes/time/beat-type')}")
    lines += [f"## {name}  ({len(root.find('part').findall('measure'))} bars)", "", "  \n".join(ts) if ts else "(no time signature)", ""]
    tk = verovio.toolkit()
    tk.setOptions({"pageWidth": 2100, "pageHeight": 2100, "scale": 30, "mnumInterval": 1, "spacingLinear": 0.32, "spacingNonLinear": 0.55, "breaks": "auto", "header": "none", "footer": "none", "adjustPageHeight": False})
    tk.loadFile(path); n = tk.getPageCount(); tmp = tempfile.mkdtemp(); svgs = []
    for i in range(1, n + 1):
        f = f"{tmp}/p{i:03d}.svg"; open(f, "w").write(tk.renderToSVG(i)); svgs.append(f)
    subprocess.run(["qlmanage", "-t", "-s", "2100", "-o", tmp, *svgs], check=True, capture_output=True)
    imgs = [Image.open(f + ".png").convert("RGB") for f in svgs]
    imgs[0].save(out + name + ".pdf", save_all=True, append_images=imgs[1:], resolution=200.0)
    print(name, n, "pages,", len(ts), "meter entries")
open(out + "meters.md", "w").write("\n".join(lines) + "\n")
