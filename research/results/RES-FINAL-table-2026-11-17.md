# Resolution experiment, final comparison (arm A 256x1280 vs arm B 384x1920), 2026-11-17

Generated 2026-11-17 18:09 PST by `eval_run1/res_final_table.py`. Same GPU pipeline for every arm (`res_eval.py`: same layout, merger, scorer, loop guard), visible notes only, **edition-corrected references for every column** (Schubert D. 899/4 against `schubert-impromptu-d899-4-reference-edition.musicxml`; the Scriabin reference is the one without the stray part). Pooled = a pitch counts if it is in the aligned bar on either staff (sounding pitch, correct octave and bar). Target: 97 % pooled pitch on every piece. The released column is the laptop CPU run of the released model after the merger fixes (not the same hardware as the GPU arms; reference only).

## 1. Runs

| column | tag | pieces scored | Schubert re-score | missing |
|---|---|---|---|---|
| released | `layout1` | 28 of 28 | existing -edition files | none |
| A s7 | `res_A_s7_gpu` | 28 of 28 | kept (already rescored) | none |
| A s11 | `res_A_s11_gpu` | 28 of 28 | kept (already rescored) | none |
| B s7 | `res_B_s7_gpu` | 28 of 28 | kept (already rescored) | none |
| B s11 | `res_B_s11_gpu` | 0 of 28 (partial) | no output | bach-fugue-873, bach-italian-concerto-2, bach-prelude-873, beethoven-appassionata-1, beethoven-hammerklavier-4, beethoven-waldstein-1, chopin-etude-op10-4, chopin-etude-op25-10, chopin-etude-op25-11, chopin-polonaise-op53, chopin-scherzo3, debussy-pour-le-piano-1, debussy-reflets, haydn-hob16-49-1, liszt-hr-6, liszt-paganini-6, liszt-sonata, liszt-te-10, liszt-te-5, mozart-k475, prokofiev-toccata, ravel-alborada, schubert-impromptu-d899-4, schubert-wanderer-3-4, schumann-kreisleriana-1, schumann-toccata, scriabin-sonata-5, stravinsky-petrushka |

## 2. Summary per run (means over the pieces scored; macro mean over pieces)

| run | pieces | staff-sens pitch | pooled pitch | pooled +onset | pooled full | worst piece (pooled) | worst without Petrushka | pieces at 97+ pooled | at 97+ staff-sens | bar count = reference |
|---|---|---|---|---|---|---|---|---|---|---|
| released | 28 | 90.25 | 91.99 | 77.05 | 75.00 | liszt-te-5 77.8 | liszt-te-5 77.8 | 6 of 28 | 5 | 14 of 28 |
| A s7 | 28 | 90.07 | 91.79 | 76.88 | 74.78 | liszt-te-5 78.7 | liszt-te-5 78.7 | 6 of 28 | 5 | 17 of 28 |
| A s11 | 28 | 90.22 | 91.92 | 77.22 | 75.13 | liszt-te-10 77.8 | liszt-te-10 77.8 | 8 of 28 | 6 | 12 of 28 |
| B s7 | 28 | 90.24 | 91.92 | 76.48 | 74.36 | stravinsky-petrushka 78.0 | liszt-te-5 78.2 | 7 of 28 | 5 | 14 of 28 |
| B s11 | 0 | missing | | | | | | | | |

Petrushka is provisional (three reference staves against two of ours; its pooled column uses one joint alignment, not verified). Bar count = reference means equal bar counts per part (a pair of counts for a piece whose hands differ).

## 3. Per piece

Percent F1. Bold figures in the pooled table are below 97. `*` = Schott scan, released column re-merged (`_am`); the GPU runs always use the current merger.

### 3a. Pooled sounding-pitch F1 (the target metric, 97)

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.6 | 99.7 | 99.4 | 99.2 | **missing** |
| bach-italian-concerto-2 | 98.9 | 98.8 | 99.0 | 98.7 | **missing** |
| bach-prelude-873 | 99.4 | 99.4 | 98.9 | 99.6 | **missing** |
| beethoven-appassionata-1 | 99.0 | 99.0 | 99.1 | 99.1 | **missing** |
| beethoven-hammerklavier-4 | **96.5** | **96.9** | **96.4** | 97.1 | **missing** |
| beethoven-waldstein-1 | 99.5 | 99.6 | 99.5 | 99.7 | **missing** |
| chopin-etude-op10-4 | **95.8** | **95.8** | **96.2** | **96.5** | **missing** |
| chopin-etude-op25-10 | **96.0** | **96.3** | 97.2 | **96.8** | **missing** |
| chopin-etude-op25-11 | **88.6** | **88.8** | **89.2** | **91.0** | **missing** |
| chopin-polonaise-op53 | **91.3** | **91.8** | **92.3** | **90.5** | **missing** |
| chopin-scherzo3 | **93.1** | **92.4** | **91.6** | **90.3** | **missing** |
| debussy-pour-le-piano-1 | **92.3** | **90.6** | **91.1** | **92.4** | **missing** |
| debussy-reflets | **85.8** | **87.5** | **87.0** | **85.9** | **missing** |
| haydn-hob16-49-1 | **95.3** | **92.9** | **95.5** | **93.5** | **missing** |
| liszt-hr-6 | **91.9** | **91.6** | **92.5** | **92.1** | **missing** |
| liszt-paganini-6 | **91.1** | **90.3** | **89.5** | **90.3** | **missing** |
| liszt-sonata * | **81.5** | **79.1** | **80.9** | **83.3** | **missing** |
| liszt-te-10 * | **79.8** | **79.9** | **77.8** | **82.2** | **missing** |
| liszt-te-5 * | **77.8** | **78.7** | **78.3** | **78.2** | **missing** |
| mozart-k475 | **95.2** | **94.4** | **94.5** | **95.0** | **missing** |
| prokofiev-toccata | **92.8** | **92.2** | **93.2** | **90.9** | **missing** |
| ravel-alborada | **82.1** | **82.1** | **81.5** | **81.4** | **missing** |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.0 | 98.6 | **missing** |
| schubert-wanderer-3-4 | **96.3** | **96.1** | **96.3** | **96.1** | **missing** |
| schumann-kreisleriana-1 | **96.9** | **96.6** | 97.6 | **96.8** | **missing** |
| schumann-toccata | **91.7** | **91.0** | **92.3** | **90.3** | **missing** |
| scriabin-sonata-5 | **89.2** | **90.1** | **89.2** | **90.4** | **missing** |
| stravinsky-petrushka (provisional) | **79.2** | **79.3** | **78.9** | **78.0** | **missing** |

