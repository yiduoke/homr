# Scan pilot, final comparison: SCAN minus CTRL_RENDER, seeds 7 and 11, 2026-11-17

Generated 2026-11-17 22:30 PST by `eval_run1/pilot_final_table.py`. Question (advisor): do real engravings add value beyond the notes themselves? Both arms start from the released `run2s7` weights, use the run3 recipe (6,716 updates, 256x1280) and see the same 881 passages 15 times in the mixture (R = 8), as the scanned crop (SCAN) or as the rendered twin (CTRL_RENDER). Spec: `scan_pairs_virtuoso/PILOT_SPEC.md`; plan: `PLAN.md` section 1, items 3 and 5. The training lists exclude every test piece and every validation work.

**Single run per arm and seed.** The earlier controls (same recipe, different seeds) differ per piece by 0.70 (mean absolute pooled-pitch difference per piece between seeds 7 and 11 of the earlier controls). A difference between the arms that is inside this spread, or that has a different sign in the two seeds, is not evidence of an effect; the tables mark it. Per-seed numbers are never averaged away: the spread is printed next to every mean.

## 1. Runs (28 real scans)

| column | tag | pieces scored | Schubert re-score | missing |
|---|---|---|---|---|
| released | `layout1` | 28 of 28 | existing -edition files | none |
| run3 ctrl s7 | `res_A_s7_gpu` | 28 of 28 | kept (already rescored) | none |
| run3 ctrl s11 | `res_A_s11_gpu` | 28 of 28 | kept (already rescored) | none |
| CTRL_RENDER s7 | `pilot_CTRL_RENDER_s7_gpu` | 28 of 28 | kept (already rescored) | none |
| CTRL_RENDER s11 | `pilot_CTRL_RENDER_s11_gpu` | 0 of 28 (partial) | no output | bach-fugue-873, bach-italian-concerto-2, bach-prelude-873, beethoven-appassionata-1, beethoven-hammerklavier-4, beethoven-waldstein-1, chopin-etude-op10-4, chopin-etude-op25-10, chopin-etude-op25-11, chopin-polonaise-op53, chopin-scherzo3, debussy-pour-le-piano-1, debussy-reflets, haydn-hob16-49-1, liszt-hr-6, liszt-paganini-6, liszt-sonata, liszt-te-10, liszt-te-5, mozart-k475, prokofiev-toccata, ravel-alborada, schubert-impromptu-d899-4, schubert-wanderer-3-4, schumann-kreisleriana-1, schumann-toccata, scriabin-sonata-5, stravinsky-petrushka |
| SCAN s7 | `pilot_SCAN_s7_gpu` | 28 of 28 | rescored note-scores+pooled+dense | none |
| SCAN s11 | `pilot_SCAN_s11_gpu` | 0 of 28 (partial) | no output | bach-fugue-873, bach-italian-concerto-2, bach-prelude-873, beethoven-appassionata-1, beethoven-hammerklavier-4, beethoven-waldstein-1, chopin-etude-op10-4, chopin-etude-op25-10, chopin-etude-op25-11, chopin-polonaise-op53, chopin-scherzo3, debussy-pour-le-piano-1, debussy-reflets, haydn-hob16-49-1, liszt-hr-6, liszt-paganini-6, liszt-sonata, liszt-te-10, liszt-te-5, mozart-k475, prokofiev-toccata, ravel-alborada, schubert-impromptu-d899-4, schubert-wanderer-3-4, schumann-kreisleriana-1, schumann-toccata, scriabin-sonata-5, stravinsky-petrushka |

## 2. Summary per run (macro means over the pieces scored)

| run | pieces | staff-sens pitch | staff-sens +onset | staff-sens full | pooled pitch | pooled +onset | pooled full | at 97 staff-sens | at 97 on every staff | at 97 pooled | worst piece (pooled) | bar count = ref | dense recall % | dense missed |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| released | 28 | 90.25 | 75.63 | 73.69 | 91.99 | 77.05 | 75.00 | 5 | n/a | 6 | liszt-te-5 77.8 | 14 of 28 | 87.37 | 8834 |
| run3 ctrl s7 | 28 | 90.07 | 75.46 | 73.48 | 91.79 | 76.88 | 74.78 | 5 | 5 | 6 | liszt-te-5 78.7 | 17 of 28 | 87.38 | 8828 |
| run3 ctrl s11 | 28 | 90.22 | 75.82 | 73.84 | 91.92 | 77.22 | 75.13 | 6 | 5 | 8 | liszt-te-10 77.8 | 12 of 28 | 87.28 | 8898 |
| CTRL_RENDER s7 | 28 | 90.38 | 76.35 | 74.48 | 92.13 | 77.78 | 75.81 | 5 | 5 | 7 | liszt-te-5 78.3 | 15 of 28 | 87.66 | 8636 |
| CTRL_RENDER s11 | 0 | missing | | | | | | | | | | | | |
| SCAN s7 | 28 | 89.81 | 75.11 | 73.07 | 91.67 | 76.54 | 74.39 | 5 | 5 | 6 | liszt-te-10 77.2 | 14 of 28 | 87.26 | 8912 |
| SCAN s11 | 0 | missing | | | | | | | | | | | | |

The released column is the laptop CPU run of the released model after the merger fixes (not the same hardware as the GPU columns; context only). The run3 columns are the same recipe with no pilot data. Petrushka is provisional (three reference staves against two of ours). `at 97 on every staff` = both printed staves at or above 97 staff-sensitive pitch F1.

### Seed spread of each arm (pooled pitch, s11 - s7 per piece)

| arm | pieces | mean absolute difference per piece | difference of the macro means |
|---|---|---|---|
| run3 ctrl | 28 | 0.70 | +0.13 |

## 3. SCAN minus CTRL_RENDER on the 28 scans (same seed = same start weights, list, steps and data order; only scanned crop against rendered twin differs)

* seed 7: CTRL_RENDER `pilot_CTRL_RENDER_s7_gpu`, SCAN `pilot_SCAN_s7_gpu`, 28 of 28 pieces in both
* seed 11: CTRL_RENDER `pilot_CTRL_RENDER_s11_gpu`, SCAN `pilot_SCAN_s11_gpu`, 0 of 28 pieces in both (left out: bach-fugue-873, bach-italian-concerto-2, bach-prelude-873, beethoven-appassionata-1, beethoven-hammerklavier-4, beethoven-waldstein-1, chopin-etude-op10-4, chopin-etude-op25-10, chopin-etude-op25-11, chopin-polonaise-op53, chopin-scherzo3, debussy-pour-le-piano-1, debussy-reflets, haydn-hob16-49-1, liszt-hr-6, liszt-paganini-6, liszt-sonata, liszt-te-10, liszt-te-5, mozart-k475, prokofiev-toccata, ravel-alborada, schubert-impromptu-d899-4, schubert-wanderer-3-4, schumann-kreisleriana-1, schumann-toccata, scriabin-sonata-5, stravinsky-petrushka)

### 3.1 pooled pitch F1

| piece | CTRL s7 | CTRL s11 | SCAN s7 | SCAN s11 | d s7 | d s11 | mean d +- range | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.5 | n/a | 99.4 | n/a | -0.07 | n/a | -0.07 | tie |
| bach-italian-concerto-2 | 98.8 | n/a | 98.6 | n/a | -0.21 | n/a | -0.21 | SCAN worse |
| bach-prelude-873 | 99.5 | n/a | 99.6 | n/a | +0.08 | n/a | +0.08 | tie |
| beethoven-appassionata-1 | 98.9 | n/a | 98.8 | n/a | -0.15 | n/a | -0.15 | SCAN worse |
| beethoven-hammerklavier-4 | 96.5 | n/a | 95.5 | n/a | -0.99 | n/a | -0.99 | SCAN worse |
| beethoven-waldstein-1 | 99.7 | n/a | 99.1 | n/a | -0.55 | n/a | -0.55 | SCAN worse |
| chopin-etude-op10-4 | 95.8 | n/a | 96.0 | n/a | +0.21 | n/a | +0.21 | SCAN better |
| chopin-etude-op25-10 | 96.9 | n/a | 96.6 | n/a | -0.28 | n/a | -0.28 | SCAN worse |
| chopin-etude-op25-11 | 88.3 | n/a | 86.7 | n/a | -1.58 | n/a | -1.58 | SCAN worse |
| chopin-polonaise-op53 | 92.1 | n/a | 92.6 | n/a | +0.53 | n/a | +0.53 | SCAN better |
| chopin-scherzo3 | 92.7 | n/a | 93.1 | n/a | +0.36 | n/a | +0.36 | SCAN better |
| debussy-pour-le-piano-1 | 93.4 | n/a | 92.7 | n/a | -0.63 | n/a | -0.63 | SCAN worse |
| debussy-reflets | 86.6 | n/a | 86.4 | n/a | -0.16 | n/a | -0.16 | SCAN worse |
| haydn-hob16-49-1 | 94.7 | n/a | 93.8 | n/a | -0.92 | n/a | -0.92 | SCAN worse |
| liszt-hr-6 | 92.5 | n/a | 92.5 | n/a | +0.01 | n/a | +0.01 | tie |
| liszt-paganini-6 | 89.2 | n/a | 88.8 | n/a | -0.41 | n/a | -0.41 | SCAN worse |
| liszt-sonata | 81.7 | n/a | 81.0 | n/a | -0.62 | n/a | -0.62 | SCAN worse |
| liszt-te-10 | 80.3 | n/a | 77.2 | n/a | -3.09 | n/a | -3.09 | SCAN worse |
| liszt-te-5 | 78.3 | n/a | 77.7 | n/a | -0.67 | n/a | -0.67 | SCAN worse |
| mozart-k475 | 94.9 | n/a | 95.5 | n/a | +0.53 | n/a | +0.53 | SCAN better |
| prokofiev-toccata | 93.0 | n/a | 93.4 | n/a | +0.45 | n/a | +0.45 | SCAN better |
| ravel-alborada | 81.5 | n/a | 81.7 | n/a | +0.23 | n/a | +0.23 | SCAN better |
| schubert-impromptu-d899-4 | 99.2 | n/a | 98.6 | n/a | -0.52 | n/a | -0.52 | SCAN worse |
| schubert-wanderer-3-4 | 96.3 | n/a | 96.5 | n/a | +0.19 | n/a | +0.19 | SCAN better |
| schumann-kreisleriana-1 | 97.5 | n/a | 95.5 | n/a | -2.02 | n/a | -2.02 | SCAN worse |
| schumann-toccata | 92.3 | n/a | 91.3 | n/a | -1.06 | n/a | -1.06 | SCAN worse |
| scriabin-sonata-5 | 90.2 | n/a | 89.3 | n/a | -0.89 | n/a | -0.89 | SCAN worse |
| stravinsky-petrushka | 79.4 | n/a | 78.7 | n/a | -0.63 | n/a | -0.63 | SCAN worse |

