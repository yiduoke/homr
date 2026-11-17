"""Render any MusicXML to WAV with the crude synth used throughout.

Engine-agnostic: takes an input file, an output path and an optional tempo map.
No piece-specific corrections live here -- the Pathetique clef repair stays in its
own script so it can't leak onto other scores.

    python render_score.py IN.musicxml OUT.wav [tempo_map.json]
"""

import json
import sys
import wave
from pathlib import Path

import numpy as np
from music21 import converter

SR = 22050
FALLBACK_BPM = 100.0
HARMONICS = [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)]


def main(src: str, dst: str, tempo_map: str | None) -> dict:
    score = converter.parse(src, forceSource=True)
    try:
        score = score.stripTies()
    except Exception:  # noqa: BLE001 -- malformed ties shouldn't stop playback
        pass

    measure_offsets: dict[int, float] = {}
    beat_units: list[tuple[int, float]] = []
    for m in score.parts[0].getElementsByClass("Measure"):
        measure_offsets.setdefault(int(m.number), float(m.offset))
        for ts in m.getElementsByClass("TimeSignature"):
            beat_units.append((int(m.number), float(ts.beatDuration.quarterLength)))
    beat_units.sort()

    def beat_unit_at(measure: int) -> float:
        ahead = [v for n, v in beat_units if measure < n <= measure + 2]
        if ahead:
            return ahead[0]
        unit = 1.0
        for number, value in beat_units:
            if number <= measure:
                unit = value
            else:
                break
        return unit

    segments: list[tuple[float, float]] = []
    if tempo_map and Path(tempo_map).exists():
        for entry in json.loads(Path(tempo_map).read_text()):
            offset = measure_offsets.get(entry["measure"])
            if offset is not None:
                segments.append((offset, float(entry["bpm"]) * beat_unit_at(entry["measure"])))
    segments.sort()
    if not segments or segments[0][0] > 0:
        segments.insert(0, (0.0, segments[0][1] if segments else FALLBACK_BPM))

    starts = [0.0]
    for i in range(1, len(segments)):
        span = segments[i][0] - segments[i - 1][0]
        starts.append(starts[-1] + span * 60.0 / segments[i - 1][1])

    def seg_index(offset_q: float) -> int:
        lo = 0
        for i, (start_q, _) in enumerate(segments):
            if start_q <= offset_q:
                lo = i
            else:
                break
        return lo

    def time_at(offset_q: float) -> float:
        i = seg_index(offset_q)
        return starts[i] + (offset_q - segments[i][0]) * 60.0 / segments[i][1]

    events = []
    for part in score.parts:
        for n in part.flatten().notes:
            for pitch in n.pitches:
                events.append((float(n.offset), float(n.quarterLength), pitch.midi))
    if not events:
        raise ValueError("no notes found")

    total_q = max(o + d for o, d, _ in events)
    seconds = time_at(total_q) + 2.0
    buf = np.zeros(int(seconds * SR) + SR, dtype=np.float64)

    for offset_q, dur_q, midi_note in events:
        bpm = segments[seg_index(offset_q)][1]
        dur = max(dur_q * 60.0 / bpm, 0.05)
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
        start = int(time_at(offset_q) * SR)
        buf[start : start + n] += sample

    peak = np.max(np.abs(buf))
    if peak > 0:
        buf = buf / peak * 0.89
    with wave.open(dst, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((buf * 32767).astype(np.int16).tobytes())

    return {
        "notes": len(events),
        "measures": len(score.parts[0].getElementsByClass("Measure")),
        "parts": len(score.parts),
        "minutes": round(seconds / 60, 2),
    }


if __name__ == "__main__":
    stats = main(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    print(json.dumps(stats))
