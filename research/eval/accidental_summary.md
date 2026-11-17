# Printed-accidental scorer

Definitions: docstring of accidental_eval.py. Percent.

## 566

| Piece | ref file | matched (score_notes pitch+onset) | sounding pitch correct | ref signs | pred signs | # P/R/F1 | b P/R/F1 | N P/R/F1 | ## P/R/F1 | bb P/R/F1 | none P/R/F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mazeppa | reference.musicxml | 3075 (2719) | 95.1 | 2053 | 159 | 5.6/0.5/0.9 (418) | 0.0/0.0/0.0 (171) | -/0.0/- (219) | -/0.0/- (5) | -/-/- (0) | 74.4/99.5/85.2 (2262) |
| la-campanella | reference.musicxml | 3215 (2947) | 92.5 | 642 | 73 | 3.2/0.8/1.3 (125) | -/-/- (0) | -/0.0/- (67) | 0.0/0.0/0.0 (153) | -/-/- (0) | 89.9/99.6/94.5 (2870) |
| rachmaninoff-op3-2 | reference.musicxml | 1155 (1077) | 93.0 | 242 | 24 | 0.0/0.0/0.0 (89) | -/-/- (0) | -/0.0/- (60) | -/0.0/- (23) | -/-/- (0) | 86.2/99.8/92.5 (983) |
| bach-prelude-848 | reference-printed.musicxml | 792 (757) | 99.2 | 63 | 4 | -/0.0/- (7) | -/-/- (0) | -/0.0/- (29) | 0.0/0.0/0.0 (25) | -/-/- (0) | 92.8/100.0/96.2 (731) |
| bach-fugue-848 | reference-printed.musicxml | 1447 (1265) | 98.6 | 108 | 12 | -/0.0/- (7) | -/-/- (0) | -/0.0/- (21) | 0.0/0.0/0.0 (79) | -/-/- (0) | 93.0/99.8/96.3 (1340) |
| mozart-kv331-theme | reference-printed.musicxml | 241 (240) | 100.0 | 1 | 0 | -/0.0/- (1) | -/-/- (0) | -/-/- (0) | -/-/- (0) | -/-/- (0) | 99.6/100.0/99.8 (240) |
| mozart-kv309-1 | reference-printed.musicxml | 2344 (2320) | 99.4 | 189 | 13 | 0.0/0.0/0.0 (133) | 0.0/0.0/0.0 (36) | -/0.0/- (19) | -/-/- (0) | -/-/- (0) | 92.4/100.0/96.1 (2156) |
| beethoven-pathetique-1 | reference-printed.musicxml | 4313 (4268) | 99.0 | 523 | 19 | 0.0/0.0/0.0 (93) | 0.0/0.0/0.0 (186) | -/0.0/- (216) | -/-/- (0) | -/-/- (0) | 88.6/99.8/93.9 (3818) |
| chopin-ballade-4 | reference.musicxml | 4924 (4738) | 96.3 | 1331 | 72 | 0.0/0.0/0.0 (129) | 6.1/0.5/1.0 (365) | -/0.0/- (576) | -/0.0/- (1) | -/0.0/- (13) | 78.6/99.6/87.8 (3840) |

Sounding pitch correct over all pieces: 96.6 of 21506 matched notes. Confusion (reference->predicted, counts, all pieces): N->none: 1081, #->none: 984, b->none: 755, ##->none: 284, N->#: 84, N->b: 42, none->#: 36, #->##: 15, bb->none: 13, none->b: 12, none->##: 4, ##->#: 2, b->#: 1

Pooled over the 8 non-Ballade pieces: 16582 matched notes, printed sign right among matched notes 86.6.

| class | P | R | F1 | reference |
|---|---|---|---|---|
| # | 2.9 | 0.3 | 0.6 | 873 |
| b | 0.0 | 0.0 | 0.0 | 393 |
| N | - | 0.0 | - | 631 |
| ## | 0.0 | 0.0 | 0.0 | 285 |
| bb | - | - | - | 0 |
| none | 87.4 | 99.7 | 93.2 | 14400 |