### 3b. Staff-sensitive pitch F1

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.6 | 99.7 | 99.3 | 99.2 | **missing** |
| bach-italian-concerto-2 | 98.9 | 98.8 | 99.0 | 98.7 | **missing** |
| bach-prelude-873 | 99.4 | 99.3 | 98.9 | 99.6 | **missing** |
| beethoven-appassionata-1 | 98.8 | 98.8 | 98.9 | 99.0 | **missing** |
| beethoven-hammerklavier-4 | 89.5 | 89.6 | 89.4 | 89.8 | **missing** |
| beethoven-waldstein-1 | 94.2 | 94.3 | 94.2 | 94.3 | **missing** |
| chopin-etude-op10-4 | 94.8 | 94.8 | 95.2 | 95.4 | **missing** |
| chopin-etude-op25-10 | 96.0 | 96.3 | 97.2 | 96.8 | **missing** |
| chopin-etude-op25-11 | 88.5 | 88.8 | 89.1 | 91.0 | **missing** |
| chopin-polonaise-op53 | 89.0 | 89.5 | 90.0 | 88.0 | **missing** |
| chopin-scherzo3 | 91.8 | 91.1 | 90.2 | 88.6 | **missing** |
| debussy-pour-le-piano-1 | 91.8 | 90.2 | 90.6 | 91.8 | **missing** |
| debussy-reflets | 85.2 | 86.8 | 86.4 | 85.4 | **missing** |
| haydn-hob16-49-1 | 95.1 | 92.7 | 95.3 | 93.3 | **missing** |
| liszt-hr-6 | 91.8 | 91.5 | 92.5 | 92.1 | **missing** |
| liszt-paganini-6 | 90.7 | 90.0 | 89.4 | 90.2 | **missing** |
| liszt-sonata * | 81.0 | 78.7 | 80.5 | 83.0 | **missing** |
| liszt-te-10 * | 79.1 | 79.3 | 77.5 | 81.9 | **missing** |
| liszt-te-5 * | 77.0 | 78.4 | 77.6 | 78.0 | **missing** |
| mozart-k475 | 92.0 | 91.3 | 91.3 | 91.9 | **missing** |
| prokofiev-toccata | 92.8 | 92.1 | 93.2 | 90.9 | **missing** |
| ravel-alborada | 81.7 | 81.6 | 81.1 | 81.0 | **missing** |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.0 | 98.6 | **missing** |
| schubert-wanderer-3-4 | 94.9 | 94.7 | 94.9 | 94.7 | **missing** |
| schumann-kreisleriana-1 | 95.8 | 95.6 | 96.5 | 95.7 | **missing** |
| schumann-toccata | 91.2 | 90.5 | 91.8 | 89.8 | **missing** |
| scriabin-sonata-5 | 89.1 | 90.0 | 89.1 | 90.3 | **missing** |
| stravinsky-petrushka (provisional) | 58.3 | 58.4 | 58.3 | 57.9 | **missing** |

