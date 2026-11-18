# Virtuoso real-scan pairs (pilot), 2026-11-17

Verified (scan crop of one piano system, tokens) pairs from IMSLP scans, labels from ASAP MusicXML. Built on the laptop only (homr integration_wt code, released weights
`pytorch_model_meteracc-r2s7-afae0e3`, `HOMR_FIXED_MARGIN=1`); no homr code changed. Times: 3:20-4:25 pm Pacific, 2026-11-17.

## Counts (crops)

| group | pieces | strong | hard | quarantined | note |
|---|---|---|---|---|---|
| A train | 19 | 712 | 14 | 222 | 60 of the quarantined are `octave_unverified` (see below) |
| B train (already in the rendered mixture) | 4 | 152 | 0 | 12 | |
| C validation (never train) | 3 | 104 | 0 | 18 | |
| train total (A+B) | 23 | 864 | 14 | 234 | **878 verified, target was about 1,500** |

Per piece and tier: `manifest.csv` (and `scripts/report.py`). Pitch F1 of the released model on the kept crops: strong mean 0.981 (median 0.995; >= 0.8 by definition), hard mean 0.73 (14 crops); by piece 0.95-1.00 for all but
Schubert D.899/1 (0.949); the hard crops are listed in `lists/train_hard.txt`.

## Files

