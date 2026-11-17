"""Octave brackets per system and direction on the red-pen-marked real pages.

    python run/system_eval.py --build            # derive run/scores/real/system_counts.csv
    python run/system_eval.py [label ...]        # score cached MusicXML per system

real_eval.py compares counts per page, so a bracket found in the wrong system hides
behind a miss elsewhere on the same page. Here a page is cut into systems (one line of
piano music, with any ossia staff) and every system is scored on its own, separately
for 8va and 8vb: correct = min(found, printed), misses = printed - correct,
false marks = found - correct. A bracket found one system off is one miss and one
false mark. The old per-page numbers are printed next to it.

Printed brackets per system (--build):
  * A pianist drew a red loop around each printed bracket on copies of four PDFs
    (run/scores/marked). Each page is rendered at 150 dpi like the test PNG, red ink
    (R>190, G<90, B<90) is dilated so a loop drawn in two strokes stays one mark, and
    every connected red component is one mark.
  * Systems come from homr's own staff detection and system grouping (the octave
    worktree, segmentation only, no transformer), so the system order is the order of
    <print new-system="yes"/> in homr's MusicXML. The scorer checks that the counts agree.
  * A mark goes to the system its centre lies in. Centre above the middle line of the
    system's first staff or between two staves: 8va. Below the middle line of the last
    staff: 8vb. In the gap between two systems: 8va of the system below (an 8vb under
    the system above can't be told apart by position; those are hand-fixed).
  * The pianist missed some brackets and a few loops touch. Where the red count differs
    from verified_counts.csv the page is listed and fixed by hand in CORRECTIONS below,
    each entry checked by eye; per-page totals then equal verified_counts.csv.

The derived counts are written to run/scores/real/system_counts.csv with the system
positions and the mark boxes, so they can be checked by hand.
"""

import csv
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = "/Users/yiduoke/Documents/homr"
WORKTREE = f"{ROOT}/run/octave_wt"
PYTHON = f"{ROOT}/.venv/bin/python"
REAL = f"{ROOT}/run/scores/real"
MARKED = f"{ROOT}/run/scores/marked"
OUT = f"{ROOT}/run/models/octave/real_eval"
COUNTS = f"{REAL}/system_counts.csv"
CACHE = "/private/tmp/claude-501/sysscore"  # renders, page copies, detected systems
LABELS = [
    "round3-checkpoint-3463-cropfix",
    "round4-checkpoint-4077-cropfix",
    "round5-checkpoint-4096-cropfix",
]
# png prefix -> marked PDF
PIECES = {
    "mussorgsky-pictures-bessel": "mussorgsky-pictures-bessel.pdf",
    "ravel-jeuxdeau-schott": "ravel-jeuxdeau-schott.pdf",
    "liszt-hungarian-rhapsody2-senff": "user-liszt-hungarian-rhapsody2.pdf",
    "liszt-mazeppa-russian": "liszt-mazeppa.pdf",
}
# Hand fixes where the red marks don't give verified_counts.csv: png -> list of
# (system 1-based, "va"/"vb", change, reason). Every entry checked on the page image.
CORRECTIONS: dict[str, list[tuple[int, str, int, str]]] = {
    "liszt-hungarian-rhapsody2-senff-p007.png": [
        (4, "va", 2, "two brackets between the staves not circled"),
    ],
    "liszt-hungarian-rhapsody2-senff-p011.png": [(1, "va", 1, "8 ... loco at the start not circled")],
    "liszt-hungarian-rhapsody2-senff-p015.png": [(1, "va", 1, "8 ... loco at the start not circled")],
    "mussorgsky-pictures-bessel-p016.png": [
        (1, "va", 1, "two touching loops read as one"),
        (2, "va", 1, "two touching loops read as one"),
    ],
    "mussorgsky-pictures-bessel-p034.png": [
        (2, "va", 5, "five one-chord brackets not circled"),
        (3, "va", 2, "two pairs of touching loops read as two marks"),
    ],
    "ravel-jeuxdeau-schott-p013.png": [(4, "va", 1, "bracket over the lower staff not circled")],
    "ravel-jeuxdeau-schott-p014.png": [
        (4, "va", 1, "bracket over the lower staff not circled"),
        (5, "va", -1, "this loop is the 8vb under system 4"),
        (4, "vb", 1, "8vb under the lower staff, loop lies in the gap"),
    ],
    "ravel-jeuxdeau-schott-p015.png": [
        (3, "va", -1, "this loop is the 8vb under system 2"),
        (2, "vb", 1, "8vb under the lower staff, loop lies in the gap"),
    ],
    "ravel-jeuxdeau-schott-p016.png": [(2, "va", 1, "bracket over the upper staff at the right not circled")],
    "ravel-jeuxdeau-schott-p017.png": [(1, "va", 2, "two brackets over the lower staff not circled")],
}


