"""Run transcoda over every score and render each to WAV.

transcoda reads a whole page and emits **kern, so there's no cropping and no
per-system joining -- pages are parsed individually and their measures appended,
the same shape as the homr merge.
"""

import json
import re
import subprocess
import sys
import time
import wave
from pathlib import Path

import numpy as np
from music21 import converter, stream

ROOT = Path("/Users/yiduoke/Documents/homr")
TRANSCODA = Path("/Users/yiduoke/Documents/transcoda")
WORK = ROOT / "run/work"
OUT = ROOT / "run/out"
SR, BPM = 22050, 100.0
HARM = [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)]


def pages_of(slug: str) -> list[Path]:
    return sorted(
        (p for p in (WORK / slug / "pages").glob("page-*.png") if "_teaser" not in p.name),
        key=lambda p: int(re.search(r"page-(\d+)", p.name).group(1)),
    )


def transcribe(page: Path) -> Path | None:
    krn = page.with_name(page.stem + "_pred.krn")
    if krn.exists():
        return krn
    subprocess.run(
        ["uv", "run", "scripts/inference.py", "--weights", "./weights/model.ckpt",
         "--image", str(page)],
        cwd=TRANSCODA, capture_output=True, text=True, timeout=1800,
    )
    return krn if krn.exists() else None


def merge(krns: list[Path]) -> stream.Score:
    merged = stream.Score()
    targets: dict[int, stream.Part] = {}
    for krn in krns:
        try:
            page = converter.parse(str(krn), forceSource=True)
        except Exception:  # noqa: BLE001 -- a page that won't parse is skipped, not fatal
            continue
        for i, src in enumerate(page.parts):
            target = targets.get(i)
            if target is None:
                target = stream.Part()
                targets[i] = target
                merged.insert(0, target)
            start = target.highestTime
            for m in src.getElementsByClass("Measure"):
                target.insert(start + m.offset, m)
    return merged


def render(score: stream.Score, dst: Path) -> dict:
    events = [
        (float(n.offset), float(n.quarterLength), p.midi)
        for part in score.parts for n in part.flatten().notes for p in n.pitches
    ]
    if not events:
        raise ValueError("no notes")
    spq = 60.0 / BPM
    total = max(o + d for o, d, _ in events) * spq + 2.0
    buf = np.zeros(int(total * SR) + SR)
    for offset_q, dur_q, midi_note in events:
        dur = max(dur_q * spq, 0.05)
        n = int((dur + 0.35) * SR)
        t = np.arange(n) / SR
        freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
        if freq > SR / 2.5 or n <= 0:
            continue
        w = np.zeros(n)
        for mult, amp in HARM:
            if freq * mult < SR / 2.5:
                w += amp * np.sin(2 * np.pi * freq * mult * t)
        start = int(offset_q * spq * SR)
        buf[start : start + n] += w * np.exp(-t * 3.0) * np.minimum(t / 0.006, 1.0) * 0.16
    buf = buf / np.max(np.abs(buf)) * 0.89
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())
    return {
        "notes": len(events),
        "measures": len(score.parts[0].getElementsByClass("Measure")),
        "minutes": round(total / 60, 2),
    }


def main() -> None:
    results_path = ROOT / "run/results.json"
    results = json.loads(results_path.read_text())
    slugs = sys.argv[1:] or sorted(p.name for p in WORK.iterdir() if (p / "pages").is_dir())
    for slug in slugs:
        started = time.time()
        pages = pages_of(slug)
        krns = [k for k in (transcribe(p) for p in pages) if k]
        print(f"  {slug}: {len(krns)}/{len(pages)} pages transcribed", flush=True)
        try:
            row = render(merge(krns), OUT / f"{slug}__transcoda.wav")
            row["wav"] = f"{slug}__transcoda.wav"
            row["pages"] = len(pages)
        except Exception as exc:  # noqa: BLE001
            row = {"error": f"{type(exc).__name__}: {exc}"[:200]}
        row["seconds"] = round(time.time() - started, 1)
        results.setdefault(slug, {"title": slug, "engines": {}})["engines"]["transcoda"] = row
        results_path.write_text(json.dumps(results, indent=2))
        print(f"  {slug}: {row}", flush=True)


main()