Mean SCAN - CTRL per seed: s7 -0.46 (28 pieces). SCAN better on 7, worse on 18, tie 3 (band 0.1); both seeds agree beyond the band on 0; sign test over the 25 decided pieces p = 0.043.

### 3.2 staff-sensitive pitch F1

| piece | CTRL s7 | CTRL s11 | SCAN s7 | SCAN s11 | d s7 | d s11 | mean d +- range | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.4 | n/a | 99.3 | n/a | -0.14 | n/a | -0.14 | SCAN worse |
| bach-italian-concerto-2 | 98.8 | n/a | 98.6 | n/a | -0.21 | n/a | -0.21 | SCAN worse |
| bach-prelude-873 | 99.5 | n/a | 99.5 | n/a | +0.00 | n/a | +0.00 | tie |
| beethoven-appassionata-1 | 98.8 | n/a | 98.2 | n/a | -0.52 | n/a | -0.52 | SCAN worse |
| beethoven-hammerklavier-4 | 89.2 | n/a | 89.1 | n/a | -0.13 | n/a | -0.13 | SCAN worse |
| beethoven-waldstein-1 | 94.3 | n/a | 93.9 | n/a | -0.48 | n/a | -0.48 | SCAN worse |
| chopin-etude-op10-4 | 94.8 | n/a | 95.2 | n/a | +0.38 | n/a | +0.38 | SCAN better |
| chopin-etude-op25-10 | 96.9 | n/a | 96.6 | n/a | -0.28 | n/a | -0.28 | SCAN worse |
| chopin-etude-op25-11 | 88.3 | n/a | 85.5 | n/a | -2.72 | n/a | -2.72 | SCAN worse |
| chopin-polonaise-op53 | 89.8 | n/a | 89.9 | n/a | +0.11 | n/a | +0.11 | SCAN better |
| chopin-scherzo3 | 91.3 | n/a | 91.4 | n/a | +0.10 | n/a | +0.10 | tie |
| debussy-pour-le-piano-1 | 92.8 | n/a | 91.1 | n/a | -1.74 | n/a | -1.74 | SCAN worse |
| debussy-reflets | 86.0 | n/a | 85.8 | n/a | -0.20 | n/a | -0.20 | SCAN worse |
| haydn-hob16-49-1 | 94.5 | n/a | 93.5 | n/a | -1.00 | n/a | -1.00 | SCAN worse |
| liszt-hr-6 | 92.4 | n/a | 92.3 | n/a | -0.09 | n/a | -0.09 | tie |
| liszt-paganini-6 | 88.8 | n/a | 88.1 | n/a | -0.71 | n/a | -0.71 | SCAN worse |
| liszt-sonata | 81.2 | n/a | 80.6 | n/a | -0.58 | n/a | -0.58 | SCAN worse |
| liszt-te-10 | 79.6 | n/a | 76.9 | n/a | -2.73 | n/a | -2.73 | SCAN worse |
| liszt-te-5 | 77.5 | n/a | 77.2 | n/a | -0.33 | n/a | -0.33 | SCAN worse |
| mozart-k475 | 91.8 | n/a | 92.2 | n/a | +0.44 | n/a | +0.44 | SCAN better |
| prokofiev-toccata | 92.9 | n/a | 92.9 | n/a | -0.02 | n/a | -0.02 | tie |
| ravel-alborada | 81.1 | n/a | 81.3 | n/a | +0.16 | n/a | +0.16 | SCAN better |
| schubert-impromptu-d899-4 | 99.2 | n/a | 98.6 | n/a | -0.56 | n/a | -0.56 | SCAN worse |
| schubert-wanderer-3-4 | 94.9 | n/a | 95.0 | n/a | +0.15 | n/a | +0.15 | SCAN better |
| schumann-kreisleriana-1 | 96.4 | n/a | 93.8 | n/a | -2.60 | n/a | -2.60 | SCAN worse |
| schumann-toccata | 91.8 | n/a | 90.6 | n/a | -1.22 | n/a | -1.22 | SCAN worse |
| scriabin-sonata-5 | 90.1 | n/a | 89.1 | n/a | -0.98 | n/a | -0.98 | SCAN worse |
| stravinsky-petrushka | 58.3 | n/a | 58.2 | n/a | -0.08 | n/a | -0.08 | tie |

Mean SCAN - CTRL per seed: s7 -0.57 (28 pieces). SCAN better on 5, worse on 18, tie 5 (band 0.1); both seeds agree beyond the band on 0; sign test over the 23 decided pieces p = 0.011.

### 3.3 staff-sensitive pitch+onset F1

| piece | CTRL s7 | CTRL s11 | SCAN s7 | SCAN s11 | d s7 | d s11 | mean d +- range | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 96.1 | n/a | 93.6 | n/a | -2.50 | n/a | -2.50 | SCAN worse |
| bach-italian-concerto-2 | 94.1 | n/a | 95.7 | n/a | +1.61 | n/a | +1.61 | SCAN better |
| bach-prelude-873 | 97.3 | n/a | 96.6 | n/a | -0.72 | n/a | -0.72 | SCAN worse |
| beethoven-appassionata-1 | 92.2 | n/a | 91.1 | n/a | -1.03 | n/a | -1.03 | SCAN worse |
| beethoven-hammerklavier-4 | 82.4 | n/a | 82.3 | n/a | -0.12 | n/a | -0.12 | SCAN worse |
| beethoven-waldstein-1 | 90.5 | n/a | 91.8 | n/a | +1.32 | n/a | +1.32 | SCAN better |
| chopin-etude-op10-4 | 92.1 | n/a | 94.8 | n/a | +2.70 | n/a | +2.70 | SCAN better |
| chopin-etude-op25-10 | 73.3 | n/a | 69.1 | n/a | -4.20 | n/a | -4.20 | SCAN worse |
| chopin-etude-op25-11 | 56.8 | n/a | 39.7 | n/a | -17.15 | n/a | -17.15 | SCAN worse |
| chopin-polonaise-op53 | 78.5 | n/a | 80.9 | n/a | +2.45 | n/a | +2.45 | SCAN better |
| chopin-scherzo3 | 89.6 | n/a | 89.3 | n/a | -0.22 | n/a | -0.22 | SCAN worse |
| debussy-pour-le-piano-1 | 78.4 | n/a | 74.3 | n/a | -4.08 | n/a | -4.08 | SCAN worse |
| debussy-reflets | 49.5 | n/a | 45.7 | n/a | -3.78 | n/a | -3.78 | SCAN worse |
| haydn-hob16-49-1 | 87.1 | n/a | 87.2 | n/a | +0.12 | n/a | +0.12 | SCAN better |
| liszt-hr-6 | 83.0 | n/a | 79.1 | n/a | -3.83 | n/a | -3.83 | SCAN worse |
| liszt-paganini-6 | 60.1 | n/a | 63.9 | n/a | +3.76 | n/a | +3.76 | SCAN better |
| liszt-sonata | 67.2 | n/a | 66.4 | n/a | -0.85 | n/a | -0.85 | SCAN worse |
| liszt-te-10 | 31.5 | n/a | 31.4 | n/a | -0.09 | n/a | -0.09 | tie |
| liszt-te-5 | 61.3 | n/a | 60.9 | n/a | -0.43 | n/a | -0.43 | SCAN worse |
| mozart-k475 | 69.0 | n/a | 74.9 | n/a | +5.85 | n/a | +5.85 | SCAN better |
| prokofiev-toccata | 83.3 | n/a | 82.2 | n/a | -1.08 | n/a | -1.08 | SCAN worse |
| ravel-alborada | 60.1 | n/a | 57.4 | n/a | -2.70 | n/a | -2.70 | SCAN worse |
| schubert-impromptu-d899-4 | 98.6 | n/a | 97.8 | n/a | -0.79 | n/a | -0.79 | SCAN worse |
| schubert-wanderer-3-4 | 93.4 | n/a | 94.0 | n/a | +0.61 | n/a | +0.61 | SCAN better |
| schumann-kreisleriana-1 | 72.1 | n/a | 67.2 | n/a | -4.87 | n/a | -4.87 | SCAN worse |
| schumann-toccata | 83.0 | n/a | 80.6 | n/a | -2.45 | n/a | -2.45 | SCAN worse |
| scriabin-sonata-5 | 74.4 | n/a | 72.1 | n/a | -2.33 | n/a | -2.33 | SCAN worse |
| stravinsky-petrushka | 43.2 | n/a | 43.2 | n/a | -0.06 | n/a | -0.06 | tie |

Mean SCAN - CTRL per seed: s7 -1.25 (28 pieces). SCAN better on 8, worse on 18, tie 2 (band 0.1); both seeds agree beyond the band on 0; sign test over the 26 decided pieces p = 0.076.

### 3.4 staff-sensitive full F1

