# Real-scan test set: released model (run2s7) vs upstream 566, 2026-11-16

F1 in %, micro over all notes; pitch / +onset / +onset+duration (full match). P, R = pitch inventory precision and recall of the released model. Bars = reference/ours. Released model code = `accidentals-run2` (without the `layout` branch). Petrushka and other Claude references are unchecked; see `test_set_plan.md`. Appassionata uses a repaired copy of ASAP's reference (12 measures had playback-expanded trills; original kept as `-reference-asap-original.musicxml`). Ravel and Hungarian Rhapsody 6 use references corrected to the 2 staves the scan prints (Ravel's third staff held only rests; Rhapsody 6's ossia staves are left out); originals kept as `-reference-original.musicxml`. Petrushka's pages print 2, 3 or 4 staves per system, so its row here is the standard scorer, which understates it (staff-ignored: ours 79.1 / 57.4 / 52.8, 566 77.3 / 54.2 / 49.6). The Liszt Schott pieces (Sonata, Etudes 5 and 10) fail staff pairing, see EXPERIMENTS T1.

| piece | bars | P | R | ours pitch | +onset | full | 566 pitch | +onset | full |
|---|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 71/71 | 100 | 98 | 99.0 | 94.0 | 93.3 | 96.2 | 93.0 | 91.8 |
| bach-italian-concerto-2 | 49/49 | 98 | 99 | 98.9 | 94.2 | 93.7 | 96.3 | 87.7 | 86.1 |
| bach-prelude-873 | 62/62 | 100 | 71 | 83.2 | 81.4 | 81.1 | 81.5 | 79.4 | 78.9 |
| balakirev-islamey | 344/346 | 86 | 88 | 87.2 | 57.3 | 54.3 | 83.7 | 53.4 | 51.0 |
| beethoven-appassionata-1 | 264/264 | 99 | 95 | 97.0 | 89.4 | 88.5 | 96.5 | 89.0 | 87.5 |
| beethoven-hammerklavier-4 | 406/406 | 90 | 69 | 78.3 | 72.0 | 71.3 | 76.3 | 68.0 | 67.4 |
| beethoven-waldstein-1 | 304/304 | 94 | 93 | 93.7 | 90.2 | 89.6 | 91.4 | 88.3 | 87.8 |
| chopin-etude-op10-4 | 83/83 | 95 | 94 | 94.8 | 93.1 | 92.9 | 89.5 | 87.2 | 86.9 |
| chopin-etude-op25-10 | 119/119 | 96 | 96 | 95.9 | 72.2 | 68.6 | 88.3 | 70.4 | 68.1 |
| chopin-etude-op25-11 | 96/96 | 89 | 88 | 88.5 | 53.4 | 50.4 | 82.9 | 56.5 | 54.9 |
| chopin-polonaise-op53 | 181/182 | 91 | 84 | 87.4 | 70.2 | 66.2 | 85.4 | 76.4 | 73.8 |
| chopin-scherzo3 | 649/648 | 92 | 92 | 91.8 | 89.6 | 88.8 | 87.9 | 85.9 | 85.0 |
| debussy-pour-le-piano-1 | 162/163 | 93 | 91 | 91.6 | 77.2 | 76.5 | 89.5 | 77.0 | 76.4 |
| debussy-reflets | 95/94 | 87 | 84 | 85.5 | 48.0 | 44.8 | 83.5 | 49.6 | 46.9 |
| haydn-hob16-49-1 | 220/222 | 95 | 95 | 95.1 | 86.8 | 86.0 | 94.2 | 87.4 | 86.5 |
| liszt-hr-6 | 225/244 | 92 | 91 | 91.6 | 81.6 | 81.0 | 83.9 | 73.0 | 72.2 |
| liszt-paganini-6 | 220/220 | 92 | 90 | 90.8 | 63.8 | 61.3 | 88.5 | 61.9 | 59.0 |
| liszt-sonata | 305/604 | 49 | 46 | 47.4 | 35.5 | 33.9 | 46.2 | 34.3 | 32.7 |
| liszt-te-10 | 182/358 | 52 | 53 | 52.3 | 18.0 | 11.3 | 53.1 | 18.9 | 12.5 |
| liszt-te-5 | 134/261 | 54 | 53 | 53.3 | 43.5 | 42.1 | 47.9 | 36.3 | 34.8 |
| mozart-k475 | 180/179 | 91 | 93 | 92.0 | 65.2 | 62.1 | 88.6 | 62.7 | 60.7 |
| prokofiev-toccata | 226/227 | 93 | 92 | 92.7 | 82.3 | 81.5 | 84.9 | 45.2 | 43.8 |
| ravel-alborada | 229/229 | 82 | 79 | 80.5 | 56.2 | 53.9 | 77.9 | 55.4 | 53.0 |
| schubert-impromptu-d899-4 | 277/277 | 97 | 97 | 96.7 | 95.8 | 95.7 | 96.1 | 95.0 | 95.0 |
| schubert-wanderer-3-4 | 475/476 | 94 | 96 | 94.9 | 93.5 | 93.0 | 93.0 | 78.2 | 77.5 |
| schumann-kreisleriana-1 | 78/77 | 96 | 96 | 95.8 | 71.4 | 67.2 | 94.6 | 69.6 | 65.4 |
| schumann-toccata | 283/275 | 91 | 92 | 91.2 | 82.5 | 80.9 | 90.7 | 82.2 | 80.4 |
| scriabin-sonata-5 | 456/432 | 73 | 66 | 69.1 | 56.0 | 53.9 | 66.7 | 50.0 | 47.5 |
| stravinsky-petrushka | 627/650 | 65 | 53 | 58.4 | 42.0 | 38.8 | 57.3 | 39.5 | 36.3 |

**Mean over 29 pieces**: ours 85.3 / 70.9 / 69.1, 566 82.5 / 67.3 / 65.5. Ours is ahead on full match in 24 of 29 pieces.
