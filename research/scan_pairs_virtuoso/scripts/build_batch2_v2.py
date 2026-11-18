"""v2 of the batch 2 lists (D23): printed-notation candidates, corrected tokens under batch2/tokens_printed/, Sonata 2 check.
Writes batch2/lists/batch2_train_all_v2.txt, batch2_val_v2.txt, batch2_train_demets_unebarque_v2.txt and lists/batch2_printed_notation_candidates.txt.
Nothing in the candidate file is admitted to a training list."""
import os, re, json, csv, collections
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); B = ROOT + "/batch2"
REL = "scan_pairs_virtuoso/"
L = lambda p: [l.strip() for l in open(p) if l.strip()]
name_of = lambda line: os.path.basename(line.split(",")[0])[:-4]
tok_of = {name_of(l): l.split(",")[1] for f in ("batch2_train_all", "batch2_val", "batch2_train_demets_unebarque") for l in L(f"{B}/lists/{f}.txt")}
man = {r["crop"]: r for r in csv.DictReader(open(B + "/manifest.csv"))}
TRIPLET = {3: 2, 6: 4, 12: 8, 24: 16, 48: 32, 96: 64}        # triplet kern -> the plain value the print shows when the meter is compound (12/8, 6/4)

# eye-checked / read-based decisions (see PILOT_SPEC.md section 7)
N9_64 = {"p-03_s1": "eye", "p-03_s2": "eye", "p-03_s3": "eye", "p-03_s4": "eye", "p-04_s4": "eye (6/4 from the last bar)", "p-05_s1": "inferred (between two checked 6/4 systems)",
         "p-05_s2": "eye", "p-05_s5": "eye", "p-06_s0": "eye (2/2 returns in the last bars)", "p-07_s0": "inferred", "p-07_s1": "eye", "p-07_s2": "eye", "p-07_s4": "inferred"}
SYMBOL = {"N9_p-01_s0": ("common (C), Grave", "2/2", "common"), "NR2_p-01_s0": ("common (C)", "4/4", "common"), "N21_p-06_s4": ("cut", "2/2", "cut")}

def kerns(txt):
    return [int(m.group(1)) for m in re.finditer(r"(?:^|&|\n)(?:note|rest)_(\d+)", txt)]

def convert(txt):
    """triplet kerns -> plain values; None unless every note and rest of the crop is a triplet kern with a time signature absent."""
    ks = kerns(txt)
    if not ks or any(k not in TRIPLET for k in ks) or "timeSignature" in txt:
        return None
    return re.sub(r"(^|&|\n)((?:note|rest)_)(\d+)", lambda m: m.group(1) + m.group(2) + str(TRIPLET[int(m.group(3))]), txt)

rows, remove = [], set()
os.makedirs(B + "/tokens_printed", exist_ok=True)
def add_row(name, printed, xml, cls, evidence, newtok=None):
    rows.append((name, man[f"images/{name.split('_')[0]}/{name}.png"]["piece"], printed, xml, cls, evidence, newtok or "-")); remove.add(name)

for name, t in sorted(tok_of.items()):
    pid = name.split("_")[0]
    txt = open(ROOT + "/../" + t).read()
    if pid == "N7":
        new = convert(txt)
        out = None
        if new:
            open(f"{B}/tokens_printed/{name}.tokens", "w").write(new); out = f"{REL}batch2/tokens_printed/{name}.tokens"
        add_row(name, "12/8 (plain eighths in groups of three)", "4/4 with triplets", "A compound meter printed, simple meter + triplets in ASAP",
                "batch2/report.md; sheet audit_printed/b1_01 (N7_p-05_s1)", out)
    elif pid == "N9" and name.split("_", 1)[1] in N9_64:
        sec = N9_64[name.split("_", 1)[1]]
        new = convert(txt) if sec == "eye" else None
        out = None
        if new:
            open(f"{B}/tokens_printed/{name}.tokens", "w").write(new); out = f"{REL}batch2/tokens_printed/{name}.tokens"
        add_row(name, "6/4 (plain quarters and eighths)", "2/2 with triplets", "A compound-like meter printed, simple meter + triplets in ASAP", sec, out)
    elif name in SYMBOL:
        pr, lab, to = SYMBOL[name]
        new = re.sub(r"timeSignature_" + re.escape(lab), "timeSignature_" + to, txt, count=1)
        assert new != txt
        open(f"{B}/tokens_printed/{name}.tokens", "w").write(new)
        add_row(name, pr, lab, "S meter symbol only (same meter)", "zoom of the time signature (audit_printed/z1)", f"{REL}batch2/tokens_printed/{name}.tokens")
    elif pid == "N19":
        txt_ = txt; ks = kerns(txt_)
        if ks and sum(k not in (1, 2, 4, 8, 16, 32, 64, 128) for k in ks) / len(ks) >= 0.5:
            add_row(name, "6/8 over 2/4 (Ravel)", "2/4 with triplets", "A meter 6/8 printed, 2/4 + triplets in ASAP (Demets list only)", "eye on N19_p-14_s0; this crop by tuplet share >= 50 %, not eye-checked", None)
os.makedirs(B + "/lists", exist_ok=True)
hdr = "crop\tpiece\tprinted meter\tASAP/label encoding\tclass\tevidence\tproposed corrected tokens (batch2/tokens_printed, originals kept)"
open(ROOT + "/lists/batch2_printed_notation_candidates.txt", "w").write(hdr + "\n" + "\n".join("\t".join(r) for r in rows) + "\n")
for f in ("batch2_train_all", "batch2_val", "batch2_train_demets_unebarque"):
    kept = [l for l in L(f"{B}/lists/{f}.txt") if name_of(l) not in remove]
    open(f"{B}/lists/{f}_v2.txt", "w").write("\n".join(kept) + "\n")
    print(f, len(L(f"{B}/lists/{f}.txt")), "->", len(kept))
c = collections.Counter((r[1], r[4][:1]) for r in rows); print(len(rows), "candidates", dict(c), "with proposed tokens:", sum(r[6] != "-" for r in rows))
