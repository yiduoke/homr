"""Render the merged score to WAV, following the tempo map if one was built.

Deliberately crude synthesis: the point is to check whether the NOTES and the
TEMPO CHANGES are right, not to sound good.
"""

import json
import os
import wave
from pathlib import Path

OUT = os.environ.get("HOMR_OUT", "run/pathetique_homr")
TEMPO_MAP = os.environ.get("HOMR_TEMPO_MAP", "run/tempo_map.json")

import numpy as np
from music21 import converter

SR = 22050
FALLBACK_BPM = 108.0

score = converter.parse(f"{OUT}.musicxml", forceSource=True)

# Without this a tied note is struck twice instead of held: stripTies merges each
# tied pair into one note of the combined length.
before = len(score.flatten().notes)
score = score.stripTies()
print(f"stripTies: {before} -> {len(score.flatten().notes)} notes")

# --- tempo map: quarter-note offset -> BPM -------------------------------------

measure_offsets: dict[int, float] = {}
beat_units: list[tuple[int, float]] = []
for m in score.parts[0].getElementsByClass("Measure"):
    measure_offsets.setdefault(int(m.number), float(m.offset))
    for ts in m.getElementsByClass("TimeSignature"):
        beat_units.append((int(m.number), float(ts.beatDuration.quarterLength)))
beat_units.sort()


def beat_unit_at(measure: int) -> float:
    """Quarter-lengths per beat where a tempo marking appears.

    music21's tempo values count quarter notes, but a marking is read against the
    beat of its time signature: "Allegro" under cut time means 132 half notes per
    minute, not 132 quarters. Taken once per marking and held for the whole
    section, so that homr spuriously dropping back to 4/4 mid-Allegro (m.20, 68,
    109, ...) can't make the tempo lurch.
    """
    # A tempo change and a meter change are printed together, but the two can land
    # a measure apart here: the marking's measure is inferred from its position on
    # the page, the meter's is exact. Look slightly ahead so the marking picks up
    # the meter it was written against.
    lookahead = 2
    ahead = [v for n, v in beat_units if measure < n <= measure + lookahead]
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
tempo_file = Path(TEMPO_MAP)
if tempo_file.exists():
    for entry in json.loads(tempo_file.read_text()):
        offset = measure_offsets.get(entry["measure"])
        if offset is not None:
            quarter_bpm = float(entry["bpm"]) * beat_unit_at(entry["measure"])
            segments.append((offset, quarter_bpm))
segments.sort()
if not segments or segments[0][0] > 0:
    segments.insert(0, (0.0, segments[0][1] if segments else FALLBACK_BPM))

# Wall-clock time at the start of each segment, so lookups are a simple walk.
segment_starts: list[float] = [0.0]
for i in range(1, len(segments)):
    span_q = segments[i][0] - segments[i - 1][0]
    segment_starts.append(segment_starts[-1] + span_q * 60.0 / segments[i - 1][1])

print("tempo segments:")
for (offset, bpm), start in zip(segments, segment_starts):
    print(f"  q={offset:8.1f}  {bpm:5.0f} bpm  starts at {start / 60:5.2f} min")


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
    return segment_starts[i] + (offset_q - segments[i][0]) * 60.0 / segments[i][1]


# --- collect notes -------------------------------------------------------------

events = []
for part in score.parts:
    for n in part.flatten().notes:
        for p in n.pitches:
            events.append((float(n.offset), float(n.quarterLength), p.midi))

total_q = max(o + d for o, d, _ in events)
total_sec = time_at(total_q) + 2.0
buf = np.zeros(int(total_sec * SR) + SR, dtype=np.float64)
print(f"\n{len(events)} note events, {total_q:.0f} quarter notes -> {total_sec / 60:.1f} min")

HARMONICS = [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)]

for offset_q, dur_q, midi_note in events:
    bpm = segments[seg_index(offset_q)][1]
    dur = max(dur_q * 60.0 / bpm, 0.05)
    ring = dur + 0.35
    n = int(ring * SR)
    t = np.arange(n) / SR
    freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
    if freq > SR / 2.5:
        continue
    wave_ = np.zeros(n)
    for mult, amp in HARMONICS:
        if freq * mult < SR / 2.5:
            wave_ += amp * np.sin(2 * np.pi * freq * mult * t)
    env = np.exp(-t * 3.0)                      # decay
    attack = np.minimum(t / 0.006, 1.0)         # short attack, avoids clicks
    sample = wave_ * env * attack * 0.16
    start = int(time_at(offset_q) * SR)
    buf[start : start + n] += sample

buf = buf / np.max(np.abs(buf)) * 0.89
pcm = (buf * 32767).astype(np.int16)

with wave.open(f"{OUT}.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes(pcm.tobytes())
print(f"wrote {OUT}.wav")
