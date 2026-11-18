## relbrace3_gpu

27 pieces audited, 118483 reference notes, 117329 output notes; micro F1 loss 8.53 points; lost bars 52 of 6031 reference bars.

| category | events | F1 points lost, micro | macro (mean over pieces) | share of loss |
|---|---|---|---|---|
| octave | 3557 | 3.02 | 2.83 | 35 % |
| unaligned bar | 2702 | 1.14 | 0.83 | 13 % |
| accidental | 1198 | 1.02 | 1.05 | 12 % |
| extra | 1795 | 0.76 | 0.70 | 9 % |
| staff assignment | 883 | 0.75 | 0.62 | 9 % |
| whole event missing | 1270 | 0.54 | 0.56 | 6 % |
| chord member missing | 1197 | 0.51 | 0.42 | 6 % |
| step | 453 | 0.38 | 0.40 | 5 % |
| other | 450 | 0.38 | 0.38 | 4 % |
| clef | 48 | 0.04 | 0.03 | 0 % |

Repeated-note runs (>= 4 equal events on a staff in one bar): 6579 reference notes in runs; missed notes (7a+7b) 2467, of them 173 (7 %) inside such runs = 0.07 F1 points.

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
| liszt-sonata | 87.8 | 88.0 | 0.2/2 | 6.1 | 1.2 | 0.4 | 0.4 | 0.8 | 0.6 | 1.3 | 0.8 | octave 6.1, extra 1.3 |
| liszt-te-10 | 88.5 | 88.5 | 0.0/0 | 4.2 | 1.2 | 2.3 | 0.1 | 1.1 | 0.4 | 1.5 | 0.7 | octave 4.2, step 2.3 |
| liszt-te-5 | 79.4 | 80.9 | 1.9/1 | 12.6 | 1.4 | 0.8 | 0.1 | 1.2 | 0.9 | 0.9 | 0.9 | octave 12.6, unaligned bar 1.9 |
| mozart-k475 | 92.0 | 93.0 | 1.1/2 | 0.1 | 1.2 | 0.2 | 2.5 | 0.7 | 0.6 | 1.6 | 0.0 | staff assignment 2.5, extra 1.6 |
| prokofiev-toccata | 92.7 | 93.0 | 0.4/1 | 2.5 | 2.0 | 0.3 | 0.0 | 0.3 | 0.9 | 0.6 | 0.5 | octave 2.5, accidental 2.0 |
| ravel-alborada | 82.0 | 83.3 | 1.6/1 | 11.0 | 1.9 | 0.3 | 0.4 | 0.7 | 0.3 | 0.8 | 0.7 | octave 11.0, accidental 1.9 |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 0.0/0 | 0.0 | 0.7 | 0.0 | 0.0 | 0.0 | 0.0 | 0.1 | 0.0 | accidental 0.7, extra 0.1 |
| schubert-wanderer-3-4 | 94.8 | 94.9 | 0.1/0 | 1.4 | 0.4 | 0.1 | 1.4 | 0.1 | 0.1 | 1.5 | 0.1 | extra 1.5, octave 1.4 |
| schumann-kreisleriana-1 | 95.9 | 96.2 | 0.3/1 | 0.5 | 1.3 | 0.0 | 0.6 | 0.2 | 0.1 | 0.5 | 0.5 | accidental 1.3, staff assignment 0.6 |
| schumann-toccata | 91.1 | 94.1 | 3.1/12 | 1.0 | 0.9 | 0.2 | 0.2 | 0.0 | 0.4 | 2.9 | 0.1 | unaligned bar 3.1, extra 2.9 |
| scriabin-sonata-5 | 89.1 | 93.3 | 4.6/24 | 3.4 | 1.3 | 0.3 | 0.1 | 0.2 | 0.3 | 0.2 | 0.6 | unaligned bar 4.6, octave 3.4 |
