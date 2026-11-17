import sys, csv, hashlib, zipfile, re
from pathlib import Path
R = Path("/workspace/extra_scores/asap/asap-dataset")
OUT = Path(sys.argv[1]); LIMIT = int(sys.argv[2])
# (composer, folder-substring) of evaluation pieces
EXCL = {
 "Liszt/Gran_Etudes_de_Paganini/2_La_campanella": "Liszt La Campanella",
 "Liszt/Transcendental_Etudes/4": "Liszt Mazeppa",
 "Liszt/Mephisto_Waltz": "Liszt Mephisto Waltz No.1",
 "Chopin/Ballades/4": "Chopin Ballade 4",
 "Chopin/Scherzos/20": "Chopin Scherzo 1 Op.20",
 "Bach/Prelude/bwv_848": "Bach WTC I Prelude 3 BWV 848",
 "Bach/Fugue/bwv_848": "Bach WTC I Fugue 3 BWV 848",
 "Mozart/Piano_Sonatas/11-3": "Mozart K.331 mvt 3 (whole sonata excluded)",
 "Beethoven/Piano_Sonatas/8-1": "Beethoven Op.13 Pathetique mvt 1",
 "Ravel/Gaspard_de_la_Nuit/1_Ondine": "Ravel Gaspard de la nuit",
}
rows = list(csv.DictReader(open(R / "metadata.csv")))
seen, scores = {}, []
for r in rows:
    if r["xml_score"] not in seen:
        seen[r["xml_score"]] = r; scores.append(r)
excluded, dups, keep, hashes = [], [], [], {}
for r in sorted(scores, key=lambda r: r["folder"]):
    f = r["folder"]
    if f in EXCL: excluded.append((f, EXCL[f])); continue
    base = re.sub(r"_(no_first_repeat|no_2_repeat|no_repeat|repeat|no_trio)$", "", f)
    if base != f and any(x["folder"] == base for x in scores):
        dups.append((f, "repeat variant of " + base)); continue
    h = hashlib.md5((R / r["xml_score"]).read_bytes()).hexdigest()
    if h in hashes: dups.append((f, "identical to " + hashes[h])); continue
    hashes[h] = f; keep.append(r)
print("EXCLUDED", excluded); print("DEDUP-SKIPPED", dups); print("KEPT", len(keep), flush=True)
if LIMIT: keep = keep[:LIMIT]
OUT.mkdir(parents=True, exist_ok=True)
for r in keep:
    data = (R / r["xml_score"]).read_bytes()
    name = r["folder"].replace("/", "_").replace(".", "_")
    with zipfile.ZipFile(OUT / (name + ".mxl"), "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/container.xml", "<?xml version=\"1.0\"?><container><rootfiles><rootfile full-path=\"score.xml\"/></rootfiles></container>")
        z.writestr("score.xml", data)