### 3c. Pooled pitch + onset F1

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 94.5 | 96.5 | 95.8 | 96.6 | **missing** |
| bach-italian-concerto-2 | 94.2 | 97.0 | 97.8 | 91.7 | **missing** |
| bach-prelude-873 | 97.2 | 97.1 | 96.8 | 99.4 | **missing** |
| beethoven-appassionata-1 | 91.2 | 90.3 | 91.5 | 90.9 | **missing** |
| beethoven-hammerklavier-4 | 89.8 | 90.1 | 88.8 | 90.6 | **missing** |
| beethoven-waldstein-1 | 96.0 | 93.8 | 93.6 | 95.5 | **missing** |
| chopin-etude-op10-4 | 94.1 | 93.8 | 94.5 | 93.8 | **missing** |
| chopin-etude-op25-10 | 72.3 | 69.1 | 71.3 | 72.9 | **missing** |
| chopin-etude-op25-11 | 53.4 | 55.6 | 53.2 | 48.8 | **missing** |
| chopin-polonaise-op53 | 73.5 | 75.6 | 77.1 | 65.8 | **missing** |
| chopin-scherzo3 | 90.6 | 90.0 | 89.3 | 87.6 | **missing** |
| debussy-pour-le-piano-1 | 77.4 | 78.0 | 78.8 | 77.8 | **missing** |
| debussy-reflets | 48.0 | 47.7 | 48.8 | 45.5 | **missing** |
| haydn-hob16-49-1 | 86.9 | 87.0 | 87.8 | 85.9 | **missing** |
| liszt-hr-6 | 81.9 | 81.3 | 80.9 | 78.8 | **missing** |
| liszt-paganini-6 | 64.1 | 62.6 | 62.6 | 67.1 | **missing** |
| liszt-sonata * | 66.9 | 63.6 | 65.4 | 68.7 | **missing** |
| liszt-te-10 * | 32.1 | 33.1 | 31.9 | 38.4 | **missing** |
| liszt-te-5 * | 62.6 | 62.3 | 61.8 | 62.3 | **missing** |
| mozart-k475 | 67.4 | 69.6 | 71.5 | 68.0 | **missing** |
| prokofiev-toccata | 82.4 | 78.9 | 82.0 | 77.1 | **missing** |
| ravel-alborada | 60.1 | 60.8 | 60.4 | 59.6 | **missing** |
| schubert-impromptu-d899-4 | 98.6 | 98.5 | 98.2 | 97.9 | **missing** |
| schubert-wanderer-3-4 | 94.9 | 94.6 | 95.1 | 94.7 | **missing** |
| schumann-kreisleriana-1 | 71.6 | 71.1 | 72.4 | 73.6 | **missing** |
| schumann-toccata | 82.9 | 81.0 | 82.6 | 80.3 | **missing** |
| scriabin-sonata-5 | 73.3 | 74.0 | 72.6 | 74.4 | **missing** |
| stravinsky-petrushka (provisional) | 59.4 | 59.7 | 59.8 | 58.0 | **missing** |

### 3d. Pooled full (pitch + onset + duration) F1

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 93.8 | 96.0 | 95.3 | 96.2 | **missing** |
| bach-italian-concerto-2 | 93.7 | 97.0 | 97.5 | 90.9 | **missing** |
| bach-prelude-873 | 96.9 | 96.8 | 96.5 | 99.2 | **missing** |
| beethoven-appassionata-1 | 90.3 | 89.4 | 90.5 | 90.2 | **missing** |
| beethoven-hammerklavier-4 | 89.0 | 89.5 | 88.0 | 89.8 | **missing** |
| beethoven-waldstein-1 | 95.4 | 93.1 | 92.9 | 94.9 | **missing** |
| chopin-etude-op10-4 | 93.9 | 93.6 | 94.3 | 93.5 | **missing** |
| chopin-etude-op25-10 | 68.7 | 64.7 | 67.4 | 68.7 | **missing** |
| chopin-etude-op25-11 | 50.4 | 52.4 | 50.0 | 45.3 | **missing** |
| chopin-polonaise-op53 | 69.3 | 71.7 | 73.8 | 60.5 | **missing** |
| chopin-scherzo3 | 89.7 | 89.1 | 88.5 | 86.7 | **missing** |
| debussy-pour-le-piano-1 | 76.7 | 77.2 | 78.1 | 76.8 | **missing** |
| debussy-reflets | 44.7 | 44.2 | 45.4 | 41.8 | **missing** |
| haydn-hob16-49-1 | 86.1 | 86.2 | 87.1 | 85.3 | **missing** |
| liszt-hr-6 | 81.3 | 80.5 | 80.2 | 78.1 | **missing** |
| liszt-paganini-6 | 61.5 | 59.5 | 60.1 | 64.8 | **missing** |
| liszt-sonata * | 64.6 | 61.2 | 63.1 | 65.9 | **missing** |
| liszt-te-10 * | 23.2 | 24.6 | 23.2 | 30.4 | **missing** |
| liszt-te-5 * | 60.7 | 60.1 | 59.3 | 60.2 | **missing** |
| mozart-k475 | 64.2 | 66.4 | 68.1 | 65.0 | **missing** |
| prokofiev-toccata | 81.6 | 77.6 | 80.6 | 75.4 | **missing** |
| ravel-alborada | 57.5 | 58.2 | 57.8 | 57.1 | **missing** |
| schubert-impromptu-d899-4 | 98.6 | 98.5 | 98.2 | 97.9 | **missing** |
| schubert-wanderer-3-4 | 94.4 | 94.1 | 94.6 | 94.3 | **missing** |
| schumann-kreisleriana-1 | 67.2 | 67.0 | 68.0 | 69.3 | **missing** |
| schumann-toccata | 81.3 | 79.5 | 80.8 | 78.9 | **missing** |
| scriabin-sonata-5 | 70.6 | 71.3 | 69.7 | 71.8 | **missing** |
| stravinsky-petrushka (provisional) | 54.6 | 54.6 | 54.9 | 53.1 | **missing** |

### 3e. Bars: ours / reference

