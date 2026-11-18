"""build_mixture2.py (D30): training / validation mixtures of the second round (arms A, B, C), built from the stored mixture of the first round
(mixture_B.npz = real piano 2,418 pairs, real songs 1,450, rendered 9,419, brace variations 2,978; the Reichardt pairs are LEFT OUT: they are a transfer test now)
plus the real-example collection of run/brace_collection (labels/*.npz).
  all arms : + curved-brace editions of the collection, split by WORK (train works / held-out works, never one work on both sides; Henle 1987, Salabert 1949 and the
             editions of test compositions are never trained on)
  B, C     : + real thin-brace (Schott) pairs: the volume's pieces I, II, III, VI, VII, VIII, IX and Piano Concertos 1 and 2 are train; XI, XII, Waldesrauschen,
             Gnomenreigen and the Concert-Etudes S.144 file are validation (pieces, not pages); NEVER used: Mazeppa (reserved), the test scans (TE 5, TE 10, Sonata), Cappi 1802, Eder 1800, Reichardt
  C        : + Schott-guided brace variations (vary_braces_schott.py on the training pages of the first round, label_pairs labels)
usage: python build_mixture2.py OUTDIR      -> OUTDIR/mixture2_{A,B,C}.npz
"""
import os, sys, glob
import numpy as np
BC = "/Users/yiduoke/Documents/homr/run/brace_collection"
RB = "/Users/yiduoke/Documents/homr/run/staff_rel_realbrace"
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/rel_wt")
import label_pairs as L

CURVED_TRAIN = ["brahms-op1-simrock1898", "brahms-op79-peters1910", "brahms-rhapsodies79-simrock1880", "chopin-nocturnes9-kistner1833",
                "chopin-sonata2-breitkopf1840", "chopin-sonata2-friedlein1850", "liszt-consolations-breitkopf1850", "liszt-hr12-peters-sauer",
                "liszt-hr2-jurgenson1878", "liszt-hr2-senff1872", "liszt-mephisto1-peters-sauer", "liszt-mephisto1-schuberth1862",
                "schumann-kinderszenen-breitkopf1839", "scriabin-sonata3-belaieff1898", "berg-sonata-op1-schlesinger1910",
                "lyapunov-op11-12-zimmermann1906", "lyapunov-op11-5-zimmermann1906"]
# held-out works (negative controls / regression): everything else curved
NOT_CURVED = {"beethoven-op13-eder1800", "beethoven-op27-2-cappi1802", "schott-concert-etudes", "schott-concerto1", "schott-concerto2",
              "schott-te-volume", "schott-te-volume.pool", "schott-te-volume.mazeppa(reserved)"}
PIECES = [(6, 7, "I"), (8, 12, "II"), (13, 15, "III"), (38, 47, "VI"), (48, 53, "VII"), (54, 64, "VIII"), (65, 75, "IX"),
          (86, 93, "XI"), (94, 103, "XII"), (104, 112, "Waldesrauschen"), (113, 121, "Gnomenreigen")]
VAL_PIECES = {"XI", "XII", "Waldesrauschen", "Gnomenreigen"}


def piece_of(page):
    n = int(page.rsplit("page-", 1)[1])
    for lo, hi, nm in PIECES:
        if lo <= n <= hi:
            return nm
    raise ValueError(page)


def load(name):
    return np.load(f"{BC}/labels/{name}.npz", allow_pickle=True)


