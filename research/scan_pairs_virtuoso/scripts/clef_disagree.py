"""Crops of the pilot lists whose initial clefs or key signature in the label tokens differ from the released model's read of the scan (work/reads).
A disagreement is either a model error or a label/print difference (the ASAP XML writes e.g. a bass clef for a passage the edition prints in the treble clef);
the rendered twin follows the label, the scan follows the print. usage: clef_disagree.py OUT.json"""
import json, glob, re, csv, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bycrop = {r["crop"]: r for r in csv.DictReader(open(ROOT + "/manifest.csv"))}
reads = {}
for f in glob.glob(ROOT + "/work/reads/*.jsonl"):
    for l in open(f):
        d = json.loads(l); reads[d["id"]] = d
def clefs(txt):
    out = {"upper": None, "lower": None}
    for line in txt.split("\n")[:3]:
        for el in line.split("&"):
            m = re.match(r"clef_(\S+) .* (upper|lower)$", el.strip())
            if m and out[m[2]] is None: out[m[2]] = m[1]
    return out
def key(txt):
    m = re.search(r"keySignature_(-?\d+)", "\n".join(txt.split("\n")[:4]))
    return m[1] if m else None
bad = {}
for lst in ("train_strong", "train_hard", "val_strong"):
    for line in open(f"{ROOT}/lists/{lst}.txt"):
        img = line.split(",")[0].strip().replace("scan_pairs_virtuoso/", "")
        if not img: continue
        r = bycrop[img]; pdf, p = r["page_image"].split("/")[1], r["page_image"].split("/")[2][:-4]
        rd = reads.get(f"{pdf}/{p}/s{r['system_index']}")
        if not rd or not rd.get("tokens"): continue
        name = os.path.basename(img)[:-4]
        lab = open(f"{ROOT}/tokens/{name}.tokens").read()
        why = [w for w, a, b in (("clef", clefs(lab), clefs(rd["tokens"])), ("key", key(lab), key(rd["tokens"]))) if a != b]
        if why: bad[name] = why
json.dump(bad, open(sys.argv[1], "w"), indent=0)
import collections
print(len(bad), "crops with a clef or key signature disagreement", collections.Counter(w for v in bad.values() for w in v))