A pair `x/y/z` means our two hands have x and y bars against z in the reference.

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 71/71 | 71/71 | 71/71 | 71/71 | **missing** |
| bach-italian-concerto-2 | 49/49 | 49/49 | 50/49 | 49/49 | **missing** |
| bach-prelude-873 | 62/62 | 62/62 | 62/62 | 62/62 | **missing** |
| beethoven-appassionata-1 | 264/264 | 264/264 | 264/264 | 264/264 | **missing** |
| beethoven-hammerklavier-4 | 406/406 | 406/406 | 406/406 | 406/406 | **missing** |
| beethoven-waldstein-1 | 304/304 | 304/304 | 304/304 | 304/304 | **missing** |
| chopin-etude-op10-4 | 83/83 | 83/83 | 83/83 | 83/83 | **missing** |
| chopin-etude-op25-10 | 119/119 | 119/119 | 119/119 | 119/119 | **missing** |
| chopin-etude-op25-11 | 96/96 | 96/96 | 96/96 | 96/96 | **missing** |
| chopin-polonaise-op53 | 182/181 | 181/181 | 181/181 | 179/181 | **missing** |
| chopin-scherzo3 | 648/649 | 649/649 | 648/649 | 649/649 | **missing** |
| debussy-pour-le-piano-1 | 163/162 | 162/162 | 163/162 | 161/162 | **missing** |
| debussy-reflets | 94/95 | 95/95 | 95/95 | 95/95 | **missing** |
| haydn-hob16-49-1 | 222/220 | 222/220 | 224/220 | 223/220 | **missing** |
| liszt-hr-6 | 244/225 | 239/225 | 239/225 | 237/225 | **missing** |
| liszt-paganini-6 | 220/220 | 220/220 | 219/220 | 219/220 | **missing** |
| liszt-sonata * | 306/305 | 309/305 | 308/305 | 306/305 | **missing** |
| liszt-te-10 * | 182/182 | 182/182 | 182/182 | 182/182 | **missing** |
| liszt-te-5 * | 134/134 | 133/134 | 133/134 | 131/134 | **missing** |
| mozart-k475 | 179/180 | 180/180 | 179/180 | 179/180 | **missing** |
| prokofiev-toccata | 227/226 | 224/226 | 227/226 | 222/226 | **missing** |
| ravel-alborada | 229/229 | 228/229 | 228/229 | 229/229 | **missing** |
| schubert-impromptu-d899-4 | 277/277 | 277/277 | 277/277 | 277/277 | **missing** |
| schubert-wanderer-3-4 | 476/475 | 476/475 | 476/475 | 476/475 | **missing** |
| schumann-kreisleriana-1 | 77/78 | 77/78 | 77/78 | 79/78 | **missing** |
| schumann-toccata | 275/283 | 272/283 | 276/283 | 271/283 | **missing** |
| scriabin-sonata-5 | 432/456 | 431/456 | 432/456 | 432/456 | **missing** |
| stravinsky-petrushka (provisional) | 598/627 | 598/627 | 595/627 | 601/627 | **missing** |

## 4. Paired differences, B minus A (same seed = same start weights, list, steps and data order; only the input size differs)

* seed 7: A = `res_A_s7_gpu`, B = `res_B_s7_gpu`, 28 of 28 pieces in both
* seed 11: no piece scored in both runs (A `res_A_s11_gpu`, B `res_B_s11_gpu`), not compared yet

### pooled pitch F1

| piece | A s7 | B s7 | d s7 | mean d | verdict |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.7 | 99.2 | -0.49 | -0.49 | B loses |
| bach-italian-concerto-2 | 98.8 | 98.7 | -0.13 | -0.13 | B loses |
| bach-prelude-873 | 99.4 | 99.6 | +0.20 | +0.20 | B wins |
| beethoven-appassionata-1 | 99.0 | 99.1 | +0.15 | +0.15 | B wins |
| beethoven-hammerklavier-4 | 96.9 | 97.1 | +0.21 | +0.21 | B wins |
| beethoven-waldstein-1 | 99.6 | 99.7 | +0.07 | +0.07 | tie |
| chopin-etude-op10-4 | 95.8 | 96.5 | +0.65 | +0.65 | B wins |
| chopin-etude-op25-10 | 96.3 | 96.8 | +0.46 | +0.46 | B wins |
| chopin-etude-op25-11 | 88.8 | 91.0 | +2.23 | +2.23 | B wins |
| chopin-polonaise-op53 | 91.8 | 90.5 | -1.34 | -1.34 | B loses |
| chopin-scherzo3 | 92.4 | 90.3 | -2.06 | -2.06 | B loses |
| debussy-pour-le-piano-1 | 90.6 | 92.4 | +1.82 | +1.82 | B wins |
| debussy-reflets | 87.5 | 85.9 | -1.56 | -1.56 | B loses |
| haydn-hob16-49-1 | 92.9 | 93.5 | +0.55 | +0.55 | B wins |
| liszt-hr-6 | 91.6 | 92.1 | +0.49 | +0.49 | B wins |
| liszt-paganini-6 | 90.3 | 90.3 | +0.05 | +0.05 | tie |
| liszt-sonata | 79.1 | 83.3 | +4.20 | +4.20 | B wins |
| liszt-te-10 | 79.9 | 82.2 | +2.28 | +2.28 | B wins |
| liszt-te-5 | 78.7 | 78.2 | -0.50 | -0.50 | B loses |
| mozart-k475 | 94.4 | 95.0 | +0.57 | +0.57 | B wins |
| prokofiev-toccata | 92.2 | 90.9 | -1.24 | -1.24 | B loses |
| ravel-alborada | 82.1 | 81.4 | -0.65 | -0.65 | B loses |
| schubert-impromptu-d899-4 | 99.2 | 98.6 | -0.60 | -0.60 | B loses |
| schubert-wanderer-3-4 | 96.1 | 96.1 | -0.00 | -0.00 | tie |
| schumann-kreisleriana-1 | 96.6 | 96.8 | +0.13 | +0.13 | B wins |
| schumann-toccata | 91.0 | 90.3 | -0.71 | -0.71 | B loses |
| scriabin-sonata-5 | 90.1 | 90.4 | +0.30 | +0.30 | B wins |
| stravinsky-petrushka | 79.3 | 78.0 | -1.31 | -1.31 | B loses |