def main():
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    b = np.load(f"{RB}/mixture_B.npz", allow_pickle=True)
    keep = b["source"] != "real_thin"          # Reichardt out
    base = {k: b[k][keep] for k in ("crops", "labels", "source", "split", "group", "page")}
    print("base", len(base["labels"]), "Reichardt removed", int((~keep).sum()))
    # ---- curved editions
    cur = {k: [] for k in base}
    for f in sorted(glob.glob(f"{BC}/labels/*.npz")):
        name = os.path.basename(f)[:-4]
        if name in NOT_CURVED or name.startswith("schott-"):
            continue
        z = np.load(f, allow_pickle=True); n = len(z["labels"])
        spl = "train" if name in CURVED_TRAIN else "val"
        for k, v in (("crops", z["crops"]), ("labels", z["labels"]), ("source", np.array(["real_curved"] * n)), ("split", np.array([spl] * n)),
                     ("group", np.array([name] * n)), ("page", z["page"])):
            cur[k].append(v)
    cur = {k: np.concatenate(v) for k, v in cur.items()}
    print("curved train", int((cur["split"] == "train").sum()), "val", int((cur["split"] == "val").sum()))
    # ---- Schott real thin braces
    sch = {k: [] for k in base}
    zp = load("schott-te-volume.pool")
    pcs = np.array([piece_of(p) for p in zp["page"]])
    spl = np.where(np.isin(pcs, list(VAL_PIECES)), "val", "train")
    for k, v in (("crops", zp["crops"]), ("labels", zp["labels"]), ("source", np.array(["real_schott"] * len(pcs))), ("split", spl),
                 ("group", np.array(["schott-etudes-" + p for p in pcs])), ("page", zp["page"])):
        sch[k].append(v)
    for name, s in (("schott-concerto1", "train"), ("schott-concerto2", "train"), ("schott-concert-etudes", "val")):
        z = load(name); n = len(z["labels"])
        for k, v in (("crops", z["crops"]), ("labels", z["labels"]), ("source", np.array(["real_schott"] * n)), ("split", np.array([s] * n)),
                     ("group", np.array([name] * n)), ("page", z["page"])):
            sch[k].append(v)
    sch = {k: np.concatenate(v) for k, v in sch.items()}
    assert not any(("mazeppa" in g or "te5" in g) for g in sch["group"])
    print("schott train", int((sch["split"] == "train").sum()), "val", int((sch["split"] == "val").sum()))
    # ---- Schott-guided variations
    var = {k: [] for k in base}
    pv, sv = set(b["group"][(b["source"] == "real_piano") & (b["split"] == "val")]), set(b["group"][(b["source"] == "real_song") & (b["split"] == "val")])
    report = {}
    for vdir, mode, src in ((f"{RB}/vary2", "piano", "extract"), (f"{RB}/vary2_song", "song", "extract_songs")):
        for f in sorted(glob.glob(f"{vdir}/*.npz")):
            name = os.path.basename(f)[:-4]; vol = name.split("__")[0]
            z = np.load(f)
            if "crops" not in z or vol in pv or vol in sv or vol.startswith("lieder-IMSLP511856"):
                continue
            base_z = np.load(f"{RB}/{src}/{name.rsplit('_v', 1)[0]}.npz")
            if len(base_z["top"]) != len(z["top"]):
                report["staff count changed"] = report.get("staff count changed", 0) + 1; continue
            lab, why = L.label_page(z, mode, check_connectors=False)
            if lab is None:
                report[why] = report.get(why, 0) + 1; continue
            # the labels must be those of the original page (same pairs order)
            n = len(lab)
            for k, v in (("crops", z["crops"]), ("labels", lab), ("source", np.array(["varied_s"] * n)), ("split", np.array(["train"] * n)),
                         ("group", np.array([vol] * n)), ("page", np.array([name] * n))):
                var[k].append(v)
    var = {k: np.concatenate(v) for k, v in var.items()}
    print("varied_s", len(var["labels"]), np.bincount(var["labels"], minlength=3), report)

    def save(name, parts):
        d = {k: np.concatenate([p[k] for p in parts]) for k in base}
        np.savez(f"{out}/{name}.npz", **d)
        s, sp, l = d["source"], d["split"], d["labels"]
        print(name, len(l))
        for a in sorted(set(s)):
            for c in ("train", "val"):
                m = (s == a) & (sp == c)
                if m.sum(): print("   ", a, c, int(m.sum()), np.bincount(l[m], minlength=3))
    save("mixture2_A", [base, cur])
    save("mixture2_B", [base, cur, sch])
    save("mixture2_C", [base, cur, sch, var])


if __name__ == "__main__":
    main()
