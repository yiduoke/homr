# Run 2 diagnosis: Mazeppa drop, K. 309 naturals, La Campanella sharps

Read-only analysis. Nothing in the reference or result files was changed. Scratch files (scripts, a no-repair re-join of run 2) are in
`/private/tmp/claude-501/-Users-yiduoke-Documents-homr/119c3411-9240-40f6-bf27-9eec4cc7d8e8/scratchpad/` (`norepair/<piece>/`).

## 0. Finding that changes the picture: merge_pages.py "restored accidentals" repair undoes run 2's printed naturals

`run/merge_pages.py` has a post-step written for run 1 (and 566): a pitch that took a non-key accidental earlier in the bar and later reverts
to exactly the key-signature spelling is "drift", and the later note is forced back to the first spelling. With printed-accidental decoding
the reversion is usually a printed natural/sharp. In run 2's per-page XML 208 of 209 (Mazeppa) and 129 of 129 (Campanella) such reversions carry an explicit sign
(run 1: 0 of 258 / 0 of 139). The repair rewrote 163 (Mazeppa) and 162 (Campanella) of run 2's notes. Example: La Campanella m121 F#@0.25 after F##@0 and E@0.75 after E#@0.5
(both printed in the PDF) were turned into F## and E#.

Re-joining run 2's page XML with the repair switched off (same HOMR_TRUST_PAGE_TIME, drop_minor_parts, score_notes):

| Piece | metric | run 2 (as reported) | run 2, no repair | run 1 |
|---|---|---|---|---|
| mazeppa | pitch inventory / +onset / +duration F1 | 77.0 / 38.3 / 33.3 | 79.0 / 38.7 / 33.7 | 78.6 / 40.5 / 35.8 |
| mazeppa | sounding pitch correct | 94.7 | 95.5 | 95.5 |
| la-campanella | pitch inv / +onset / +dur | 82.6 / 72.2 / 70.9 | 85.2 / 73.2 / 72.1 | 79.4 / 71.1 / 69.9 |
| la-campanella | sounding pitch | 97.2 | 99.2 | 93.2 |
| la-campanella | # P/R/F1 | 65.6 / 54.1 / 59.3 | 77.1 / 77.1 / 77.1 | |
| la-campanella | N recall | 59.4 | 89.7 | |
| la-campanella | ## F1 | 86.1 | 93.0 | |
| mozart-kv309-1 | pitch inv / +onset / +dur | 98.4 / 95.5 / 95.3 | 98.95 / 96.1 / 95.8 | 99.1 / 95.7 / 95.5 |
| mozart-kv309-1 | sounding pitch | 99.0 | 100.0 | 99.0 |
| mozart-kv309-1 | #, b P/R | 91.4/100, 89.5/100 | 100/100, 100/100 | |

(The 566 and run 1 columns are unaffected in kind: their repair fixes real drift. The repair has to become sign-aware or be skipped for run 2.)

## 1. Mazeppa, pages 8, 13, 14, 15, 16

Method: reference bar i and run 1 / run 2 bars are paired by score_notes' alignment; reference notes are matched by letter+octave+onset (accidental_eval.match).
Regression = note matched with right sounding pitch in run 1 but not in run 2 (pitch+onset level; durations not separated).
(a) same letter+onset exists in run 2 but sounding pitch differs; (c) reference bar unmatched in run 2; (b) everything else (letter or onset differs).
Run 2 has one predicted bar fewer from page 10 on (ref m80 unmatched in run 2), so all later pairs are index-shifted by one; that shift is not itself an error.

| Page | F1 run1 -> run2 | (a) accidental | (b) onset/pitch, no accidental | (c) alignment | gains run 2 over run 1 (not counted) |
|---|---|---|---|---|---|
| 8 | 13.8 -> 10.9 | 0 | 7 | 0 | 5 |
| 13 | 62.4 -> 56.2 | 1 | 19 | 0 | 7 |
| 14 | 68.3 -> 62.9 | 21 | 8 | 16 | 13 |
| 15 | 71.4 -> 67.9 | 10 | 24 | 0 | 32 |
| 16 | 56.2 -> 42.1 | 0 | 61 | 0 | 26 |
| total | | 32 | 119 | 16 | 83 |