| piece | CTRL s7 | CTRL s11 | SCAN s7 | SCAN s11 | d s7 | d s11 | mean d +- range | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 95.1 | n/a | 93.1 | n/a | -2.01 | n/a | -2.01 | SCAN worse |
| bach-italian-concerto-2 | 93.9 | n/a | 95.5 | n/a | +1.61 | n/a | +1.61 | SCAN better |
| bach-prelude-873 | 97.1 | n/a | 96.0 | n/a | -1.13 | n/a | -1.13 | SCAN worse |
| beethoven-appassionata-1 | 91.4 | n/a | 90.3 | n/a | -1.06 | n/a | -1.06 | SCAN worse |
| beethoven-hammerklavier-4 | 81.5 | n/a | 81.6 | n/a | +0.03 | n/a | +0.03 | tie |
| beethoven-waldstein-1 | 90.0 | n/a | 91.5 | n/a | +1.51 | n/a | +1.51 | SCAN better |
| chopin-etude-op10-4 | 91.9 | n/a | 94.6 | n/a | +2.70 | n/a | +2.70 | SCAN better |
| chopin-etude-op25-10 | 69.4 | n/a | 64.5 | n/a | -4.93 | n/a | -4.93 | SCAN worse |
| chopin-etude-op25-11 | 53.9 | n/a | 34.8 | n/a | -19.18 | n/a | -19.18 | SCAN worse |
| chopin-polonaise-op53 | 75.5 | n/a | 78.5 | n/a | +3.00 | n/a | +3.00 | SCAN better |
| chopin-scherzo3 | 88.7 | n/a | 88.5 | n/a | -0.22 | n/a | -0.22 | SCAN worse |
| debussy-pour-le-piano-1 | 77.6 | n/a | 73.1 | n/a | -4.52 | n/a | -4.52 | SCAN worse |
| debussy-reflets | 46.5 | n/a | 42.6 | n/a | -3.96 | n/a | -3.96 | SCAN worse |
| haydn-hob16-49-1 | 86.2 | n/a | 86.3 | n/a | +0.12 | n/a | +0.12 | SCAN better |
| liszt-hr-6 | 82.3 | n/a | 77.4 | n/a | -4.86 | n/a | -4.86 | SCAN worse |
| liszt-paganini-6 | 57.7 | n/a | 61.7 | n/a | +3.93 | n/a | +3.93 | SCAN better |
| liszt-sonata | 65.0 | n/a | 64.1 | n/a | -0.86 | n/a | -0.86 | SCAN worse |
| liszt-te-10 | 23.1 | n/a | 23.4 | n/a | +0.29 | n/a | +0.29 | SCAN better |
| liszt-te-5 | 59.4 | n/a | 58.6 | n/a | -0.75 | n/a | -0.75 | SCAN worse |
| mozart-k475 | 66.5 | n/a | 73.0 | n/a | +6.52 | n/a | +6.52 | SCAN better |
| prokofiev-toccata | 82.3 | n/a | 81.0 | n/a | -1.37 | n/a | -1.37 | SCAN worse |
| ravel-alborada | 57.9 | n/a | 54.4 | n/a | -3.57 | n/a | -3.57 | SCAN worse |
| schubert-impromptu-d899-4 | 98.5 | n/a | 97.7 | n/a | -0.79 | n/a | -0.79 | SCAN worse |
| schubert-wanderer-3-4 | 92.9 | n/a | 93.5 | n/a | +0.61 | n/a | +0.61 | SCAN better |
| schumann-kreisleriana-1 | 68.0 | n/a | 62.9 | n/a | -5.04 | n/a | -5.04 | SCAN worse |
| schumann-toccata | 81.4 | n/a | 78.7 | n/a | -2.73 | n/a | -2.73 | SCAN worse |
| scriabin-sonata-5 | 71.7 | n/a | 69.3 | n/a | -2.42 | n/a | -2.42 | SCAN worse |
| stravinsky-petrushka | 39.8 | n/a | 39.5 | n/a | -0.33 | n/a | -0.33 | SCAN worse |

Mean SCAN - CTRL per seed: s7 -1.41 (28 pieces). SCAN better on 9, worse on 18, tie 1 (band 0.1); both seeds agree beyond the band on 0; sign test over the 27 decided pieces p = 0.122.

### 3.5 pooled pitch+onset F1

| piece | CTRL s7 | CTRL s11 | SCAN s7 | SCAN s11 | d s7 | d s11 | mean d +- range | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 96.1 | n/a | 93.6 | n/a | -2.50 | n/a | -2.50 | SCAN worse |
| bach-italian-concerto-2 | 94.1 | n/a | 95.7 | n/a | +1.61 | n/a | +1.61 | SCAN better |
| bach-prelude-873 | 97.3 | n/a | 96.6 | n/a | -0.64 | n/a | -0.64 | SCAN worse |
| beethoven-appassionata-1 | 92.3 | n/a | 91.6 | n/a | -0.77 | n/a | -0.77 | SCAN worse |
| beethoven-hammerklavier-4 | 89.0 | n/a | 88.1 | n/a | -0.82 | n/a | -0.82 | SCAN worse |
| beethoven-waldstein-1 | 95.4 | n/a | 97.0 | n/a | +1.61 | n/a | +1.61 | SCAN better |
| chopin-etude-op10-4 | 93.1 | n/a | 95.6 | n/a | +2.53 | n/a | +2.53 | SCAN better |
| chopin-etude-op25-10 | 73.3 | n/a | 69.1 | n/a | -4.20 | n/a | -4.20 | SCAN worse |
| chopin-etude-op25-11 | 56.9 | n/a | 39.8 | n/a | -17.09 | n/a | -17.09 | SCAN worse |
| chopin-polonaise-op53 | 80.5 | n/a | 83.1 | n/a | +2.60 | n/a | +2.60 | SCAN better |
| chopin-scherzo3 | 90.6 | n/a | 90.5 | n/a | -0.05 | n/a | -0.05 | tie |
| debussy-pour-le-piano-1 | 78.4 | n/a | 74.9 | n/a | -3.52 | n/a | -3.52 | SCAN worse |
| debussy-reflets | 49.8 | n/a | 46.3 | n/a | -3.51 | n/a | -3.51 | SCAN worse |
| haydn-hob16-49-1 | 87.2 | n/a | 87.4 | n/a | +0.19 | n/a | +0.19 | SCAN better |
| liszt-hr-6 | 83.0 | n/a | 79.2 | n/a | -3.85 | n/a | -3.85 | SCAN worse |
| liszt-paganini-6 | 60.5 | n/a | 64.1 | n/a | +3.69 | n/a | +3.69 | SCAN better |
| liszt-sonata | 67.9 | n/a | 66.7 | n/a | -1.20 | n/a | -1.20 | SCAN worse |
| liszt-te-10 | 31.8 | n/a | 31.6 | n/a | -0.24 | n/a | -0.24 | SCAN worse |
| liszt-te-5 | 62.0 | n/a | 61.0 | n/a | -0.92 | n/a | -0.92 | SCAN worse |
| mozart-k475 | 71.5 | n/a | 77.4 | n/a | +5.91 | n/a | +5.91 | SCAN better |
| prokofiev-toccata | 83.4 | n/a | 82.7 | n/a | -0.62 | n/a | -0.62 | SCAN worse |
| ravel-alborada | 60.4 | n/a | 57.8 | n/a | -2.61 | n/a | -2.61 | SCAN worse |
| schubert-impromptu-d899-4 | 98.6 | n/a | 97.8 | n/a | -0.75 | n/a | -0.75 | SCAN worse |
| schubert-wanderer-3-4 | 94.8 | n/a | 95.5 | n/a | +0.65 | n/a | +0.65 | SCAN better |
| schumann-kreisleriana-1 | 72.7 | n/a | 67.8 | n/a | -4.87 | n/a | -4.87 | SCAN worse |
| schumann-toccata | 83.4 | n/a | 81.1 | n/a | -2.28 | n/a | -2.28 | SCAN worse |
| scriabin-sonata-5 | 74.5 | n/a | 72.2 | n/a | -2.32 | n/a | -2.32 | SCAN worse |
| stravinsky-petrushka | 59.6 | n/a | 58.6 | n/a | -0.95 | n/a | -0.95 | SCAN worse |

Mean SCAN - CTRL per seed: s7 -1.25 (28 pieces). SCAN better on 8, worse on 19, tie 1 (band 0.1); both seeds agree beyond the band on 0; sign test over the 27 decided pieces p = 0.052.

### 3.6 pooled full F1

| piece | CTRL s7 | CTRL s11 | SCAN s7 | SCAN s11 | d s7 | d s11 | mean d +- range | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 95.2 | n/a | 93.1 | n/a | -2.01 | n/a | -2.01 | SCAN worse |
| bach-italian-concerto-2 | 93.9 | n/a | 95.5 | n/a | +1.61 | n/a | +1.61 | SCAN better |
| bach-prelude-873 | 97.1 | n/a | 96.1 | n/a | -1.05 | n/a | -1.05 | SCAN worse |
| beethoven-appassionata-1 | 91.5 | n/a | 90.8 | n/a | -0.75 | n/a | -0.75 | SCAN worse |
| beethoven-hammerklavier-4 | 88.0 | n/a | 87.4 | n/a | -0.69 | n/a | -0.69 | SCAN worse |
| beethoven-waldstein-1 | 94.8 | n/a | 96.7 | n/a | +1.84 | n/a | +1.84 | SCAN better |
| chopin-etude-op10-4 | 92.9 | n/a | 95.4 | n/a | +2.53 | n/a | +2.53 | SCAN better |
| chopin-etude-op25-10 | 69.4 | n/a | 64.5 | n/a | -4.93 | n/a | -4.93 | SCAN worse |
| chopin-etude-op25-11 | 53.9 | n/a | 34.8 | n/a | -19.18 | n/a | -19.18 | SCAN worse |
| chopin-polonaise-op53 | 77.4 | n/a | 80.6 | n/a | +3.26 | n/a | +3.26 | SCAN better |
| chopin-scherzo3 | 89.7 | n/a | 89.6 | n/a | -0.05 | n/a | -0.05 | tie |
| debussy-pour-le-piano-1 | 77.7 | n/a | 73.7 | n/a | -3.97 | n/a | -3.97 | SCAN worse |
| debussy-reflets | 46.6 | n/a | 42.8 | n/a | -3.82 | n/a | -3.82 | SCAN worse |
| haydn-hob16-49-1 | 86.3 | n/a | 86.4 | n/a | +0.12 | n/a | +0.12 | SCAN better |
| liszt-hr-6 | 82.3 | n/a | 77.5 | n/a | -4.84 | n/a | -4.84 | SCAN worse |
| liszt-paganini-6 | 58.0 | n/a | 61.8 | n/a | +3.84 | n/a | +3.84 | SCAN better |
| liszt-sonata | 65.7 | n/a | 64.4 | n/a | -1.26 | n/a | -1.26 | SCAN worse |
| liszt-te-10 | 23.2 | n/a | 23.4 | n/a | +0.24 | n/a | +0.24 | SCAN better |
| liszt-te-5 | 60.0 | n/a | 58.8 | n/a | -1.26 | n/a | -1.26 | SCAN worse |
| mozart-k475 | 68.7 | n/a | 75.4 | n/a | +6.66 | n/a | +6.66 | SCAN better |
| prokofiev-toccata | 82.4 | n/a | 81.5 | n/a | -0.90 | n/a | -0.90 | SCAN worse |
| ravel-alborada | 58.1 | n/a | 54.6 | n/a | -3.55 | n/a | -3.55 | SCAN worse |
| schubert-impromptu-d899-4 | 98.5 | n/a | 97.8 | n/a | -0.75 | n/a | -0.75 | SCAN worse |
| schubert-wanderer-3-4 | 94.3 | n/a | 95.0 | n/a | +0.65 | n/a | +0.65 | SCAN better |
| schumann-kreisleriana-1 | 68.5 | n/a | 63.4 | n/a | -5.04 | n/a | -5.04 | SCAN worse |
| schumann-toccata | 81.8 | n/a | 79.2 | n/a | -2.63 | n/a | -2.63 | SCAN worse |
| scriabin-sonata-5 | 71.8 | n/a | 69.4 | n/a | -2.42 | n/a | -2.42 | SCAN worse |
| stravinsky-petrushka | 54.7 | n/a | 53.5 | n/a | -1.20 | n/a | -1.20 | SCAN worse |

