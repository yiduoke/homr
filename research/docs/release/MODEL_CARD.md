# Time signatures and printed accidentals, fine-tuned on this fork (meteracc-r2s7-afae0e3)

Day: 16 November 2026
Branch: `accidentals-run2` (code commit afae0e3); model name `pytorch_model_meteracc-r2s7-afae0e3`.

Upstream model 566 fine-tuned in two steps on one RTX 3090, each 2 epochs (about an hour):

1. **Complete time signatures** (branch `meter-run1`): tokens `timeSignature_<num>/<den>` for 34
   numeric meters plus `timeSignature_common` (C) and `timeSignature_cut` (cut C), replacing the
   denominator-only `timeSignature/<den>`. The new rows started from the old row of the same
   denominator. The MusicXML writer writes the recognised meter (with `symbol="common|cut"`) and
   carries it across systems and pages; the numerator guess from bar lengths is only a fallback.
2. **Printed accidentals** (branch `accidentals-run2`): the lift field is the sign printed before
   the note (`#`, `b`, `N`, `##`, `bb`, or none), not the sounding alteration. `homr/accidentals.py`
   derives the sounding pitch from the key signature, signs earlier in the bar (per staff, step
   and octave) and ties; MusicXML gets both `<alter>` and `<accidental>`. The lift head was
   re-initialised. This release is the second training of this step (seed 7); the first (seed 42)
   gave the same mean.

Training data: upstream's sets (OpenScore Lieder, GrandStaff, PDMX `no_license_conflict`) plus the
fork's octave-bracket staffs (LilyPond and MuseScore renders of the same sources), in round 3's
mix; labels regenerated for the same images and checked against them. Evaluation pieces were
removed from all sources.

Results on eight reference pieces (individual-note F1, pitch + onset + duration, one frozen
pipeline for every model; `validation/score_notes.py`):

| Piece | 566 | this model |
|---|---|---|
| Liszt, Mazeppa (real scan) | 34.8 | 33.6 |
| Liszt, La Campanella | 68.0 | 71.8 |
| Rachmaninoff, Prelude Op. 3 No. 2 | 57.8 | 61.7 |
| Bach, Prelude BWV 848 | 91.4 | 94.0 |
| Bach, Fugue BWV 848 | 86.0 | 86.0 |
| Mozart, K. 331 theme | 99.6 | 99.6 |
| Mozart, K. 309/1 | 96.9 | 97.1 |
| Beethoven, Op. 13/1 | 97.0 | 97.2 |
| Mean | 78.9 | 80.1 |

Notes sounding right (on matched notes): 99.0% (566: 97.2%). Printed signs: roughly 86-99% F1 per
sign on most pieces (566 writes none). Time signatures: C and cut C read, e.g. 5 of 6 printed
signatures of the Pathetique exactly (566: 0).

Known limits: Mazeppa, the only real scan among the references, is about 1 point below 566 (both
trainings); a misread key signature now affects the whole system, since the sounding pitch is
computed from it. A misread meter is carried until the next printed one. Seven of the eight
reference pieces are digital engravings; three references are Claude transcriptions checked only
in part. Two identical trainings differ by up to ~1.8 points on single pieces.

License: AGPL-3.0 like upstream's weights; the training data carries the conditions listed in
LICENSE_FAQ.md (no non-commercial sources). Built on homr (liebharc/homr), Polyphonic-TrOMR
(NetEase, Apache-2.0) and oemer (MIT). AI use: the training code, data conversion and evaluation
were written and run with Claude (Anthropic) and Codex (OpenAI); the owner directed the work and
checked results.

