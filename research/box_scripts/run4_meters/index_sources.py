"""Index the source MusicXML scores of the meter arm (bar level): meter, key, bar length check, flags.
usage: index_sources.py <out.jsonl> [shard k of n]
Sources = scores that have staffs in the run-3 lists (so they passed the test-set exclusions by composition):
  train pool: stems in cand_train_nooct_v3 + run2_train_excl_v3
  val pool:   stems in cand_val_v3 / run2_val_excl_v3 / cand_val_hard_v3 that are in no train list
The test exclusions are applied again here (hash and id lists) as a safety net.
Run with nice -n 19. Reads only.
"""
import collections
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

R3 = "/workspace/run3"
SRC_DIRS = {
    "pdmx": "/workspace/homr566/datasets/pdmx/rendered_scores",
    "pdmx_hard": "/workspace/homr566/datasets/pdmx/hard/rendered_scores",
    "Lieder-main": "/workspace/homr566/datasets/Lieder-main/rendered_scores",
    "asap": "/workspace/run3/ms_export/asap",
    "kern_scriabin": "/workspace/run3/ms_export/kern_scriabin",
}
VRV = re.compile(r"^(.*)-vrv-(\d+)-(\d+)$")
MS = re.compile(r"^(.*)-(\d+)-(\d+)$")


def stems_of(lists):
    out = collections.defaultdict(set)
    for lst in lists:
        for ln in open(lst):
            ln = ln.strip()
            if not ln:
                continue
            tok = ln.split(",")[1]
            if "/datasets_meter/" not in tok:
                continue
            parts = tok.split("/datasets_meter/")[1].split("/")
            sset = parts[0]
            if sset == "pdmx" and parts[1] == "hard":
                sset = "pdmx_hard"
            base = os.path.basename(tok)[: -len(".tokens")]
            m = VRV.match(base) or MS.match(base)
            if m and sset in SRC_DIRS:
                out[sset].add(m[1])
    return out


def pools():
    train = stems_of([f"{R3}/cand_train_nooct_v3.txt", f"{R3}/run2_train_excl_v3.txt"])
    val = stems_of([f"{R3}/cand_val_v3.txt", f"{R3}/run2_val_excl_v3.txt", f"{R3}/cand_val_hard_v3.txt"])
    excl = set()
    for fn in (f"{R3}/exclude_leak_hashes_v2.txt", "/workspace/exclude_hashes_v2.txt", f"{R3}/exclude_leak_hashes.txt"):
        if os.path.exists(fn):
            excl |= {ln.strip() for ln in open(fn) if ln.strip() and not ln.startswith("#")}
    ids = {ln.strip() for ln in open(f"{R3}/exclude_ids.txt") if ln.strip()}
    return train, val, excl, ids


def duration_of(measure):
    cursor = maxc = 0
    for el in measure:
        if el.tag == "note":
            if el.find("grace") is not None:
                continue
            if el.find("chord") is None:
                cursor += int(el.findtext("duration") or 0)
        elif el.tag == "backup":
            cursor -= int(el.findtext("duration") or 0)
        elif el.tag == "forward":
            cursor += int(el.findtext("duration") or 0)
        maxc = max(maxc, cursor)
    return maxc


def scan(path):
    root = ET.parse(path).getroot()
    res = {"parts": []}
    for part in root.findall("part"):
        divisions = None
        meter = None  # (beats, type, symbol, hidden)
        fifths = 0
        staves = 1
        clefs = {}
        measures = []
        for mi, m in enumerate(part.findall("measure")):
            info = {}
            for att in m.findall("attributes"):
                d = att.findtext("divisions")
                if d:
                    divisions = int(d)
                s = att.findtext("staves")
                if s:
                    staves = int(s)
                for c in att.findall("clef"):
                    clefs[c.get("number", "1")] = (c.findtext("sign"), c.findtext("line"))
                k = att.find("key")
                if k is not None and k.findtext("fifths") is not None:
                    fifths = int(k.findtext("fifths"))
                for t in att.findall("time"):
                    b, bt = t.findtext("beats"), t.findtext("beat-type")
                    if b is None or bt is None:
                        continue
                    hidden = t.get("print-object") == "no"
                    meter = (b, bt, t.get("symbol") or "", hidden)
                    info["time_here"] = True
            dur = duration_of(m)
            ok = None
            if meter and divisions and re.fullmatch(r"\d+", meter[0]) and re.fullmatch(r"\d+", meter[1]):
                exp = int(meter[0]) * 4 * divisions / int(meter[1])
                ok = abs(dur - exp) < 1e-6
            types = [n.findtext("type") for n in m.findall("note")]
            info.update(
                n=m.get("number"), meter=None if meter is None else f"{meter[0]}/{meter[1]}",
                sym=None if meter is None else meter[2], hidden=bool(meter and meter[3]),
                fifths=fifths, ok=ok, implicit=m.get("implicit") == "yes",
                octave=m.find(".//octave-shift") is not None,
                mmrest=m.find(".//multiple-rest") is not None,
                tuplet=m.find(".//time-modification") is not None,
                notes=sum(1 for n in m.findall("note") if n.find("rest") is None),
                short=sum(1 for t in types if t in ("32nd", "64th", "128th", "256th")),
                breve=sum(1 for t in types if t in ("breve", "long")),
                lyrics=m.find(".//lyric") is not None,
            )
            measures.append(info)
        res["parts"].append(
            dict(id=part.get("id"), staves=staves, divisions=divisions, clefs=[clefs.get(str(i + 1)) for i in range(staves)],
                 transpose=part.find(".//transpose") is not None, measures=measures)
        )
    res["n_parts"] = len(res["parts"])
    return res


def main():
    out = sys.argv[1]
    k, n = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
    train, val, excl, ids = pools()
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from mine_meters import load_pdmx  # noqa: PLC0415

    pdmx_meta = load_pdmx()  # hash -> (composer, musescore id, title)
    todo = []
    for sset, d in SRC_DIRS.items():
        for pool_name, pool in (("train", train), ("val", val)):
            for stem in sorted(pool.get(sset, ())):
                if pool_name == "val" and stem in train.get(sset, ()):
                    continue
                if stem in excl:
                    continue
                if sset in ("pdmx", "pdmx_hard") and pdmx_meta.get(stem, ("", "", ""))[1] in ids:
                    continue
                path = f"{d}/{stem}.musicxml"
                if os.path.exists(path):
                    todo.append((sset, pool_name, stem, path))
    todo = todo[k::n]
    print("todo", len(todo), "excluded hashes", len(excl), flush=True)
    with open(out, "w") as f:
        for i, (sset, pool_name, stem, path) in enumerate(todo):
            try:
                r = scan(path)
            except Exception as e:  # noqa: BLE001
                r = {"error": repr(e)[:100], "parts": []}
            r.update(set=sset, pool=pool_name, stem=stem, path=path)
            f.write(json.dumps(r) + "\n")
            if i % 500 == 0:
                print(i, len(todo), flush=True)
                f.flush()


if __name__ == "__main__":
    main()
