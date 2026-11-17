"""Build run-2 lists from run-1 lists: same PNGs, same order, new token paths; drop lines without new tokens."""
import collections, json, os
OUT = "/workspace/run2"
names = ["run1_train", "run1_val", "holdout_real", "holdout_inserted"]
outname = {"run1_train": "run2_train", "run1_val": "run2_val", "holdout_real": "holdout_real", "holdout_inserted": "holdout_inserted"}


def source(png, tok):
    for s in ("Lieder-main", "grandstaff", "musescore_octave"):
        if f"/datasets_meter/{s}/" in tok:
            return s
    if "/datasets_meter/pdmx/hard/" in tok:
        return "pdmx_hard"
    if "/datasets_meter/pdmx/" in tok:
        return "pdmx"
    if "/datasets_meter/lilypond/" in tok:
        return "lilypond_round2" if "/datasets/lilypond_round2/" in png else "lilypond"
    return "other"


summary = {}
for n in names:
    cnt = collections.defaultdict(collections.Counter)
    out = []
    for ln in open(f"/workspace/run1/{n}.txt"):
        ln = ln.strip()
        if not ln:
            continue
        png, tok = ln.split(",")
        s = source(png, tok)
        cnt[s]["in"] += 1
        new = f"{OUT}/tokens/{tok[len('/workspace/'):]}"
        if os.path.exists(new):
            out.append(f"{png},{new}")
            cnt[s]["out"] += 1
        else:
            cnt[s]["dropped"] += 1
    with open(f"{OUT}/{outname[n]}.txt", "w") as f:
        f.write("\n".join(out) + "\n")
    summary[n] = {s: dict(c) for s, c in cnt.items()}
    summary[n]["_total"] = {k: sum(c[k] for c in cnt.values()) for k in ("in", "out", "dropped")}
json.dump(summary, open(f"{OUT}/lists_summary.json", "w"), indent=1)
print(json.dumps(summary, indent=1))
