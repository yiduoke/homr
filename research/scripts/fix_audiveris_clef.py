"""Move the mis-clefed measures of Audiveris's lower staff back down.

Audiveris read the lower staff in treble clef for m.1-19 (plus m.136 and m.308),
so those pitches came out a thirteenth high -- 12 diatonic steps, not a fixed
number of semitones, which is why it sounds shifted rather than transposed.
Accidentals are re-derived from the key signature afterwards, since the ones
Audiveris wrote belong to the pitches it thought it was reading.
"""
from music21 import converter

SHIFTED = set(range(1, 9)) | set(range(10, 20)) | {136, 308}
STEPS_DOWN = 12  # a thirteenth, in diatonic steps

score = converter.parse("run/pathetique_audiveris_patched.musicxml", forceSource=True)

moved = 0
for m in score.parts[1].getElementsByClass("Measure"):
    if int(m.number) not in SHIFTED:
        continue
    key = m.getContextByClass("KeySignature")
    for n in m.flatten().notes:
        for p in n.pitches:
            p.diatonicNoteNum = p.diatonicNoteNum - STEPS_DOWN
            p.accidental = key.accidentalByStep(p.step) if key else None
        moved += 1

score.write("musicxml", fp="run/pathetique_audiveris_fixed.musicxml")
print(f"shifted {moved} notes down a thirteenth across {len(SHIFTED)} measures")
