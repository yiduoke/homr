"""Render Audiveris's MusicXML to WAV with the same synth used for homr.

Audiveris exports the whole 9-page book as one file with both staves already in
sync, so there is nothing to stitch or repair. It doesn't export the tempo words
though, so the six markings found by OCR are paired in order with the six time
signature changes Audiveris found -- they are the same six places in the score.
"""

import wave
from pathlib import Path

import numpy as np
from music21 import converter

SRC = Path("run/pathetique_audiveris_patched.musicxml")
SR = 22050

# Grave, Allegro, Tempo I, Allegro, Grave, Allegro -- music21's conventional values,
# read against the beat of the time signature in force at each marking.
MARKINGS = [40.0, 132.0, 40.0, 132.0, 40.0, 132.0]

score = converter.parse(SRC, forceSource=True)

# Audiveris read the lower staff in treble clef for m.1-19 (plus m.136 and m.308),
# putting those pitches a thirteenth high. That's 12 diatonic steps rather than a
# fixed number of semitones, which is why it sounds displaced instead of
# transposed. Accidentals are re-derived from the key, since the letter changes.
# Done in memory: music21's MusicXML writer trips over Audiveris's voice numbering.
SHIFTED = set(range(1, 9)) | set(range(10, 20)) | {136, 308}
STEPS_DOWN = 12

key_for: dict[int, object] = {}
for m in score.parts[0].getElementsByClass("Measure"):
    ks = m.getContextByClass("KeySignature")
    if ks is not None:
        key_for[int(m.number)] = ks

moved = 0
for m in score.parts[1].getElementsByClass("Measure"):
    number = int(m.number)
    if number not in SHIFTED:
        continue
    key = key_for.get(number)
    for n in m.flatten().notes:
        for p in n.pitches:
            p.diatonicNoteNum -= STEPS_DOWN
            p.accidental = key.accidentalByStep(p.step) if key is not None else None
        moved += 1
print(f"corrected {moved} notes across {len(SHIFTED)} mis-clefed measures")

score = score.stripTies()

changes: list[tuple[int, float, float]] = []   # measure, offset, beat unit
for m in score.parts[0].getElementsByClass("Measure"):
    for ts in m.getElementsByClass("TimeSignature"):
        changes.append((int(m.number), float(m.offset), float(ts.beatDuration.quarterLength)))

if len(changes) != len(MARKINGS):
    print(f"warning: {len(changes)} time signature changes vs {len(MARKINGS)} markings")

segments = [
    (offset, MARKINGS[i] * unit)
    for i, (_num, offset, unit) in enumerate(changes)
    if i < len(MARKINGS)
]
if not segments or segments[0][0] > 0:
    segments.insert(0, (0.0, 108.0))

segment_starts = [0.0]
for i in range(1, len(segments)):
    span = segments[i][0] - segments[i - 1][0]
    segment_starts.append(segment_starts[-1] + span * 60.0 / segments[i - 1][1])

print("tempo segments:")
for (num, _o, _u), (offset, bpm), start in zip(changes, segments, segment_starts):
    print(f"  m.{num:<4} q={offset:8.1f}  {bpm:5.0f} bpm  at {start / 60:5.2f} min")


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


events = []
for part in score.parts:
    for n in part.flatten().notes:
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
with wave.open("run/pathetique_audiveris.wav", "wb") as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(SR)
    w.writeframes((buf * 32767).astype(np.int16).tobytes())
print("wrote run/pathetique_audiveris.wav")
