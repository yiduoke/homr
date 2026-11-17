"""Locate tempo markings on each page and map them to a global measure number.

homr's own OCR only looks above the first staff of a page, so mid-page tempo
changes are never seen. This scans the whole page instead, then works out which
measure each marking belongs to:

    tempo text (x, y)  ->  staff system (by y)  ->  measure (by x within system)

Writes run/tempo_map.json. Nothing here changes homr itself; the BPM values are
music21's conventions and stay out of the repo's own output.
"""

import json
import os
import re
from pathlib import Path

PAGES = Path(os.environ.get("HOMR_PAGES", "run/pages150"))
TEMPO_MAP = Path(os.environ.get("HOMR_TEMPO_MAP", "run/tempo_map.json"))

from PIL import Image
from music21 import tempo as m21tempo
from rapidocr import RapidOCR

from homr.title_detection import cleanup_text, is_tempo_text

PAGES = sorted(
    PAGES.glob("page-[0-9]*.png"),
    key=lambda p: int(p.stem.split("-")[1]),
)
TEMPO_VALUES = m21tempo.defaultTempoValues


def bpm_for(text: str) -> float | None:
    """Longest matching phrase wins, so 'allegro moderato' beats 'allegro'."""
    words = text.lower().split()
    best: tuple[int, float] | None = None
    for phrase, value in TEMPO_VALUES.items():
        parts = phrase.split()
        for i in range(len(words) - len(parts) + 1):
            if words[i : i + len(parts)] == parts and (best is None or len(parts) > best[0]):
                best = (len(parts), float(value))
    return best[1] if best else None


def read_systems(txt_path: Path, size: tuple[int, int]) -> list[dict]:
    """Staff boxes (YOLO-normalised) grouped into systems by vertical proximity."""
    width, height = size
    boxes = []
    for line in txt_path.read_text().splitlines():
        if not line.strip():
            continue
        _cls, cx, cy, w, h = (float(v) for v in line.split())
        boxes.append(
            {
                "top": (cy - h / 2) * height,
                "bottom": (cy + h / 2) * height,
                "left": (cx - w / 2) * width,
                "right": (cx + w / 2) * width,
            }
        )
    # homr writes one box per grand staff, so each line is already a system.
    boxes.sort(key=lambda b: b["top"])
    return boxes


def measures_per_system(xml_path: Path) -> list[int]:
    """Measure counts per system, read from the <print new-system> markers."""
    xml = xml_path.read_text()
    first_part = re.search(r"<part\b.*?</part>", xml, re.S)
    body = first_part.group(0) if first_part else xml
    chunks = re.split(r"<measure\b", body)[1:]
    counts: list[int] = []
    for chunk in chunks:
        if 'new-system="yes"' in chunk or not counts:
            counts.append(0)
        counts[-1] += 1
    return counts


def main() -> None:
    reader = RapidOCR()
    entries: list[dict] = []
    measure_offset = 0

    for page in PAGES:
        width, height = Image.open(page).size
        systems = read_systems(page.with_suffix(".txt"), (width, height))
        per_system = measures_per_system(page.with_suffix(".musicxml"))
        page_measures = sum(per_system)

        result = reader(str(page))
        hits = []
        if result.txts is None:
            measure_offset += page_measures
            continue
        for box, txt, score in zip(result.boxes, result.txts, result.scores, strict=True):
            text = cleanup_text(txt)
            # "attacca subito il Allegro" is a cue to run on into the next section,
            # not a tempo change at that spot. The tempo itself is marked separately.
            if not is_tempo_text(text) or "attacca" in text.lower():
                continue
            hits.append((min(p[1] for p in box), min(p[0] for p in box), text, float(score)))

        for y, x, text, score in sorted(hits):
            below = [i for i, s in enumerate(systems) if s["bottom"] > y]
            if not below:
                continue
            si = below[0]
            system = systems[si]
            before = sum(per_system[:si]) if si < len(per_system) else page_measures
            count = per_system[si] if si < len(per_system) else 1
            # Measures aren't positioned in the MusicXML, so place the marking
            # proportionally across the system's width.
            span = max(system["right"] - system["left"], 1.0)
            frac = min(max((x - system["left"]) / span, 0.0), 0.999)
            local = before + int(frac * count)

            entries.append(
                {
                    "page": int(page.stem.split("-")[1]),
                    "text": text,
                    "confidence": round(score, 3),
                    "system": si,
                    "measure": measure_offset + local + 1,
                    "bpm": bpm_for(text),
                }
            )
        measure_offset += page_measures

    # "Tempo I" means go back to the movement's opening tempo.
    opening = next((e["bpm"] for e in entries if e["bpm"]), None)
    for e in entries:
        if e["bpm"] is None and re.search(r"\btempo\b", e["text"], re.I):
            e["bpm"] = opening
            e["note"] = "resolved as Tempo I -> opening tempo"

    entries = [e for e in entries if e["bpm"]]
    entries.sort(key=lambda e: e["measure"])
    TEMPO_MAP.write_text(json.dumps(entries, indent=2))

    print(f"{len(entries)} tempo markings, total measures {measure_offset}\n")
    for e in entries:
        print(f"  m.{e['measure']:<4} p{e['page']} sys{e['system']}  {e['bpm']:>5.0f} bpm  {e['text']}")


main()
