## shipped_merge_role_gpu

28 pieces audited, 133966 reference notes, 129844 output notes; micro F1 loss 10.65 points; lost bars 113 of 6658 reference bars.

| category | events | F1 points lost, micro | macro (mean over pieces) | share of loss |
|---|---|---|---|---|
| octave | 4503 | 3.41 | 3.08 | 32 % |
| unaligned bar | 4437 | 1.67 | 1.15 | 16 % |
| chord member missing | 2987 | 1.13 | 0.65 | 11 % |
| accidental | 1423 | 1.08 | 1.08 | 10 % |
| extra | 2278 | 0.86 | 0.82 | 8 % |
| whole event missing | 2100 | 0.80 | 0.69 | 7 % |
| staff assignment | 899 | 0.68 | 0.61 | 6 % |
| step | 686 | 0.52 | 0.50 | 5 % |
| other | 553 | 0.42 | 0.42 | 4 % |
| clef | 96 | 0.07 | 0.05 | 1 % |

Repeated-note runs (>= 4 equal events on a staff in one bar): 6985 reference notes in runs; missed notes (7a+7b) 5087, of them 196 (4 %) inside such runs = 0.07 F1 points.

| piece | F1 audit | reading-only | lost bars | octave | accidental | step | wrong staff | missing event | missing chord member | extra | other | top two |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.5 | 99.5 | 0.0/0 | 0.0 | 0.1 | 0.1 | 0.0 | 0.0 | 0.0 | 0.2 | 0.0 | extra 0.2, step 0.1 |
| bach-italian-concerto-2 | 98.9 | 98.9 | 0.0/0 | 0.0 | 0.3 | 0.1 | 0.0 | 0.0 | 0.0 | 0.6 | 0.2 | extra 0.6, accidental 0.3 |
| bach-prelude-873 | 99.3 | 99.3 | 0.0/0 | 0.0 | 0.2 | 0.2 | 0.0 | 0.1 | 0.0 | 0.0 | 0.0 | step 0.2, accidental 0.2 |
| beethoven-appassionata-1 | 98.9 | 98.9 | 0.0/0 | 0.0 | 0.4 | 0.1 | 0.2 | 0.1 | 0.1 | 0.0 | 0.2 | accidental 0.4, other 0.2 |
| beethoven-hammerklavier-4 | 89.5 | 92.0 | 2.7/5 | 0.9 | 0.4 | 0.2 | 4.1 | 0.6 | 0.5 | 0.9 | 0.3 | staff assignment 4.1, unaligned bar 2.7 |
| beethoven-waldstein-1 | 94.0 | 96.2 | 2.3/0 | 0.1 | 0.2 | 0.0 | 1.1 | 0.4 | 1.5 | 0.1 | 0.3 | unaligned bar 2.3, chord member missing 1.5 |
| chopin-etude-op10-4 | 94.8 | 94.8 | 0.0/0 | 0.5 | 2.2 | 0.2 | 1.0 | 0.5 | 0.2 | 0.2 | 0.4 | accidental 2.2, staff assignment 1.0 |
| chopin-etude-op25-10 | 96.1 | 96.1 | 0.0/0 | 1.6 | 1.8 | 0.3 | 0.0 | 0.0 | 0.1 | 0.1 | 0.1 | accidental 1.8, octave 1.6 |
| chopin-etude-op25-11 | 89.2 | 89.2 | 0.0/0 | 7.8 | 1.0 | 0.8 | 0.0 | 0.9 | 0.0 | 0.1 | 0.1 | octave 7.8, accidental 1.0 |
| chopin-polonaise-op53 | 89.2 | 89.4 | 0.2/0 | 2.9 | 1.5 | 0.8 | 1.9 | 0.3 | 1.9 | 0.7 | 0.3 | octave 2.9, chord member missing 1.9 |
| chopin-scherzo3 | 91.7 | 92.0 | 0.4/2 | 5.1 | 0.5 | 0.4 | 0.8 | 0.3 | 0.2 | 0.3 | 0.3 | octave 5.1, staff assignment 0.8 |
| debussy-pour-le-piano-1 | 91.8 | 92.2 | 0.4/0 | 1.9 | 1.4 | 0.5 | 0.5 | 1.6 | 0.5 | 0.8 | 0.6 | octave 1.9, whole event missing 1.6 |
| debussy-reflets | 86.0 | 86.4 | 0.5/1 | 5.4 | 1.7 | 0.7 | 0.6 | 1.7 | 0.2 | 1.9 | 1.2 | octave 5.4, extra 1.9 |
| haydn-hob16-49-1 | 95.1 | 95.5 | 0.4/0 | 0.2 | 1.0 | 1.3 | 0.2 | 0.3 | 0.3 | 0.4 | 0.7 | step 1.3, accidental 1.0 |
| liszt-hr-6 | 91.8 | 93.9 | 2.3/0 | 1.7 | 0.9 | 0.1 | 0.1 | 1.9 | 0.7 | 0.2 | 0.3 | unaligned bar 2.3, whole event missing 1.9 |
| liszt-paganini-6 | 90.7 | 90.7 | 0.0/0 | 5.6 | 1.0 | 0.1 | 0.3 | 1.2 | 0.5 | 0.5 | 0.2 | octave 5.6, whole event missing 1.2 |
| liszt-sonata | 80.0 | 82.1 | 2.6/7 | 9.3 | 1.4 | 1.0 | 0.4 | 1.6 | 0.8 | 2.0 | 0.8 | octave 9.3, unaligned bar 2.6 |
| liszt-te-10 | 77.3 | 78.8 | 2.0/3 | 8.6 | 1.4 | 3.4 | 0.3 | 1.8 | 0.8 | 3.1 | 1.2 | octave 8.6, step 3.4 |
| liszt-te-5 | 77.2 | 79.6 | 3.1/4 | 10.0 | 1.8 | 1.2 | 0.3 | 1.5 | 0.8 | 2.4 | 1.5 | octave 10.0, unaligned bar 3.1 |
| mozart-k475 | 92.0 | 93.0 | 1.1/2 | 0.1 | 1.2 | 0.2 | 2.5 | 0.7 | 0.6 | 1.6 | 0.0 | staff assignment 2.5, extra 1.6 |
| prokofiev-toccata | 92.7 | 93.0 | 0.4/1 | 2.5 | 2.0 | 0.3 | 0.0 | 0.3 | 0.9 | 0.6 | 0.5 | octave 2.5, accidental 2.0 |
| ravel-alborada | 82.0 | 83.3 | 1.6/1 | 11.0 | 1.9 | 0.3 | 0.4 | 0.7 | 0.3 | 0.8 | 0.7 | octave 11.0, accidental 1.9 |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 0.0/0 | 0.0 | 0.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 | 0.0 | accidental 0.7, extra 0.1 |
| schubert-wanderer-3-4 | 94.8 | 94.9 | 0.1/0 | 1.4 | 0.4 | 0.1 | 1.4 | 0.1 | 0.1 | 1.5 | 0.1 | extra 1.5, octave 1.4 |
| schumann-kreisleriana-1 | 95.9 | 96.2 | 0.3/1 | 0.5 | 1.3 | 0.0 | 0.6 | 0.2 | 0.1 | 0.5 | 0.5 | accidental 1.3, staff assignment 0.6 |
| schumann-toccata | 91.1 | 94.1 | 3.1/12 | 1.0 | 0.9 | 0.2 | 0.2 | 0.0 | 0.4 | 2.9 | 0.1 | unaligned bar 3.1, extra 2.9 |
| scriabin-sonata-5 | 89.1 | 93.3 | 4.6/24 | 3.4 | 1.3 | 0.3 | 0.1 | 0.2 | 0.3 | 0.2 | 0.6 | unaligned bar 4.6, octave 3.4 |
| stravinsky-petrushka* | 79.2 | 82.6 | 4.1/50 | 4.8 | 1.4 | 0.9 | 0.0 | 2.3 | 6.2 | 0.5 | 0.4 | chord member missing 6.2, octave 4.8 |