Mean SCAN - CTRL per seed: s7 -1.41 (28 pieces). SCAN better on 9, worse on 18, tie 1 (band 0.1); both seeds agree beyond the band on 0; sign test over the 27 decided pieces p = 0.122.

### 3.7 dense-bar recall of pitches

| piece | CTRL s7 | CTRL s11 | SCAN s7 | SCAN s11 | d s7 | d s11 | mean d +- range | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 100.0 | n/a | 100.0 | n/a | +0.00 | n/a | +0.00 | tie |
| bach-italian-concerto-2 | 99.5 | n/a | 99.6 | n/a | +0.12 | n/a | +0.12 | SCAN better |
| bach-prelude-873 | 98.5 | n/a | 99.2 | n/a | +0.77 | n/a | +0.77 | SCAN better |
| beethoven-appassionata-1 | 98.9 | n/a | 98.4 | n/a | -0.48 | n/a | -0.48 | SCAN worse |
| beethoven-hammerklavier-4 | 93.4 | n/a | 93.2 | n/a | -0.13 | n/a | -0.13 | SCAN worse |
| beethoven-waldstein-1 | 100.0 | n/a | 99.7 | n/a | -0.28 | n/a | -0.28 | SCAN worse |
| chopin-etude-op10-4 | 95.7 | n/a | 95.3 | n/a | -0.40 | n/a | -0.40 | SCAN worse |
| chopin-etude-op25-10 | 96.5 | n/a | 96.3 | n/a | -0.23 | n/a | -0.23 | SCAN worse |
| chopin-etude-op25-11 | 87.5 | n/a | 85.8 | n/a | -1.74 | n/a | -1.74 | SCAN worse |
| chopin-polonaise-op53 | 90.5 | n/a | 90.3 | n/a | -0.12 | n/a | -0.12 | SCAN worse |
| debussy-pour-le-piano-1 | 89.7 | n/a | 89.9 | n/a | +0.20 | n/a | +0.20 | SCAN better |
| debussy-reflets | 84.1 | n/a | 84.8 | n/a | +0.65 | n/a | +0.65 | SCAN better |
| haydn-hob16-49-1 | 81.0 | n/a | 83.5 | n/a | +2.53 | n/a | +2.53 | SCAN better |
| liszt-hr-6 | 90.2 | n/a | 89.7 | n/a | -0.53 | n/a | -0.53 | SCAN worse |
| liszt-paganini-6 | 83.0 | n/a | 82.9 | n/a | -0.15 | n/a | -0.15 | SCAN worse |
| liszt-sonata | 80.3 | n/a | 79.8 | n/a | -0.46 | n/a | -0.46 | SCAN worse |
| liszt-te-10 | 82.2 | n/a | 78.9 | n/a | -3.36 | n/a | -3.36 | SCAN worse |
| liszt-te-5 | 77.1 | n/a | 76.5 | n/a | -0.64 | n/a | -0.64 | SCAN worse |
| mozart-k475 | 93.8 | n/a | 94.3 | n/a | +0.53 | n/a | +0.53 | SCAN better |
| prokofiev-toccata | 92.2 | n/a | 94.3 | n/a | +2.18 | n/a | +2.18 | SCAN better |
| ravel-alborada | 76.9 | n/a | 78.6 | n/a | +1.71 | n/a | +1.71 | SCAN better |
| schubert-impromptu-d899-4 | 99.3 | n/a | 99.3 | n/a | +0.00 | n/a | +0.00 | tie |
| schubert-wanderer-3-4 | 96.0 | n/a | 96.8 | n/a | +0.81 | n/a | +0.81 | SCAN better |
| schumann-kreisleriana-1 | 95.8 | n/a | 85.4 | n/a | -10.42 | n/a | -10.42 | SCAN worse |
| schumann-toccata | 90.9 | n/a | 89.8 | n/a | -1.07 | n/a | -1.07 | SCAN worse |
| scriabin-sonata-5 | 81.3 | n/a | 81.5 | n/a | +0.13 | n/a | +0.13 | SCAN better |
| stravinsky-petrushka | 75.4 | n/a | 74.2 | n/a | -1.16 | n/a | -1.16 | SCAN worse |

Mean SCAN - CTRL per seed: s7 -0.43 (27 pieces). SCAN better on 10, worse on 15, tie 2 (band 0.1); both seeds agree beyond the band on 0; sign test over the 25 decided pieces p = 0.424.

### 3.x Pieces where SCAN is worse than CTRL_RENDER by 1 point or more

Rule: change of at least -1.0 point in the same direction in both seeds (a single-seed drop is listed separately). The repository rule is that original scans must not get worse; a better average does not excuse a worse page.

* pooled pitch, both seeds: none; one seed only: chopin-etude-op25-11 (s7 -1.6), liszt-te-10 (s7 -3.1), schumann-kreisleriana-1 (s7 -2.0), schumann-toccata (s7 -1.1)
* staff-sensitive pitch, both seeds: none; one seed only: chopin-etude-op25-11 (s7 -2.7), debussy-pour-le-piano-1 (s7 -1.7), liszt-te-10 (s7 -2.7), schumann-kreisleriana-1 (s7 -2.6), schumann-toccata (s7 -1.2)

### 3.y Where SCAN is better by 1 point or more in both seeds (pooled pitch)

none

## 4. Context: both pilot arms against the run3 control (same recipe, no pilot data) and the released model

Mean over pieces scored in both runs of the pair, difference of the macro means per seed (pooled pitch, staff-sensitive pitch, pooled +onset, pooled full, dense recall). The run3 control saw the base list 2.00 times, the pilot arms 1.88 times plus 15 passes over the 881 pilot passages.

| pair | pooled pitch s7 | s11 | staff-sens pitch s7 | s11 | pooled +onset s7 | s11 | pooled full s7 | s11 | dense recall s7 | s11 |
|---|---|---|---|---|---|---|---|---|---|---|
| CTRL_RENDER - run3 ctrl | +0.34 | n/a | +0.31 | n/a | +0.90 | n/a | +1.03 | n/a | +0.36 | n/a |
| SCAN - run3 ctrl | -0.12 | n/a | -0.26 | n/a | -0.34 | n/a | -0.39 | n/a | -0.07 | n/a |

## 5. Per piece, all columns

Percent F1. `*` = Schott scan (released column re-merged). Bold = below 97 in the pooled table.

### 5a. Pooled sounding-pitch F1

| piece | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.6 | 99.7 | 99.4 | 99.5 | **missing** | 99.4 | **missing** |
| bach-italian-concerto-2 | 98.9 | 98.8 | 99.0 | 98.8 | **missing** | 98.6 | **missing** |
| bach-prelude-873 | 99.4 | 99.4 | 98.9 | 99.5 | **missing** | 99.6 | **missing** |
| beethoven-appassionata-1 | 99.0 | 99.0 | 99.1 | 98.9 | **missing** | 98.8 | **missing** |
| beethoven-hammerklavier-4 | **96.5** | **96.9** | **96.4** | **96.5** | **missing** | **95.5** | **missing** |
| beethoven-waldstein-1 | 99.5 | 99.6 | 99.5 | 99.7 | **missing** | 99.1 | **missing** |
| chopin-etude-op10-4 | **95.8** | **95.8** | **96.2** | **95.8** | **missing** | **96.0** | **missing** |
| chopin-etude-op25-10 | **96.0** | **96.3** | 97.2 | **96.9** | **missing** | **96.6** | **missing** |
| chopin-etude-op25-11 | **88.6** | **88.8** | **89.2** | **88.3** | **missing** | **86.7** | **missing** |
| chopin-polonaise-op53 | **91.3** | **91.8** | **92.3** | **92.1** | **missing** | **92.6** | **missing** |
| chopin-scherzo3 | **93.1** | **92.4** | **91.6** | **92.7** | **missing** | **93.1** | **missing** |
| debussy-pour-le-piano-1 | **92.3** | **90.6** | **91.1** | **93.4** | **missing** | **92.7** | **missing** |
| debussy-reflets | **85.8** | **87.5** | **87.0** | **86.6** | **missing** | **86.4** | **missing** |
| haydn-hob16-49-1 | **95.3** | **92.9** | **95.5** | **94.7** | **missing** | **93.8** | **missing** |
| liszt-hr-6 | **91.9** | **91.6** | **92.5** | **92.5** | **missing** | **92.5** | **missing** |
| liszt-paganini-6 | **91.1** | **90.3** | **89.5** | **89.2** | **missing** | **88.8** | **missing** |
| liszt-sonata * | **81.5** | **79.1** | **80.9** | **81.7** | **missing** | **81.0** | **missing** |
| liszt-te-10 * | **79.8** | **79.9** | **77.8** | **80.3** | **missing** | **77.2** | **missing** |
| liszt-te-5 * | **77.8** | **78.7** | **78.3** | **78.3** | **missing** | **77.7** | **missing** |
| mozart-k475 | **95.2** | **94.4** | **94.5** | **94.9** | **missing** | **95.5** | **missing** |
| prokofiev-toccata | **92.8** | **92.2** | **93.2** | **93.0** | **missing** | **93.4** | **missing** |
| ravel-alborada | **82.1** | **82.1** | **81.5** | **81.5** | **missing** | **81.7** | **missing** |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.0 | 99.2 | **missing** | 98.6 | **missing** |
| schubert-wanderer-3-4 | **96.3** | **96.1** | **96.3** | **96.3** | **missing** | **96.5** | **missing** |
| schumann-kreisleriana-1 | **96.9** | **96.6** | 97.6 | 97.5 | **missing** | **95.5** | **missing** |
| schumann-toccata | **91.7** | **91.0** | **92.3** | **92.3** | **missing** | **91.3** | **missing** |
| scriabin-sonata-5 | **89.2** | **90.1** | **89.2** | **90.2** | **missing** | **89.3** | **missing** |
| stravinsky-petrushka (provisional) | **79.2** | **79.3** | **78.9** | **79.4** | **missing** | **78.7** | **missing** |

