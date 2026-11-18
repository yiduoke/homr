# Pairing models on the 28 real scans: same GPU pipeline, same merger, same scorer (D28)

Pooled = pitch counted in the aligned bar on either staff (a piece whose parts have different bar counts, e.g. Petrushka, has no joint bar list and carries its per-staff numbers, marked `*`). Bars = bars per output part (reference in the second column; `x2` = two parts with that count). Hands = share of output bars where both hands point to the same reference bar (`hand_sync.py`, two-staff pieces only). Delta = pooled pitch of the model minus the shipped control (same box, GPU, merger by staff role).

## pooled pitch F1

| piece | control | rb2 | rb3 | rb2 - ctl | rb3 - ctl |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.5 | 99.5 | 99.5 | +0.0 | +0.0 |
| bach-italian-concerto-2 | 98.9 | 98.9 | 98.9 | +0.0 | +0.0 |
| bach-prelude-873 | 99.4 | 99.4 | 99.4 | +0.0 | +0.0 |
| beethoven-appassionata-1 | 99.0 | 99.0 | 99.0 | +0.0 | +0.0 |
| beethoven-hammerklavier-4 | 96.5 | 96.5 | 96.5 | +0.0 | +0.0 |
| beethoven-waldstein-1 | 99.2 | 99.2 | 99.2 | +0.0 | +0.0 |
| chopin-etude-op10-4 | 95.8 | 95.8 | 95.8 | +0.0 | +0.0 |
| chopin-etude-op25-10 | 96.1 | 96.1 | 96.1 | +0.0 | +0.0 |
| chopin-etude-op25-11 | 89.2 | 89.2 | 89.2 | +0.0 | +0.0 |
| chopin-polonaise-op53 | 91.5 | 91.5 | 91.5 | +0.0 | +0.0 |
| chopin-scherzo3 | 92.9 | 92.9 | 92.9 | +0.0 | +0.0 |
| debussy-pour-le-piano-1 | 92.2 | 92.2 | 92.2 | +0.0 | +0.0 |
| debussy-reflets | 86.6 | 86.6 | 86.6 | +0.0 | +0.0 |
| haydn-hob16-49-1 | 95.4 | 95.4 | 95.4 | +0.0 | +0.0 |
| liszt-hr-6 | 91.9 | 91.9 | 91.9 | +0.0 | +0.0 |
| liszt-paganini-6 | 91.0 | 91.0 | 91.0 | +0.0 | +0.0 |
| liszt-sonata (Schott) | 80.5 | 86.9 | 88.2 | +6.4 | +7.8 |
| liszt-te-10 (Schott) | 77.9 | 91.2 | 88.6 | +13.2 | +10.7 |
| liszt-te-5 (Schott) | 78.0 | 79.5 | 79.5 | +1.5 | +1.5 |
| mozart-k475 | 95.2 | 95.2 | 95.2 | +0.0 | +0.0 |
| prokofiev-toccata | 92.7 | 92.7 | 92.7 | +0.0 | +0.0 |
| ravel-alborada | 82.4 | 82.4 | 82.4 | +0.0 | +0.0 |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.2 | +0.0 | +0.0 |
| schubert-wanderer-3-4 | 96.2 | 96.2 | 96.2 | +0.0 | +0.0 |
| schumann-kreisleriana-1 | 97.0 | 97.0 | 97.0 | +0.0 | +0.0 |
| schumann-toccata | 91.7 | 91.7 | 91.7 | +0.0 | +0.0 |
| scriabin-sonata-5 | 89.1 | 89.1 | 89.1 | +0.0 | +0.0 |
| stravinsky-petrushka | 79.2 | 44.8* | 58.8* | -34.4 | -20.4 |
| **mean of 28** | 91.94 | 91.46 | 91.92 | -0.47 | -0.01 |
| **mean of the 25 non-Schott** | 93.51 | 92.14 | 92.70 | -1.38 | -0.81 |

## staff-sensitive pitch F1

