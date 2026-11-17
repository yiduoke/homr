# Pooled-staff pitch table after the merger fixes (visible notes only), 2026-11-17

Visible notes only (`print-object="no"` and invisible noteheads are not counted). Scriabin is scored against its reference without the stray 47-note second part (original kept). **After-merger** = `merge_pages.py` keeps the simultaneous same-name parts of a page apart and gives the part with fewer bars on a page rests for the missing bars at the end of that page (the lost bars sit mid-page and cannot be located), so both hands have the same bars per page. This affects only liszt-sonata, liszt-te-5 and liszt-te-10 (tag `T_am`); the Schott staves are still not joined as grand staffs, that is handled separately. Run B has only its final files locally: not re-merged, its Schott rows keep the old doubled bars. **Petrushka is provisional**: it is scored staff-ignored with per-staff bar alignment in the staff-sensitive column (58.3), the pooled column uses one joint alignment (79.2) because the reference has three staves and ours two; the pooled figure is not verified. Rendered columns use the earlier outputs (not re-merged).

Pooled = a pitch counts if it appears on either staff of the aligned bar. Staff-sensitive = the pitch must be on the reference staff. Pitch inventory F1 in %; P, R, +onset and full are pooled. Bars = our bars per part / reference bars (a pair of numbers when the two hands have different counts).

## Released model, per scan

| piece | bars ours / ref | staff-sens pitch | staff-sens +onset | staff-sens full | pooled P | pooled R | pooled pitch | pooled +onset | pooled full |
|---|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 71 / 71 | 99.6 | 94.5 | 93.8 | 99.4 | 99.7 | 99.6 | 94.5 | 93.8 |
| bach-italian-concerto-2 | 49 / 49 | 98.9 | 94.2 | 93.7 | 98.4 | 99.5 | 98.9 | 94.2 | 93.7 |
| bach-prelude-873 | 62 / 62 | 99.4 | 97.2 | 96.9 | 99.4 | 99.3 | 99.4 | 97.2 | 96.9 |
| beethoven-appassionata-1 | 264 / 264 | 98.8 | 91.0 | 90.1 | 99.1 | 98.8 | 99.0 | 91.2 | 90.3 |
| beethoven-hammerklavier-4 | 406 / 406 | 89.5 | 83.0 | 82.3 | 96.3 | 96.8 | 96.5 | 89.8 | 89.0 |
| beethoven-waldstein-1 | 304 / 304 | 94.2 | 90.9 | 90.3 | 99.5 | 99.5 | 99.5 | 96.0 | 95.4 |
| chopin-etude-op10-4 | 83 / 83 | 94.8 | 93.1 | 92.9 | 96.3 | 95.3 | 95.8 | 94.1 | 93.9 |
| chopin-etude-op25-10 | 119 / 119 | 96.0 | 72.3 | 68.7 | 96.0 | 96.0 | 96.0 | 72.3 | 68.7 |
| chopin-etude-op25-11 | 96 / 96 | 88.5 | 53.4 | 50.4 | 89.2 | 87.9 | 88.6 | 53.4 | 50.4 |
| chopin-polonaise-op53 | 182 / 181 | 89.0 | 71.4 | 67.4 | 93.0 | 89.7 | 91.3 | 73.5 | 69.3 |
| chopin-scherzo3 | 648 / 649 | 91.8 | 89.6 | 88.8 | 93.1 | 93.2 | 93.1 | 90.6 | 89.7 |
| debussy-pour-le-piano-1 | 163 / 162 | 91.8 | 77.4 | 76.6 | 93.1 | 91.5 | 92.3 | 77.4 | 76.7 |
| debussy-reflets | 94 / 95 | 85.2 | 47.7 | 44.7 | 86.8 | 84.9 | 85.8 | 48.0 | 44.7 |
| haydn-hob16-49-1 | 222 / 220 | 95.1 | 86.8 | 86.0 | 95.5 | 95.1 | 95.3 | 86.9 | 86.1 |
| liszt-hr-6 | 244 / 225 | 91.8 | 81.8 | 81.2 | 92.2 | 91.7 | 91.9 | 81.9 | 81.3 |
| liszt-paganini-6 | 220 / 220 | 90.7 | 63.8 | 61.3 | 92.2 | 90.0 | 91.1 | 64.1 | 61.5 |
| liszt-sonata * | 306 / 305 | 81.0 | 66.0 | 63.8 | 81.8 | 81.3 | 81.5 | 66.9 | 64.6 |
| liszt-te-10 * | 182 / 182 | 79.1 | 31.7 | 23.0 | 79.4 | 80.3 | 79.8 | 32.1 | 23.2 |
| liszt-te-5 * | 134 / 134 | 77.0 | 62.3 | 60.4 | 79.0 | 76.7 | 77.8 | 62.6 | 60.7 |
| mozart-k475 | 179 / 180 | 92.0 | 65.2 | 62.1 | 94.5 | 95.9 | 95.2 | 67.4 | 64.2 |
| prokofiev-toccata | 227 / 226 | 92.8 | 82.3 | 81.5 | 93.3 | 92.2 | 92.8 | 82.4 | 81.6 |
| ravel-alborada | 229 / 229 | 81.7 | 59.7 | 57.3 | 82.3 | 82.0 | 82.1 | 60.1 | 57.5 |
| schubert-impromptu-d899-4 | 277 / 277 | 96.7 | 95.8 | 95.7 | 96.7 | 96.7 | 96.7 | 95.8 | 95.7 |
| schubert-wanderer-3-4 | 476 / 475 | 94.9 | 93.5 | 93.0 | 95.0 | 97.6 | 96.3 | 94.9 | 94.4 |
| schumann-kreisleriana-1 | 77 / 78 | 95.8 | 71.4 | 67.2 | 96.9 | 96.9 | 96.9 | 71.6 | 67.2 |
| schumann-toccata | 275 / 283 | 91.2 | 82.5 | 80.9 | 91.4 | 92.1 | 91.7 | 82.9 | 81.3 |
| scriabin-sonata-5 | 432 / 456 | 89.1 | 73.2 | 70.6 | 93.3 | 85.4 | 89.2 | 73.3 | 70.6 |
| stravinsky-petrushka (provisional) | 598 / 627 | 58.3 | 43.1 | 39.7 | 88.8 | 71.4 | 79.2 | 59.4 | 54.6 |