### 5b. Staff-sensitive pitch F1

| piece | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.6 | 99.7 | 99.3 | 99.4 | **missing** | 99.3 | **missing** |
| bach-italian-concerto-2 | 98.9 | 98.8 | 99.0 | 98.8 | **missing** | 98.6 | **missing** |
| bach-prelude-873 | 99.4 | 99.3 | 98.9 | 99.5 | **missing** | 99.5 | **missing** |
| beethoven-appassionata-1 | 98.8 | 98.8 | 98.9 | 98.8 | **missing** | 98.2 | **missing** |
| beethoven-hammerklavier-4 | 89.5 | 89.6 | 89.4 | 89.2 | **missing** | 89.1 | **missing** |
| beethoven-waldstein-1 | 94.2 | 94.3 | 94.2 | 94.3 | **missing** | 93.9 | **missing** |
| chopin-etude-op10-4 | 94.8 | 94.8 | 95.2 | 94.8 | **missing** | 95.2 | **missing** |
| chopin-etude-op25-10 | 96.0 | 96.3 | 97.2 | 96.9 | **missing** | 96.6 | **missing** |
| chopin-etude-op25-11 | 88.5 | 88.8 | 89.1 | 88.3 | **missing** | 85.5 | **missing** |
| chopin-polonaise-op53 | 89.0 | 89.5 | 90.0 | 89.8 | **missing** | 89.9 | **missing** |
| chopin-scherzo3 | 91.8 | 91.1 | 90.2 | 91.3 | **missing** | 91.4 | **missing** |
| debussy-pour-le-piano-1 | 91.8 | 90.2 | 90.6 | 92.8 | **missing** | 91.1 | **missing** |
| debussy-reflets | 85.2 | 86.8 | 86.4 | 86.0 | **missing** | 85.8 | **missing** |
| haydn-hob16-49-1 | 95.1 | 92.7 | 95.3 | 94.5 | **missing** | 93.5 | **missing** |
| liszt-hr-6 | 91.8 | 91.5 | 92.5 | 92.4 | **missing** | 92.3 | **missing** |
| liszt-paganini-6 | 90.7 | 90.0 | 89.4 | 88.8 | **missing** | 88.1 | **missing** |
| liszt-sonata * | 81.0 | 78.7 | 80.5 | 81.2 | **missing** | 80.6 | **missing** |
| liszt-te-10 * | 79.1 | 79.3 | 77.5 | 79.6 | **missing** | 76.9 | **missing** |
| liszt-te-5 * | 77.0 | 78.4 | 77.6 | 77.5 | **missing** | 77.2 | **missing** |
| mozart-k475 | 92.0 | 91.3 | 91.3 | 91.8 | **missing** | 92.2 | **missing** |
| prokofiev-toccata | 92.8 | 92.1 | 93.2 | 92.9 | **missing** | 92.9 | **missing** |
| ravel-alborada | 81.7 | 81.6 | 81.1 | 81.1 | **missing** | 81.3 | **missing** |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.0 | 99.2 | **missing** | 98.6 | **missing** |
| schubert-wanderer-3-4 | 94.9 | 94.7 | 94.9 | 94.9 | **missing** | 95.0 | **missing** |
| schumann-kreisleriana-1 | 95.8 | 95.6 | 96.5 | 96.4 | **missing** | 93.8 | **missing** |
| schumann-toccata | 91.2 | 90.5 | 91.8 | 91.8 | **missing** | 90.6 | **missing** |
| scriabin-sonata-5 | 89.1 | 90.0 | 89.1 | 90.1 | **missing** | 89.1 | **missing** |
| stravinsky-petrushka (provisional) | 58.3 | 58.4 | 58.3 | 58.3 | **missing** | 58.2 | **missing** |

### 5c. Staff-sensitive pitch + onset F1

| piece | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 94.5 | 96.5 | 95.7 | 96.1 | **missing** | 93.6 | **missing** |
| bach-italian-concerto-2 | 94.2 | 97.0 | 97.8 | 94.1 | **missing** | 95.7 | **missing** |
| bach-prelude-873 | 97.2 | 97.1 | 96.8 | 97.3 | **missing** | 96.6 | **missing** |
| beethoven-appassionata-1 | 91.0 | 90.1 | 91.3 | 92.2 | **missing** | 91.1 | **missing** |
| beethoven-hammerklavier-4 | 83.0 | 83.2 | 82.3 | 82.4 | **missing** | 82.3 | **missing** |
| beethoven-waldstein-1 | 90.9 | 88.7 | 88.4 | 90.5 | **missing** | 91.8 | **missing** |
| chopin-etude-op10-4 | 93.1 | 92.8 | 93.5 | 92.1 | **missing** | 94.8 | **missing** |
| chopin-etude-op25-10 | 72.3 | 69.0 | 71.3 | 73.3 | **missing** | 69.1 | **missing** |
| chopin-etude-op25-11 | 53.4 | 55.6 | 53.1 | 56.8 | **missing** | 39.7 | **missing** |
| chopin-polonaise-op53 | 71.4 | 73.6 | 75.1 | 78.5 | **missing** | 80.9 | **missing** |
| chopin-scherzo3 | 89.6 | 89.0 | 88.3 | 89.6 | **missing** | 89.3 | **missing** |
| debussy-pour-le-piano-1 | 77.4 | 78.0 | 78.7 | 78.4 | **missing** | 74.3 | **missing** |
| debussy-reflets | 47.7 | 47.2 | 48.5 | 49.5 | **missing** | 45.7 | **missing** |
| haydn-hob16-49-1 | 86.8 | 86.9 | 87.7 | 87.1 | **missing** | 87.2 | **missing** |
| liszt-hr-6 | 81.8 | 81.2 | 80.8 | 83.0 | **missing** | 79.1 | **missing** |
| liszt-paganini-6 | 63.8 | 62.3 | 62.4 | 60.1 | **missing** | 63.9 | **missing** |
| liszt-sonata * | 66.0 | 63.1 | 65.0 | 67.2 | **missing** | 66.4 | **missing** |
| liszt-te-10 * | 31.7 | 32.7 | 31.6 | 31.5 | **missing** | 31.4 | **missing** |
| liszt-te-5 * | 62.3 | 61.8 | 61.2 | 61.3 | **missing** | 60.9 | **missing** |
| mozart-k475 | 65.2 | 67.2 | 68.8 | 69.0 | **missing** | 74.9 | **missing** |
| prokofiev-toccata | 82.3 | 78.8 | 82.0 | 83.3 | **missing** | 82.2 | **missing** |
| ravel-alborada | 59.7 | 60.4 | 60.0 | 60.1 | **missing** | 57.4 | **missing** |
| schubert-impromptu-d899-4 | 98.6 | 98.5 | 98.2 | 98.6 | **missing** | 97.8 | **missing** |
| schubert-wanderer-3-4 | 93.5 | 93.2 | 93.7 | 93.4 | **missing** | 94.0 | **missing** |
| schumann-kreisleriana-1 | 71.4 | 70.9 | 72.1 | 72.1 | **missing** | 67.2 | **missing** |
| schumann-toccata | 82.5 | 80.6 | 82.1 | 83.0 | **missing** | 80.6 | **missing** |
| scriabin-sonata-5 | 73.2 | 73.9 | 72.6 | 74.4 | **missing** | 72.1 | **missing** |
| stravinsky-petrushka (provisional) | 43.1 | 43.3 | 43.8 | 43.2 | **missing** | 43.2 | **missing** |

### 5d. Pooled pitch + onset F1

