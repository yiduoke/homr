import sys, os, multiprocessing as mp
from pathlib import Path
SRC = Path("/workspace/extra_scores/kern/scriabin")
OUT = Path(sys.argv[1]); LIMIT = int(sys.argv[2])
EXCL = ["op8_no12", "op08_no12", "op30"]   # Etude Op.8 No.12, Sonata 4 Op.30
def conv(p):
    import music21 as m21
    out = OUT / (p.stem + ".mxl")
    try:
        s = m21.converter.parse(str(p), format="humdrum")
        if len(s.parts) == 2:
            for q in s.parts: q.__class__ = m21.stream.PartStaff
            s.insert(0, m21.layout.StaffGroup(list(s.parts), symbol="brace", barTogether=True))
        s.write("mxl", fp=str(out))
        return p.name, "ok"
    except Exception as e:
        return p.name, "FAIL " + repr(e)[:200]
if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in SRC.rglob("*.krn"))
    ex = [p for p in files if any(e in p.name for e in EXCL)]
    files = [p for p in files if p not in ex]
    print("EXCLUDED", [str(p.relative_to(SRC)) for p in ex], flush=True)
    if LIMIT: files = files[:LIMIT]
    with mp.Pool(16) as pool:
        for n, r in pool.imap_unordered(conv, files):
            print(n, r, flush=True)