- `images/<pid>/<pid>_p-NN_s<j>.png`: system crops (cut by homr's staff detection and `prepare_staff_image`, stored without the white canvas padding, like D6).
- `pages/<pdf>/p-NN.png`: full page, 150 dpi (`pdftoppm -r 150 -gray`), only pages that hold systems of the selected music. Beethoven Op.31/2 (Schirmer): each PDF page is a two-page spread with one half upside down; `scripts/split_b4.py` splits it in the middle and rotates halves upright (`pages/beethoven-op31-2-schirmer-split/p-NN.png`, NN = half-page number, PDF pages 14-22, two halves each); only the upright halves 1,4,5,8,9,12,13,16,17 (consecutive book pages) were used.
- `manifest.csv`: crop, page_image, page_bbox_xyxy (the crop region on that page, in page pixels), system_index (on the page, 0 = top), piece, pid, edition, group,
  asap_measure_range (1-based index in the ASAP part, not printed measure numbers; first-last), tier, verification, pitch_f1, bar_counter_groups, label_bars, reasons.
- `lists/{train_strong,train_hard,val_strong,val_hard,val,A_*,B_*,C_*}.txt`: `image.png,tokens.tokens` lines, paths relative to `run/` (same format as D6).
  `lists/*_octave_unverified.txt`: systems whose label and the model's read disagree on an 8va/8vb sign; NOT in the training lists, see "Gaps".
- `tokens/`: label token files (current format: printed accidental as lift, octave shifts as `octaveShift_8va/8vb` + `octaveShiftStop`, complete time signature only where the XML declares one in the first measure of the system).
- `quarantine.txt`: `image,tokens,reasons` for every non-kept system. `scripts/`: all code. `work/`: model reads (`reads/`), alignment (`assign/`), per-system records (`export/`), by-eye sheets (`eye_*`), `eye_wrong.json`.

## Method

1. Pages rendered at 150 dpi; homr detection (segnet, staff detection, relation model, `repair_systems`) per page; one crop per grand-staff system.
   If the relation model finds no grand staff on a page (missing braces: Beethoven Op.31/2 split pages 2, Liszt Peters 1 page) the detected staffs are paired top-down in `scripts/detect_pages.py` (homr untouched).
2. Page ranges of selected works inside the volumes found by eye (`scripts/pieces.py`). Pieces: Liszt TE1/TE3/TE9 in the Peters volume (pp. 3-5, 11-15, 69-81), Op.10/1 and Op.10/12 in Durand, Op.25/5 and /12 in Aibl, Sonata 2 mvt 2 and 4 in the Peters sonata file, etc.
3. Alignment (`scripts/align.py`): Viterbi over cumulative measure counts of the ASAP part (no repeat unfolding: the ASAP scores carry written repeats), the score of a system covering measures [s, s+L) is
   4 x bar-by-bar similarity of the released model's read + 1 x pitch-multiset F1 - penalty for differing from the barline counter's bar count (`scripts/crop_bars.py` from D6); gaps (skipped label measures) are allowed at a cost.
   All 26 pieces end exactly at the last measure (or one short), no gaps except one each in Op.25/5, Sonata 2 mvt 4 and Op.31/2.
4. Labels: `MeasureCutter.extract_measures` (training/omr_datasets/convert_lieder.py) on `music_xml_parser` output; octave brackets that continue across systems are repeated at the system start by that class.
5. Tiers. strong = barline-counter bar count equals the label's (or the model read does within 1 when the counter is undetermined, only with F1 >= 0.8) AND the model's pitch F1 >= 0.8. hard = bar count agrees, F1 < 0.8, plus guards: bar-by-bar similarity of the read with the assigned window >= 0.35 and no shifted window (+-3 measures, +-2 length) matching 0.05 better, a strong system within 6 systems in the same segment, key signature of label and read agree.
   Both tiers also need: the label and the read agree on whether an 8va/8vb sign appears in the system; trainer filters (vocabulary, length, at most 5 ledger lines); no irregular tuplet or two-octave shift in the converted measures.
6. By eye: engraving of the label measures (Verovio, `scripts/render_label.py`) under the crop (`scripts/eye.py`).

## Verification result (by eye)

- strong: random sample of 36 (seed 20261118): 0 wrong.
- hard: **only 16 hard crops existed after the guards (14 kept); all 16 were checked: 2 wrong** (Liszt TE1: label shifted by one measure, ASAP and Sauer text differ, the whole TE1 piece quarantined; Chopin Ballade 2: ASAP writes out trills that the print shows as trill signs). Before the guards 25 random hard crops were checked: 3 wrong (the two above kinds, plus Chopin Etude Op.25/12 systems whose label was shifted by one measure (page montage), fixed by the bar-by-bar alignment score; since the guards were added, such systems fail the shift check).
  The 40-crop sample asked for is not possible: the guards leave 14. Chopin Etude Op.25/12 and Liszt TE1 passed with shifted labels until the bar-by-bar score was added.
- Estimated label error rate (Clopper-Pearson, 95% upper bound): strong 0/36 = 0%, upper 9.7%; hard 2/16 (before removing them) = 12.5%, upper 38%; strong + hard pooled 2/52 = 3.8%, upper 13.2%. These are small samples: treat the bound as wide.
  Bias: strong = what the model already reads; hard = the model disagrees, and its disagreement is mostly the model, not the label (14 of 16 labels right).

## Quarantine reasons (all groups, crops)

ledger lines > 5: 59; octave-bracket disagreement label/read: 66 (52 A, 8 B, 6 C; the 60 of A+B and 6 of C are in `lists/*_octave_unverified.txt`); irregular tuplet the converter rounds: 39; conversion errors (durations not in the vocabulary) 20 and one two-octave shift; edition mismatch / key-signature difference / shifted label: 16;
alignment ambiguous: 11; not music of the piece (before/after, title): 11; vocabulary: 9; bar mismatch: 9; crop not one grand staff: 4; skipped before piece start: 3; octave shift (pitch classes agree, octaves differ): 3; label wrong by eye: 1. Total 252 (all groups).
Edition: no pairing used a repeat unfolding; Liszt TE1 (Peters/Sauer) was dropped as a piece; Op.25 Kullak, Op.111 Cotta, Op.110 Ricordi pieces align to the end with no gap, so their text agrees with ASAP where it was kept (edits that change notes would have shown as bar mismatch or low F1).

## Gaps (training set is 878, not 1,500)

The 23 training pieces have 208 music pages (not about 350) with 1,112 detected systems (5.3 per page); 878 of them are verified, so the target is missed by about 620 because the pieces are short, not because the filters are severe (234 quarantined). Candidates that would add ~170 from the same pieces: 60 octave-bracket crops after an eye check of the brackets, 54 over-5-ledger-line crops
(trainer filter), 39 irregular tuplets and 20 duration conversion errors. What the 878 contain: 122 + 2 crops with an octave bracket (47 continue from the previous system), few multi-bar repeated-note passages and no checked unnumbered-tuplet or cross-staff class (not labelled in the manifest). Extra works needed:
(1) multi-system octave-bracket continuations (Liszt Hungarian Rhapsodies, Paganini etudes outside the test set, Chopin Polonaise-Fantaisie, Rachmaninoff Etudes-Tableaux), (2) unnumbered tuplets (the irregular-tuplet quarantine needs a converter fix first), (3) repeated notes and chord repetition (Scarlatti-like, Chopin Etude Op.10/4 and Prokofiev are test pieces: use others),
(4) cross-staff and hand-crossing passages. Do not pad with easy classical pieces.

## Reproduce

`scripts/detect_pages.py`, `scripts/queue_reads.sh` (model reads), `scripts/run_all.sh <pid ...>` (align + export), `scripts/assemble.py` (copies, lists, manifest), `scripts/report.py`. The page images of `work/pages` were deleted to save disk; they re-render with `pdftoppm -r 150 -gray`.