\* re-merged (after-merger). Bar counts equal to the reference: 14 of 28 scans.

## All checkpoints, mean over 28 scans

| model | staff-sens pitch | staff-sens +onset | staff-sens full | pooled pitch | pooled +onset | pooled full | at 97+ staff-sens | at 97+ pooled | worst piece staff-sens | worst piece pooled (without Petrushka) |
|---|---|---|---|---|---|---|---|---|---|---|
| released | 90.2 | 75.5 | 73.6 | 91.9 | 76.9 | 74.9 | 4 | 5 | stravinsky-petrushka 58.3 | liszt-te-5 77.8 |
| run B (not re-merged) | 86.0 | 73.0 | 71.2 | 88.2 | 74.7 | 72.8 | 4 | 5 | liszt-sonata 49.8 | liszt-te-5 54.5 |
| control s7 (unguarded loops) | 89.7 | 75.3 | 73.3 | 91.5 | 76.8 | 74.6 | 4 | 5 | stravinsky-petrushka 58.1 | liszt-te-5 78.9 |
| control s11 (unguarded loops) | 89.9 | 75.6 | 73.6 | 91.6 | 77.0 | 74.9 | 5 | 7 | stravinsky-petrushka 58.3 | liszt-te-10 77.8 |
| harder-data s7 | 90.1 | 75.5 | 73.5 | 91.8 | 76.9 | 74.9 | 4 | 7 | stravinsky-petrushka 58.3 | liszt-te-5 77.7 |
| harder-data s11 | 90.4 | 75.8 | 73.9 | 92.1 | 77.2 | 75.2 | 4 | 6 | stravinsky-petrushka 58.2 | liszt-te-10 80.8 |

Same means without Petrushka (provisional) and without the three Schott scans:

| model | staff-sens pitch (27) | pooled pitch (27) | staff-sens pitch (25) | pooled pitch (25) |
|---|---|---|---|---|
| released | 91.3 | 92.4 | 92.9 | 94.0 |
| run B (not re-merged) | 87.1 | 88.6 | 91.6 | 92.9 |
| control s7 (unguarded loops) | 90.9 | 91.9 | 92.4 | 93.5 |
| control s11 (unguarded loops) | 91.1 | 92.1 | 92.6 | 93.7 |
| harder-data s7 | 91.2 | 92.3 | 92.9 | 94.0 |
| harder-data s11 | 91.6 | 92.6 | 92.9 | 94.0 |

Rendered (released, 28 pieces): staff-sensitive 95.2, pooled 95.3; at 97+ pooled: 15.

## The three Schott Liszt scans, released model, step by step

Original = hands poured into one part (about twice the bars). Merge fix = parts kept apart, per-staff bar alignment (unequal bars, no pooled score possible). After-merger = parts lined up per page, joint bar alignment.

| piece | stage | bars ours / ref | staff-sens pitch | staff-sens +onset | pooled pitch | pooled +onset |
|---|---|---|---|---|---|---|
| liszt-sonata | original | 604 / 305 | 48.8 | 37.3 | 53.8 | 42.7 |
| liszt-sonata | merge fix, hands not lined up | 298/306 / 305 | 84.6 | 69.4 | n/a | n/a |
| liszt-sonata | after-merger | 306 / 305 | 81.0 | 66.0 | 81.5 | 66.9 |
| liszt-te-10 | original | 358 / 182 | 52.3 | 17.7 | 55.2 | 16.5 |
| liszt-te-10 | merge fix, hands not lined up | 176/182 / 182 | 86.0 | 34.9 | n/a | n/a |
| liszt-te-10 | after-merger | 182 / 182 | 79.1 | 31.7 | 79.8 | 32.1 |
| liszt-te-5 | original | 261 / 134 | 53.3 | 43.5 | 56.9 | 45.8 |
| liszt-te-5 | merge fix, hands not lined up | 132/129 / 134 | 82.6 | 67.4 | n/a | n/a |
| liszt-te-5 | after-merger | 134 / 134 | 77.0 | 62.3 | 77.8 | 62.6 |
