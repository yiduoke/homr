# Octave brackets read by the released model (meteracc-r2s7) on the real-page test set

Model: pytorch_model_meteracc-r2s7-afae0e3 in run/acc_wt. Scorer: copy of run/real_eval.py
(real_eval_acc.py, worktree acc_wt, model copy step removed), same per-page hits/extras scoring.
Caches: real_eval_acc/released-fixed (HOMR_FIXED_MARGIN=1) and released-default (bracket-aware cutting).
Test: 73 hand-checked scan pages, 322 printed brackets (counts for non-verified pages are approximate, as before).

| Model / cutting | Found (of 322) | False marks | 8vb found (of 15) | False 8vb | False marks on 34 clean pages |
|---|---|---|---|---|---|
| Released, upstream cutting (FIXED_MARGIN=1) | 238 | 4 | 13 | 4 | 1 |
| Released, bracket-aware cutting (default) | 254 | 13 | 12 | 5 | 3 |
| Round 3 e1 (published), bracket-aware | 244 | 14 | 8 | 4 | 1 |
| Upstream 566, upstream cutting | 180 | 8 | | | |

Other sets (found of printed): Chopin italic "8va": fixed 9/11, default 11/11. La Campanella MuseScore: fixed 28/40, default 36/40.
Caveat: the old real_eval caches by page basename, so Chopin page-05/07/11/16/17 and La Campanella page-05 collide;
those two small sets (not the 322) may be slightly off, here and in earlier numbers.

## Per piece (found / false)

| Piece | Printed | Upstream cutting | Bracket-aware |
|---|---|---|---|
| Hungarian Rhapsody 2 | 63 | 52/3 | 59/7 |
| Mazeppa | 57 | 39/0 | 44/2 |
| Mussorgsky Pictures | 55 | 28/0 | 27/0 |
| Jeux d'eau | 42 | 37/0 | 38/3 |
| Campanella (Breitkopf scan) | 23 | 13/0 | 15/0 |
| Mephisto 1 | 21 | 20/1 | 20/1 |
| Totentanz | 17 | 12/0 | 14/0 |
| Scarbo | 15 | 11/0 | 11/0 |
| Chopin Scherzo 1 | 11 | 11/0 | 11/0 |
| Liebestraum 3 | 10 | 8/0 | 8/0 |
| Scriabin sonata 4 | 6 | 6/0 | 6/0 |
| Scriabin etude 8/12 | 2 | 1/0 | 1/0 |

## La Campanella (MuseScore, eval_run1/run2s7/la-campanella, joined.musicxml)

Reference: 49 brackets, all on the upper staff (part P1, staff 1). Output: tokens are predicted.
Upper-staff part has 15 bracket starts, lower-staff part 33 starts (reference has none on the lower staff).
Writing is correct: music_xml_generator transposes written to sounding pitch per staff, and
validation/score_notes does not apply octave-shift again, so there is no double shift.
- Bar 13 (reference bracket 13-15): model emits down and stop in the same measure, so bars 14-15 get no shift: bar 14 comes out C#5 B4 ... against reference C#6 B5 ... (an octave low). A reading problem (bracket start found, extent not), not a writing one.
- Bar 86 (reference bracket starts at bar 84): no bracket predicted in bars 84-86 (a bracket stop at 82 only); bar 86 is D#6 E6, reference D#7 E7. Missed bracket.
- Bars 14/86 are covered by brackets that begin earlier or on the previous system, so continuation lines are the weak spot.
- Lower staff has false 8va marks (e.g. bar 1), which also shift pitches there.