def _pages() -> list[str]:
    return sorted(
        f for f in os.listdir(REAL) if f.endswith(".png") and any(f.startswith(p + "-p") for p in PIECES)
    )


def _piece(png: str) -> str:
    return next(p for p in PIECES if png.startswith(p + "-p"))


def _verified() -> dict[str, tuple[int, int]]:
    with open(f"{REAL}/verified_counts.csv") as f:
        return {r["png"]: (int(r["n_8va"]), int(r["n_8vb"])) for r in csv.DictReader(f)}


# ---------------------------------------------------------------- build the truth


def _detect_systems_in_worktree(out_path: str, pages: list[str]) -> None:
    """Runs inside WORKTREE: homr staff detection + system grouping, no transformer."""
    import shutil

    import numpy as np

    sys.path.insert(0, os.getcwd())
    from homr import staff_parsing
    from homr.main import ProcessingConfig, detect_staffs_in_image
    from homr.system_repair import repair_systems

    result = json.load(open(out_path)) if os.path.exists(out_path) else {}
    os.makedirs(f"{CACHE}/work", exist_ok=True)
    for page in pages:
        name = os.path.basename(page)
        if name in result:
            continue
        local = f"{CACHE}/work/{name}"
        shutil.copy(page, local)
        # debug, cache, write/read staff positions, selected staff, transformer gpu,
        # segnet gpu (CoreML, as homr picks on a Mac), coreml encoder, title
        config = ProcessingConfig(False, False, False, False, -1, False, True, False, False)
        multi, _image, debug, _title, _n, to_input = detect_staffs_in_image(local, config)
        multi = repair_systems(debug, multi)
        mode = "normal"
        # Same as parse_staffs(): if the layout can't be matched, every staff is a system
        if len({len(s.staffs) for s in multi}) > 1:
            if staff_parsing._assign_parts(multi) is None:  # noqa: SLF001
                multi = [single for s in multi for single in s.break_apart()]
                mode = "broken_apart"
            else:
                mode = "assigned"
        systems = []
        for s in multi:
            staves = []
            for st in s.staffs:
                lines = np.median(np.array([p.y for p in st.grid]), axis=0)
                for k in range(0, len(lines), 5):  # a grand staff has 10 lines
                    x0, top = to_input((st.min_x, float(lines[k])))
                    x1, bottom = to_input((st.max_x, float(lines[k + 4])))
                    staves.append({"top": round(top, 1), "bottom": round(bottom, 1),
                                   "x0": round(x0, 1), "x1": round(x1, 1)})
            systems.append(sorted(staves, key=lambda t: t["top"]))
        result[name] = {"mode": mode, "systems": systems}
        print(name, mode, [len(s) for s in systems], flush=True)
        with open(out_path, "w") as f:
            json.dump(result, f, indent=1)


def _render_marked(png: str) -> str:
    out = f"{CACHE}/marked/{png}"
    if not os.path.exists(out):
        os.makedirs(f"{CACHE}/marked", exist_ok=True)
        page = int(png.split("-p")[-1].split("-")[0].split(".")[0])
        subprocess.run(  # noqa: S603
            ["pdftoppm", "-r", "150", "-f", str(page), "-l", str(page), "-singlefile", "-png",
             f"{MARKED}/{PIECES[_piece(png)]}", out[: -len(".png")]],
            check=True,
        )
    return out


def _red_marks(path: str) -> list[tuple[int, int, int, int]]:
    """Boxes (x, y, w, h) of the red loops."""
    import cv2
    import numpy as np

    im = cv2.imread(path).astype(int)
    b, g, r = im[:, :, 0], im[:, :, 1], im[:, :, 2]
    red = ((r > 190) & (g < 90) & (b < 90)).astype(np.uint8)
    red = cv2.dilate(red, np.ones((15, 15), np.uint8))
    n, _labels, stats, _ = cv2.connectedComponentsWithStats(red)
    return sorted(
        (int(x), int(y), int(w), int(h)) for x, y, w, h, _a in stats[1:n] if max(w, h) >= 40
    )