Whole piece (all pages): (a) 34, (b) 160, (c) 22, against 152 gained notes (16 of those are (a) gains). With the repair off: (a) 37 vs 30 (a) gains, so the net accidental effect on Mazeppa is -7 notes, about 0.4 point of F1 on the worst page and nothing on pages 8, 13, 16.

(a) judged on the page images (bars checked: ref m107, m130, m136, m137, m141, m142, m145, p15 m169-172; the other p.14 bars follow the same pattern but were not individually viewed):
- p.15 m169, m171, m172 (10 notes): the system starting at printed bar 168 is read as key 0 in run 2 (pred m159-162, key_eval: key 0 for that system; the page shows one flat). B-flat with no printed sign then decodes as B natural. Reference right; model (key signature) wrong. Run 1 reads the same wrong key (0) but its sounding-pitch labels do not depend on it, so run 1 got the notes right by accident. This is a real cost of the label change.
- p.14 m137, m141, m142, m145 and p.12 m107, p.13 m130 (about 19 notes): the PDF prints a sharp or natural (page 12 bar 106 beat 4, page 13 bar 129 last chord natural on B, page 14 chords at bars 135, 139, 143 with several sharps); run 2 predicts no sign or a different sign, the carry then gives the wrong pitch. Reference right; model wrong.
- p.14 m136 (2 notes, C5/C6 at beat 0): printed bar 134 has no sign before the first C; reference has C# with a printed #. Reference wrong, run 2 right (run 1 "agrees" with the wrong reference).
- No carry-within-bar or tie-across-barline failure was found among the (a) notes.