| piece | control | rb2 | rb3 | rb2 - ctl | rb3 - ctl |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.5 | 99.5 | 99.5 | +0.0 | +0.0 |
| bach-italian-concerto-2 | 98.9 | 98.9 | 98.9 | +0.0 | +0.0 |
| bach-prelude-873 | 99.4 | 99.4 | 99.4 | +0.0 | +0.0 |
| beethoven-appassionata-1 | 98.9 | 98.9 | 98.9 | +0.0 | +0.0 |
| beethoven-hammerklavier-4 | 89.5 | 89.5 | 89.5 | +0.0 | +0.0 |
| beethoven-waldstein-1 | 93.9 | 93.9 | 93.9 | +0.0 | +0.0 |
| chopin-etude-op10-4 | 94.8 | 94.8 | 94.8 | +0.0 | +0.0 |
| chopin-etude-op25-10 | 96.1 | 96.1 | 96.1 | +0.0 | +0.0 |
| chopin-etude-op25-11 | 89.1 | 89.1 | 89.1 | +0.0 | +0.0 |
| chopin-polonaise-op53 | 89.2 | 89.2 | 89.2 | +0.0 | +0.0 |
| chopin-scherzo3 | 91.6 | 91.6 | 91.6 | +0.0 | +0.0 |
| debussy-pour-le-piano-1 | 91.8 | 91.8 | 91.8 | +0.0 | +0.0 |
| debussy-reflets | 86.0 | 86.0 | 86.0 | +0.0 | +0.0 |
| haydn-hob16-49-1 | 95.1 | 95.1 | 95.1 | +0.0 | +0.0 |
| liszt-hr-6 | 91.8 | 91.8 | 91.8 | +0.0 | +0.0 |
| liszt-paganini-6 | 90.7 | 90.7 | 90.7 | +0.0 | +0.0 |
| liszt-sonata (Schott) | 80.0 | 86.5 | 87.8 | +6.5 | +7.9 |
| liszt-te-10 (Schott) | 77.3 | 91.1 | 88.5 | +13.8 | +11.3 |
| liszt-te-5 (Schott) | 77.2 | 79.3 | 79.4 | +2.2 | +2.2 |
| mozart-k475 | 92.0 | 92.0 | 92.0 | +0.0 | +0.0 |
| prokofiev-toccata | 92.7 | 92.7 | 92.7 | +0.0 | +0.0 |
| ravel-alborada | 82.0 | 82.0 | 82.0 | +0.0 | +0.0 |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.2 | +0.0 | +0.0 |
| schubert-wanderer-3-4 | 94.8 | 94.8 | 94.8 | +0.0 | +0.0 |
| schumann-kreisleriana-1 | 95.9 | 95.9 | 95.9 | +0.0 | +0.0 |
| schumann-toccata | 91.1 | 91.1 | 91.1 | +0.0 | +0.0 |
| scriabin-sonata-5 | 89.1 | 89.1 | 89.1 | +0.0 | +0.0 |
| stravinsky-petrushka | 58.6 | 44.8 | 58.8 | -13.7 | +0.3 |
| **mean of 28** | 90.21 | 90.53 | 90.99 | +0.31 | +0.77 |
| **mean of the 25 non-Schott** | 91.66 | 91.12 | 91.68 | -0.55 | +0.01 |

## pooled +onset and pooled full note F1