def _assign(mark: tuple[int, int, int, int], systems: list[list[dict]]) -> tuple[int, str, str]:
    """(system index, 'va'/'vb', remark) for one red mark."""
    x, y, w, h = mark
    cy = y + h / 2
    tops = [s[0]["top"] for s in systems]
    bottoms = [max(t["bottom"] for t in s) for s in systems]
    remark = ""
    if h > 5 * max(t["bottom"] - t["top"] for s in systems for t in s):
        remark = "tall mark, may enclose two brackets"
    if cy < tops[0]:
        return 0, "va", remark
    if cy > bottoms[-1]:
        return len(systems) - 1, "vb", remark
    for i, (top, bottom) in enumerate(zip(tops, bottoms, strict=True)):
        if top <= cy <= bottom:
            # staves of the system under the mark (an ossia staff is narrower)
            staves = [t for t in systems[i] if t["x0"] < x + w and t["x1"] > x] or systems[i]
            first, last = staves[0], staves[-1]
            if cy < (first["top"] + first["bottom"]) / 2:
                return i, "va", remark
            if cy > (last["top"] + last["bottom"]) / 2:
                return i, "vb", remark
            return i, "va", remark  # between two staves: 8va over the lower one
        if i + 1 < len(systems) and bottom < cy < tops[i + 1]:
            # The loop's centre doesn't tell an 8vb under this system from an 8va over
            # the next (checked on these pages), 8va is far more common
            return i + 1, "va", remark
    raise AssertionError("unreachable")


def build() -> None:
    pages = _pages()
    detected = f"{CACHE}/systems.json"
    missing = [p for p in pages if not os.path.exists(detected) or p not in json.load(open(detected))]
    if missing:
        subprocess.run(  # noqa: S603
            [PYTHON, os.path.abspath(__file__), "--detect", detected] + [f"{REAL}/{p}" for p in missing],
            cwd=WORKTREE, check=True,
        )
    with open(detected) as f:
        systems_of = json.load(f)
    verified = _verified()
    rows = []
    disagree = []
    for png in pages:
        info = systems_of[png]
        systems = info["systems"]
        counts = [{"va": 0, "vb": 0, "marks": [], "notes": []} for _ in systems]
        for mark in _red_marks(_render_marked(png)):
            i, kind, remark = _assign(mark, systems)
            counts[i][kind] += 1
            counts[i]["marks"].append("{},{},{},{}:{}".format(*mark, kind))
            if remark:
                counts[i]["notes"].append(remark)
        red = (sum(c["va"] for c in counts), sum(c["vb"] for c in counts))
        want = verified.get(png, (0, 0))
        if red != want:
            disagree.append((png, red, want))
        for system, kind, change, reason in CORRECTIONS.get(png, []):
            counts[system - 1][kind] += change
            counts[system - 1]["notes"].append(f"hand fix {kind} {change:+d}: {reason}")
        fixed = (sum(c["va"] for c in counts), sum(c["vb"] for c in counts))
        for i, (staves, c) in enumerate(zip(systems, counts, strict=True)):
            rows.append(
                {
                    "png": png,
                    "system": i + 1,
                    "y_top": round(staves[0]["top"]),
                    "y_bottom": round(max(t["bottom"] for t in staves)),
                    "staves": len(staves),
                    "n_8va": c["va"],
                    "n_8vb": c["vb"],
                    "red_marks": ";".join(c["marks"]),
                    "note": "; ".join(c["notes"]),
                    "page_check": "ok" if fixed == want else f"page total {fixed} != verified {want}",
                }
            )
    with open(COUNTS, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} systems of {len(pages)} pages to {COUNTS}")
    print("pages where the red marks (8va, 8vb) disagree with verified_counts.csv:")
    for png, red, want in disagree:
        print(f"  {png}: red {red}, verified {want}" + ("  (hand-fixed)" if png in CORRECTIONS else ""))
    broken = [r for r in rows if r["page_check"] != "ok"]
    if broken:
        print("STILL OFF after hand fixes:", sorted({r["png"] for r in broken}))