Correct pairs (diagonal): none->none: 18188, #->#: 3, b->b: 2

## control

| Piece | ref file | matched (score_notes pitch+onset) | sounding pitch correct | ref signs | pred signs | # P/R/F1 | b P/R/F1 | N P/R/F1 | ## P/R/F1 | bb P/R/F1 | none P/R/F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mazeppa | reference.musicxml | 3041 (2664) | 94.8 | 2053 | 147 | 2.9/0.2/0.4 (446) | 5.0/0.6/1.0 (176) | -/0.0/- (231) | -/0.0/- (5) | -/-/- (0) | 72.9/99.7/84.2 (2183) |
| la-campanella | reference.musicxml | 3183 (2891) | 92.2 | 642 | 66 | 0.0/0.0/0.0 (135) | -/-/- (0) | -/0.0/- (68) | 0.0/0.0/0.0 (148) | -/-/- (0) | 89.6/99.6/94.3 (2832) |
| rachmaninoff-op3-2 | reference.musicxml | 1169 (1091) | 93.1 | 242 | 23 | 0.0/0.0/0.0 (88) | -/-/- (0) | -/0.0/- (58) | -/0.0/- (22) | -/-/- (0) | 86.8/99.8/92.8 (1001) |
| bach-prelude-848 | reference-printed.musicxml | 817 (747) | 96.8 | 63 | 0 | -/0.0/- (7) | -/-/- (0) | -/0.0/- (30) | -/0.0/- (25) | -/-/- (0) | 92.4/100.0/96.1 (755) |
| bach-fugue-848 | reference-printed.musicxml | 1437 (1214) | 95.0 | 108 | 5 | -/0.0/- (7) | -/-/- (0) | -/0.0/- (21) | 0.0/0.0/0.0 (79) | -/-/- (0) | 92.7/100.0/96.2 (1330) |
| mozart-kv331-theme | reference-printed.musicxml | 241 (240) | 100.0 | 1 | 0 | -/0.0/- (1) | -/-/- (0) | -/-/- (0) | -/-/- (0) | -/-/- (0) | 99.6/100.0/99.8 (240) |
| mozart-kv309-1 | reference-printed.musicxml | 2326 (2293) | 99.4 | 189 | 13 | 0.0/0.0/0.0 (133) | 0.0/0.0/0.0 (36) | -/0.0/- (19) | -/-/- (0) | -/-/- (0) | 92.4/100.0/96.0 (2138) |
| beethoven-pathetique-1 | reference-printed.musicxml | 4284 (4243) | 99.1 | 523 | 20 | 0.0/0.0/0.0 (93) | 0.0/0.0/0.0 (184) | -/0.0/- (216) | -/-/- (0) | -/-/- (0) | 88.6/99.8/93.8 (3791) |

Sounding pitch correct over all pieces: 96.1 of 16498 matched notes. Confusion (reference->predicted, counts, all pieces): #->none: 904, N->none: 544, b->none: 395, ##->none: 277, N->#: 78, none->#: 22, N->b: 21, none->b: 6, #->##: 5, ##->#: 2, none->##: 1

Pooled over the 8 non-Ballade pieces: 16498 matched notes, printed sign right among matched notes 86.3.

| class | P | R | F1 | reference |
|---|---|---|---|---|
| # | 1.0 | 0.1 | 0.2 | 910 |
| b | 3.6 | 0.3 | 0.5 | 396 |
| N | - | 0.0 | - | 643 |
| ## | 0.0 | 0.0 | 0.0 | 279 |
| bb | - | - | - | 0 |
| none | 87.0 | 99.8 | 93.0 | 14270 |

Correct pairs (diagonal): none->none: 14241, #->#: 1, b->b: 1

## run1