Mean B - A per seed: s7 +0.13 (28 pieces). B wins 14, loses 11, ties 3 (tie band 0.1); both seeds agree beyond the band on 0; sign test over the 25 decided pieces p = 0.690.

### staff-sensitive pitch F1

| piece | A s7 | B s7 | d s7 | mean d | verdict |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.7 | 99.2 | -0.49 | -0.49 | B loses |
| bach-italian-concerto-2 | 98.8 | 98.7 | -0.13 | -0.13 | B loses |
| bach-prelude-873 | 99.3 | 99.6 | +0.28 | +0.28 | B wins |
| beethoven-appassionata-1 | 98.8 | 99.0 | +0.15 | +0.15 | B wins |
| beethoven-hammerklavier-4 | 89.6 | 89.8 | +0.19 | +0.19 | B wins |
| beethoven-waldstein-1 | 94.3 | 94.3 | +0.07 | +0.07 | tie |
| chopin-etude-op10-4 | 94.8 | 95.4 | +0.65 | +0.65 | B wins |
| chopin-etude-op25-10 | 96.3 | 96.8 | +0.46 | +0.46 | B wins |
| chopin-etude-op25-11 | 88.8 | 91.0 | +2.20 | +2.20 | B wins |
| chopin-polonaise-op53 | 89.5 | 88.0 | -1.43 | -1.43 | B loses |
| chopin-scherzo3 | 91.1 | 88.6 | -2.45 | -2.45 | B loses |
| debussy-pour-le-piano-1 | 90.2 | 91.8 | +1.58 | +1.58 | B wins |
| debussy-reflets | 86.8 | 85.4 | -1.38 | -1.38 | B loses |
| haydn-hob16-49-1 | 92.7 | 93.3 | +0.55 | +0.55 | B wins |
| liszt-hr-6 | 91.5 | 92.1 | +0.57 | +0.57 | B wins |
| liszt-paganini-6 | 90.0 | 90.2 | +0.23 | +0.23 | B wins |
| liszt-sonata | 78.7 | 83.0 | +4.23 | +4.23 | B wins |
| liszt-te-10 | 79.3 | 81.9 | +2.57 | +2.57 | B wins |
| liszt-te-5 | 78.4 | 78.0 | -0.39 | -0.39 | B loses |
| mozart-k475 | 91.3 | 91.9 | +0.62 | +0.62 | B wins |
| prokofiev-toccata | 92.1 | 90.9 | -1.24 | -1.24 | B loses |
| ravel-alborada | 81.6 | 81.0 | -0.61 | -0.61 | B loses |
| schubert-impromptu-d899-4 | 99.2 | 98.6 | -0.62 | -0.62 | B loses |
| schubert-wanderer-3-4 | 94.7 | 94.7 | +0.02 | +0.02 | tie |
| schumann-kreisleriana-1 | 95.6 | 95.7 | +0.13 | +0.13 | B wins |
| schumann-toccata | 90.5 | 89.8 | -0.71 | -0.71 | B loses |
| scriabin-sonata-5 | 90.0 | 90.3 | +0.28 | +0.28 | B wins |
| stravinsky-petrushka | 58.4 | 57.9 | -0.51 | -0.51 | B loses |

Mean B - A per seed: s7 +0.17 (28 pieces). B wins 15, loses 11, ties 2 (tie band 0.1); both seeds agree beyond the band on 0; sign test over the 26 decided pieces p = 0.557.

### pooled pitch+onset F1