# ---------------------------------------------------------------- score


def _found_per_system(xml_path: str) -> list[dict[str, int]]:
    """8va/8vb starts per system, summed over the parts (ossia staves are extra parts)."""
    root = ET.parse(xml_path).getroot()
    per_part = []
    for part in root.findall("part"):
        systems = [{"va": 0, "vb": 0}]
        for measure in part.findall("measure"):
            for el in measure.iter():  # document order, a print may follow a direction
                if el.tag == "print" and el.get("new-system") == "yes":
                    systems.append({"va": 0, "vb": 0})
                elif el.tag == "octave-shift" and el.get("type") in ("down", "up"):
                    # MusicXML: "down" = notes written an octave down = 8va
                    systems[-1]["va" if el.get("type") == "down" else "vb"] += 1
        per_part.append(systems)
    n = max(len(p) for p in per_part)
    if any(len(p) != n for p in per_part):
        raise ValueError(f"parts disagree on the number of systems: {[len(p) for p in per_part]}")
    return [{k: sum(p[i][k] for p in per_part) for k in ("va", "vb")} for i in range(n)]


def score(labels: list[str]) -> None:
    truth: dict[str, list[dict[str, int]]] = {}
    with open(COUNTS) as f:
        for r in csv.DictReader(f):
            truth.setdefault(r["png"], []).append({"va": int(r["n_8va"]), "vb": int(r["n_8vb"])})
    keys = ("printed", "found", "correct", "misses", "false", "p_correct", "p_misses", "p_false")
    overall = {}
    for label in labels:
        totals: dict[str, dict[str, int]] = {}
        skipped = []
        for png, printed in truth.items():
            xml_path = f"{OUT}/{label}/{png.replace('.png', '.musicxml')}"
            if not os.path.exists(xml_path):
                skipped.append(png + " (no MusicXML)")
                continue
            found = _found_per_system(xml_path)
            if len(found) != len(printed):
                skipped.append(f"{png} ({len(found)} systems in MusicXML, {len(printed)} on the page)")
                continue
            t = totals.setdefault(_piece(png), dict.fromkeys(keys, 0))
            for kind in ("va", "vb"):
                for f_sys, p_sys in zip(found, printed, strict=True):
                    ok = min(f_sys[kind], p_sys[kind])
                    t["correct"] += ok
                    t["misses"] += p_sys[kind] - ok
                    t["false"] += f_sys[kind] - ok
                    t["printed"] += p_sys[kind]
                    t["found"] += f_sys[kind]
                # the old per-page score of real_eval.py
                f_page = sum(s[kind] for s in found)
                p_page = sum(s[kind] for s in printed)
                t["p_correct"] += min(f_page, p_page)
                t["p_misses"] += p_page - min(f_page, p_page)
                t["p_false"] += f_page - min(f_page, p_page)
        total = {k: sum(t[k] for t in totals.values()) for k in keys}
        overall[label] = total
        print(f"\n{label}")
        print(f"  {'piece':34} {'printed':>7} {'found':>5} | per system: {'correct':>7} {'misses':>6}"
              f" {'false':>5} | per page: {'correct':>7} {'misses':>6} {'false':>5}")
        for name, t in [*sorted(totals.items()), ("all four pieces", total)]:
            print(f"  {name:34} {t['printed']:7} {t['found']:5} |             {t['correct']:7}"
                  f" {t['misses']:6} {t['false']:5} |           {t['p_correct']:7} {t['p_misses']:6}"
                  f" {t['p_false']:5}")
        for s in skipped:
            print("  skipped:", s)
    if len(labels) > 1:
        print("\nAll four pieces: per system correct / misses / false (per page in brackets)")
        for label, t in overall.items():
            print(f"  {label:34} {t['correct']:3} / {t['misses']:3} / {t['false']:3}"
                  f"   ({t['p_correct']} / {t['p_misses']} / {t['p_false']})  of {t['printed']} printed")


if __name__ == "__main__":
    if sys.argv[1:2] == ["--detect"]:
        _detect_systems_in_worktree(sys.argv[2], sys.argv[3:])
    elif sys.argv[1:2] == ["--build"]:
        build()
    else:
        score(sys.argv[1:] or LABELS)