| Piece | ref file | matched (score_notes pitch+onset) | sounding pitch correct | ref signs | pred signs | # P/R/F1 | b P/R/F1 | N P/R/F1 | ## P/R/F1 | bb P/R/F1 | none P/R/F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mazeppa | reference.musicxml | 3174 (2796) | 94.9 | 2053 | 175 | 6.2/0.7/1.2 (448) | 0.0/0.0/0.0 (175) | -/0.0/- (258) | -/0.0/- (3) | -/-/- (0) | 73.4/99.6/84.5 (2290) |
| la-campanella | reference.musicxml | 3359 (3032) | 91.2 | 642 | 67 | 0.0/0.0/0.0 (154) | -/-/- (0) | -/0.0/- (78) | 0.0/0.0/0.0 (168) | -/-/- (0) | 88.8/99.6/93.9 (2959) |
| rachmaninoff-op3-2 | reference.musicxml | 1166 (1089) | 93.1 | 242 | 23 | 0.0/0.0/0.0 (88) | -/-/- (0) | -/0.0/- (58) | -/0.0/- (22) | -/-/- (0) | 86.8/99.8/92.8 (998) |
| bach-prelude-848 | reference-printed.musicxml | 802 (742) | 96.9 | 63 | 0 | -/0.0/- (7) | -/-/- (0) | -/0.0/- (29) | -/0.0/- (25) | -/-/- (0) | 92.4/100.0/96.0 (741) |
| bach-fugue-848 | reference-printed.musicxml | 1438 (1214) | 94.9 | 108 | 3 | -/0.0/- (7) | -/-/- (0) | -/0.0/- (21) | 0.0/0.0/0.0 (79) | -/-/- (0) | 92.7/100.0/96.2 (1331) |
| mozart-kv331-theme | reference-printed.musicxml | 241 (240) | 100.0 | 1 | 0 | -/0.0/- (1) | -/-/- (0) | -/-/- (0) | -/-/- (0) | -/-/- (0) | 99.6/100.0/99.8 (240) |
| mozart-kv309-1 | reference-printed.musicxml | 2319 (2286) | 99.4 | 189 | 13 | 0.0/0.0/0.0 (133) | 0.0/0.0/0.0 (36) | -/0.0/- (19) | -/-/- (0) | -/-/- (0) | 92.4/100.0/96.0 (2131) |
| beethoven-pathetique-1 | reference-printed.musicxml | 4313 (4266) | 99.0 | 523 | 19 | 0.0/0.0/0.0 (94) | 0.0/0.0/0.0 (187) | -/0.0/- (220) | -/-/- (0) | -/-/- (0) | 88.5/99.8/93.8 (3812) |

Sounding pitch correct over all pieces: 95.9 of 16812 matched notes. Confusion (reference->predicted, counts, all pieces): #->none: 925, N->none: 568, b->none: 398, ##->none: 297, N->#: 91, none->#: 30, N->b: 24, none->b: 4, #->##: 4, none->##: 1

Pooled over the 8 non-Ballade pieces: 16812 matched notes, printed sign right among matched notes 86.1.

| class | P | R | F1 | reference |
|---|---|---|---|---|
| # | 2.4 | 0.3 | 0.6 | 932 |
| b | 0.0 | 0.0 | 0.0 | 398 |
| N | - | 0.0 | - | 683 |
| ## | 0.0 | 0.0 | 0.0 | 297 |
| bb | - | - | - | 0 |
| none | 86.9 | 99.8 | 92.9 | 14502 |

Correct pairs (diagonal): none->none: 14467, #->#: 3

## run2

