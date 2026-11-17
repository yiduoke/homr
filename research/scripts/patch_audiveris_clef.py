"""Add the bass clef Audiveris left out of the lower staff.

Its measure 1 declares <staves>2</staves> but only writes clef number="1", so any
reader falls back to treble for staff 2 and the whole left hand sounds a sixth
high until the next clef appears at m.9. The key signature for staff 2 is missing
for the same reason.
"""
import re
import zipfile
from pathlib import Path

SRC = Path("/Users/yiduoke/Documents/audiveris/run/out/pathetique-1-a4.mxl")
OUT = Path("run/pathetique_audiveris_patched.musicxml")

with zipfile.ZipFile(SRC) as z:
    name = next(n for n in z.namelist() if n.endswith(".xml") and "META-INF" not in n)
    xml = z.read(name).decode("utf-8")

first = re.search(r'<measure number="1".*?</attributes>', xml, re.S)
block = first.group(0)
patched = block

if 'clef number="2"' not in block:
    patched = re.sub(
        r'(<clef number="1">.*?</clef>)',
        r'\1\n        <clef number="2">\n          <sign>F</sign>\n          <line>4</line>\n        </clef>',
        patched,
        count=1,
        flags=re.S,
    )
if 'key number="2"' not in block:
    patched = re.sub(
        r'(<key number="1">.*?</key>)',
        r'\1\n        <key number="2">\n          <fifths>-3</fifths>\n        </key>',
        patched,
        count=1,
        flags=re.S,
    )

xml = xml.replace(block, patched, 1)
OUT.write_text(xml)
print(f"patched -> {OUT}")
print("clef number=2 present:", 'clef number="2"' in patched)
