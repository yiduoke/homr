# Run 2 evaluation: printed accidentals

Pipeline identical to run 1 (README.md): fp32 ONNX acc_run2 from vast-homr4:/workspace/onnx/acc_run2/, code run/acc_wt (accidentals-run2, uncommitted local configs.py edit), HOMR_FIXED_MARGIN=1, HOMR_TRUST_PAGE_TIME=1 for run1 and run2 (join_score.sh), score_notes defaults. Percent.

## 1. Pitch inventory F1

| Piece | 566 | control | run1 | run2 | run2-run1 |
|---|---|---|---|---|---|
| mazeppa | 76.7 | 78.7 | 78.6 | 77.0 | -1.6 |
| la-campanella | 75.2 | 77.3 | 79.4 | 82.6 | +3.2 |
| rachmaninoff-op3-2 | 68.9 | 68.6 | 68.8 | 70.1 | +1.4 |
| bach-prelude-848 | 93.6 | 91.2 | 91.4 | 93.6 | +2.2 |
| bach-fugue-848 | 86.5 | 83.8 | 83.8 | 87.2 | +3.4 |
| mozart-kv331-theme | 99.6 | 99.6 | 99.6 | 99.6 | +0.0 |
| mozart-kv309-1 | 99.2 | 99.2 | 99.1 | 98.4 | -0.7 |
| beethoven-pathetique-1 | 98.3 | 98.2 | 98.2 | 98.1 | -0.1 |
| mean | 87.3 | 87.1 | 87.4 | 88.3 | +1.0 |

## 1. Pitch+onset F1

| Piece | 566 | control | run1 | run2 | run2-run1 |
|---|---|---|---|---|---|
| mazeppa | 39.3 | 38.6 | 40.5 | 38.3 | -2.2 |
| la-campanella | 69.0 | 67.8 | 71.1 | 72.2 | +1.0 |
| rachmaninoff-op3-2 | 58.9 | 59.7 | 59.6 | 61.8 | +2.2 |
| bach-prelude-848 | 92.1 | 90.9 | 90.3 | 92.6 | +2.3 |
| bach-fugue-848 | 86.0 | 82.6 | 82.6 | 85.8 | +3.2 |
| mozart-kv331-theme | 99.6 | 99.6 | 99.6 | 99.6 | +0.0 |
| mozart-kv309-1 | 97.1 | 96.0 | 95.7 | 95.5 | -0.2 |
| beethoven-pathetique-1 | 97.2 | 96.7 | 97.2 | 96.5 | -0.7 |
| mean | 79.9 | 79.0 | 79.6 | 80.3 | +0.7 |

## 1. Pitch+onset+duration F1

| Piece | 566 | control | run1 | run2 | run2-run1 |
|---|---|---|---|---|---|
| mazeppa | 34.8 | 33.6 | 35.8 | 33.3 | -2.5 |
| la-campanella | 68.0 | 66.7 | 69.9 | 70.9 | +1.0 |
| rachmaninoff-op3-2 | 57.8 | 59.0 | 58.9 | 61.2 | +2.4 |
| bach-prelude-848 | 91.4 | 90.9 | 90.0 | 92.1 | +2.1 |
| bach-fugue-848 | 86.0 | 82.4 | 82.4 | 85.7 | +3.3 |
| mozart-kv331-theme | 99.6 | 99.6 | 99.6 | 99.6 | +0.0 |
| mozart-kv309-1 | 96.9 | 95.8 | 95.5 | 95.3 | -0.2 |
| beethoven-pathetique-1 | 97.0 | 96.5 | 97.0 | 96.3 | -0.7 |
| mean | 78.9 | 78.1 | 78.6 | 79.3 | +0.7 |

## 2a. Sounding pitch correct on matched notes (%)

