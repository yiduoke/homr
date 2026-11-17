# Run 1 evaluation: complete time signatures

Pipeline and commands: README.md. Per-note scores in percent (F1; P and R in results.json).

## Pitch inventory F1

| Piece | 566 | control | run1 | run2 | run2s7 |
|---|---|---|---|---|---|
| mazeppa | 76.7 | 78.7 | 78.6 | 79.0 | 80.3 |
| la-campanella | 75.2 | 77.3 | 79.4 | 85.2 | 85.2 |
| rachmaninoff-op3-2 | 68.9 | 68.6 | 68.8 | 72.3 | 72.4 |
| bach-prelude-848 | 93.6 | 91.2 | 91.4 | 94.0 | 94.0 |
| bach-fugue-848 | 86.5 | 83.8 | 83.8 | 87.7 | 87.6 |
| mozart-kv331-theme | 99.6 | 99.6 | 99.6 | 99.6 | 99.6 |
| mozart-kv309-1 | 99.2 | 99.2 | 99.1 | 99.0 | 99.7 |
| beethoven-pathetique-1 | 98.3 | 98.2 | 98.2 | 99.2 | 99.4 |

## Pitch+onset F1

| Piece | 566 | control | run1 | run2 | run2s7 |
|---|---|---|---|---|---|
| mazeppa | 39.3 | 38.6 | 40.5 | 38.6 | 38.7 |
| la-campanella | 69.0 | 67.8 | 71.1 | 73.3 | 73.5 |
| rachmaninoff-op3-2 | 58.9 | 59.7 | 59.6 | 64.1 | 62.6 |
| bach-prelude-848 | 92.1 | 90.9 | 90.3 | 93.1 | 94.0 |
| bach-fugue-848 | 86.0 | 82.6 | 82.6 | 86.3 | 86.2 |
| mozart-kv331-theme | 99.6 | 99.6 | 99.6 | 99.6 | 99.6 |
| mozart-kv309-1 | 97.1 | 96.0 | 95.7 | 96.1 | 97.4 |
| beethoven-pathetique-1 | 97.2 | 96.7 | 97.2 | 97.3 | 97.4 |

## Pitch+onset+duration F1 (P / R in brackets)

| Piece | 566 | control | run1 | run2 | run2s7 |
|---|---|---|---|---|---|
| mazeppa | 34.8 (36.4 / 33.4) | 33.6 (35.2 / 32.2) | 35.8 (37.5 / 34.3) | 33.7 (35.2 / 32.3) | 33.6 (35.0 / 32.3) |
| la-campanella | 68.0 (67.6 / 68.3) | 66.7 (66.5 / 66.9) | 69.9 (69.7 / 70.1) | 72.1 (71.9 / 72.3) | 71.8 (71.4 / 72.1) |
| rachmaninoff-op3-2 | 57.8 (58.1 / 57.5) | 59.0 (59.4 / 58.7) | 58.9 (59.2 / 58.5) | 63.5 (63.6 / 63.4) | 61.7 (62.0 / 61.4) |
| bach-prelude-848 | 91.4 (91.4 / 91.4) | 90.9 (90.9 / 90.9) | 90.0 (90.0 / 90.0) | 92.6 (92.6 / 92.6) | 94.0 (94.0 / 94.0) |
| bach-fugue-848 | 86.0 (86.0 / 85.9) | 82.4 (82.5 / 82.4) | 82.4 (82.4 / 82.4) | 86.3 (86.3 / 86.3) | 86.0 (85.9 / 86.1) |
| mozart-kv331-theme | 99.6 (99.6 / 99.6) | 99.6 (99.6 / 99.6) | 99.6 (99.6 / 99.6) | 99.6 (99.6 / 99.6) | 99.6 (99.6 / 99.6) |
| mozart-kv309-1 | 96.9 (96.8 / 96.9) | 95.8 (95.7 / 95.8) | 95.5 (95.4 / 95.5) | 95.8 (95.9 / 95.7) | 97.1 (97.1 / 97.2) |
| beethoven-pathetique-1 | 97.0 (97.1 / 96.9) | 96.5 (96.6 / 96.4) | 97.0 (97.1 / 96.9) | 97.1 (97.2 / 97.0) | 97.2 (97.3 / 97.1) |