| piece | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 94.5 | 96.5 | 95.8 | 96.1 | **missing** | 93.6 | **missing** |
| bach-italian-concerto-2 | 94.2 | 97.0 | 97.8 | 94.1 | **missing** | 95.7 | **missing** |
| bach-prelude-873 | 97.2 | 97.1 | 96.8 | 97.3 | **missing** | 96.6 | **missing** |
| beethoven-appassionata-1 | 91.2 | 90.3 | 91.5 | 92.3 | **missing** | 91.6 | **missing** |
| beethoven-hammerklavier-4 | 89.8 | 90.1 | 88.8 | 89.0 | **missing** | 88.1 | **missing** |
| beethoven-waldstein-1 | 96.0 | 93.8 | 93.6 | 95.4 | **missing** | 97.0 | **missing** |
| chopin-etude-op10-4 | 94.1 | 93.8 | 94.5 | 93.1 | **missing** | 95.6 | **missing** |
| chopin-etude-op25-10 | 72.3 | 69.1 | 71.3 | 73.3 | **missing** | 69.1 | **missing** |
| chopin-etude-op25-11 | 53.4 | 55.6 | 53.2 | 56.9 | **missing** | 39.8 | **missing** |
| chopin-polonaise-op53 | 73.5 | 75.6 | 77.1 | 80.5 | **missing** | 83.1 | **missing** |
| chopin-scherzo3 | 90.6 | 90.0 | 89.3 | 90.6 | **missing** | 90.5 | **missing** |
| debussy-pour-le-piano-1 | 77.4 | 78.0 | 78.8 | 78.4 | **missing** | 74.9 | **missing** |
| debussy-reflets | 48.0 | 47.7 | 48.8 | 49.8 | **missing** | 46.3 | **missing** |
| haydn-hob16-49-1 | 86.9 | 87.0 | 87.8 | 87.2 | **missing** | 87.4 | **missing** |
| liszt-hr-6 | 81.9 | 81.3 | 80.9 | 83.0 | **missing** | 79.2 | **missing** |
| liszt-paganini-6 | 64.1 | 62.6 | 62.6 | 60.5 | **missing** | 64.1 | **missing** |
| liszt-sonata * | 66.9 | 63.6 | 65.4 | 67.9 | **missing** | 66.7 | **missing** |
| liszt-te-10 * | 32.1 | 33.1 | 31.9 | 31.8 | **missing** | 31.6 | **missing** |
| liszt-te-5 * | 62.6 | 62.3 | 61.8 | 62.0 | **missing** | 61.0 | **missing** |
| mozart-k475 | 67.4 | 69.6 | 71.5 | 71.5 | **missing** | 77.4 | **missing** |
| prokofiev-toccata | 82.4 | 78.9 | 82.0 | 83.4 | **missing** | 82.7 | **missing** |
| ravel-alborada | 60.1 | 60.8 | 60.4 | 60.4 | **missing** | 57.8 | **missing** |
| schubert-impromptu-d899-4 | 98.6 | 98.5 | 98.2 | 98.6 | **missing** | 97.8 | **missing** |
| schubert-wanderer-3-4 | 94.9 | 94.6 | 95.1 | 94.8 | **missing** | 95.5 | **missing** |
| schumann-kreisleriana-1 | 71.6 | 71.1 | 72.4 | 72.7 | **missing** | 67.8 | **missing** |
| schumann-toccata | 82.9 | 81.0 | 82.6 | 83.4 | **missing** | 81.1 | **missing** |
| scriabin-sonata-5 | 73.3 | 74.0 | 72.6 | 74.5 | **missing** | 72.2 | **missing** |
| stravinsky-petrushka (provisional) | 59.4 | 59.7 | 59.8 | 59.6 | **missing** | 58.6 | **missing** |

### 5e. Pooled full F1

| piece | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 93.8 | 96.0 | 95.3 | 95.2 | **missing** | 93.1 | **missing** |
| bach-italian-concerto-2 | 93.7 | 97.0 | 97.5 | 93.9 | **missing** | 95.5 | **missing** |
| bach-prelude-873 | 96.9 | 96.8 | 96.5 | 97.1 | **missing** | 96.1 | **missing** |
| beethoven-appassionata-1 | 90.3 | 89.4 | 90.5 | 91.5 | **missing** | 90.8 | **missing** |
| beethoven-hammerklavier-4 | 89.0 | 89.5 | 88.0 | 88.0 | **missing** | 87.4 | **missing** |
| beethoven-waldstein-1 | 95.4 | 93.1 | 92.9 | 94.8 | **missing** | 96.7 | **missing** |
| chopin-etude-op10-4 | 93.9 | 93.6 | 94.3 | 92.9 | **missing** | 95.4 | **missing** |
| chopin-etude-op25-10 | 68.7 | 64.7 | 67.4 | 69.4 | **missing** | 64.5 | **missing** |
| chopin-etude-op25-11 | 50.4 | 52.4 | 50.0 | 53.9 | **missing** | 34.8 | **missing** |
| chopin-polonaise-op53 | 69.3 | 71.7 | 73.8 | 77.4 | **missing** | 80.6 | **missing** |
| chopin-scherzo3 | 89.7 | 89.1 | 88.5 | 89.7 | **missing** | 89.6 | **missing** |
| debussy-pour-le-piano-1 | 76.7 | 77.2 | 78.1 | 77.7 | **missing** | 73.7 | **missing** |
| debussy-reflets | 44.7 | 44.2 | 45.4 | 46.6 | **missing** | 42.8 | **missing** |
| haydn-hob16-49-1 | 86.1 | 86.2 | 87.1 | 86.3 | **missing** | 86.4 | **missing** |
| liszt-hr-6 | 81.3 | 80.5 | 80.2 | 82.3 | **missing** | 77.5 | **missing** |
| liszt-paganini-6 | 61.5 | 59.5 | 60.1 | 58.0 | **missing** | 61.8 | **missing** |
| liszt-sonata * | 64.6 | 61.2 | 63.1 | 65.7 | **missing** | 64.4 | **missing** |
| liszt-te-10 * | 23.2 | 24.6 | 23.2 | 23.2 | **missing** | 23.4 | **missing** |
| liszt-te-5 * | 60.7 | 60.1 | 59.3 | 60.0 | **missing** | 58.8 | **missing** |
| mozart-k475 | 64.2 | 66.4 | 68.1 | 68.7 | **missing** | 75.4 | **missing** |
| prokofiev-toccata | 81.6 | 77.6 | 80.6 | 82.4 | **missing** | 81.5 | **missing** |
| ravel-alborada | 57.5 | 58.2 | 57.8 | 58.1 | **missing** | 54.6 | **missing** |
| schubert-impromptu-d899-4 | 98.6 | 98.5 | 98.2 | 98.5 | **missing** | 97.8 | **missing** |
| schubert-wanderer-3-4 | 94.4 | 94.1 | 94.6 | 94.3 | **missing** | 95.0 | **missing** |
| schumann-kreisleriana-1 | 67.2 | 67.0 | 68.0 | 68.5 | **missing** | 63.4 | **missing** |
| schumann-toccata | 81.3 | 79.5 | 80.8 | 81.8 | **missing** | 79.2 | **missing** |
| scriabin-sonata-5 | 70.6 | 71.3 | 69.7 | 71.8 | **missing** | 69.4 | **missing** |
| stravinsky-petrushka (provisional) | 54.6 | 54.6 | 54.9 | 54.7 | **missing** | 53.5 | **missing** |

### 5f. Dense-bar recall of pitches % (bars with >= 24 notes; missed in brackets)

| piece | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 100.0 (0) | 100.0 (0) | 98.8 (4) | 100.0 (0) | **missing** | 100.0 (0) | **missing** |
| bach-italian-concerto-2 | 99.5 (4) | 99.6 (3) | 99.5 (4) | 99.5 (4) | **missing** | 99.6 (3) | **missing** |
| bach-prelude-873 | 98.5 (4) | 98.5 (4) | 98.5 (4) | 98.5 (4) | **missing** | 99.2 (2) | **missing** |
| beethoven-appassionata-1 | 98.7 (61) | 98.8 (57) | 98.8 (53) | 98.9 (50) | **missing** | 98.4 (72) | **missing** |
| beethoven-hammerklavier-4 | 94.1 (92) | 94.6 (85) | 92.9 (111) | 93.4 (104) | **missing** | 93.2 (106) | **missing** |
| beethoven-waldstein-1 | 99.8 (10) | 99.9 (5) | 99.8 (10) | 100.0 (2) | **missing** | 99.7 (14) | **missing** |
| chopin-etude-op10-4 | 96.1 (77) | 95.8 (83) | 96.1 (78) | 95.7 (85) | **missing** | 95.3 (93) | **missing** |
| chopin-etude-op25-10 | 95.7 (91) | 96.2 (82) | 97.0 (64) | 96.5 (74) | **missing** | 96.3 (79) | **missing** |
| chopin-etude-op25-11 | 87.7 (383) | 87.8 (378) | 88.3 (364) | 87.5 (389) | **missing** | 85.8 (443) | **missing** |
| chopin-polonaise-op53 | 89.4 (603) | 89.9 (574) | 90.5 (540) | 90.5 (541) | **missing** | 90.3 (548) | **missing** |
| chopin-scherzo3 | n/a | n/a | n/a | n/a | **missing** | n/a | **missing** |
| debussy-pour-le-piano-1 | 87.2 (189) | 83.5 (243) | 85.2 (219) | 89.7 (152) | **missing** | 89.9 (149) | **missing** |
| debussy-reflets | 82.0 (251) | 84.9 (211) | 84.8 (212) | 84.1 (221) | **missing** | 84.8 (212) | **missing** |
| haydn-hob16-49-1 | 86.1 (11) | 77.2 (18) | 78.5 (17) | 81.0 (15) | **missing** | 83.5 (13) | **missing** |
| liszt-hr-6 | 89.1 (285) | 89.7 (269) | 90.2 (257) | 90.2 (256) | **missing** | 89.7 (270) | **missing** |
| liszt-paganini-6 | 86.6 (275) | 84.8 (311) | 84.2 (323) | 83.0 (348) | **missing** | 82.9 (351) | **missing** |
| liszt-sonata * | 79.5 (800) | 77.1 (892) | 79.2 (811) | 80.3 (769) | **missing** | 79.8 (787) | **missing** |
| liszt-te-10 * | 82.2 (408) | 81.9 (414) | 77.9 (507) | 82.2 (407) | **missing** | 78.9 (484) | **missing** |
| liszt-te-5 * | 76.7 (984) | 78.0 (931) | 77.1 (969) | 77.1 (969) | **missing** | 76.5 (996) | **missing** |
| mozart-k475 | 94.1 (123) | 93.3 (140) | 92.8 (150) | 93.8 (130) | **missing** | 94.3 (119) | **missing** |
| prokofiev-toccata | 92.1 (175) | 92.4 (168) | 92.6 (164) | 92.2 (173) | **missing** | 94.3 (125) | **missing** |
| ravel-alborada | 78.0 (449) | 77.9 (451) | 76.9 (472) | 76.9 (473) | **missing** | 78.6 (438) | **missing** |
| schubert-impromptu-d899-4 | 99.5 (5) | 99.3 (7) | 99.3 (7) | 99.3 (7) | **missing** | 99.3 (7) | **missing** |
| schubert-wanderer-3-4 | 96.0 (105) | 95.8 (108) | 96.0 (105) | 96.0 (104) | **missing** | 96.8 (83) | **missing** |
| schumann-kreisleriana-1 | 95.8 (2) | 95.8 (2) | 95.8 (2) | 95.8 (2) | **missing** | 85.4 (7) | **missing** |
| schumann-toccata | 90.3 (416) | 89.7 (442) | 90.3 (417) | 90.9 (389) | **missing** | 89.8 (435) | **missing** |
| scriabin-sonata-5 | 80.6 (612) | 82.3 (557) | 81.2 (592) | 81.3 (587) | **missing** | 81.5 (583) | **missing** |
| stravinsky-petrushka (provisional) | 75.0 (2419) | 75.3 (2393) | 74.8 (2442) | 75.4 (2381) | **missing** | 74.2 (2493) | **missing** |