| Piece | 566 | control | run1 | run2 |
|---|---|---|---|---|
| mazeppa | 95.8 | 95.4 | 95.5 | 94.7 |
| la-campanella | 94.9 | 94.4 | 93.2 | 97.2 |
| rachmaninoff-op3-2 | 93.9 | 94.3 | 94.3 | 96.2 |
| bach-prelude-848 | 99.2 | 96.5 | 97.0 | 99.5 |
| bach-fugue-848 | 98.9 | 95.8 | 95.8 | 99.4 |
| mozart-kv331-theme | 100.0 | 100.0 | 100.0 | 100.0 |
| mozart-kv309-1 | 99.0 | 99.0 | 99.0 | 99.0 |
| beethoven-pathetique-1 | 99.3 | 99.6 | 99.2 | 99.2 |
| all pooled | 97.2 | 96.7 | 96.3 | 97.8 |
| matched notes | 8581 | 8572 | 8787 | 8583 |

## 2b. Printed-accidental P/R/F1, pooled, all eight pieces, all matched notes

| Class | ref n | run1 P/R/F1 | run2 P/R/F1 |
|---|---|---|---|
| # | 476 | 1.9/0.2/0.4 | 87.6/84.2/85.9 |
| b | 209 | 0.0/0.0/0.0 | 84.9/94.3/89.3 |
| N | 386 | -/0.0/- | 83.1/82.6/82.9 |
| ## | 133 | 0.0/0.0/0.0 | 77.8/94.7/85.4 |
| bb | 0 | -/-/- | -/-/- |
| none | 7379 | 86.5/99.8/92.6 | 98.8/98.4/98.6 |

## 2b. Printed-accidental P/R/F1, pooled, all eight pieces, matched notes with right sounding pitch

| Class | ref n | run1 P/R/F1 | run2 P/R/F1 |
|---|---|---|---|
| # | 420 | 50.0/0.2/0.5 | 95.9/95.5/95.7 |
| b | 200 | 0.0/0.0/0.0 | 90.4/98.5/94.3 |
| N | 335 | -/0.0/- | 85.5/95.2/90.1 |
| ## | 127 | -/0.0/- | 94.7/99.2/96.9 |
| bb | 0 | -/-/- | -/-/- |
| none | 7308 | 88.2/100.0/93.7 | 99.5/98.6/99.1 |

## 2b. Printed-accidental P/R/F1, pooled, five KernScores/LilyPond pieces (verified-reference pieces), all matched notes

| Class | ref n | run1 P/R/F1 | run2 P/R/F1 |
|---|---|---|---|
| # | 151 | 0.0/0.0/0.0 | 93.6/97.4/95.5 |
| b | 140 | 0.0/0.0/0.0 | 83.1/98.6/90.2 |
| N | 211 | -/0.0/- | 83.7/92.4/87.8 |
| ## | 52 | 0.0/0.0/0.0 | 92.6/96.2/94.3 |
| bb | 0 | -/-/- | -/-/- |
| none | 3856 | 87.7/99.9/93.4 | 99.8/98.4/99.1 |

## 2b. Printed-accidental P/R/F1, pooled, five KernScores/LilyPond pieces (verified-reference pieces), matched notes with right sounding pitch

| Class | ref n | run1 P/R/F1 | run2 P/R/F1 |
|---|---|---|---|
| # | 147 | -/0.0/- | 99.3/100.0/99.7 |
| b | 138 | -/0.0/- | 87.9/100.0/93.6 |
| N | 195 | -/0.0/- | 84.1/100.0/91.3 |
| ## | 51 | -/0.0/- | 100.0/98.0/99.0 |
| bb | 0 | -/-/- | -/-/- |
| none | 3846 | 88.7/100.0/94.0 | 100.0/98.5/99.2 |

## 2c. Printed-accidental per piece, run2 (P/R/F1, all matched notes)

