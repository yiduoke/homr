from music21 import converter
import glob
for f in sorted(glob.glob("run/pages150/page-*.musicxml")):
    s = converter.parse(f)
    info = [(p.id, len(p.getElementsByClass('Measure'))) for p in s.parts]
    print(f.split('/')[-1], "parts:", info)
