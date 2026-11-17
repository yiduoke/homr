import music21 as m21, sys, collections
from pathlib import Path
for p in sorted(Path("/workspace/extra_scores/kern/scriabin").rglob("*.krn"))[:int(sys.argv[1])]:
    s = m21.converter.parse(str(p), format="humdrum")
    print(p.name, len(s.parts), [type(x).__name__ for x in s.parts], [ (x.recurse().getElementsByClass("Clef").first() or "").__class__.__name__ for x in s.parts], len(s.getElementsByClass("StaffGroup")), flush=True)