## Meter

Exact = number, denominator and symbol; numeric = number and denominator. Counts are printed signatures matched / printed in the reference. Change P/R: matched changes within +-1 aligned measure / predicted, / reference changes. Share = reference measures whose meter in effect matches.

| Piece | Model | printed | exact (symbol as printed) | exact (ref file symbol) | numeric | changes (ref / pred / hit) | change P | change R | share |
|---|---|---|---|---|---|---|---|---|---|
| mazeppa | 566 | 8 | 2 | 2 | 6 | 7 / 2 / 2 | 100.0 | 28.6 | 81.7 |
| mazeppa | control | 8 | 2 | 2 | 5 | 7 / 1 / 1 | 100.0 | 14.3 | 71.8 |
| mazeppa | run1 | 8 | 4 | 4 | 5 | 7 / 2 / 2 | 100.0 | 28.6 | 60.4 |
| mazeppa | run2 | 8 | 5 | 5 | 6 | 7 / 2 / 2 | 100.0 | 28.6 | 81.7 |
| mazeppa | run2s7 | 8 | 5 | 5 | 6 | 7 / 2 / 2 | 100.0 | 28.6 | 83.2 |
| la-campanella | 566 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 98.0 |
| la-campanella | control | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 96.6 |
| la-campanella | run1 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 98.0 |
| la-campanella | run2 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 98.0 |
| la-campanella | run2s7 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 98.0 |
| rachmaninoff-op3-2 | 566 | 1 | 0 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 93.5 |
| rachmaninoff-op3-2 | control | 1 | 0 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 93.5 |
| rachmaninoff-op3-2 | run1 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 93.5 |
| rachmaninoff-op3-2 | run2 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 93.5 |
| rachmaninoff-op3-2 | run2s7 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 93.5 |
| bach-prelude-848 | 566 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-prelude-848 | control | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-prelude-848 | run1 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-prelude-848 | run2 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-prelude-848 | run2s7 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-fugue-848 | 566 | 1 | 0 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-fugue-848 | control | 1 | 0 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-fugue-848 | run1 | 1 | 1 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-fugue-848 | run2 | 1 | 1 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| bach-fugue-848 | run2s7 | 1 | 1 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv331-theme | 566 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv331-theme | control | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv331-theme | run1 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv331-theme | run2 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv331-theme | run2s7 | 1 | 1 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv309-1 | 566 | 1 | 0 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv309-1 | control | 1 | 0 | 1 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv309-1 | run1 | 1 | 1 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| mozart-kv309-1 | run2 | 1 | 1 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 99.4 |
| mozart-kv309-1 | run2s7 | 1 | 1 | 0 | 1 | 0 / 0 / 0 | n/a | n/a | 100.0 |
| beethoven-pathetique-1 | 566 | 6 | 0 | 6 | 6 | 5 / 5 / 5 | 100.0 | 100.0 | 100.0 |
| beethoven-pathetique-1 | control | 6 | 0 | 5 | 5 | 5 / 3 / 3 | 100.0 | 60.0 | 98.7 |
| beethoven-pathetique-1 | run1 | 6 | 4 | 2 | 6 | 5 / 5 / 5 | 100.0 | 100.0 | 100.0 |
| beethoven-pathetique-1 | run2 | 6 | 5 | 0 | 5 | 5 / 5 / 5 | 100.0 | 100.0 | 98.7 |
| beethoven-pathetique-1 | run2s7 | 6 | 5 | 0 | 5 | 5 / 3 / 3 | 100.0 | 60.0 | 60.3 |

