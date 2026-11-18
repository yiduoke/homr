"""D31 diagnosis: for every page of Petrushka in the three runs (control, realbrace-2, realbrace-3): staves per system (replay of the pairing, brace_models/replay_all.json),
the staves and parts of the saved page XML (music21 part ids, clef, bars, notes, median pitch) and where the D24 merger and the slot tracker put them.
usage: python merge_tracking_diagnose.py [piece]  -> merge_tracking/diagnose_<piece>.md (all pages) and stdout of the 8 representative pages"""
import glob
import json
import os
import re
import sys
import warnings
from collections import Counter

warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/yiduoke/Documents/homr/run/merge2_wt")
from music21 import clef as m21clef  # noqa: E402
from music21 import converter  # noqa: E402
from slot_tracking import SlotTracker, StaffProfile  # noqa: E402

E = "/Users/yiduoke/Documents/homr/run/eval_run1"
TAGS = {"ctl": "shipped_merge_role_gpu", "rb2": "relbrace2_gpu", "rb3": "relbrace3_gpu"}
MODEL = {"ctl": "shipped", "rb2": "rb2", "rb3": "rb3"}
piece = sys.argv[1] if len(sys.argv) > 1 else "stravinsky-petrushka"
replay = json.load(open(f"{E}/brace_models/replay_all.json")).get(piece, {})


def staves_of(path):
    s = converter.parse(path, forceSource=True)
    out = []
    for p in s.parts:
        cl = p.recurse().getElementsByClass(m21clef.Clef)
        sign = getattr(cl[0], "sign", None) if len(cl) else None
        pit = Counter(round(x.ps) for n in p.recurse().notes for x in n.pitches)
        total = sum(pit.values())
        med = None
        if total:
            seen = 0
            for k in sorted(pit):
                seen += pit[k]
                if 2 * seen >= total:
                    med = k
                    break
        out.append({"id": p.id, "clef": sign, "bars": len(list(p.getElementsByClass("Measure"))), "notes": total, "med": med, "profile": StaffProfile(sign, pit)})
    return out


def d24_stack(ids):
    """staff_stack() of the D24 merger: None unless the page is one uniform stack of k >= 2 staves."""
    if len(ids) < 2:
        return None
    if len(set(ids)) == 1:
        return list(range(len(ids)))
    m = [re.fullmatch(r"(.+)-Staff(\d+)", i) for i in ids]
    if all(m) and len({x.group(1) for x in m}) == 1 and [int(x.group(2)) for x in m] == list(range(1, len(ids) + 1)):
        return list(range(len(ids)))
    return None


def d24_roles(ids):
    """The D24 rule: a page which is one uniform stack gets the key of its role, any other page is matched by id."""
    if len(ids) >= 2 and (len(set(ids)) == 1 or (all(re.fullmatch(r".+-Staff\d+", i) for i in ids) and len({i.rsplit("-Staff", 1)[0] for i in ids}) == 1)):
        return "stack"
    return "by id"


rows = {}
d24_parts = {}  # run -> part key -> [pages, bars]
for k, tag in TAGS.items():
    tracker = SlotTracker()
    role_key = {}
    d24_parts[k] = {}
    for f in sorted(glob.glob(f"{E}/testset/{tag}/{piece}/page-xml/page-*.musicxml")):
        pg = os.path.basename(f)[5:-9]
        st = staves_of(f)
        keys, seen = [], {}
        for s in st:
            seen[s["id"]] = seen.get(s["id"], 0) + 1
            keys.append(s["id"] if seen[s["id"]] == 1 else f"{s['id']}#{seen[s['id']]}")
        roles = d24_stack([s["id"] for s in st])
        d24_keys = []
        for n, key in enumerate(keys):
            if roles is not None:
                key = role_key.setdefault((len(roles), roles[n]), key)
            d24_keys.append(key)
            e = d24_parts[k].setdefault(key, [0, 0])
            e[0] += 1
            e[1] += st[n]["bars"]
        res = tracker.assign([s["profile"] for s in st], keys)
        names = {slot.key: n for n, slot in enumerate(tracker.slots)}
        sys_ = replay.get(f"page-{pg.zfill(2) if len(pg) < 3 else pg}", {}).get("models", {}).get(MODEL[k], {}).get("repaired")
        per_system = [n + sum(fl) for n, fl in sys_] if sys_ else None
        rows.setdefault(pg, {})[k] = {"staves": st, "slots": [names[slot.key] for slot, _ in res], "n_slots": len(tracker.slots), "per_system": per_system, "role": d24_roles([s["id"] for s in st]), "d24": d24_keys}

summary = ["", "D24 merger: parts after the merge (key: pages, bars)", ""]
for k in TAGS:
    longest = max(v[1] for v in d24_parts[k].values())
    summary.append(f"* {k}: " + "; ".join(f"{key[:12]}: {v[0]} staves, {v[1]} bars" + (" (dropped, < 50 %)" if v[1] < 0.5 * longest else "") for key, v in d24_parts[k].items()))
lines = ["| page | run | staves per system (replay) | page XML staves: part id, clef, bars/notes, median | D24 | slot of each staff (K slots so far) |", "|---|---|---|---|---|---|"]
for pg, r in sorted(rows.items()):
    for k in TAGS:
        x = r[k]
        desc = "; ".join(f"{s['id'][:9]} {s['clef']} {s['bars']}/{s['notes']} m{s['med']}" for s in x["staves"])
        lines.append(f"| {pg} | {k} | {x['per_system']} | {desc} | {x['role']} {[d[:12] for d in x['d24']]} | {x['slots']} (K={x['n_slots']}) |")
os.makedirs(f"{E}/merge_tracking", exist_ok=True)
open(f"{E}/merge_tracking/diagnose_{piece}.md", "w").write("\n".join(lines + summary) + "\n")
print("\n".join(summary))
print("\n".join(l for l in lines if re.match(r"\| (07|09|10|11|13|16|23|32|33|35) ", l)))
