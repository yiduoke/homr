"""usage: render_one_svg.py REF.musicxml SCALE OUTDIR -> writes pNNN.svg pages. Unusually dense bars (cadenzas, long runs) get a system of their own
so that their notes are not squeezed; warnings go to stderr."""
import os, statistics, sys, tempfile
import xml.etree.ElementTree as ET
import verovio
ref, scale, out = sys.argv[1], int(sys.argv[2]), sys.argv[3]
tree = ET.parse(ref); root = tree.getroot()
# A stray minor part (Scriabin Sonata 5 has one with 47 notes) would be engraved as an extra staff under the piano
_sizes = {p.get("id"): sum(1 for n in p.iter("note") if n.find("rest") is None) for p in root.findall("part")}
_big = max(_sizes.values()) if _sizes else 0
for _p in list(root.findall("part")):
    if _sizes[_p.get("id")] < 0.05 * _big:
        root.remove(_p)
        for _sp in list(root.iter("score-part")):
            if _sp.get("id") == _p.get("id"):
                _pl = root.find("part-list"); _pl.remove(_sp)
part = root.find("part")
measures = part.findall("measure")
counts = [sum(1 for n in m.findall("note") if n.find("rest") is None) for m in measures]
med = statistics.median(c for c in counts if c) if any(counts) else 0
dense = {i for i, c in enumerate(counts) if c >= max(48, 2.4 * med)}
def mark(m):
    p = m.find("print")
    if p is None:
        p = ET.Element("print"); m.insert(0, p)
    p.set("new-system", "yes")
for i in sorted(dense):
    mark(measures[i])
    if i + 1 < len(measures): mark(measures[i + 1])
tmp = os.path.join(tempfile.mkdtemp(), "ref.musicxml"); tree.write(tmp, encoding="UTF-8", xml_declaration=True)
tk = verovio.toolkit()
tk.setOptions({"pageWidth": 2100, "pageHeight": 2100, "scale": scale, "breaks": "smart", "header": "none", "footer": "none", "adjustPageHeight": False,
               "mnumInterval": 0, "spacingLinear": 0.32, "spacingNonLinear": 0.55})
tk.loadFile(tmp); n = tk.getPageCount()
for i in range(1, n + 1): open(f"{out}/p{i:03d}.svg", "w").write(tk.renderToSVG(i))
print(n, "pages;", len(dense), "dense bars given their own system:", [measures[i].get("number") for i in sorted(dense)][:12])