### 5g. Bars: ours / reference

| piece | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 |
|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 71/71 | 71/71 | 71/71 | 71/71 | **missing** | 71/71 | **missing** |
| bach-italian-concerto-2 | 49/49 | 49/49 | 50/49 | 49/49 | **missing** | 49/49 | **missing** |
| bach-prelude-873 | 62/62 | 62/62 | 62/62 | 62/62 | **missing** | 62/62 | **missing** |
| beethoven-appassionata-1 | 264/264 | 264/264 | 264/264 | 264/264 | **missing** | 264/264 | **missing** |
| beethoven-hammerklavier-4 | 406/406 | 406/406 | 406/406 | 406/406 | **missing** | 406/406 | **missing** |
| beethoven-waldstein-1 | 304/304 | 304/304 | 304/304 | 304/304 | **missing** | 304/304 | **missing** |
| chopin-etude-op10-4 | 83/83 | 83/83 | 83/83 | 83/83 | **missing** | 82/83 | **missing** |
| chopin-etude-op25-10 | 119/119 | 119/119 | 119/119 | 119/119 | **missing** | 119/119 | **missing** |
| chopin-etude-op25-11 | 96/96 | 96/96 | 96/96 | 96/96 | **missing** | 96/96 | **missing** |
| chopin-polonaise-op53 | 182/181 | 181/181 | 181/181 | 181/181 | **missing** | 181/181 | **missing** |
| chopin-scherzo3 | 648/649 | 649/649 | 648/649 | 647/649 | **missing** | 648/649 | **missing** |
| debussy-pour-le-piano-1 | 163/162 | 162/162 | 163/162 | 164/162 | **missing** | 162/162 | **missing** |
| debussy-reflets | 94/95 | 95/95 | 95/95 | 95/95 | **missing** | 95/95 | **missing** |
| haydn-hob16-49-1 | 222/220 | 222/220 | 224/220 | 221/220 | **missing** | 226/220 | **missing** |
| liszt-hr-6 | 244/225 | 239/225 | 239/225 | 242/225 | **missing** | 244/225 | **missing** |
| liszt-paganini-6 | 220/220 | 220/220 | 219/220 | 220/220 | **missing** | 220/220 | **missing** |
| liszt-sonata * | 306/305 | 309/305 | 308/305 | 309/305 | **missing** | 309/305 | **missing** |
| liszt-te-10 * | 182/182 | 182/182 | 182/182 | 182/182 | **missing** | 182/182 | **missing** |
| liszt-te-5 * | 134/134 | 133/134 | 133/134 | 133/134 | **missing** | 137/134 | **missing** |
| mozart-k475 | 179/180 | 180/180 | 179/180 | 179/180 | **missing** | 181/180 | **missing** |
| prokofiev-toccata | 227/226 | 224/226 | 227/226 | 227/226 | **missing** | 227/226 | **missing** |
| ravel-alborada | 229/229 | 228/229 | 228/229 | 229/229 | **missing** | 228/229 | **missing** |
| schubert-impromptu-d899-4 | 277/277 | 277/277 | 277/277 | 277/277 | **missing** | 277/277 | **missing** |
| schubert-wanderer-3-4 | 476/475 | 476/475 | 476/475 | 476/475 | **missing** | 476/475 | **missing** |
| schumann-kreisleriana-1 | 77/78 | 77/78 | 77/78 | 77/78 | **missing** | 77/78 | **missing** |
| schumann-toccata | 275/283 | 272/283 | 276/283 | 276/283 | **missing** | 273/283 | **missing** |
| scriabin-sonata-5 | 432/456 | 431/456 | 432/456 | 432/456 | **missing** | 432/456 | **missing** |
| stravinsky-petrushka (provisional) | 598/627 | 598/627 | 595/627 | 598/627 | **missing** | 599/627 | **missing** |

## 6. Held-out passages (never trained on; free generation per staff crop, GPU)

`pilot_val_eval.py`: per crop the pitch-multiset F1 and the (pitch, rhythm-token) F1 of the read against the label, bar-count agreement, exact multiset match; means over crops. These are NOT the onset-based scores of section 3. Lists: **val** = the 72 v2 validation passages (Liszt TE3 = C1, Schubert D.899/2 = C3); **ext** = the independent 145-crop extension `batch2_val_v2` (four works). Each as the scan crop and as the rendered twin; the twins of the extension exist for 134 of the 145 crops (11 did not render: octave-bracket mismatch or touching notes), `ext scan (134)` is the scan of exactly those crops. Seeds: s7 / s11; spread = |s7 - s11|.

Missing held-out results: CTRL_RENDER s11 val_scan_v2, CTRL_RENDER s11 val_twin_v2, CTRL_RENDER s11 b2_scan, CTRL_RENDER s11 b2_scan_matched, CTRL_RENDER s11 b2_twin, SCAN s11 val_scan_v2, SCAN s11 val_twin_v2, SCAN s11 b2_scan, SCAN s11 b2_scan_matched, SCAN s11 b2_twin

### 6.1 Mean pitch F1 by work (crops with a read; all values x100)

**val scan (72)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 Liszt TE3 Paysage | 19 | 98.9 | 98.6 | 99.0 | 99.0 | missing | 98.8 | missing | n/a | n/a |
| C3 Schubert Impromptu D.899/2 | 53 | 99.1 | 99.2 | 99.2 | 99.2 | missing | 99.2 | missing | n/a | n/a |
| all crops | 72 | 99.1 | 99.0 | 99.2 | 99.1 | missing | 99.1 | missing | n/a | n/a |

**val twin (72)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 Liszt TE3 Paysage | 19 | 99.3 | 99.6 | 99.6 | 99.7 | missing | 99.6 | missing | n/a | n/a |
| C3 Schubert Impromptu D.899/2 | 53 | 99.7 | 99.7 | 99.6 | 99.8 | missing | 99.8 | missing | n/a | n/a |
| all crops | 72 | 99.6 | 99.7 | 99.6 | 99.7 | missing | 99.7 | missing | n/a | n/a |

**ext scan (145)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| N11 Beethoven Op.81a mvt 3 | 46 | 99.1 | 99.2 | 99.2 | 99.2 | missing | 99.1 | missing | n/a | n/a |
| N12 Beethoven Op.81a mvt 1 | 34 | 97.9 | 97.9 | 97.9 | 98.0 | missing | 98.0 | missing | n/a | n/a |
| N2 Liszt Concert Etude S.145/2 Gnomenreigen | 44 | 96.9 | 96.3 | 96.8 | 96.9 | missing | 96.9 | missing | n/a | n/a |
| N4 Chopin Etude Op.10/5 | 21 | 97.9 | 97.9 | 97.9 | 98.0 | missing | 97.4 | missing | n/a | n/a |
| all crops | 145 | 98.0 | 97.8 | 98.0 | 98.0 | missing | 98.0 | missing | n/a | n/a |

**ext scan (134)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| N11 Beethoven Op.81a mvt 3 | 41 | 99.1 | 99.2 | 99.2 | 99.2 | missing | 99.1 | missing | n/a | n/a |
| N12 Beethoven Op.81a mvt 1 | 31 | 97.8 | 97.8 | 97.8 | 97.8 | missing | 97.9 | missing | n/a | n/a |
| N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | 96.8 | 96.2 | 96.7 | 96.9 | missing | 96.9 | missing | n/a | n/a |
| N4 Chopin Etude Op.10/5 | 20 | 97.8 | 97.7 | 97.8 | 97.9 | missing | 97.3 | missing | n/a | n/a |
| all crops | 134 | 97.9 | 97.7 | 97.9 | 97.9 | missing | 97.9 | missing | n/a | n/a |

**ext twin (134)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| N11 Beethoven Op.81a mvt 3 | 41 | 100.0 | 100.0 | 100.0 | 100.0 | missing | 100.0 | missing | n/a | n/a |
| N12 Beethoven Op.81a mvt 1 | 31 | 99.7 | 99.5 | 99.8 | 99.7 | missing | 99.8 | missing | n/a | n/a |
| N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | 99.2 | 98.6 | 99.2 | 99.3 | missing | 99.1 | missing | n/a | n/a |
| N4 Chopin Etude Op.10/5 | 20 | 99.6 | 99.6 | 99.6 | 99.6 | missing | 99.6 | missing | n/a | n/a |
| all crops | 134 | 99.6 | 99.4 | 99.6 | 99.6 | missing | 99.6 | missing | n/a | n/a |

### 6.2 Mean (pitch, rhythm) F1 by work (crops with a read; all values x100)

**val scan (72)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 Liszt TE3 Paysage | 19 | 98.1 | 98.1 | 98.4 | 98.5 | missing | 97.6 | missing | n/a | n/a |
| C3 Schubert Impromptu D.899/2 | 53 | 61.5 | 60.4 | 59.4 | 75.2 | missing | 88.2 | missing | n/a | n/a |
| all crops | 72 | 71.2 | 70.4 | 69.7 | 81.3 | missing | 90.7 | missing | n/a | n/a |