Printed signatures per reference: mazeppa: m1 4/4 common, m28 3/2, m29 4/4 common, m55 4/4, m60 4/4 common, m115 6/8, m137 2/4, m183 4/4 common; la-campanella: m1 6/8; rachmaninoff-op3-2: m1 4/4 common; bach-prelude-848: m1 3/8; bach-fugue-848: m1 4/4; mozart-kv331-theme: m1 6/8; mozart-kv309-1: m1 4/4; beethoven-pathetique-1: m1 4/4, m11 2/2, m135 4/4, m139 2/2, m297 4/4, m301 2/2

## Page regressions (pitch+onset+duration F1; flagged when run1 is more than 2 points below 566 or control)

| Piece | Page | 566 | control | run1 | run2 | run2s7 | flag |
|---|---|---|---|---|---|---|---|
| mazeppa | page-03.musicxml | 23.0 | 31.9 | 31.7 | 33.9 | 33.9 | below run2, below run2s7 |
| mazeppa | page-04.musicxml | 30.4 | 30.2 | 30.2 | 30.2 | 30.2 |  |
| mazeppa | page-05.musicxml | 21.8 | 19.0 | 19.0 | 19.6 | 19.6 | below 566 |
| mazeppa | page-06.musicxml | 0.4 | 0.2 | 0.2 | 0.2 | 0.2 |  |
| mazeppa | page-07.musicxml | 18.3 | 18.3 | 20.2 | 26.3 | 20.2 | below run2 |
| mazeppa | page-08.musicxml | 14.5 | 13.8 | 13.8 | 10.9 | 12.0 |  |
| mazeppa | page-09.musicxml | 17.9 | 24.0 | 22.9 | 25.9 | 29.4 | below run2, below run2s7 |
| mazeppa | page-10.musicxml | 47.6 | 41.3 | 45.4 | 45.5 | 34.9 | below 566 |
| mazeppa | page-11.musicxml | n/a | n/a | n/a | n/a | n/a |  |
| mazeppa | page-12.musicxml | 5.4 | 9.1 | 8.9 | 9.1 | 10.3 |  |
| mazeppa | page-13.musicxml | 59.4 | 65.5 | 62.4 | 57.0 | 60.6 | below control |
| mazeppa | page-14.musicxml | 64.7 | 61.6 | 68.3 | 61.8 | 65.4 |  |
| mazeppa | page-15.musicxml | 63.5 | 71.4 | 71.4 | 69.3 | 69.8 |  |
| mazeppa | page-16.musicxml | 66.6 | 40.8 | 56.2 | 42.4 | 42.9 | below 566 |
| la-campanella | page-01.musicxml | 68.0 | 50.2 | 55.9 | 60.6 | 55.1 | below 566, below run2 |
| la-campanella | page-02.musicxml | 74.3 | 74.6 | 72.4 | 80.4 | 75.4 | below control, below run2, below run2s7 |
| la-campanella | page-03.musicxml | 89.0 | 82.8 | 85.9 | 92.2 | 92.1 | below 566, below run2, below run2s7 |
| la-campanella | page-04.musicxml | 68.6 | 77.4 | 77.4 | 71.8 | 80.2 | below run2s7 |
| la-campanella | page-05.musicxml | 14.3 | 13.4 | 14.4 | 16.8 | 16.8 | below run2, below run2s7 |
| la-campanella | page-06.musicxml | 24.6 | 24.3 | 29.0 | 26.4 | 33.8 | below run2s7 |
| la-campanella | page-07.musicxml | 75.8 | 75.8 | 75.8 | 66.1 | 68.7 |  |
| la-campanella | page-08.musicxml | 80.4 | 77.2 | 79.0 | 86.0 | 76.7 | below run2 |
| la-campanella | page-09.musicxml | 72.4 | 68.3 | 77.0 | 82.0 | 85.4 | below run2, below run2s7 |
| la-campanella | page-10.musicxml | 81.3 | 99.3 | 99.3 | 99.3 | 99.3 |  |
| rachmaninoff-op3-2 | page-1.musicxml | 86.9 | 86.9 | 86.5 | 100.0 | 89.4 | below run2, below run2s7 |
| rachmaninoff-op3-2 | page-2.musicxml | 86.5 | 92.1 | 92.1 | 91.7 | 94.8 | below run2s7 |
| rachmaninoff-op3-2 | page-3.musicxml | 78.4 | 84.9 | 85.7 | 88.0 | 89.0 | below run2, below run2s7 |
| rachmaninoff-op3-2 | page-4.musicxml | 46.1 | 42.6 | 42.3 | 45.0 | 45.3 | below 566, below run2, below run2s7 |
| rachmaninoff-op3-2 | page-5.musicxml | n/a | n/a | n/a | n/a | n/a |  |
| bach-prelude-848 | page-1.musicxml | 99.1 | 96.0 | 96.4 | 99.8 | 99.8 | below 566, below run2, below run2s7 |
| bach-prelude-848 | page-2.musicxml | 82.1 | 84.8 | 82.4 | 84.0 | 87.2 | below control, below run2s7 |
| bach-fugue-848 | page-1.musicxml | 85.9 | 79.5 | 79.3 | 86.3 | 86.1 | below 566, below run2, below run2s7 |
| bach-fugue-848 | page-2.musicxml | 86.0 | 85.1 | 85.2 | 86.2 | 85.9 |  |
| mozart-kv331-theme | page-1.musicxml | 99.6 | 99.6 | 99.6 | 99.6 | 99.6 |  |
| mozart-kv309-1 | page-01.musicxml | 100.0 | 91.4 | 90.8 | 94.3 | 100.0 | below 566, below run2, below run2s7 |
| mozart-kv309-1 | page-02.musicxml | 99.4 | 98.6 | 98.6 | 99.8 | 100.0 |  |
| mozart-kv309-1 | page-03.musicxml | 96.1 | 96.1 | 96.1 | 97.0 | 97.0 |  |
| mozart-kv309-1 | page-04.musicxml | 99.2 | 97.5 | 94.9 | 96.6 | 97.5 | below 566, below control, below run2s7 |
| mozart-kv309-1 | page-05.musicxml | 96.8 | 96.8 | 96.8 | 97.2 | 97.2 |  |
| mozart-kv309-1 | page-06.musicxml | 89.2 | 89.2 | 89.2 | 89.2 | 89.2 |  |
| mozart-kv309-1 | page-07.musicxml | 94.3 | 93.4 | 93.9 | 91.3 | 95.6 |  |
| mozart-kv309-1 | page-08.musicxml | 99.2 | 98.8 | 98.8 | 99.5 | 99.5 |  |
| mozart-kv309-1 | page-09.musicxml | 99.2 | 99.2 | 99.2 | 100.0 | 100.0 |  |
| mozart-kv309-1 | page-10.musicxml | 90.3 | 89.9 | 90.2 | 89.9 | 89.9 |  |
| beethoven-pathetique-1 | page-1.musicxml | 87.9 | 85.3 | 89.1 | 87.6 | 88.3 |  |
| beethoven-pathetique-1 | page-2.musicxml | 99.1 | 97.7 | 97.7 | 97.7 | 97.5 |  |
| beethoven-pathetique-1 | page-3.musicxml | 99.4 | 99.4 | 99.4 | 100.0 | 100.0 |  |
| beethoven-pathetique-1 | page-4.musicxml | 98.4 | 98.6 | 98.4 | 99.6 | 99.6 |  |
| beethoven-pathetique-1 | page-5.musicxml | 99.8 | 99.8 | 99.8 | 99.8 | 99.8 |  |
| beethoven-pathetique-1 | page-6.musicxml | 99.2 | 99.2 | 99.2 | 99.2 | 99.2 |  |
| beethoven-pathetique-1 | page-7.musicxml | 99.9 | 99.9 | 99.9 | 99.9 | 99.9 |  |
| beethoven-pathetique-1 | page-8.musicxml | 98.3 | 98.3 | 98.3 | 99.9 | 99.9 |  |
| beethoven-pathetique-1 | page-9.musicxml | 91.6 | 91.6 | 91.6 | 91.3 | 91.6 |  |