| piece | ctl +onset | rb2 | rb3 | ctl full | rb2 | rb3 |
|---|---|---|---|---|---|---|
| bach-fugue-873 | 94.5 | 94.5 | 94.5 | 93.8 | 93.8 | 93.8 |
| bach-italian-concerto-2 | 94.2 | 94.2 | 94.2 | 93.7 | 93.7 | 93.7 |
| bach-prelude-873 | 97.2 | 97.2 | 97.2 | 96.9 | 96.9 | 96.9 |
| beethoven-appassionata-1 | 91.2 | 91.2 | 91.2 | 90.4 | 90.4 | 90.4 |
| beethoven-hammerklavier-4 | 89.8 | 89.8 | 89.8 | 89.0 | 89.0 | 89.0 |
| beethoven-waldstein-1 | 95.2 | 95.2 | 95.2 | 94.6 | 94.6 | 94.6 |
| chopin-etude-op10-4 | 94.1 | 94.1 | 94.1 | 93.9 | 93.9 | 93.9 |
| chopin-etude-op25-10 | 69.1 | 69.1 | 69.1 | 65.0 | 65.0 | 65.0 |
| chopin-etude-op25-11 | 54.2 | 54.2 | 54.2 | 51.2 | 51.2 | 51.2 |
| chopin-polonaise-op53 | 73.2 | 73.2 | 73.2 | 68.9 | 68.9 | 68.9 |
| chopin-scherzo3 | 90.4 | 90.4 | 90.4 | 89.5 | 89.5 | 89.5 |
| debussy-pour-le-piano-1 | 77.7 | 77.7 | 77.7 | 77.0 | 77.0 | 77.0 |
| debussy-reflets | 48.7 | 48.7 | 48.7 | 45.2 | 45.2 | 45.2 |
| haydn-hob16-49-1 | 86.5 | 86.5 | 86.5 | 85.7 | 85.7 | 85.7 |
| liszt-hr-6 | 81.9 | 81.9 | 81.9 | 81.3 | 81.3 | 81.3 |
| liszt-paganini-6 | 64.3 | 64.3 | 64.3 | 61.7 | 61.7 | 61.7 |
| liszt-sonata | 64.6 | 74.5 | 76.5 | 62.4 | 72.6 | 74.6 |
| liszt-te-10 | 31.2 | 49.8 | 45.3 | 22.4 | 43.0 | 38.5 |
| liszt-te-5 | 61.6 | 65.1 | 66.5 | 59.7 | 63.8 | 65.4 |
| mozart-k475 | 68.2 | 68.2 | 68.2 | 65.1 | 65.1 | 65.1 |
| prokofiev-toccata | 82.1 | 82.1 | 82.1 | 81.2 | 81.2 | 81.2 |
| ravel-alborada | 60.2 | 60.2 | 60.2 | 57.6 | 57.6 | 57.6 |
| schubert-impromptu-d899-4 | 98.6 | 98.6 | 98.6 | 98.6 | 98.6 | 98.6 |
| schubert-wanderer-3-4 | 94.9 | 94.9 | 94.9 | 94.4 | 94.4 | 94.4 |
| schumann-kreisleriana-1 | 71.5 | 71.5 | 71.5 | 67.2 | 67.2 | 67.2 |
| schumann-toccata | 82.4 | 82.4 | 82.4 | 80.8 | 80.8 | 80.8 |
| scriabin-sonata-5 | 73.2 | 73.2 | 73.2 | 70.6 | 70.6 | 70.6 |
| stravinsky-petrushka | 59.1 | 32.2 | 43.7 | 54.2 | 29.5 | 40.2 |
| **mean of 28** | 76.77 | 76.95 | 77.32 | 74.72 | 75.08 | 75.43 |

## Bars per part, equality with the reference, hands in the same bar

