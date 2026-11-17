# Pooled-staff pitch table (visible notes only), 2026-11-17

Pooled = a pitch counts if it appears on either staff of the bar (bars are aligned again with staves ignored, so totals can differ by a few notes). Staff-sensitive = the pitch must be on the reference staff. Pitch inventory F1 in %; P and R are pooled precision and recall; +onset and full are pooled as well. Scriabin is scored against its reference without the stray 47-note second part (original kept). Petrushka is scored staff-ignored in both columns.

## Released model, per scan

| piece | staff-sensitive F1 | pooled P | pooled R | pooled F1 | pooled +onset | pooled full |
|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.6 | 99.4 | 99.7 | 99.6 | 94.5 | 93.8 |
| bach-italian-concerto-2 | 98.9 | 98.4 | 99.5 | 98.9 | 94.2 | 93.7 |
| bach-prelude-873 | 99.4 | 99.4 | 99.3 | 99.4 | 97.2 | 96.9 |
| beethoven-appassionata-1 | 98.8 | 99.1 | 98.8 | 99.0 | 91.2 | 90.3 |
| beethoven-hammerklavier-4 | 89.5 | 96.3 | 96.8 | 96.5 | 89.8 | 89.0 |
| beethoven-waldstein-1 | 94.2 | 99.5 | 99.5 | 99.5 | 96.0 | 95.4 |
| chopin-etude-op10-4 | 94.8 | 96.3 | 95.3 | 95.8 | 94.1 | 93.9 |
| chopin-etude-op25-10 | 96.0 | 96.0 | 96.0 | 96.0 | 72.3 | 68.7 |
| chopin-etude-op25-11 | 88.5 | 89.2 | 87.9 | 88.6 | 53.4 | 50.4 |
| chopin-polonaise-op53 | 89.0 | 93.0 | 89.7 | 91.3 | 73.5 | 69.3 |
| chopin-scherzo3 | 91.8 | 93.1 | 93.2 | 93.1 | 90.6 | 89.7 |
| debussy-pour-le-piano-1 | 91.8 | 93.1 | 91.5 | 92.3 | 77.4 | 76.7 |
| debussy-reflets | 85.2 | 86.8 | 84.9 | 85.8 | 48.0 | 44.7 |
| haydn-hob16-49-1 | 95.1 | 95.5 | 95.1 | 95.3 | 86.9 | 86.1 |
| liszt-hr-6 | 91.8 | 92.2 | 91.7 | 91.9 | 81.9 | 81.3 |
| liszt-paganini-6 | 90.7 | 92.2 | 90.0 | 91.1 | 64.1 | 61.5 |
| liszt-sonata | 48.8 | 54.0 | 53.7 | 53.8 | 42.7 | 41.1 |
| liszt-te-10 | 52.3 | 54.9 | 55.5 | 55.2 | 16.5 | 9.5 |
| liszt-te-5 | 53.3 | 57.7 | 56.1 | 56.9 | 45.8 | 44.4 |
| mozart-k475 | 92.0 | 94.5 | 95.9 | 95.2 | 67.4 | 64.2 |
| prokofiev-toccata | 92.8 | 93.3 | 92.2 | 92.8 | 82.4 | 81.6 |
| ravel-alborada | 81.7 | 82.3 | 82.0 | 82.1 | 60.1 | 57.5 |
| schubert-impromptu-d899-4 | 96.7 | 96.7 | 96.7 | 96.7 | 95.8 | 95.7 |
| schubert-wanderer-3-4 | 94.9 | 95.0 | 97.6 | 96.3 | 94.9 | 94.4 |
| schumann-kreisleriana-1 | 95.8 | 96.9 | 96.9 | 96.9 | 71.6 | 67.2 |
| schumann-toccata | 91.2 | 91.4 | 92.1 | 91.7 | 82.9 | 81.3 |
| scriabin-sonata-5 | 89.1 | 93.3 | 85.4 | 89.2 | 73.3 | 70.6 |
| stravinsky-petrushka | 58.3 | 88.8 | 71.4 | 79.2 | 59.4 | 54.6 |

## All checkpoints, mean over 28 scans

| model | staff-sensitive F1 | pooled F1 | pooled +onset | pooled full | scans at 97+ (staff-sensitive) | scans at 97+ (pooled) |
|---|---|---|---|---|---|---|
| released | 87.2 | 89.3 | 74.9 | 73.0 | 4 | 5 |
| run B | 86.0 | 88.2 | 74.7 | 72.8 | 4 | 5 |
| control s7 (unguarded loops) | 86.8 | 88.9 | 74.8 | 72.8 | 4 | 5 |
| control s11 (unguarded loops) | 87.0 | 89.1 | 75.0 | 73.0 | 5 | 7 |
| harder-data s7 | 87.2 | 89.3 | 74.9 | 72.9 | 4 | 7 |
| harder-data s11 | 87.2 | 89.3 | 75.1 | 73.1 | 4 | 6 |

Rendered (released, 28 pieces): staff-sensitive 95.2, pooled 95.3; at 97+ pooled: 15.
