"""Find training staffs whose note sequence shares long pitch runs with a test reference (name-independent leak check)."""
import glob, os, re, sys, collections, hashlib
import xml.etree.ElementTree as ET
from multiprocessing import Pool
N = 12
STEPS = {"C": 0, "D": 1, "E": 2, "F": 3, "G": 4, "A": 5, "B": 6}
def grams(seq):
    out = set()
    for i in range(len(seq) - N + 1):
        w = seq[i:i + N]
        if len(set(w)) >= 5: out.add(hash(tuple(w)))
    return out
REFS = {}
for f in sorted(glob.glob("/workspace/run3/refs/*-reference.musicxml")):
    name = os.path.basename(f).replace("-reference.musicxml", "")
    g = set(); root = ET.parse(f).getroot()
    for part in root.findall("part"):
        seqs = collections.defaultdict(list)
        for m in part.findall("measure"):
            per = collections.defaultdict(list)
            for n in m.findall("note"):
                if n.find("pitch") is None or n.find("grace") is not None: continue
                p = n.findtext("pitch/step") + n.findtext("pitch/octave")
                per[(n.findtext("staff"), n.findtext("voice"))].append(p)
            for k, v in per.items(): seqs[k] += v
        for s in seqs.values(): g |= grams(s)
    REFS[name] = g
ALL = {}
for name, g in REFS.items():
    for h in g: ALL.setdefault(h, set()).add(name)
def staff_hits(path):
    try: lines = open(path).read().splitlines()
    except Exception: return None
    seqs = collections.defaultdict(list)
    for ln in lines:
        per = collections.defaultdict(list)
        for g in ln.split("&"):
            t = g.split()
            if len(t) >= 6 and t[0].startswith("note_"): per[t[5]].append(t[1])
        for pos, ps in per.items(): seqs[pos] += sorted(ps)
    hit = collections.Counter(); 
    for s in seqs.values():
        for h in grams(s):
            for nm in ALL.get(h, ()): hit[nm] += 1
    return {k: v for k, v in hit.items() if v >= 2}
def work(line):
    png, tok = line.split(",")
    return line, staff_hits(tok)
if __name__ == "__main__":
    lists = sys.argv[1:]
    for lst in lists:
        L = [l.strip() for l in open(lst) if l.strip()]
        with Pool(14) as p: res = p.map(work, L, chunksize=200)
        flagged = [(l, h) for l, h in res if h]
        per = collections.Counter(); 
        for l, h in flagged:
            for k in h: per[k] += 1
        print(lst, "staffs", len(L), "flagged", len(flagged), dict(per.most_common(12)))
        with open("/workspace/run3/leak_" + os.path.basename(lst), "w") as f:
            for l, h in flagged: f.write(l + "\t" + str(h) + "\n")