| piece | A s7 | B s7 | d s7 | mean d | verdict |
|---|---|---|---|---|---|
| bach-fugue-873 | 96.5 | 96.6 | +0.07 | +0.07 | tie |
| bach-italian-concerto-2 | 97.0 | 91.7 | -5.31 | -5.31 | B loses |
| bach-prelude-873 | 97.1 | 99.4 | +2.23 | +2.23 | B wins |
| beethoven-appassionata-1 | 90.3 | 90.9 | +0.63 | +0.63 | B wins |
| beethoven-hammerklavier-4 | 90.1 | 90.6 | +0.53 | +0.53 | B wins |
| beethoven-waldstein-1 | 93.8 | 95.5 | +1.65 | +1.65 | B wins |
| chopin-etude-op10-4 | 93.8 | 93.8 | -0.02 | -0.02 | tie |
| chopin-etude-op25-10 | 69.1 | 72.9 | +3.82 | +3.82 | B wins |
| chopin-etude-op25-11 | 55.6 | 48.8 | -6.81 | -6.81 | B loses |
| chopin-polonaise-op53 | 75.6 | 65.8 | -9.79 | -9.79 | B loses |
| chopin-scherzo3 | 90.0 | 87.6 | -2.39 | -2.39 | B loses |
| debussy-pour-le-piano-1 | 78.0 | 77.8 | -0.24 | -0.24 | B loses |
| debussy-reflets | 47.7 | 45.5 | -2.16 | -2.16 | B loses |
| haydn-hob16-49-1 | 87.0 | 85.9 | -1.13 | -1.13 | B loses |
| liszt-hr-6 | 81.3 | 78.8 | -2.55 | -2.55 | B loses |
| liszt-paganini-6 | 62.6 | 67.1 | +4.50 | +4.50 | B wins |
| liszt-sonata | 63.6 | 68.7 | +5.14 | +5.14 | B wins |
| liszt-te-10 | 33.1 | 38.4 | +5.29 | +5.29 | B wins |
| liszt-te-5 | 62.3 | 62.3 | +0.07 | +0.07 | tie |
| mozart-k475 | 69.6 | 68.0 | -1.65 | -1.65 | B loses |
| prokofiev-toccata | 78.9 | 77.1 | -1.76 | -1.76 | B loses |
| ravel-alborada | 60.8 | 59.6 | -1.22 | -1.22 | B loses |
| schubert-impromptu-d899-4 | 98.5 | 97.9 | -0.62 | -0.62 | B loses |
| schubert-wanderer-3-4 | 94.6 | 94.7 | +0.15 | +0.15 | B wins |
| schumann-kreisleriana-1 | 71.1 | 73.6 | +2.53 | +2.53 | B wins |
| schumann-toccata | 81.0 | 80.3 | -0.73 | -0.73 | B loses |
| scriabin-sonata-5 | 74.0 | 74.4 | +0.35 | +0.35 | B wins |
| stravinsky-petrushka | 59.7 | 58.0 | -1.66 | -1.66 | B loses |

Mean B - A per seed: s7 -0.40 (28 pieces). B wins 11, loses 14, ties 3 (tie band 0.1); both seeds agree beyond the band on 0; sign test over the 25 decided pieces p = 0.690.

### pooled full F1

| piece | A s7 | B s7 | d s7 | mean d | verdict |
|---|---|---|---|---|---|
| bach-fugue-873 | 96.0 | 96.2 | +0.20 | +0.20 | B wins |
| bach-italian-concerto-2 | 97.0 | 90.9 | -6.09 | -6.09 | B loses |
| bach-prelude-873 | 96.8 | 99.2 | +2.39 | +2.39 | B wins |
| beethoven-appassionata-1 | 89.4 | 90.2 | +0.85 | +0.85 | B wins |
| beethoven-hammerklavier-4 | 89.5 | 89.8 | +0.36 | +0.36 | B wins |
| beethoven-waldstein-1 | 93.1 | 94.9 | +1.79 | +1.79 | B wins |
| chopin-etude-op10-4 | 93.6 | 93.5 | -0.11 | -0.11 | B loses |
| chopin-etude-op25-10 | 64.7 | 68.7 | +3.94 | +3.94 | B wins |
| chopin-etude-op25-11 | 52.4 | 45.3 | -7.09 | -7.09 | B loses |
| chopin-polonaise-op53 | 71.7 | 60.5 | -11.13 | -11.13 | B loses |
| chopin-scherzo3 | 89.1 | 86.7 | -2.36 | -2.36 | B loses |
| debussy-pour-le-piano-1 | 77.2 | 76.8 | -0.45 | -0.45 | B loses |
| debussy-reflets | 44.2 | 41.8 | -2.40 | -2.40 | B loses |
| haydn-hob16-49-1 | 86.2 | 85.3 | -0.87 | -0.87 | B loses |
| liszt-hr-6 | 80.5 | 78.1 | -2.36 | -2.36 | B loses |
| liszt-paganini-6 | 59.5 | 64.8 | +5.34 | +5.34 | B wins |
| liszt-sonata | 61.2 | 65.9 | +4.75 | +4.75 | B wins |
| liszt-te-10 | 24.6 | 30.4 | +5.80 | +5.80 | B wins |
| liszt-te-5 | 60.1 | 60.2 | +0.12 | +0.12 | B wins |
| mozart-k475 | 66.4 | 65.0 | -1.38 | -1.38 | B loses |
| prokofiev-toccata | 77.6 | 75.4 | -2.17 | -2.17 | B loses |
| ravel-alborada | 58.2 | 57.1 | -1.07 | -1.07 | B loses |
| schubert-impromptu-d899-4 | 98.5 | 97.9 | -0.60 | -0.60 | B loses |
| schubert-wanderer-3-4 | 94.1 | 94.3 | +0.17 | +0.17 | B wins |
| schumann-kreisleriana-1 | 67.0 | 69.3 | +2.28 | +2.28 | B wins |
| schumann-toccata | 79.5 | 78.9 | -0.58 | -0.58 | B loses |
| scriabin-sonata-5 | 71.3 | 71.8 | +0.41 | +0.41 | B wins |
| stravinsky-petrushka | 54.6 | 53.1 | -1.51 | -1.51 | B loses |

Mean B - A per seed: s7 -0.42 (28 pieces). B wins 13, loses 15, ties 0 (tie band 0.1); both seeds agree beyond the band on 0; sign test over the 28 decided pieces p = 0.851.

### dense-bar recall of pitches

