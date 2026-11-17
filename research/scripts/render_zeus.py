"""Stitch Zeus's per-system MusicXML into one score and render it to WAV.

Zeus writes one file per staff system with both staves inside a single part, so
merging is just appending measures in page/system order. Tempo comes from the same
map built for homr, keyed by (page, system) since the measure numbering differs.
"""

import json
import re
import wave
from pathlib import Path

import numpy as np
from music21 import converter, spanner, stream

ZEUS = Path("/Users/yiduoke/Documents/olimpic-icdar24/run/zeus-xml2")
SR = 22050
FALLBACK_BPM = 108.0


def sort_key(p: Path) -> tuple[int, int]:
    m = re.match(r"page-(\d+)-sys(\d+)", p.stem)
    return (int(m.group(1)), int(m.group(2)))


files = sorted(ZEUS.glob("page-*-sys*.musicxml"), key=sort_key)

merged = stream.Score()
targets: dict[str, stream.Part] = {}

system_start_measure: dict[tuple[int, int], int] = {}
measure_no = 0

for path in files:
    page, sysno = sort_key(path)
    score = converter.parse(path, forceSource=True)
    system_start_measure[(page, sysno)] = measure_no + 1
    added = 0
    # music21 splits a Zeus system into one part per staff, so both have to be
    # carried over -- taking only the first silently drops the whole left hand.
    for src in score.parts:
        target = targets.get(src.id)
        if target is None:
            target = stream.Part()
            target.id = src.id
            targets[src.id] = target
            merged.insert(0, target)
        start = target.highestTime
        for m in src.getElementsByClass("Measure"):
            added += 1

            target.insert(start + m.offset, m)
        for sp in src.getElementsByClass(spanner.Spanner):
            target.insert(0, sp)
    measure_no += added // max(len(score.parts), 1)

for target in merged.parts:
    for i, m in enumerate(target.getElementsByClass("Measure"), start=1):
        m.number = i

print(
    f"{len(files)} systems -> {len(merged.parts)} parts, "
    f"{measure_no} measures, {merged.parts[0].highestTime:.0f} quarter notes"
)

merged.write("musicxml", fp="run/pathetique_zeus.musicxml")
merged.write("midi", fp="run/pathetique_zeus.mid")

# --- tempo ---------------------------------------------------------------------

score = converter.parse("run/pathetique_zeus.musicxml", forceSource=True)
score = score.stripTies()

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
for entry in json.loads(Path("run/tempo_map.json").read_text()):
    # Keyed by system, not measure: Zeus and homr don't agree on measure numbers.
    key = (entry["page"], entry["system"])
    measure = system_start_measure.get(key)
    if measure is None:
        continue
    offset = measure_offsets.get(measure)
    if offset is not None:
        segments.append((offset, float(entry["bpm"]) * beat_unit_at(measure)))
segments.sort()
if not segments or segments[0][0] > 0:
    segments.insert(0, (0.0, segments[0][1] if segments else FALLBACK_BPM))

segment_starts = [0.0]
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


# --- render --------------------------------------------------------------------

events = []
for p in score.parts:
    for n in p.flatten().notes:
        for pitch in n.pitches:
            events.append((float(n.offset), float(n.quarterLength), pitch.midi))

total_q = max(o + d for o, d, _ in events)
buf = np.zeros(int((time_at(total_q) + 2.0) * SR) + SR, dtype=np.float64)
print(f"\n{len(events)} note events -> {time_at(total_q) / 60:.1f} min")

HARMONICS = [(1, 1.0), (2, 0.45), (3, 0.22), (4, 0.12), (5, 0.06)]

for offset_q, dur_q, midi_note in events:
    bpm = segments[seg_index(offset_q)][1]
    dur = max(dur_q * 60.0 / bpm, 0.05)
    n = int((dur + 0.35) * SR)
    t = np.arange(n) / SR
    freq = 440.0 * 2 ** ((midi_note - 69) / 12.0)
    if freq > SR / 2.5:
        continue
    wave_ = np.zeros(n)
    for mult, amp in HARMONICS:
        if freq * mult < SR / 2.5:
            wave_ += amp * np.sin(2 * np.pi * freq * mult * t)
    sample = wave_ * np.exp(-t * 3.0) * np.minimum(t / 0.006, 1.0) * 0.16
    start = int(time_at(offset_q) * SR)
    buf[start : start + n] += sample

buf = buf / np.max(np.abs(buf)) * 0.89
with wave.open("run/pathetique_zeus.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((buf * 32767).astype(np.int16).tobytes())
print("wrote run/pathetique_zeus.wav")