| Piece | ref file | matched (score_notes pitch+onset) | sounding pitch correct | ref signs | pred signs | # P/R/F1 | b P/R/F1 | N P/R/F1 | ## P/R/F1 | bb P/R/F1 | none P/R/F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mazeppa | reference.musicxml | 3029 (2671) | 95.3 | 2053 | 1643 | 93.2/90.3/91.7 (442) | 93.6/89.6/91.6 (164) | 86.7/92.1/89.3 (227) | 100.0/20.0/33.3 (5) | -/-/- (0) | 97.5/98.0/97.8 (2191) |
| la-campanella | reference.musicxml | 3203 (3121) | 99.0 | 642 | 622 | 80.7/79.6/80.1 (142) | 0.0/-/- (0) | 98.5/90.3/94.2 (72) | 94.2/93.6/93.9 (157) | -/-/- (0) | 98.5/98.8/98.7 (2832) |
| rachmaninoff-op3-2 | reference.musicxml | 1190 (1175) | 98.7 | 242 | 255 | 90.8/94.7/92.7 (94) | -/-/- (0) | 90.6/95.1/92.8 (61) | 88.0/95.7/91.7 (23) | -/-/- (0) | 99.6/98.7/99.2 (1012) |
| bach-prelude-848 | reference-printed.musicxml | 802 (765) | 99.8 | 63 | 63 | 85.7/85.7/85.7 (7) | -/-/- (0) | 96.7/100.0/98.3 (29) | 100.0/96.0/98.0 (25) | -/-/- (0) | 99.9/99.9/99.9 (741) |
| bach-fugue-848 | reference-printed.musicxml | 1431 (1270) | 99.7 | 108 | 108 | 85.7/85.7/85.7 (7) | 0.0/-/- (0) | 95.5/100.0/97.7 (21) | 98.7/96.2/97.4 (79) | -/-/- (0) | 99.7/99.7/99.7 (1324) |
| mozart-kv331-theme | reference-printed.musicxml | 241 (240) | 100.0 | 1 | 1 | 100.0/100.0/100.0 (1) | -/-/- (0) | -/-/- (0) | -/-/- (0) | -/-/- (0) | 100.0/100.0/100.0 (240) |
| mozart-kv309-1 | reference-printed.musicxml | 2307 (2291) | 100.0 | 189 | 227 | 100.0/100.0/100.0 (133) | 100.0/100.0/100.0 (36) | 33.3/100.0/50.0 (19) | -/-/- (0) | -/-/- (0) | 100.0/98.2/99.1 (2119) |
| beethoven-pathetique-1 | reference-printed.musicxml | 4283 (4271) | 99.8 | 523 | 559 | 98.9/100.0/99.5 (93) | 89.3/99.5/94.1 (184) | 91.4/98.1/94.6 (216) | -/-/- (0) | -/-/- (0) | 99.9/98.9/99.4 (3790) |

Sounding pitch correct over all pieces: 98.8 of 16486 matched notes. Confusion (reference->predicted, counts, all pieces): none->N: 77, #->none: 62, none->#: 56, none->b: 33, N->none: 21, ##->none: 17, #->N: 14, N->#: 11, b->none: 10, none->##: 10, b->N: 8, #->##: 3, ##->b: 1, ##->#: 1

Pooled over the 8 non-Ballade pieces: 16486 matched notes, printed sign right among matched notes 98.0.

| class | P | R | F1 | reference |
|---|---|---|---|---|
| # | 92.5 | 91.4 | 92.0 | 919 |
| b | 91.5 | 95.3 | 93.4 | 384 |
| N | 86.1 | 95.0 | 90.3 | 645 |
| ## | 95.4 | 93.4 | 94.4 | 289 |
| bb | - | - | - | 0 |
| none | 99.2 | 98.8 | 99.0 | 14249 |

Correct pairs (diagonal): none->none: 14073, #->#: 840, N->N: 613, b->b: 366, ##->##: 270

## run2s7