**val twin (72)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| C1 Liszt TE3 Paysage | 19 | 98.4 | 99.0 | 98.9 | 99.2 | missing | 99.1 | missing | n/a | n/a |
| C3 Schubert Impromptu D.899/2 | 53 | 99.4 | 99.6 | 99.3 | 99.5 | missing | 99.6 | missing | n/a | n/a |
| all crops | 72 | 99.1 | 99.5 | 99.2 | 99.4 | missing | 99.5 | missing | n/a | n/a |

**ext scan (145)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| N11 Beethoven Op.81a mvt 3 | 46 | 98.3 | 97.0 | 98.5 | 97.0 | missing | 96.0 | missing | n/a | n/a |
| N12 Beethoven Op.81a mvt 1 | 34 | 97.0 | 96.9 | 97.0 | 97.1 | missing | 97.3 | missing | n/a | n/a |
| N2 Liszt Concert Etude S.145/2 Gnomenreigen | 44 | 93.6 | 91.6 | 92.5 | 95.0 | missing | 93.8 | missing | n/a | n/a |
| N4 Chopin Etude Op.10/5 | 21 | 67.2 | 73.1 | 69.8 | 72.8 | missing | 75.3 | missing | n/a | n/a |
| all crops | 145 | 92.1 | 91.9 | 92.2 | 92.9 | missing | 92.6 | missing | n/a | n/a |

**ext scan (134)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| N11 Beethoven Op.81a mvt 3 | 41 | 98.2 | 96.7 | 98.4 | 96.7 | missing | 95.6 | missing | n/a | n/a |
| N12 Beethoven Op.81a mvt 1 | 31 | 96.8 | 96.7 | 96.8 | 96.9 | missing | 97.1 | missing | n/a | n/a |
| N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | 93.4 | 91.3 | 92.2 | 94.8 | missing | 93.6 | missing | n/a | n/a |
| N4 Chopin Etude Op.10/5 | 20 | 68.7 | 74.9 | 71.4 | 74.5 | missing | 74.1 | missing | n/a | n/a |
| all crops | 134 | 92.0 | 91.8 | 92.1 | 92.9 | missing | 92.1 | missing | n/a | n/a |

**ext twin (134)**

| work | crops | released | run3 ctrl s7 | run3 ctrl s11 | CTRL_RENDER s7 | CTRL_RENDER s11 | SCAN s7 | SCAN s11 | spread CTRL (s7-s11) | spread SCAN |
|---|---|---|---|---|---|---|---|---|---|---|
| N11 Beethoven Op.81a mvt 3 | 41 | 99.3 | 99.1 | 99.2 | 99.0 | missing | 99.2 | missing | n/a | n/a |
| N12 Beethoven Op.81a mvt 1 | 31 | 99.2 | 99.0 | 99.2 | 99.1 | missing | 99.2 | missing | n/a | n/a |
| N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | 99.1 | 98.5 | 99.1 | 99.1 | missing | 99.0 | missing | n/a | n/a |
| N4 Chopin Etude Op.10/5 | 20 | 39.6 | 39.6 | 38.9 | 39.6 | missing | 39.6 | missing | n/a | n/a |
| all crops | 134 | 90.3 | 90.0 | 90.2 | 90.2 | missing | 90.2 | missing | n/a | n/a |

### 6.3 SCAN minus CTRL_RENDER on the same crops (paired per crop)

Per crop d = SCAN - CTRL_RENDER (x100). `seeds avg` first averages the two seeds of each arm per crop (the contrast of the spec), then the mean and a bootstrap 95 % interval over crops (5,000 resamples, crops treated as independent although they come from few works: the interval is optimistic). `s7`, `s11`: the same with one seed. Wins / losses use a +-0.5 point band per crop.

| list | metric | work | crops | s7 | s11 | seeds avg [95 % interval] | better / worse / equal (seeds avg) |
|---|---|---|---|---|---|---|---|
| val scan (72) | pitch | C1 Liszt TE3 Paysage | 19 | -0.18 | n/a | n/a | n/a |
| val scan (72) | pitch | C3 Schubert Impromptu D.899/2 | 53 | +0.02 | n/a | n/a | n/a |
| val scan (72) | pitch | all | 72 | -0.04 | n/a | n/a | n/a |
| val scan (72) | pitch+rhythm | C1 Liszt TE3 Paysage | 19 | -0.87 | n/a | n/a | n/a |
| val scan (72) | pitch+rhythm | C3 Schubert Impromptu D.899/2 | 53 | +12.99 | n/a | n/a | n/a |
| val scan (72) | pitch+rhythm | all | 72 | +9.34 | n/a | n/a | n/a |
| val twin (72) | pitch | C1 Liszt TE3 Paysage | 19 | -0.06 | n/a | n/a | n/a |
| val twin (72) | pitch | C3 Schubert Impromptu D.899/2 | 53 | +0.02 | n/a | n/a | n/a |
| val twin (72) | pitch | all | 72 | +0.00 | n/a | n/a | n/a |
| val twin (72) | pitch+rhythm | C1 Liszt TE3 Paysage | 19 | -0.15 | n/a | n/a | n/a |
| val twin (72) | pitch+rhythm | C3 Schubert Impromptu D.899/2 | 53 | +0.14 | n/a | n/a | n/a |
| val twin (72) | pitch+rhythm | all | 72 | +0.07 | n/a | n/a | n/a |
| ext scan (145) | pitch | N11 Beethoven Op.81a mvt 3 | 46 | -0.05 | n/a | n/a | n/a |
| ext scan (145) | pitch | N12 Beethoven Op.81a mvt 1 | 34 | +0.04 | n/a | n/a | n/a |
| ext scan (145) | pitch | N2 Liszt Concert Etude S.145/2 Gnomenreigen | 44 | -0.02 | n/a | n/a | n/a |
| ext scan (145) | pitch | N4 Chopin Etude Op.10/5 | 21 | -0.54 | n/a | n/a | n/a |
| ext scan (145) | pitch | all | 145 | -0.09 | n/a | n/a | n/a |
| ext scan (145) | pitch+rhythm | N11 Beethoven Op.81a mvt 3 | 46 | -0.98 | n/a | n/a | n/a |
| ext scan (145) | pitch+rhythm | N12 Beethoven Op.81a mvt 1 | 34 | +0.17 | n/a | n/a | n/a |
| ext scan (145) | pitch+rhythm | N2 Liszt Concert Etude S.145/2 Gnomenreigen | 44 | -1.15 | n/a | n/a | n/a |
| ext scan (145) | pitch+rhythm | N4 Chopin Etude Op.10/5 | 21 | +2.50 | n/a | n/a | n/a |
| ext scan (145) | pitch+rhythm | all | 145 | -0.26 | n/a | n/a | n/a |
| ext scan (134) | pitch | N11 Beethoven Op.81a mvt 3 | 41 | -0.06 | n/a | n/a | n/a |
| ext scan (134) | pitch | N12 Beethoven Op.81a mvt 1 | 31 | +0.07 | n/a | n/a | n/a |
| ext scan (134) | pitch | N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | -0.02 | n/a | n/a | n/a |
| ext scan (134) | pitch | N4 Chopin Etude Op.10/5 | 20 | -0.57 | n/a | n/a | n/a |
| ext scan (134) | pitch | all | 134 | -0.09 | n/a | n/a | n/a |
| ext scan (134) | pitch+rhythm | N11 Beethoven Op.81a mvt 3 | 41 | -1.10 | n/a | n/a | n/a |
| ext scan (134) | pitch+rhythm | N12 Beethoven Op.81a mvt 1 | 31 | +0.22 | n/a | n/a | n/a |
| ext scan (134) | pitch+rhythm | N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | -1.20 | n/a | n/a | n/a |
| ext scan (134) | pitch+rhythm | N4 Chopin Etude Op.10/5 | 20 | -0.49 | n/a | n/a | n/a |
| ext scan (134) | pitch+rhythm | all | 134 | -0.74 | n/a | n/a | n/a |
| ext twin (134) | pitch | N11 Beethoven Op.81a mvt 3 | 41 | +0.00 | n/a | n/a | n/a |
| ext twin (134) | pitch | N12 Beethoven Op.81a mvt 1 | 31 | +0.11 | n/a | n/a | n/a |
| ext twin (134) | pitch | N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | -0.19 | n/a | n/a | n/a |
| ext twin (134) | pitch | N4 Chopin Etude Op.10/5 | 20 | -0.04 | n/a | n/a | n/a |
| ext twin (134) | pitch | all | 134 | -0.04 | n/a | n/a | n/a |
| ext twin (134) | pitch+rhythm | N11 Beethoven Op.81a mvt 3 | 41 | +0.13 | n/a | n/a | n/a |
| ext twin (134) | pitch+rhythm | N12 Beethoven Op.81a mvt 1 | 31 | +0.08 | n/a | n/a | n/a |
| ext twin (134) | pitch+rhythm | N2 Liszt Concert Etude S.145/2 Gnomenreigen | 42 | -0.13 | n/a | n/a | n/a |
| ext twin (134) | pitch+rhythm | N4 Chopin Etude Op.10/5 | 20 | +0.01 | n/a | n/a | n/a |
| ext twin (134) | pitch+rhythm | all | 134 | +0.02 | n/a | n/a | n/a |

## 7. Reading (generated from the numbers above; check against the tables)

* 28 scans, pooled pitch F1: one seed only (s7) -0.46; provisional.
* 28 scans, staff-sensitive pitch F1: one seed only (s7) -0.57; provisional.
* 28 scans, staff-sensitive pitch+onset F1: one seed only (s7) -1.25; provisional.
* 28 scans, staff-sensitive full F1: one seed only (s7) -1.41; provisional.
* 28 scans, pooled pitch+onset F1: one seed only (s7) -1.25; provisional.
* 28 scans, pooled full F1: one seed only (s7) -1.41; provisional.
* 28 scans, dense-bar recall of pitches: one seed only (s7) -0.43; provisional.

Everything above is one training run per arm and seed, 28 scans from 28 works, 72 + 145 held-out crops from six works. Two seeds give a range, not a confidence interval.