| piece | A s7 | B s7 | d s7 | mean d | verdict |
|---|---|---|---|---|---|
| bach-fugue-873 | 100.0 | 99.7 | -0.31 | -0.31 | B loses |
| bach-italian-concerto-2 | 99.6 | 99.3 | -0.36 | -0.36 | B loses |
| bach-prelude-873 | 98.5 | 99.2 | +0.77 | +0.77 | B wins |
| beethoven-appassionata-1 | 98.8 | 99.0 | +0.24 | +0.24 | B wins |
| beethoven-hammerklavier-4 | 94.6 | 93.9 | -0.70 | -0.70 | B loses |
| beethoven-waldstein-1 | 99.9 | 99.9 | +0.02 | +0.02 | tie |
| chopin-etude-op10-4 | 95.8 | 96.3 | +0.50 | +0.50 | B wins |
| chopin-etude-op25-10 | 96.2 | 96.6 | +0.47 | +0.47 | B wins |
| chopin-etude-op25-11 | 87.8 | 90.4 | +2.57 | +2.57 | B wins |
| chopin-polonaise-op53 | 89.9 | 88.1 | -1.78 | -1.78 | B loses |
| debussy-pour-le-piano-1 | 83.5 | 87.5 | +3.93 | +3.93 | B wins |
| debussy-reflets | 84.9 | 83.6 | -1.22 | -1.22 | B loses |
| haydn-hob16-49-1 | 77.2 | 82.3 | +5.06 | +5.06 | B wins |
| liszt-hr-6 | 89.7 | 89.4 | -0.34 | -0.34 | B loses |
| liszt-paganini-6 | 84.8 | 80.7 | -4.10 | -4.10 | B loses |
| liszt-sonata | 77.1 | 82.3 | +5.16 | +5.16 | B wins |
| liszt-te-10 | 81.9 | 83.4 | +1.53 | +1.53 | B wins |
| liszt-te-5 | 78.0 | 77.2 | -0.80 | -0.80 | B loses |
| mozart-k475 | 93.3 | 92.7 | -0.58 | -0.58 | B loses |
| prokofiev-toccata | 92.4 | 91.8 | -0.54 | -0.54 | B loses |
| ravel-alborada | 77.9 | 77.4 | -0.59 | -0.59 | B loses |
| schubert-impromptu-d899-4 | 99.3 | 99.7 | +0.38 | +0.38 | B wins |
| schubert-wanderer-3-4 | 95.8 | 95.8 | -0.08 | -0.08 | tie |
| schumann-kreisleriana-1 | 95.8 | 95.8 | +0.00 | +0.00 | tie |
| schumann-toccata | 89.7 | 88.6 | -1.07 | -1.07 | B loses |
| scriabin-sonata-5 | 82.3 | 82.1 | -0.19 | -0.19 | B loses |
| stravinsky-petrushka | 75.3 | 74.3 | -0.99 | -0.99 | B loses |

Mean B - A per seed: s7 +0.26 (27 pieces). B wins 10, loses 14, ties 3 (tie band 0.1); both seeds agree beyond the band on 0; sign test over the 24 decided pieces p = 0.541.

Seed noise, arm A: s11 - s7 pooled pitch over 28 pieces: mean +0.13, mean absolute difference 0.70, largest +2.62, pieces with |diff| >= 1 point: 5.

## 5. Missed notes in dense passages

Dense = reference bars (all staves together, visible notes) with at least 24 notes. Recall = share of the reference pitches found in the aligned bar (pooled alignment; Petrushka is per staff). Missed = number of reference notes not found.

| run | pieces | dense bars | dense reference notes | dense pitches missed | dense recall % |
|---|---|---|---|---|---|
| released | 28 | 2110 | 69957 | 8834 | 87.37 |
| A s7 | 28 | 2110 | 69957 | 8828 | 87.38 |
| A s11 | 28 | 2110 | 69957 | 8898 | 87.28 |
| B s7 | 28 | 2110 | 69957 | 8858 | 87.34 |
| B s11 | 0 | | | | |

Per piece dense-bar recall % (pitches missed in brackets):