| Piece | ref file | matched (score_notes pitch+onset) | sounding pitch correct | ref signs | pred signs | # P/R/F1 | b P/R/F1 | N P/R/F1 | ## P/R/F1 | bb P/R/F1 | none P/R/F1 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mazeppa | reference.musicxml | 3027 (2682) | 95.8 | 2053 | 1685 | 93.4/91.7/92.5 (446) | 93.3/89.4/91.3 (170) | 86.3/92.3/89.2 (233) | -/0.0/- (3) | -/-/- (0) | 97.8/97.9/97.9 (2175) |
| la-campanella | reference.musicxml | 3190 (3138) | 99.5 | 642 | 626 | 80.4/82.6/81.5 (149) | -/-/- (0) | 97.0/84.4/90.3 (77) | 93.3/94.5/93.9 (163) | -/-/- (0) | 98.5/98.6/98.5 (2801) |
| rachmaninoff-op3-2 | reference.musicxml | 1159 (1144) | 98.7 | 242 | 250 | 92.1/95.3/93.7 (86) | -/-/- (0) | 88.7/94.8/91.7 (58) | 87.5/95.5/91.3 (22) | -/-/- (0) | 99.6/98.7/99.1 (993) |
| bach-prelude-848 | reference-printed.musicxml | 822 (773) | 99.8 | 63 | 63 | 85.7/85.7/85.7 (7) | -/-/- (0) | 96.9/100.0/98.4 (31) | 100.0/96.0/98.0 (25) | -/-/- (0) | 99.9/99.9/99.9 (759) |
| bach-fugue-848 | reference-printed.musicxml | 1433 (1269) | 99.7 | 108 | 109 | 85.7/85.7/85.7 (7) | -/-/- (0) | 95.5/100.0/97.7 (21) | 97.4/96.2/96.8 (78) | -/-/- (0) | 99.7/99.7/99.7 (1327) |
| mozart-kv331-theme | reference-printed.musicxml | 241 (240) | 100.0 | 1 | 1 | 100.0/100.0/100.0 (1) | -/-/- (0) | -/-/- (0) | -/-/- (0) | -/-/- (0) | 100.0/100.0/100.0 (240) |
| mozart-kv309-1 | reference-printed.musicxml | 2338 (2325) | 100.0 | 189 | 227 | 100.0/100.0/100.0 (133) | 100.0/100.0/100.0 (36) | 33.3/100.0/50.0 (19) | -/-/- (0) | -/-/- (0) | 100.0/98.2/99.1 (2150) |
| beethoven-pathetique-1 | reference-printed.musicxml | 4284 (4276) | 99.9 | 523 | 557 | 98.9/100.0/99.5 (93) | 89.7/98.9/94.1 (184) | 91.8/98.6/95.1 (216) | -/-/- (0) | -/-/- (0) | 99.9/98.9/99.4 (3791) |
| chopin-ballade-4 | reference.musicxml | 4911 (4813) | 98.1 | 1331 | 1323 | 96.9/99.2/98.0 (125) | 96.3/96.0/96.1 (351) | 96.9/96.9/96.9 (554) | 50.0/100.0/66.7 (1) | 100.0/92.9/96.3 (14) | 99.4/99.3/99.4 (3866) |

Sounding pitch correct over all pieces: 98.8 of 21405 matched notes. Confusion (reference->predicted, counts, all pieces): none->N: 92, none->#: 61, #->none: 50, none->b: 41, N->none: 40, b->none: 21, ##->none: 17, #->N: 16, none->##: 13, N->#: 11, b->N: 11, #->##: 3, N->b: 2, #->b: 1, b->#: 1, b->##: 1, bb->b: 1

Pooled over the 8 non-Ballade pieces: 16494 matched notes, printed sign right among matched notes 98.0.

| class | P | R | F1 | reference |
|---|---|---|---|---|
| # | 92.5 | 92.5 | 92.5 | 922 |
| b | 92.0 | 94.9 | 93.4 | 390 |
| N | 85.9 | 94.5 | 90.0 | 655 |
| ## | 94.5 | 94.2 | 94.3 | 291 |
| bb | - | - | - | 0 |
| none | 99.3 | 98.7 | 99.0 | 14236 |

Correct pairs (diagonal): none->none: 17895, N->N: 1156, #->#: 977, b->b: 707, ##->##: 275, bb->bb: 13

