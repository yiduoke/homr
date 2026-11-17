"""Octave marks a model finds on real pages (never used for training).

    python run/real_eval.py <dir with encoder_*.onnx and decoder_*.onnx> [label]

Runs the full homr pipeline (octave-branch checkout in run/octave_wt) on fixed pages and
counts the <octave-shift> elements in the MusicXML it writes, page by page.

Scoring is per page, because a total hides a miss on one page behind a false alarm on
another: for each page, hits = min(found, printed) and extras = max(0, found - printed),
separately for marks above the staff (8va) and below it (8vb). It still does not check
*where* on the page a mark was found.

Printed counts come from, in order of trust:
  1. run/scores/real/verified_counts.csv  (png,n_8va,n_8vb) - checked by eye, zoomed in
  2. counts derived from the PDF itself (Chopin: text search; La Campanella: font glyphs)
  3. run/scores/real/inventory.csv - a helper model's count by eye, part of it low
     confidence; sets that rely on it are reported as approximate.

The MusicXML of every page is cached per model under real_eval/<label>/, so adding
pages to the test set only costs the new pages.
"""

import csv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = "/Users/yiduoke/Documents/homr"
WORKTREE = f"{ROOT}/run/acc_wt"
PYTHON = f"{ROOT}/.venv/bin/python"
REAL = f"{ROOT}/run/scores/real"
OUT = f"{ROOT}/run/eval_run1/real_eval_acc"


def _load_sets() -> dict[str, list[dict]]:
    """name -> pages, each {path, va, vb, firm} with the printed label counts."""
    sets: dict[str, list[dict]] = {}
    chopin = {"05": 2, "07": 2, "11": 1, "16": 4, "17": 2}  # "8va" in the PDF text, per page
    sets["Chopin Ballade 4 (LilyPond, italic 8va)"] = [
        {"path": f"{ROOT}/run/work/chopin-ballade-4-a4/pages/page-{p}.png", "va": n, "vb": 0, "firm": True}
        for p, n in chopin.items()
    ]
    # SMuFL "ottava" glyph (U+E510) per page of the PDF, page 6 checked by eye; all above the staff
    campanella = {"01": 9, "02": 6, "03": 8, "04": 6, "05": 6, "06": 5}
    sets["La Campanella (MuseScore)"] = [
        {"path": f"{ROOT}/run/work/liszt-la-campanella/pages/page-{p}.png", "va": n, "vb": 0, "firm": True}
        for p, n in campanella.items()
    ]
    verified: dict[str, tuple[int, int]] = {}
    if os.path.exists(f"{REAL}/verified_counts.csv"):
        with open(f"{REAL}/verified_counts.csv") as f:
            for row in csv.DictReader(f):
                verified[row["png"]] = (int(row["n_8va"]), int(row["n_8vb"]))
    if os.path.exists(f"{REAL}/inventory.csv"):
        with open(f"{REAL}/inventory.csv") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            png = row["png"]
            if not os.path.exists(f"{REAL}/{png}"):
                continue
            va, vb = int(row["n_8va_labels"] or 0), int(row["n_8vb_labels"] or 0)
            firm = png in verified
            if firm:
                va, vb = verified[png]
            if "-none" in png:
                name = "Control pages with no octave marks"
            elif row.get("kind") == "typeset":
                name = "Other typeset PDFs"
            else:
                name = "Printed-edition scans"
            sets.setdefault(name, []).append({"path": f"{REAL}/{png}", "va": va, "vb": vb, "firm": firm})
    return sets


def _transcribe(page: str, cache_dir: str) -> str | None:
    """MusicXML of one page with the model currently installed in the worktree, cached."""
    cached = os.path.join(cache_dir, os.path.basename(page).replace(".png", ".musicxml"))
    if not os.path.exists(cached):
        with tempfile.TemporaryDirectory() as work:
            local = os.path.join(work, os.path.basename(page))
            shutil.copy(page, local)
            subprocess.run(  # noqa: S603
                [PYTHON, "-m", "homr.main", local], cwd=WORKTREE, capture_output=True, check=False
            )
            produced = local.replace(".png", ".musicxml")
            if not os.path.exists(produced):
                return None
            shutil.copy(produced, cached)
    with open(cached) as f:
        return f.read()


def main() -> None:
    model_dir = sys.argv[1]  # unused
    label = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(model_dir.rstrip("/"))
    # released model already in acc_wt: do not copy anything
    cache_dir = f"{OUT}/{label}"
    os.makedirs(cache_dir, exist_ok=True)

    report: dict = {"model": label, "sets": {}}
    for name, pages in _load_sets().items():
        total = {"printed": 0, "found": 0, "hits": 0, "extras": 0, "failed_pages": 0}
        per_page = []
        for page in pages:
            xml = _transcribe(page["path"], cache_dir)
            if xml is None:
                total["failed_pages"] += 1
                total["printed"] += page["va"] + page["vb"]
                continue
            kinds = re.findall(r'<octave-shift[^>]*type="([a-z]+)"', xml)
            # MusicXML: type "down" means the notes are written an octave down, i.e. 8va
            found_va, found_vb = kinds.count("down"), kinds.count("up")
            hits = min(found_va, page["va"]) + min(found_vb, page["vb"])
            extras = max(0, found_va - page["va"]) + max(0, found_vb - page["vb"])
            total["printed"] += page["va"] + page["vb"]
            total["found"] += found_va + found_vb
            total["hits"] += hits
            total["extras"] += extras
            per_page.append(
                {
                    "page": os.path.basename(page["path"]),
                    "printed_8va": page["va"],
                    "printed_8vb": page["vb"],
                    "found_8va": found_va,
                    "found_8vb": found_vb,
                    "stops": kinds.count("stop"),
                    "notes": xml.count("<note>"),
                    "firm": page["firm"],
                }
            )
        firm = all(p["firm"] for p in pages)
        report["sets"][name] = {"pages": len(pages), "counts_firm": firm, **total, "per_page": per_page}
        print(
            f"{label} | {name}: hits {total['hits']} of {total['printed']} printed"
            f"{'' if firm else ' (approx.)'}, extras {total['extras']}, found {total['found']},"
            f" {len(pages)} pages" + (f", {total['failed_pages']} failed" if total["failed_pages"] else "")
        )
    with open(f"{OUT}/{label}.json", "w") as f:
        json.dump(report, f, indent=1)


if __name__ == "__main__":
    main()