| piece | dense bars / notes | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|---|
| bach-fugue-873 | 13 / 323 | 100.0 (0) | 100.0 (0) | 98.8 (4) | 99.7 (1) | **missing** |
| bach-italian-concerto-2 | 30 / 829 | 99.5 (4) | 99.6 (3) | 99.5 (4) | 99.3 (6) | **missing** |
| bach-prelude-873 | 10 / 261 | 98.5 (4) | 98.5 (4) | 98.5 (4) | 99.2 (2) | **missing** |
| beethoven-appassionata-1 | 137 / 4587 | 98.7 (61) | 98.8 (57) | 98.8 (53) | 99.0 (46) | **missing** |
| beethoven-hammerklavier-4 | 50 / 1569 | 94.1 (92) | 94.6 (85) | 92.9 (111) | 93.9 (96) | **missing** |
| beethoven-waldstein-1 | 146 / 4295 | 99.8 (10) | 99.9 (5) | 99.8 (10) | 99.9 (4) | **missing** |
| chopin-etude-op10-4 | 69 / 1999 | 96.1 (77) | 95.8 (83) | 96.1 (78) | 96.3 (73) | **missing** |
| chopin-etude-op25-10 | 43 / 2134 | 95.7 (91) | 96.2 (82) | 97.0 (64) | 96.6 (72) | **missing** |
| chopin-etude-op25-11 | 89 / 3111 | 87.7 (383) | 87.8 (378) | 88.3 (364) | 90.4 (298) | **missing** |
| chopin-polonaise-op53 | 156 / 5666 | 89.4 (603) | 89.9 (574) | 90.5 (540) | 88.1 (675) | **missing** |
| chopin-scherzo3 | 0 / 0 | n/a | n/a | n/a | n/a | **missing** |
| debussy-pour-le-piano-1 | 44 / 1476 | 87.2 (189) | 83.5 (243) | 85.2 (219) | 87.5 (185) | **missing** |
| debussy-reflets | 45 / 1393 | 82.0 (251) | 84.9 (211) | 84.8 (212) | 83.6 (228) | **missing** |
| haydn-hob16-49-1 | 2 / 79 | 86.1 (11) | 77.2 (18) | 78.5 (17) | 82.3 (14) | **missing** |
| liszt-hr-6 | 85 / 2618 | 89.1 (285) | 89.7 (269) | 90.2 (257) | 89.4 (278) | **missing** |
| liszt-paganini-6 | 58 / 2050 | 86.6 (275) | 84.8 (311) | 84.2 (323) | 80.7 (395) | **missing** |
| liszt-sonata | 123 / 3898 | 79.5 (800) | 77.1 (892) | 79.2 (811) | 82.3 (691) | **missing** |
| liszt-te-10 | 83 / 2290 | 82.2 (408) | 81.9 (414) | 77.9 (507) | 83.4 (379) | **missing** |
| liszt-te-5 | 115 / 4231 | 76.7 (984) | 78.0 (931) | 77.1 (969) | 77.2 (965) | **missing** |
| mozart-k475 | 61 / 2086 | 94.1 (123) | 93.3 (140) | 92.8 (150) | 92.7 (152) | **missing** |
| prokofiev-toccata | 71 / 2205 | 92.1 (175) | 92.4 (168) | 92.6 (164) | 91.8 (180) | **missing** |
| ravel-alborada | 63 / 2045 | 78.0 (449) | 77.9 (451) | 76.9 (472) | 77.4 (463) | **missing** |
| schubert-impromptu-d899-4 | 38 / 1064 | 99.5 (5) | 99.3 (7) | 99.3 (7) | 99.7 (3) | **missing** |
| schubert-wanderer-3-4 | 75 / 2599 | 96.0 (105) | 95.8 (108) | 96.0 (105) | 95.8 (110) | **missing** |
| schumann-kreisleriana-1 | 2 / 48 | 95.8 (2) | 95.8 (2) | 95.8 (2) | 95.8 (2) | **missing** |
| schumann-toccata | 151 / 4280 | 90.3 (416) | 89.7 (442) | 90.3 (417) | 88.6 (488) | **missing** |
| scriabin-sonata-5 | 99 / 3147 | 80.6 (612) | 82.3 (557) | 81.2 (592) | 82.1 (563) | **missing** |
| stravinsky-petrushka | 252 / 9674 | 75.0 (2419) | 75.3 (2393) | 74.8 (2442) | 74.3 (2489) | **missing** |

## 6. What moved

Rule: SINGLE SEED (7) only, provisional: pieces where the pooled pitch F1 changes by at least 1 point (a one-seed change is not yet distinguishable from seed noise, see the seed-noise line in section 4).

| piece | direction | d s7 | A pooled (mean) | B pooled (mean) |
|---|---|---|---|---|
| liszt-sonata | B better | +4.20 | 79.1 | 83.3 |
| liszt-te-10 | B better | +2.28 | 79.9 | 82.2 |
| chopin-etude-op25-11 | B better | +2.23 | 88.8 | 91.0 |
| chopin-scherzo3 | B worse | -2.06 | 92.4 | 90.3 |
| debussy-pour-le-piano-1 | B better | +1.82 | 90.6 | 92.4 |
| debussy-reflets | B worse | -1.56 | 87.5 | 85.9 |
| chopin-polonaise-op53 | B worse | -1.34 | 91.8 | 90.5 |
| stravinsky-petrushka | B worse | -1.31 | 79.3 | 78.0 |
| prokofiev-toccata | B worse | -1.24 | 92.2 | 90.9 |

## 7. Inference cost on the box (wall time per page from the saved per-piece times)

From `eval_run1/testset/<tag>/<piece>/wall_seconds.txt` (the `run_homr.py` call of the piece: segmentation, staff detection, transformer; merge and scoring not included) divided by the page count. Pieces are run one after the other by `res_eval.py`, but **the box is shared** with other agents' jobs, so these times are only indicative; a clean comparison needs a quiet box (`res_timing.py` on 5 pages, see `RESOLUTION_EVAL.md`, 'Final comparison').

| run | pieces with a time | pages | wall s per page (total / pages) | median of per-piece s/page |
|---|---|---|---|---|
| A s7 | 28 | 302 | 5.10 | 4.61 |
| A s11 | 28 | 302 | 6.17 | 5.38 |
| B s7 | 28 | 302 | 5.81 | 5.83 |
| B s11 | 0 | | missing (per-piece times not pulled) | |

Seed 7, 28 common pieces: B/A wall ratio 1.14 (summed), per-piece median 1.15, range 0.44-1.60. Spread of the same measure between A s7 and A s11 (same model size, different run) gives the noise of this timing.
Noise yardstick: A s11 / A s7 wall ratio per piece, median 1.27, range 0.39-2.76 over 28 pieces (the same architecture, so the ratio would be 1.0 on a quiet box).