| Piece | # | b | N | ## | bb | none |
|---|---|---|---|---|---|---|
| mazeppa | 90.5/88.1/89.3 (194) | 89.4/85.5/87.4 (69) | 87.2/78.8/82.8 (104) | -/0.0/- (1) | -/-/- (0) | 96.6/98.4/97.5 (1037) |
| la-campanella | 65.6/54.1/59.3 (74) | -/-/- (0) | 95.0/59.4/73.1 (32) | 79.5/93.9/86.1 (66) | -/-/- (0) | 98.3/99.1/98.7 (1796) |
| rachmaninoff-op3-2 | 84.3/75.4/79.6 (57) | -/-/- (0) | 62.2/59.0/60.5 (39) | 46.7/100.0/63.6 (14) | -/-/- (0) | 97.5/96.4/96.9 (690) |
| bach-prelude-848 | 100.0/33.3/50.0 (3) | -/-/- (0) | 100.0/100.0/100.0 (14) | 87.5/100.0/93.3 (14) | -/-/- (0) | 100.0/100.0/100.0 (366) |
| bach-fugue-848 | 100.0/33.3/50.0 (3) | 0.0/-/- (0) | 91.7/100.0/95.7 (11) | 94.7/94.7/94.7 (38) | -/-/- (0) | 99.7/99.7/99.7 (777) |
| mozart-kv331-theme | -/-/- (0) | -/-/- (0) | -/-/- (0) | -/-/- (0) | -/-/- (0) | 100.0/100.0/100.0 (119) |
| mozart-kv309-1 | 91.4/100.0/95.5 (85) | 89.5/100.0/94.4 (17) | 21.7/35.7/27.0 (14) | -/-/- (0) | -/-/- (0) | 100.0/97.9/98.9 (913) |
| beethoven-pathetique-1 | 96.8/100.0/98.4 (60) | 82.9/98.4/90.0 (123) | 89.7/95.9/92.7 (172) | -/-/- (0) | -/-/- (0) | 99.8/97.6/98.6 (1681) |

## 2d. Confusion (reference->predicted, matched notes, pooled all pieces)

| model | confusion |
|---|---|
| run1 | none->none: 7535, #->none: 474, N->none: 355, b->none: 216, ##->none: 136, N->#: 39, none->#: 14, N->b: 11, none->b: 4, #->##: 2, #->#: 1 |
| run2 | none->none: 7258, #->#: 401, N->N: 319, b->b: 197, ##->##: 126, none->N: 57, #->none: 44, N->#: 33, none->b: 27, N->none: 26, none->#: 24, #->##: 23, none->##: 13, b->none: 12, #->N: 8, N->b: 8, ##->none: 7 |

## 3. Key signatures and meter vs run 1

See key_summary.md and summary.md (Meter section), both now with run2 rows; old model entries unchanged (checked equal to the pre-run2 files).

## 4. Page regressions: run2 more than 2 points below run1 (pitch+onset+duration F1)

| Piece | Page | run1 | run2 | diff |
|---|---|---|---|---|
| mazeppa | page-08.musicxml | 13.8 | 10.9 | -2.9 |
| mazeppa | page-13.musicxml | 62.4 | 56.2 | -6.2 |
| mazeppa | page-14.musicxml | 68.3 | 62.9 | -5.3 |
| mazeppa | page-15.musicxml | 71.4 | 67.9 | -3.6 |
| mazeppa | page-16.musicxml | 56.2 | 42.1 | -14.1 |
| la-campanella | page-04.musicxml | 77.4 | 69.5 | -7.9 |
| la-campanella | page-07.musicxml | 75.8 | 65.6 | -10.2 |
| rachmaninoff-op3-2 | page-2.musicxml | 92.1 | 88.5 | -3.6 |
| mozart-kv309-1 | page-07.musicxml | 93.9 | 89.5 | -4.4 |
| beethoven-pathetique-1 | page-1.musicxml | 89.1 | 84.2 | -4.8 |

10 pages flagged. Pages improving by more than 2 points: 13.
