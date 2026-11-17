# Why run2s7 misses or invents pitches (companion to timing_audit.md)

Model: run2s7 (released). Read-only; no result or reference file changed.
Scripts in `run/eval_run1/`: `pitch_audit.py` (classifier, writes `pitch_audit.json`, one record per error), `pitch_audit_tables.py` (tables),
`pitch_audit_staffless.py` (F1 with the staff ignored); page crops reuse `timing_audit_crops.py`. Parsing, bar alignment (from each note-scores json,
staff remap included) and per-bar inventories are those of `timing_audit_a.py`/`score_notes.py`; my recomputed F1 equals the saved pitch F1 for all 9 pieces.

## Method

Unit: per aligned bar pair, multiset of `(staff, pitch)`. Misses = reference notes left after the inventory intersection; extras = predicted notes left.
Counting: a miss/extra pair counts as one error, a single miss or single extra counts as one, so errors are "events", not notes. Order of classification
(departures from the brief are marked):
1. unaligned: every note of a reference/predicted bar without partner. Added: an aligned pair with bar overlap < 10 % (>= 4 notes both sides) or a staff-bar empty on one side (>= 4 notes on the other) is treated the same (a layout loss, not note errors).
6. (done first, because it is exact) same pitch, other staff, same aligned bar. Brief ranks it 6th; pitch equality makes it unambiguous.
2. same letter and alteration, octave differs by 1-2. 3. same letter and octave, alteration differs. 4. diatonic position differs by 1.
5. >= 3 pairs in one staff/bar with the same diatonic shift of 3 steps (3rd) or 6 steps (6th) (a clef shift).
9. leftover miss and extra on the same staff and onset (substitution). 7a/7b. leftover miss: other members of its reference chord (same staff, same onset) have their pitch in the predicted bar (7a) or not (7b).
8. leftover extra. Octave state (8va/8vb) is read from `octave-shift` directions of reference and prediction.

## Counts per piece (errors)

| piece | pitch F1 | errors | 1 unaligned bar | 2 octave | 3 accidental | 4 step | 5 clef | 6 staff assignment | 7a chord member missing | 7b whole event missing | 8 extra | 9 other |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mazeppa | 80.3 | 2162 | 897 | 167 | 145 | 39 | 4 | 221 | 255 | 310 | 114 | 10 |
| la-campanella | 85.2 | 865 | 156 | 293 | 14 | 11 | 4 | 71 | 51 | 104 | 153 | 8 |
| rachmaninoff-op3-2 | 72.4 | 951 | 451 | 23 | 19 | 7 | 0 | 0 | 55 | 79 | 307 | 10 |
| chopin-ballade-4 | 96.8 | 254 | 29 | 24 | 89 | 15 | 4 | 1 | 13 | 16 | 56 | 7 |
| bach-fugue-848 | 87.6 | 200 | 12 | 0 | 5 | 0 | 0 | 161 | 13 | 3 | 6 | 0 |
| bach-prelude-848 | 94.0 | 71 | 28 | 0 | 2 | 0 | 0 | 25 | 0 | 0 | 16 | 0 |
| mozart-kv331-theme | 99.6 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| mozart-kv309-1 | 99.7 | 9 | 0 | 0 | 0 | 1 | 0 | 5 | 1 | 0 | 2 | 0 |
| beethoven-pathetique-1 | 99.4 | 35 | 0 | 1 | 5 | 5 | 0 | 4 | 9 | 2 | 3 | 6 |
| **all** | | 4548 | 1573 (35%) | 508 (11%) | 279 (6%) | 78 (2%) | 12 (0%) | 489 (11%) | 397 (9%) | 514 (11%) | 657 (14%) | 41 (1%) |

