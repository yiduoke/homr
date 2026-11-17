"""(a) every new token file equals its run-1 file apart from the lift field; (b) lift distribution old vs new per source."""
import collections, json, os, sys
from multiprocessing import Pool
OUT = "/workspace/run2"


def src(t):
    for s in ("Lieder-main", "grandstaff", "musescore_octave"):
        if f"/datasets_meter/{s}/" in t:
            return s
    if "/datasets_meter/pdmx/hard/" in t:
        return "pdmx_hard"
    if "/datasets_meter/pdmx/" in t:
        return "pdmx"
    return "lilypond"


def one(new):
    old = "/workspace/" + new[len(OUT + "/tokens/"):]
    a = open(old).read().split("\n")
    b = open(new).read().split("\n")
    res = {"src": src(old), "bad": None, "old": collections.Counter(), "new": collections.Counter(), "chg": collections.Counter()}
    if len(a) != len(b):
        res["bad"] = "line count"
        return res
    for i, (x, y) in enumerate(zip(a, b)):
        px, py = x.split("&"), y.split("&")
        if len(px) != len(py):
            res["bad"] = f"line {i} parts"
            return res
        for p, q in zip(px, py):
            f, g = p.split(" "), q.split(" ")
            if len(f) != len(g):
                res["bad"] = f"line {i} fields"
                return res
            if len(f) == 6:
                lo, ln = f[2], g[2]
                f2, g2 = list(f), list(g)
                f2[2] = g2[2] = ""
                if f2 != g2:
                    res["bad"] = f"line {i}: {p} | {q}"
                    return res
                if f[0].startswith("note"):
                    res["old"][lo] += 1
                    res["new"][ln] += 1
                    res["chg"][f"{lo}->{ln}"] += 1
            elif p != q:
                res["bad"] = f"line {i}: {p} | {q}"
                return res
    return res


if __name__ == "__main__":
    files = []
    for d, _, fs in os.walk(f"{OUT}/tokens"):
        files += [f"{d}/{f}" for f in fs if f.endswith(".tokens")]
    tot = collections.defaultdict(lambda: {"files": 0, "bad": 0, "old": collections.Counter(), "new": collections.Counter(), "chg": collections.Counter()})
    bads = []
    with Pool(32) as p:
        for new, r in zip(files, p.imap(one, files, chunksize=64)):
            t = tot[r["src"]]
            t["files"] += 1
            if r["bad"]:
                t["bad"] += 1
                bads.append((new, r["bad"]))
            t["old"].update(r["old"]); t["new"].update(r["new"]); t["chg"].update(r["chg"])
    for s, t in sorted(tot.items()):
        n = sum(t["old"].values())
        print(s, "files", t["files"], "other-field differences", t["bad"], "notes", n)
        print("  old", {k: t["old"][k] for k in ("_", "#", "b", "N", "##", "bb")})
        print("  new", {k: t["new"][k] for k in ("_", "#", "b", "N", "##", "bb")})
    print("BAD", bads[:10], len(bads))
    json.dump({s: {k: (dict(v) if isinstance(v, collections.Counter) else v) for k, v in t.items()} for s, t in tot.items()}, open(f"{OUT}/verify_a_b.json", "w"), indent=1)
