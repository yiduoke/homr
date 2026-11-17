"""Mine the training staffs for time signatures (step 1 of the meter arm).
usage: mine_meters.py <out.json> list1.txt [list2.txt ...]    (lines "image.png,tokens.tokens")
For every staff: the time signature at the start of the staff, every mid-staff change (a timeSignature
line after the first note/rest/barline line), the staff space from the crop json, set, score stem, composer.
Also: a system-start signature "after a change" = a start signature different from the last meter seen
earlier in the same score (staffs of a score ordered by system/page and part).
Run with nice -n 19. Reads only.
"""
import collections
import csv
import json
import os
import re
import statistics
import sys

PDMX_CSV = "/workspace/homr566/datasets/pdmx/PDMX.csv"
LIEDER = "/workspace/homr566/datasets/Lieder-main/scores"
VRV = re.compile(r"^(.*)-vrv-(\d+)-(\d+)$")
MS = re.compile(r"^(.*)-(\d+)-(\d+)$")


def load_pdmx():
    out = {}
    csv.field_size_limit(10**9)
    with open(PDMX_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            h = row["mxl"].rsplit("/", 1)[-1][:-4]
            c = row.get("composer_name") or "NA"
            if c in ("NA", ""):
                c = row.get("artist_name") or "NA"
            out[h] = (c.strip().lower(), os.path.basename(row["metadata"])[:-5], row.get("title", ""))
    return out


def load_lieder():
    out = {}
    for root, _d, files in os.walk(LIEDER):
        for fn in files:
            if fn.endswith(".mscx"):
                out[fn[:-5]] = os.path.relpath(root, LIEDER).split(os.sep)[0].lower()
    return out


def parse_name(path):
    """set, stem, (a, b) sort key from a token path."""
    rest = path.split("/datasets_meter/", 1)[1]
    parts = rest.split("/")
    sset = parts[0]
    if sset == "pdmx" and parts[1] == "hard":
        sset = "pdmx_hard"
    base = os.path.basename(path)[: -len(".tokens")]
    m = VRV.match(base)
    if m:
        return sset, m[1], (int(m[2]), int(m[3])), parts
    m = MS.match(base)
    if m:
        return sset, m[1], (int(m[2]), int(m[3])), parts
    return sset, base, (0, 0), parts


def analyse(text):
    lines = text.split("\n")
    start = None
    mids = []
    seen_content = False
    for ln in lines:
        toks = [t.strip().split(" ")[0] for t in ln.split("&")]
        first = toks[0] if toks else ""
        ts = [t for t in toks if t.startswith("timeSignature")]
        if ts:
            sig = ts[0][len("timeSignature_"):]
            if not seen_content and start is None:
                start = sig
            else:
                mids.append(sig)
            continue
        if first.startswith(("note", "rest", "barline", "doublebarline", "repeat", "bold", "final")) or "barline" in first:
            seen_content = True
    return start, mids


def main():
    out_path, lists = sys.argv[1], sys.argv[2:]
    pdmx = load_pdmx()
    lieder = load_lieder()
    staffs = []
    seen = set()
    missing = 0
    for lst in lists:
        for ln in open(lst):
            ln = ln.strip()
            if not ln:
                continue
            img, tok = ln.split(",", 1)
            if tok in seen:
                continue
            seen.add(tok)
            try:
                text = open(tok).read()
            except OSError:
                missing += 1
                continue
            sset, stem, key, parts = parse_name(tok)
            if sset == "grandstaff":
                stem = "/".join(parts[1:-2]) if len(parts) > 3 else stem
            start, mids = analyse(text)
            try:
                crop = json.load(open(img[:-4] + ".json")) if os.path.exists(img[:-4] + ".json") else None
            except Exception:
                crop = None
            ss = crop["staff_space"] if crop else None
            if sset in ("pdmx", "pdmx_hard"):
                comp = pdmx.get(stem[:46].split("-")[0], ("unknown",))[0]
            elif sset == "Lieder-main":
                comp = lieder.get(stem, "unknown")
            elif sset == "asap":
                comp = stem.split("_")[0].lower()
            elif sset == "kern_scriabin":
                comp = "scriabin"
            elif sset == "grandstaff":
                comp = parts[1] if len(parts) > 1 else "unknown"
            else:
                comp = "unknown"
            staffs.append(dict(set=sset, stem=stem, key=key, start=start, mids=mids, ss=ss, comp=comp, tok=tok))
    print("staffs", len(staffs), flush=True)

    # system-start signature after a change
    by_score = collections.defaultdict(list)
    for s in staffs:
        by_score[(s["set"], s["stem"])].append(s)
    for sc, lst in by_score.items():
        lst.sort(key=lambda s: s["key"])
        cur = None
        for s in lst:
            s["after_change"] = False
            if s["start"] is not None:
                if cur is not None and s["start"] != cur:
                    s["after_change"] = True
                cur = s["start"]
            if s["mids"]:
                cur = s["mids"][-1]

    res = {"n_staffs": len(staffs)}
    res["with_start"] = sum(1 for s in staffs if s["start"])
    res["with_mid"] = sum(1 for s in staffs if s["mids"])
    res["with_any"] = sum(1 for s in staffs if s["start"] or s["mids"])
    res["after_change"] = sum(1 for s in staffs if s["after_change"])
    res["mid_or_after_change"] = sum(1 for s in staffs if s["mids"] or s["after_change"])
    res["by_set"] = {}
    for sset in sorted({s["set"] for s in staffs}):
        sub = [s for s in staffs if s["set"] == sset]
        res["by_set"][sset] = dict(
            staffs=len(sub),
            with_any=sum(1 for s in sub if s["start"] or s["mids"]),
            with_mid=sum(1 for s in sub if s["mids"]),
            after_change=sum(1 for s in sub if s["after_change"]),
            scores=len({s["stem"] for s in sub}),
            staff_space_median=statistics.median([s["ss"] for s in sub if s["ss"]] or [0]),
        )
    meters = collections.defaultdict(lambda: dict(start=0, mid_to=0, staffs=0, scores=set(), composers=set(), ss=[], scores_start=set(), scores_mid=set()))
    pairs = collections.defaultdict(lambda: dict(staffs=0, scores=set(), composers=set(), sets=collections.Counter()))
    for s in staffs:
        seen_m = set()
        prev = s["start"]
        if s["start"]:
            m = meters[s["start"]]
            m["start"] += 1
            m["scores_start"].add((s["set"], s["stem"]))
            seen_m.add(s["start"])
        for new in s["mids"]:
            m = meters[new]
            m["mid_to"] += 1
            m["scores_mid"].add((s["set"], s["stem"]))
            seen_m.add(new)
            p = pairs[f"{prev or '?'}->{new}"]
            p["staffs"] += 1
            p["scores"].add((s["set"], s["stem"]))
            p["composers"].add(s["comp"])
            p["sets"][s["set"]] += 1
            prev = new
        for mm in seen_m:
            m = meters[mm]
            m["staffs"] += 1
            m["scores"].add((s["set"], s["stem"]))
            m["composers"].add(s["comp"])
            if s["ss"]:
                m["ss"].append(s["ss"])
    res["meters"] = {}
    for k, m in meters.items():
        ss = m["ss"] or [0]
        res["meters"][k] = dict(
            staffs=m["staffs"], start=m["start"], mid_to=m["mid_to"], scores=len(m["scores"]),
            composers=len(m["composers"]), ss_median=round(statistics.median(ss), 2),
            ss_min=round(min(ss), 2), ss_max=round(max(ss), 2),
        )
    res["pairs"] = {
        k: dict(staffs=p["staffs"], scores=len(p["scores"]), composers=len(p["composers"]), sets=dict(p["sets"]))
        for k, p in sorted(pairs.items(), key=lambda kv: -kv[1]["staffs"])
    }
    sss = sorted(s["ss"] for s in staffs if s["ss"])
    res["ss_all"] = dict(
        n=len(sss), median=round(statistics.median(sss), 2),
        p5=round(sss[int(0.05 * len(sss))], 2), p95=round(sss[int(0.95 * len(sss))], 2),
    )
    res["n_missing_tokens"] = missing
    json.dump(res, open(out_path, "w"), indent=1)
    # keep the per-staff records for later composing
    json.dump(
        [dict(set=s["set"], stem=s["stem"], start=s["start"], mids=s["mids"], ss=s["ss"], comp=s["comp"],
              after_change=s["after_change"], tok=s["tok"]) for s in staffs],
        open(out_path.replace(".json", "_staffs.json"), "w"),
    )
    print("done")


if __name__ == "__main__":
    main()