shares per focus piece (% of that piece's errors)

Staff-ignored pitch F1 (same alignment): mazeppa 80.3 -> 84.2, la-campanella 85.2 -> 87.2, rachmaninoff 72.4 -> 72.5, chopin 96.8 -> 96.9,
**bach-fugue 87.6 -> 99.3**, bach-prelude 94.0 -> 99.8, KV331 99.6 -> 100.0, KV309 99.7 -> 99.9, Pathetique 99.4 -> 99.5.

## Findings per category

* **Staff assignment (6)** explains Bach fugue (161 of 200 errors) and Bach prelude: pitches are right, 141 reference notes in staff 1 sit in staff 2 of the prediction (32 the other way); the
  reference follows the voice, the prediction follows the printed staff (bar 53 page 2: sixteenth runs in the lower staff). This is mostly a reference/convention mismatch, not misreading.
  Mazeppa: 221, mainly middle-C-region notes moved between hands; La Campanella 71.
* **Unaligned / lost (1)** is the largest class: Mazeppa 897 of 2162. Reference bars 93-104 (printed p. 25 = page 11, the "Ossia" page with 13 staffs, layout [1,1,2,2,1]) and 12 predicted bars
  (93-104) were left unaligned (429 reference, 334 predicted notes in whole unaligned bars; another 134 in aligned bars with <10 % overlap). The pages produced notes (472 pitches on page 11); the 24 measures of that page do not line up with the
  reference's 12, because the ossia staves become extra bars.
  Rachmaninoff 451 of 951: ref bars 48-54 (page 5, four staves per system: treble, small treble, bass, bass) have 36 notes per staff in the reference; the prediction has 18 in staff 1 and 0 in staff 2 (253 notes in "staff-bar empty"). The
  prediction also contains a third part (291 notes, 44 bars) that the scorer folds into staff 2, which is where most of the 307 extras sit (290 extras in staff 2).
* **Octave (2)** is the first class for La Campanella (293 of 865, 34 %) and Chopin's second: 229 of 293 (La Campanella) and 21 of 24 (Chopin) sit in bars where the reference has an 8va/8vb bracket and the prediction has none (prediction
  pitch lower in 206 of 293 and in 24 of 24 cases: the printed pitch is kept, the bracket is lost). Mazeppa 167: only 82 under reference brackets, 62 of those where the prediction also has a bracket (bracket extent or direction wrong); Rachmaninoff 23 and Beethoven 1 have none under brackets.
* **Accidental (3)**: Chopin's biggest class (89 of 254, 35 %), bars 121-123 and 166 (19 + 12 + 6): -1 -> 0 (50) and 0 -> -1 (33): a flat dropped or invented; Mazeppa 145 (1->0 62, -1->0 52, dropped sharps and flats).
* **Chord members (7a) vs whole events (7b)**: Mazeppa 255 / 310, La Campanella 51 / 104, Rachmaninoff 55 / 79, Chopin 13 / 16. Missed-note chord sizes (missed / all reference notes in chords of that size):
  Mazeppa 1: 149/503 (30 %), 2: 338/3908 (9 %), 3: 55/1362 (4 %), 4: 20/1024 (2 %); La Campanella 1: 89/1646 (5 %), 2: 48/1832 (3 %), 3: 18/720 (3 %);
  Rachmaninoff 4: 76/424 (18 %), 6: 9/30 (30 %), 2: 30/472 (6 %), 3: 6/606 (1 %); Chopin all < 1 % except 5-note chords (2/20). So misses do **not** cluster in big chords (except Rachmaninoff's 4-6 note chords); in Mazeppa single notes
  (isolated notes between chords, runs) are dropped most.
* **Extras (8)** 657 (14 %): Rachmaninoff 307 (third part), La Campanella 153 (cadenza-like runs; bar 125/126 and 80 have 25-30 each), Chopin 56. **Step (4)** 78 and **clef (5)** 12 (four-note runs in Chopin 224, Mazeppa 105, La Campanella 27) are negligible.

## Overall shares (all 9 pieces, 4548 errors)

unaligned 35 %, extra 14 %, octave 11 %, staff assignment 11 %, whole event missing 11 %, chord member missing 9 %, accidental 6 %, step 2 %, other 1 %, clef 0.3 %.

## Examples checked on page images

| piece, bar (pred index) | page | what the print shows | verdict |
|---|---|---|---|
| chopin 117 | page 7 | "8va" bracket over a right-hand run; prediction one octave lower | confirmed octave / lost bracket |
| la-campanella 86, 14 | pages 6, 1 | dashed 8va line and "8" over right-hand sixteenths | confirmed octave / bracket |
| mazeppa 195 (last bar) | page 16 | final chord with "8" bracket under the bass chord, bracket present in both but octaves differ | octave, bracket handled in wrong octave |
| mazeppa 93-104 | page 11 (printed 25) | "Ossia" staves between systems, 13 staffs | confirmed lost bars (extra staves) |
| rachmaninoff 48-54 | page 5 | four staves per system | confirmed layout loss (staff 2 empty) |
| bach-fugue 53 | page 2 | inner-voice sixteenth runs written in the lower staff | staff assignment, pitches correct |
| mazeppa 24 | page 5 | dense chord figures with clef changes mid bar | chord members dropped (7a) |

Limits: 7 of the bars were viewed; Mazeppa/La Campanella octave examples that are not under a bracket (167-82, 293-229) and the Chopin accidentals were not individually viewed. Pairing is greedy by onset; "aligned bar unrelated" folds some real misreads into class 1.

## What to fix first

1. Layout loss: extra staves (ossia, four-staff systems) and bar-count mismatch from them: 35 % of errors and 47 % of Rachmaninoff.
2. Carry the 8va/8vb bracket into the pitches (La Campanella 34 %, Chopin 9 %).
3. Staff assignment convention for the Bach pieces (not a model fault; score it staff-agnostic or follow the reference voice assignment).
4. Then spurious extra part (Rachmaninoff), dropped accidentals (Chopin).
