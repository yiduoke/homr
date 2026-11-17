"""Turn banked rokot ABC into one WAV per piece.

Each system is a self-contained ABC tune, so they're converted individually with
abc2midi and then laid end to end. Joining them measure-wise into a single score
is the pipeline work rokot's own card describes; for listening, sequential
concatenation reproduces the piece without inventing anything.
"""

import json
import re
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np
from music21 import converter

ROOT = Path("/Users/yiduoke/Documents/homr")
WORK = ROOT / "run/work"
OUT = ROOT / "run/out"
SR = 22050
HARMONICS = [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)]


def system_events(abc_path: Path, mid_path: Path) -> tuple[list, float]:
    text = abc_path.read_text().strip()
    if not text:
        return [], 0.0
    subprocess.run(
        ["abc2midi", str(abc_path), "-o", str(mid_path)],
        capture_output=True, text=True, timeout=120,
    )
    if not mid_path.exists() or mid_path.stat().st_size < 40:
        return [], 0.0
    try:
        score = converter.parse(str(mid_path), forceSource=True)
    except Exception:  # noqa: BLE001
        return [], 0.0
    events = []
    end = 0.0
    for part in score.parts:
        for n in part.flatten().notes:
            off, dur = float(n.offset), float(n.quarterLength)
            end = max(end, off + dur)
            for pitch in n.pitches:
                events.append((off, dur, pitch.midi))
    return events, end


def render(events: list, dst: Path, bpm: float = 100.0) -> dict:
    if not events:
        raise ValueError("no notes")
    spq = 60.0 / bpm
    total = max(o + d for o, d, _ in events) * spq + 2.0
    buf = np.zeros(int(total * SR) + SR, dtype=np.float64)
    for offset_q, dur_q, midi_note in events:
        dur = max(dur_q * spq, 0.05)
        n = int((dur + 0.35) * SR)
        t = np.arange(n) / SR
        freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
        if freq > SR / 2.5 or n <= 0:
            continue
        wave_ = np.zeros(n)
        for mult, amp in HARMONICS:
            if freq * mult < SR / 2.5:
                wave_ += amp * np.sin(2 * np.pi * freq * mult * t)
        sample = wave_ * np.exp(-t * 3.0) * np.minimum(t / 0.006, 1.0) * 0.16
        start = int(offset_q * spq * SR)
        buf[start : start + n] += sample
    peak = np.max(np.abs(buf))
    if peak:
        buf = buf / peak * 0.89
    with wave.open(str(dst), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())
    return {"notes": len(events), "minutes": round(total / 60, 2)}


def main() -> None:
    results = json.loads((ROOT / "run/results.json").read_text())
    for piece in sorted(WORK.iterdir()):
        abcs = sorted((piece / "rokot").glob("sys-*.abc")) if (piece / "rokot").is_dir() else []
        if not abcs:
            continue
        slug = piece.name
        mid_dir = piece / "rokot" / "mid"
        mid_dir.mkdir(exist_ok=True)
        all_events: list = []
        cursor = 0.0
        empty = 0
        for abc in abcs:
            events, end = system_events(abc, mid_dir / (abc.stem + ".mid"))
            if not events:
                empty += 1
                continue
            all_events.extend((o + cursor, d, p) for o, d, p in events)
            cursor += end
        wav = OUT / f"{slug}__rokot.wav"
        try:
            stats = render(all_events, wav)
        except Exception as exc:  # noqa: BLE001
            row = {"error": f"{type(exc).__name__}: {exc}"[:200]}
        else:
            row = {"wav": wav.name, "systems": len(abcs), "empty_systems": empty, **stats}
        results.setdefault(slug, {"title": slug, "engines": {}})["engines"]["rokot"] = row
        print(f"  {slug:42} {row}", flush=True)
    (ROOT / "run/results.json").write_text(json.dumps(results, indent=2))


main()