(b) 119 notes: dense octave/tremolo passages (page 16 printed bars ~190-200; pages 13, 15). Differences are in onsets, doubled notes and which octave is kept, no accidental involved. Model variance: on page 16 the control model (same recipe as run 1, no new labels) scores 40.8, run 1 56.2, run 2 42.1, 566 66.6; on page 13: 59.4 / 65.5 / 62.4 / 56.2 (566 / control / run1 / run2); page 14: 64.7 / 61.6 / 68.3 / 62.9; page 15: 63.5 / 71.4 / 71.4 / 67.9. Mean |run1 - control| per page is 2.5 points, max 15.4.
(c) 16 notes: ref m135 is unmatched in run 2 on page 14 (run 1 aligned it); an alignment artefact (about 2 points of the page's 5.3 drop).

Share of the page drops explained by (a): p.8 0 of 2.9; p.13 about 0.2 of 6.2; p.14 about 3.0 of 5.3 (2.3 more from (c)); p.15 about 1.8 of 3.6; p.16 0 of 14.1. After the no-repair re-join the page F1 hardly move (p.13 57.0, p.14 61.6, p.15 69.3, p.16 42.4), so the repair does not explain the Mazeppa page drops; it explains the sounding-pitch figure (94.7 -> 95.5, equal to run 1).

## 2a. K. 309 naturals (mozart-kv309-1)

Run 2 N: precision 21.7 (5 of 23), recall 35.7. All 18 notes predicted N where the reference has none (m31, 50 x2, 63, 69, 77 x2, 81, 92, 105, 108, 118 x2, 120 x2, 128, 133, 145; reference bar numbers) were looked up on the PDF pages 2, 4, 5, 6, 7, 8, 9: the PDF prints a natural in every one of the 18 (checked 18 of 18; bar mapping inside a system may be off by one for m69/m77, the natural is there either way). Typical: page 8 bars 110, 112, 120 have a natural in front of D, C, F after a D#, C#, F# in the previous bar; page 4 bar 48 and bar 60; page 9 bars 125 and 137.
So these are reference errors. The reference rule (make_printed_refs.py) only creates a natural after an accidental in the same bar; the engraver (LilyPond 2.10.33 with cautionary naturals) also prints a natural in the bar after an alteration of the same letter (13 of 18 follow a bar with an alteration of that letter; hand corrections cover m1-31 only and still miss m31).
With the repair off, run 2 on K. 309 has sounding pitch 100%, # and b perfect, natural recall 100% (14 of 14); the remaining N "precision" is only these 18 reference gaps. Corrected reference: N would be 32 and P/R about 100/72 (all 23 predicted naturals right), F1 about 84 instead of 27 (60.9 with the repair off).

## 2b. La Campanella sharps (la-campanella, reference = Claude's transcription)

With the repair on, # F1 59: 74 reference #, 61 predicted. 40 matched, 22 #->none, 12 #->##, 12 none->#, 9 N->#. Most of the sounding-pitch disagreements (#->##, N->#, #->none with different pitch) were repair artefacts (see 0): after the repair is off, 44 sign mismatches remain, 34 with identical sounding pitch, 10 with different pitch.
Checked on the pages (15 bar groups, 8 notes of repair artefacts re-verified, rest on the no-repair file):
- Reference wrong, model right (sign printed by the reference, not in the PDF, or sign in the PDF missing in the reference): m38 A5#, A6# (PDF shows only double sharps; A# is in the key), m133 B5/B6 at 0.25, 0.5, 0.75 (PDF prints one sharp at beat 0 only; reference repeats it, 6 notes), m122 D3/D4/A3/A4 beat 1 and 2, m123 D4/D5 beat 0, m124 A5/A6 beat 0 and D6/D7 beats 1, 2 (the PDF prints a natural or sharp on every note of the alternating run; the reference has the sign only on the double sharps), m69 E6 beat 1.5 (PDF prints the sharp). 6 groups, 21 notes.
- Reference right, model wrong in the repaired file: m119/m120/m121 F#->F## and E natural->E# (printed in the PDF, run 2 predicted them but the repair reverted them): 5 groups, 10 notes. m64 B4@2 natural (PDF shows it), m69 D6#@1.75, D6#@2.625, E6@2.75 (PDF shows sharp, sharp, natural; run 2 had missed or the repair undid them): 4 groups. Of these the m119-121 and the m64 B4@2 cases are repair artefacts; the rest are model misses.
- Matching artefact, unverified on the image: m10, 14, 15, 19 (page 1, F5## present twice in the prediction, one without sign).
Not individually viewed: m65, m72, m75, m77, m81, m84, m95, m97, m99.
Conclusion for the sample: of the sign-only mismatches in the no-repair file most are reference problems (the transcription's printed signs do not follow the engraving where the same note repeats in a bar or alternates natural/sharp); the sounding-pitch errors that remain (10 notes, 99.2% sounding) are the real model errors.

## 3. Conclusions and fixes

1. Mazeppa drop: not caused by the printed-accidental decoding rule or labels as such. Of the lost matches, 119 (b) are model variance in dense passages (the control model is as far from run 1 as run 2 is), 16 (c) are an alignment gap, 32 (a) are accidental-related of which 10 are a key-signature misread (a real weakness of the new labels: sounding pitch now depends on the key being right) and about 19 are missed printed signs; 2 are reference errors. Net accidental effect on Mazeppa after the repair is removed: -7 notes of about 1400 matched. Run 2's page falls (p.16 -14, p.13 -6) are ordinary run-to-run variance. The sounding-pitch dip (94.7 vs 95.5) comes from the merge_pages repair, not from the model.
2. K. 309 naturals (F1 27) and Campanella sharps (F1 59): mostly reference problems in the printed-sign reference plus the repair artefact. K. 309: 18 of 18 predicted naturals are printed in the PDF. Campanella: after removing the repair # F1 is 77 and most of the rest are reference signs that do not follow the engraving. The model's real errors there are in dense chromatic runs (about 10 notes).
3. Fixes, in order of value:
   - Rule/postprocess: make the `merge_pages.py` accidental repair sign-aware (do not revert a note that carries an explicit printed sign) or skip it for run 2 models; rescore run 2 on all eight pieces (all sounding-pitch figures for run 2 above are understated).
   - Reference fix (K. 309): in `make_printed_refs.py` add the cautionary natural after an alteration of the same letter in the previous bar (check octave handling on page 8 bar 110, where one natural stands for the chord); then hand-check m32 onwards (only m1-31 are verified; m31 is missing a natural).
   - Reference fix (Campanella): the printed-sign layer should be re-derived with the engraver's rule (sign on the first of repeated notes only; sign on each note of alternating runs) and corrected from the PDF; known wrong: m38, m69 E6@1.5, m122-124, m133. Mazeppa m136 beat 0 (C#, no printed sign).
   - Model: the key-signature misread on Mazeppa p.15 system 168-171 (run 2 key 0, page 1 flat) costs 10 notes only in run 2; consider a post-step that takes the key from neighbouring systems when it flips for one system and flips back. Add training/validation weight on natural signs in dense chromatic runs (Campanella m64-69).