| piece | ref bars | ctl bars | eq | hands % | rb2 bars | eq | hands % | rb3 bars | eq | hands % |
|---|---|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 71 | 71x2 | yes | 100 | 71x2 | yes | 100 | 71x2 | yes | 100 |
| bach-italian-concerto-2 | 49 | 49x2 | yes | 100 | 49x2 | yes | 100 | 49x2 | yes | 100 |
| bach-prelude-873 | 62 | 62x2 | yes | 100 | 62x2 | yes | 100 | 62x2 | yes | 100 |
| beethoven-appassionata-1 | 264 | 264x2 | yes | 100 | 264x2 | yes | 100 | 264x2 | yes | 100 |
| beethoven-hammerklavier-4 | 406 | 406x2 | yes | 98 | 406x2 | yes | 98 | 406x2 | yes | 98 |
| beethoven-waldstein-1 | 304 | 304x2 | yes | 100 | 304x2 | yes | 100 | 304x2 | yes | 100 |
| chopin-etude-op10-4 | 83 | 83x2 | yes | 100 | 83x2 | yes | 100 | 83x2 | yes | 100 |
| chopin-etude-op25-10 | 119 | 119x2 | yes | 100 | 119x2 | yes | 100 | 119x2 | yes | 100 |
| chopin-etude-op25-11 | 96 | 96x2 | yes | 97 | 96x2 | yes | 97 | 96x2 | yes | 97 |
| chopin-polonaise-op53 | 181 | 181x2 | yes | 100 | 181x2 | yes | 100 | 181x2 | yes | 100 |
| chopin-scherzo3 | 649 | 648x2 | NO | 96 | 648x2 | NO | 96 | 648x2 | NO | 96 |
| debussy-pour-le-piano-1 | 162 | 163x2 | NO | 100 | 163x2 | NO | 100 | 163x2 | NO | 100 |
| debussy-reflets | 95 | 94x2 | NO | 98 | 94x2 | NO | 98 | 94x2 | NO | 98 |
| haydn-hob16-49-1 | 220 | 223x2 | NO | 100 | 223x2 | NO | 100 | 223x2 | NO | 100 |
| liszt-hr-6 | 225 | 244x2 | NO | 100 | 244x2 | NO | 100 | 244x2 | NO | 100 |
| liszt-paganini-6 | 220 | 220x2 | yes | 98 | 220x2 | yes | 98 | 220x2 | yes | 98 |
| liszt-sonata | 305 | 307x2 | NO | 79 | 306x2 | NO | 93 | 304x2 | NO | 96 |
| liszt-te-10 | 182 | 181x2 | NO | 67 | 182x2 | yes | 95 | 182x2 | yes | 91 |
| liszt-te-5 | 134 | 134x2 | yes | 71 | 134x2 | yes | 88 | 133x2 | NO | 92 |
| mozart-k475 | 180 | 179x2 | NO | 99 | 179x2 | NO | 99 | 179x2 | NO | 99 |
| prokofiev-toccata | 226 | 227x2 | NO | 94 | 227x2 | NO | 94 | 227x2 | NO | 94 |
| ravel-alborada | 229 | 229x2 | yes | 96 | 229x2 | yes | 96 | 229x2 | yes | 96 |
| schubert-impromptu-d899-4 | 277 | 277x2 | yes | 100 | 277x2 | yes | 100 | 277x2 | yes | 100 |
| schubert-wanderer-3-4 | 475 | 476x2 | NO | 100 | 476x2 | NO | 100 | 476x2 | NO | 100 |
| schumann-kreisleriana-1 | 78 | 77x2 | NO | 100 | 77x2 | NO | 100 | 77x2 | NO | 100 |
| schumann-toccata | 283 | 275x2 | NO | 99 | 275x2 | NO | 99 | 275x2 | NO | 99 |
| scriabin-sonata-5 | 456 | 432x2 | NO | 97 | 432x2 | NO | 97 | 432x2 | NO | 97 |
| stravinsky-petrushka | 627 | 598x2 | NO | 81 | 475/390/390/286/286 | NO | 16 | 516/499/499 | NO | 14 |

shipped_merge_role_gpu: bar counts equal to the reference on 14 of 28 pieces; hands in the same bar, mean 95.3 % over 28 pieces, below 100 on 15.

relbrace2_gpu: bar counts equal to the reference on 15 of 28 pieces; hands in the same bar, mean 95.1 % over 28 pieces, below 100 on 15.

relbrace3_gpu: bar counts equal to the reference on 14 of 28 pieces; hands in the same bar, mean 95.1 % over 28 pieces, below 100 on 15.

## Regressions against the shipped control (task 4)

### relbrace2_gpu

* stravinsky-petrushka: pooled pitch -34.4; hands 16 % vs 81 %

Pooled change, all 28: stravinsky-petrushka -34.4, liszt-te-5 +1.5, liszt-sonata +6.4, liszt-te-10 +13.2

### relbrace3_gpu

* liszt-te-5: bars 133x2 vs control 134x2 (reference 134)
* stravinsky-petrushka: pooled pitch -20.4; hands 14 % vs 81 %

Pooled change, all 28: stravinsky-petrushka -20.4, liszt-te-5 +1.5, liszt-sonata +7.8, liszt-te-10 +10.7
