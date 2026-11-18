# Resolution experiment, final comparison (arm A 256x1280 vs arm B 384x1920), 2026-11-17

Generated 2026-11-17 22:08 PST by `eval_run1/res_final_table.py`. Same GPU pipeline for every arm (`res_eval.py`: same layout, merger, scorer, loop guard), visible notes only, **edition-corrected references for every column** (Schubert D. 899/4 against `schubert-impromptu-d899-4-reference-edition.musicxml`; the Scriabin reference is the one without the stray part). Pooled = a pitch counts if it is in the aligned bar on either staff (sounding pitch, correct octave and bar). Target: 97 % pooled pitch on every piece. The released column is the laptop CPU run of the released model after the merger fixes (not the same hardware as the GPU arms; reference only).

## 1. Runs

| column | tag | pieces scored | Schubert re-score | missing |
|---|---|---|---|---|
| released | `layout1` | 28 of 28 | existing -edition files | none |
| A s7 | `res_A_s7_gpu` | 28 of 28 | schubert-impromptu-d899-4: kept (already rescored) | none |
| A s11 | `res_A_s11_gpu` | 28 of 28 | schubert-impromptu-d899-4: kept (already rescored) | none |
| B s7 | `res_B_s7_gpu` | 28 of 28 | schubert-impromptu-d899-4: kept (already rescored) | none |
| B s11 | `res_B_s11_gpu` | 28 of 28 | schubert-impromptu-d899-4: kept (already rescored) | none |

## 2. Summary per run (means over the pieces scored; macro mean over pieces)

| run | pieces | staff-sens pitch | pooled pitch | pooled +onset | pooled full | worst piece (pooled) | worst without Petrushka | pieces at 97+ pooled | at 97+ staff-sens | bar count = reference |
|---|---|---|---|---|---|---|---|---|---|---|
| released | 28 | 90.25 | 91.99 | 77.05 | 75.00 | liszt-te-5 77.8 | liszt-te-5 77.8 | 6 of 28 | 5 | 14 of 28 |
| A s7 | 28 | 90.07 | 91.79 | 76.88 | 74.78 | liszt-te-5 78.7 | liszt-te-5 78.7 | 6 of 28 | 5 | 17 of 28 |
| A s11 | 28 | 90.22 | 91.92 | 77.22 | 75.13 | liszt-te-10 77.8 | liszt-te-10 77.8 | 8 of 28 | 6 | 12 of 28 |
| B s7 | 28 | 90.24 | 91.92 | 76.48 | 74.36 | stravinsky-petrushka 78.0 | liszt-te-5 78.2 | 7 of 28 | 5 | 14 of 28 |
| B s11 | 28 | 90.26 | 91.96 | 76.59 | 74.48 | stravinsky-petrushka 77.8 | liszt-te-5 79.4 | 8 of 28 | 6 | 16 of 28 |

Petrushka is provisional (three reference staves against two of ours; its pooled column uses one joint alignment, not verified). Bar count = reference means equal bar counts per part (a pair of counts for a piece whose hands differ).

## 3. Per piece

Percent F1. Bold figures in the pooled table are below 97. `*` = Schott scan, released column re-merged (`_am`); the GPU runs always use the current merger.

### 3a. Pooled sounding-pitch F1 (the target metric, 97)

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.6 | 99.7 | 99.4 | 99.2 | 99.5 |
| bach-italian-concerto-2 | 98.9 | 98.8 | 99.0 | 98.7 | 98.8 |
| bach-prelude-873 | 99.4 | 99.4 | 98.9 | 99.6 | 99.6 |
| beethoven-appassionata-1 | 99.0 | 99.0 | 99.1 | 99.1 | 99.2 |
| beethoven-hammerklavier-4 | **96.5** | **96.9** | **96.4** | 97.1 | **96.7** |
| beethoven-waldstein-1 | 99.5 | 99.6 | 99.5 | 99.7 | 99.7 |
| chopin-etude-op10-4 | **95.8** | **95.8** | **96.2** | **96.5** | **96.7** |
| chopin-etude-op25-10 | **96.0** | **96.3** | 97.2 | **96.8** | 97.2 |
| chopin-etude-op25-11 | **88.6** | **88.8** | **89.2** | **91.0** | **90.9** |
| chopin-polonaise-op53 | **91.3** | **91.8** | **92.3** | **90.5** | **90.8** |
| chopin-scherzo3 | **93.1** | **92.4** | **91.6** | **90.3** | **90.3** |
| debussy-pour-le-piano-1 | **92.3** | **90.6** | **91.1** | **92.4** | **93.9** |
| debussy-reflets | **85.8** | **87.5** | **87.0** | **85.9** | **86.6** |
| haydn-hob16-49-1 | **95.3** | **92.9** | **95.5** | **93.5** | **93.1** |
| liszt-hr-6 | **91.9** | **91.6** | **92.5** | **92.1** | **92.1** |
| liszt-paganini-6 | **91.1** | **90.3** | **89.5** | **90.3** | **90.3** |
| liszt-sonata * | **81.5** | **79.1** | **80.9** | **83.3** | **81.4** |
| liszt-te-10 * | **79.8** | **79.9** | **77.8** | **82.2** | **80.5** |
| liszt-te-5 * | **77.8** | **78.7** | **78.3** | **78.2** | **79.4** |
| mozart-k475 | **95.2** | **94.4** | **94.5** | **95.0** | **95.4** |
| prokofiev-toccata | **92.8** | **92.2** | **93.2** | **90.9** | **90.8** |
| ravel-alborada | **82.1** | **82.1** | **81.5** | **81.4** | **82.0** |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.0 | 98.6 | 98.6 |
| schubert-wanderer-3-4 | **96.3** | **96.1** | **96.3** | **96.1** | **96.2** |
| schumann-kreisleriana-1 | **96.9** | **96.6** | 97.6 | **96.8** | 97.2 |
| schumann-toccata | **91.7** | **91.0** | **92.3** | **90.3** | **89.5** |
| scriabin-sonata-5 | **89.2** | **90.1** | **89.2** | **90.4** | **90.6** |
| stravinsky-petrushka (provisional) | **79.2** | **79.3** | **78.9** | **78.0** | **77.8** |

### 3b. Staff-sensitive pitch F1

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 99.6 | 99.7 | 99.3 | 99.2 | 99.5 |
| bach-italian-concerto-2 | 98.9 | 98.8 | 99.0 | 98.7 | 98.8 |
| bach-prelude-873 | 99.4 | 99.3 | 98.9 | 99.6 | 99.6 |
| beethoven-appassionata-1 | 98.8 | 98.8 | 98.9 | 99.0 | 99.1 |
| beethoven-hammerklavier-4 | 89.5 | 89.6 | 89.4 | 89.8 | 89.7 |
| beethoven-waldstein-1 | 94.2 | 94.3 | 94.2 | 94.3 | 94.3 |
| chopin-etude-op10-4 | 94.8 | 94.8 | 95.2 | 95.4 | 95.8 |
| chopin-etude-op25-10 | 96.0 | 96.3 | 97.2 | 96.8 | 97.1 |
| chopin-etude-op25-11 | 88.5 | 88.8 | 89.1 | 91.0 | 90.9 |
| chopin-polonaise-op53 | 89.0 | 89.5 | 90.0 | 88.0 | 88.3 |
| chopin-scherzo3 | 91.8 | 91.1 | 90.2 | 88.6 | 88.7 |
| debussy-pour-le-piano-1 | 91.8 | 90.2 | 90.6 | 91.8 | 93.2 |
| debussy-reflets | 85.2 | 86.8 | 86.4 | 85.4 | 86.0 |
| haydn-hob16-49-1 | 95.1 | 92.7 | 95.3 | 93.3 | 92.8 |
| liszt-hr-6 | 91.8 | 91.5 | 92.5 | 92.1 | 92.1 |
| liszt-paganini-6 | 90.7 | 90.0 | 89.4 | 90.2 | 90.1 |
| liszt-sonata * | 81.0 | 78.7 | 80.5 | 83.0 | 81.0 |
| liszt-te-10 * | 79.1 | 79.3 | 77.5 | 81.9 | 79.9 |
| liszt-te-5 * | 77.0 | 78.4 | 77.6 | 78.0 | 79.1 |
| mozart-k475 | 92.0 | 91.3 | 91.3 | 91.9 | 92.2 |
| prokofiev-toccata | 92.8 | 92.1 | 93.2 | 90.9 | 90.8 |
| ravel-alborada | 81.7 | 81.6 | 81.1 | 81.0 | 81.6 |
| schubert-impromptu-d899-4 | 99.2 | 99.2 | 99.0 | 98.6 | 98.6 |
| schubert-wanderer-3-4 | 94.9 | 94.7 | 94.9 | 94.7 | 94.9 |
| schumann-kreisleriana-1 | 95.8 | 95.6 | 96.5 | 95.7 | 96.0 |
| schumann-toccata | 91.2 | 90.5 | 91.8 | 89.8 | 89.0 |
| scriabin-sonata-5 | 89.1 | 90.0 | 89.1 | 90.3 | 90.6 |
| stravinsky-petrushka (provisional) | 58.3 | 58.4 | 58.3 | 57.9 | 57.6 |

### 3c. Pooled pitch + onset F1

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 94.5 | 96.5 | 95.8 | 96.6 | 97.6 |
| bach-italian-concerto-2 | 94.2 | 97.0 | 97.8 | 91.7 | 97.5 |
| bach-prelude-873 | 97.2 | 97.1 | 96.8 | 99.4 | 99.4 |
| beethoven-appassionata-1 | 91.2 | 90.3 | 91.5 | 90.9 | 92.6 |
| beethoven-hammerklavier-4 | 89.8 | 90.1 | 88.8 | 90.6 | 90.2 |
| beethoven-waldstein-1 | 96.0 | 93.8 | 93.6 | 95.5 | 95.0 |
| chopin-etude-op10-4 | 94.1 | 93.8 | 94.5 | 93.8 | 94.4 |
| chopin-etude-op25-10 | 72.3 | 69.1 | 71.3 | 72.9 | 71.3 |
| chopin-etude-op25-11 | 53.4 | 55.6 | 53.2 | 48.8 | 53.5 |
| chopin-polonaise-op53 | 73.5 | 75.6 | 77.1 | 65.8 | 64.1 |
| chopin-scherzo3 | 90.6 | 90.0 | 89.3 | 87.6 | 88.0 |
| debussy-pour-le-piano-1 | 77.4 | 78.0 | 78.8 | 77.8 | 79.1 |
| debussy-reflets | 48.0 | 47.7 | 48.8 | 45.5 | 45.2 |
| haydn-hob16-49-1 | 86.9 | 87.0 | 87.8 | 85.9 | 84.8 |
| liszt-hr-6 | 81.9 | 81.3 | 80.9 | 78.8 | 79.1 |
| liszt-paganini-6 | 64.1 | 62.6 | 62.6 | 67.1 | 64.9 |
| liszt-sonata * | 66.9 | 63.6 | 65.4 | 68.7 | 65.7 |
| liszt-te-10 * | 32.1 | 33.1 | 31.9 | 38.4 | 35.1 |
| liszt-te-5 * | 62.6 | 62.3 | 61.8 | 62.3 | 63.2 |
| mozart-k475 | 67.4 | 69.6 | 71.5 | 68.0 | 68.2 |
| prokofiev-toccata | 82.4 | 78.9 | 82.0 | 77.1 | 77.6 |
| ravel-alborada | 60.1 | 60.8 | 60.4 | 59.6 | 59.9 |
| schubert-impromptu-d899-4 | 98.6 | 98.5 | 98.2 | 97.9 | 97.9 |
| schubert-wanderer-3-4 | 94.9 | 94.6 | 95.1 | 94.7 | 94.9 |
| schumann-kreisleriana-1 | 71.6 | 71.1 | 72.4 | 73.6 | 73.1 |
| schumann-toccata | 82.9 | 81.0 | 82.6 | 80.3 | 80.9 |
| scriabin-sonata-5 | 73.3 | 74.0 | 72.6 | 74.4 | 73.8 |
| stravinsky-petrushka (provisional) | 59.4 | 59.7 | 59.8 | 58.0 | 57.6 |

### 3d. Pooled full (pitch + onset + duration) F1

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 93.8 | 96.0 | 95.3 | 96.2 | 97.3 |
| bach-italian-concerto-2 | 93.7 | 97.0 | 97.5 | 90.9 | 97.1 |
| bach-prelude-873 | 96.9 | 96.8 | 96.5 | 99.2 | 99.2 |
| beethoven-appassionata-1 | 90.3 | 89.4 | 90.5 | 90.2 | 91.7 |
| beethoven-hammerklavier-4 | 89.0 | 89.5 | 88.0 | 89.8 | 89.5 |
| beethoven-waldstein-1 | 95.4 | 93.1 | 92.9 | 94.9 | 94.5 |
| chopin-etude-op10-4 | 93.9 | 93.6 | 94.3 | 93.5 | 94.0 |
| chopin-etude-op25-10 | 68.7 | 64.7 | 67.4 | 68.7 | 66.5 |
| chopin-etude-op25-11 | 50.4 | 52.4 | 50.0 | 45.3 | 50.3 |
| chopin-polonaise-op53 | 69.3 | 71.7 | 73.8 | 60.5 | 58.6 |
| chopin-scherzo3 | 89.7 | 89.1 | 88.5 | 86.7 | 87.2 |
| debussy-pour-le-piano-1 | 76.7 | 77.2 | 78.1 | 76.8 | 78.0 |
| debussy-reflets | 44.7 | 44.2 | 45.4 | 41.8 | 42.1 |
| haydn-hob16-49-1 | 86.1 | 86.2 | 87.1 | 85.3 | 84.2 |
| liszt-hr-6 | 81.3 | 80.5 | 80.2 | 78.1 | 78.4 |
| liszt-paganini-6 | 61.5 | 59.5 | 60.1 | 64.8 | 62.6 |
| liszt-sonata * | 64.6 | 61.2 | 63.1 | 65.9 | 63.3 |
| liszt-te-10 * | 23.2 | 24.6 | 23.2 | 30.4 | 26.6 |
| liszt-te-5 * | 60.7 | 60.1 | 59.3 | 60.2 | 61.1 |
| mozart-k475 | 64.2 | 66.4 | 68.1 | 65.0 | 64.9 |
| prokofiev-toccata | 81.6 | 77.6 | 80.6 | 75.4 | 76.0 |
| ravel-alborada | 57.5 | 58.2 | 57.8 | 57.1 | 57.6 |
| schubert-impromptu-d899-4 | 98.6 | 98.5 | 98.2 | 97.9 | 97.9 |
| schubert-wanderer-3-4 | 94.4 | 94.1 | 94.6 | 94.3 | 94.4 |
| schumann-kreisleriana-1 | 67.2 | 67.0 | 68.0 | 69.3 | 68.9 |
| schumann-toccata | 81.3 | 79.5 | 80.8 | 78.9 | 79.6 |
| scriabin-sonata-5 | 70.6 | 71.3 | 69.7 | 71.8 | 71.2 |
| stravinsky-petrushka (provisional) | 54.6 | 54.6 | 54.9 | 53.1 | 52.8 |

### 3e. Bars: ours / reference

A pair `x/y/z` means our two hands have x and y bars against z in the reference.

| piece | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|
| bach-fugue-873 | 71/71 | 71/71 | 71/71 | 71/71 | 71/71 |
| bach-italian-concerto-2 | 49/49 | 49/49 | 50/49 | 49/49 | 49/49 |
| bach-prelude-873 | 62/62 | 62/62 | 62/62 | 62/62 | 62/62 |
| beethoven-appassionata-1 | 264/264 | 264/264 | 264/264 | 264/264 | 264/264 |
| beethoven-hammerklavier-4 | 406/406 | 406/406 | 406/406 | 406/406 | 406/406 |
| beethoven-waldstein-1 | 304/304 | 304/304 | 304/304 | 304/304 | 304/304 |
| chopin-etude-op10-4 | 83/83 | 83/83 | 83/83 | 83/83 | 83/83 |
| chopin-etude-op25-10 | 119/119 | 119/119 | 119/119 | 119/119 | 119/119 |
| chopin-etude-op25-11 | 96/96 | 96/96 | 96/96 | 96/96 | 96/96 |
| chopin-polonaise-op53 | 182/181 | 181/181 | 181/181 | 179/181 | 181/181 |
| chopin-scherzo3 | 648/649 | 649/649 | 648/649 | 649/649 | 649/649 |
| debussy-pour-le-piano-1 | 163/162 | 162/162 | 163/162 | 161/162 | 163/162 |
| debussy-reflets | 94/95 | 95/95 | 95/95 | 95/95 | 95/95 |
| haydn-hob16-49-1 | 222/220 | 222/220 | 224/220 | 223/220 | 225/220 |
| liszt-hr-6 | 244/225 | 239/225 | 239/225 | 237/225 | 242/225 |
| liszt-paganini-6 | 220/220 | 220/220 | 219/220 | 219/220 | 221/220 |
| liszt-sonata * | 306/305 | 309/305 | 308/305 | 306/305 | 307/305 |
| liszt-te-10 * | 182/182 | 182/182 | 182/182 | 182/182 | 182/182 |
| liszt-te-5 * | 134/134 | 133/134 | 133/134 | 131/134 | 130/134 |
| mozart-k475 | 179/180 | 180/180 | 179/180 | 179/180 | 179/180 |
| prokofiev-toccata | 227/226 | 224/226 | 227/226 | 222/226 | 222/226 |
| ravel-alborada | 229/229 | 228/229 | 228/229 | 229/229 | 229/229 |
| schubert-impromptu-d899-4 | 277/277 | 277/277 | 277/277 | 277/277 | 277/277 |
| schubert-wanderer-3-4 | 476/475 | 476/475 | 476/475 | 476/475 | 476/475 |
| schumann-kreisleriana-1 | 77/78 | 77/78 | 77/78 | 79/78 | 78/78 |
| schumann-toccata | 275/283 | 272/283 | 276/283 | 271/283 | 268/283 |
| scriabin-sonata-5 | 432/456 | 431/456 | 432/456 | 432/456 | 431/456 |
| stravinsky-petrushka (provisional) | 598/627 | 598/627 | 595/627 | 601/627 | 601/627 |

## 4. Paired differences, B minus A (same seed = same start weights, list, steps and data order; only the input size differs)

* seed 7: A = `res_A_s7_gpu`, B = `res_B_s7_gpu`, 28 of 28 pieces in both
* seed 11: A = `res_A_s11_gpu`, B = `res_B_s11_gpu`, 28 of 28 pieces in both

### pooled pitch F1

| piece | A s7 | A s11 | B s7 | B s11 | d s7 | d s11 | mean d +- sd | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.7 | 99.4 | 99.2 | 99.5 | -0.49 | +0.14 | -0.17 +- 0.44 | B loses |
| bach-italian-concerto-2 | 98.8 | 99.0 | 98.7 | 98.8 | -0.13 | -0.13 | -0.13 +- 0.00 | B loses (both seeds) |
| bach-prelude-873 | 99.4 | 98.9 | 99.6 | 99.6 | +0.20 | +0.65 | +0.43 +- 0.31 | B wins (both seeds) |
| beethoven-appassionata-1 | 99.0 | 99.1 | 99.1 | 99.2 | +0.15 | +0.17 | +0.16 +- 0.01 | B wins (both seeds) |
| beethoven-hammerklavier-4 | 96.9 | 96.4 | 97.1 | 96.7 | +0.21 | +0.25 | +0.23 +- 0.03 | B wins (both seeds) |
| beethoven-waldstein-1 | 99.6 | 99.5 | 99.7 | 99.7 | +0.07 | +0.14 | +0.10 +- 0.05 | B wins |
| chopin-etude-op10-4 | 95.8 | 96.2 | 96.5 | 96.7 | +0.65 | +0.53 | +0.59 +- 0.08 | B wins (both seeds) |
| chopin-etude-op25-10 | 96.3 | 97.2 | 96.8 | 97.2 | +0.46 | -0.07 | +0.19 +- 0.37 | B wins |
| chopin-etude-op25-11 | 88.8 | 89.2 | 91.0 | 90.9 | +2.23 | +1.74 | +1.98 +- 0.34 | B wins (both seeds) |
| chopin-polonaise-op53 | 91.8 | 92.3 | 90.5 | 90.8 | -1.34 | -1.49 | -1.41 +- 0.11 | B loses (both seeds) |
| chopin-scherzo3 | 92.4 | 91.6 | 90.3 | 90.3 | -2.06 | -1.34 | -1.70 +- 0.51 | B loses (both seeds) |
| debussy-pour-le-piano-1 | 90.6 | 91.1 | 92.4 | 93.9 | +1.82 | +2.84 | +2.33 +- 0.72 | B wins (both seeds) |
| debussy-reflets | 87.5 | 87.0 | 85.9 | 86.6 | -1.56 | -0.46 | -1.01 +- 0.78 | B loses (both seeds) |
| haydn-hob16-49-1 | 92.9 | 95.5 | 93.5 | 93.1 | +0.55 | -2.42 | -0.94 +- 2.10 | B loses |
| liszt-hr-6 | 91.6 | 92.5 | 92.1 | 92.1 | +0.49 | -0.40 | +0.04 +- 0.63 | tie |
| liszt-paganini-6 | 90.3 | 89.5 | 90.3 | 90.3 | +0.05 | +0.86 | +0.45 +- 0.57 | B wins |
| liszt-sonata | 79.1 | 80.9 | 83.3 | 81.4 | +4.20 | +0.45 | +2.33 +- 2.65 | B wins (both seeds) |
| liszt-te-10 | 79.9 | 77.8 | 82.2 | 80.5 | +2.28 | +2.63 | +2.45 +- 0.25 | B wins (both seeds) |
| liszt-te-5 | 78.7 | 78.3 | 78.2 | 79.4 | -0.50 | +1.09 | +0.30 +- 1.12 | B wins |
| mozart-k475 | 94.4 | 94.5 | 95.0 | 95.4 | +0.57 | +0.87 | +0.72 +- 0.21 | B wins (both seeds) |
| prokofiev-toccata | 92.2 | 93.2 | 90.9 | 90.8 | -1.24 | -2.38 | -1.81 +- 0.81 | B loses (both seeds) |
| ravel-alborada | 82.1 | 81.5 | 81.4 | 82.0 | -0.65 | +0.53 | -0.06 +- 0.83 | tie |
| schubert-impromptu-d899-4 | 99.2 | 99.0 | 98.6 | 98.6 | -0.60 | -0.37 | -0.48 +- 0.17 | B loses (both seeds) |
| schubert-wanderer-3-4 | 96.1 | 96.3 | 96.1 | 96.2 | -0.00 | -0.03 | -0.02 +- 0.02 | tie |
| schumann-kreisleriana-1 | 96.6 | 97.6 | 96.8 | 97.2 | +0.13 | -0.41 | -0.14 +- 0.38 | B loses |
| schumann-toccata | 91.0 | 92.3 | 90.3 | 89.5 | -0.71 | -2.81 | -1.76 +- 1.48 | B loses (both seeds) |
| scriabin-sonata-5 | 90.1 | 89.2 | 90.4 | 90.6 | +0.30 | +1.43 | +0.86 +- 0.80 | B wins (both seeds) |
| stravinsky-petrushka | 79.3 | 78.9 | 78.0 | 77.8 | -1.31 | -1.09 | -1.20 +- 0.16 | B loses (both seeds) |

Mean B - A per seed: s7 +0.13 (28 pieces), s11 +0.03 (28 pieces); mean +0.08 +- 0.07 (range of the two seeds, n = 2, not a confidence interval). B wins 14, loses 11, ties 3 (tie band 0.1); both seeds agree beyond the band on 18; sign test over the 25 decided pieces p = 0.690.

### staff-sensitive pitch F1

| piece | A s7 | A s11 | B s7 | B s11 | d s7 | d s11 | mean d +- sd | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 99.7 | 99.3 | 99.2 | 99.5 | -0.49 | +0.28 | -0.10 +- 0.54 | B loses |
| bach-italian-concerto-2 | 98.8 | 99.0 | 98.7 | 98.8 | -0.13 | -0.13 | -0.13 +- 0.00 | B loses (both seeds) |
| bach-prelude-873 | 99.3 | 98.9 | 99.6 | 99.6 | +0.28 | +0.73 | +0.51 +- 0.31 | B wins (both seeds) |
| beethoven-appassionata-1 | 98.8 | 98.9 | 99.0 | 99.1 | +0.15 | +0.18 | +0.17 +- 0.02 | B wins (both seeds) |
| beethoven-hammerklavier-4 | 89.6 | 89.4 | 89.8 | 89.7 | +0.19 | +0.30 | +0.25 +- 0.08 | B wins (both seeds) |
| beethoven-waldstein-1 | 94.3 | 94.2 | 94.3 | 94.3 | +0.07 | +0.14 | +0.10 +- 0.05 | B wins |
| chopin-etude-op10-4 | 94.8 | 95.2 | 95.4 | 95.8 | +0.65 | +0.58 | +0.61 +- 0.05 | B wins (both seeds) |
| chopin-etude-op25-10 | 96.3 | 97.2 | 96.8 | 97.1 | +0.46 | -0.10 | +0.18 +- 0.40 | B wins |
| chopin-etude-op25-11 | 88.8 | 89.1 | 91.0 | 90.9 | +2.20 | +1.77 | +1.98 +- 0.30 | B wins (both seeds) |
| chopin-polonaise-op53 | 89.5 | 90.0 | 88.0 | 88.3 | -1.43 | -1.69 | -1.56 +- 0.18 | B loses (both seeds) |
| chopin-scherzo3 | 91.1 | 90.2 | 88.6 | 88.7 | -2.45 | -1.51 | -1.98 +- 0.67 | B loses (both seeds) |
| debussy-pour-le-piano-1 | 90.2 | 90.6 | 91.8 | 93.2 | +1.58 | +2.66 | +2.12 +- 0.76 | B wins (both seeds) |
| debussy-reflets | 86.8 | 86.4 | 85.4 | 86.0 | -1.38 | -0.46 | -0.92 +- 0.65 | B loses (both seeds) |
| haydn-hob16-49-1 | 92.7 | 95.3 | 93.3 | 92.8 | +0.55 | -2.53 | -0.99 +- 2.18 | B loses |
| liszt-hr-6 | 91.5 | 92.5 | 92.1 | 92.1 | +0.57 | -0.36 | +0.11 +- 0.66 | B wins |
| liszt-paganini-6 | 90.0 | 89.4 | 90.2 | 90.1 | +0.23 | +0.74 | +0.49 +- 0.36 | B wins (both seeds) |
| liszt-sonata | 78.7 | 80.5 | 83.0 | 81.0 | +4.23 | +0.47 | +2.35 +- 2.66 | B wins (both seeds) |
| liszt-te-10 | 79.3 | 77.5 | 81.9 | 79.9 | +2.57 | +2.36 | +2.46 +- 0.14 | B wins (both seeds) |
| liszt-te-5 | 78.4 | 77.6 | 78.0 | 79.1 | -0.39 | +1.56 | +0.58 +- 1.38 | B wins |
| mozart-k475 | 91.3 | 91.3 | 91.9 | 92.2 | +0.62 | +0.90 | +0.76 +- 0.19 | B wins (both seeds) |
| prokofiev-toccata | 92.1 | 93.2 | 90.9 | 90.8 | -1.24 | -2.40 | -1.82 +- 0.82 | B loses (both seeds) |
| ravel-alborada | 81.6 | 81.1 | 81.0 | 81.6 | -0.61 | +0.53 | -0.04 +- 0.80 | tie |
| schubert-impromptu-d899-4 | 99.2 | 99.0 | 98.6 | 98.6 | -0.62 | -0.39 | -0.50 +- 0.17 | B loses (both seeds) |
| schubert-wanderer-3-4 | 94.7 | 94.9 | 94.7 | 94.9 | +0.02 | -0.03 | -0.00 +- 0.04 | tie |
| schumann-kreisleriana-1 | 95.6 | 96.5 | 95.7 | 96.0 | +0.13 | -0.49 | -0.18 +- 0.44 | B loses |
| schumann-toccata | 90.5 | 91.8 | 89.8 | 89.0 | -0.71 | -2.77 | -1.74 +- 1.46 | B loses (both seeds) |
| scriabin-sonata-5 | 90.0 | 89.1 | 90.3 | 90.6 | +0.28 | +1.44 | +0.86 +- 0.83 | B wins (both seeds) |
| stravinsky-petrushka | 58.4 | 58.3 | 57.9 | 57.6 | -0.51 | -0.73 | -0.62 +- 0.16 | B loses (both seeds) |

Mean B - A per seed: s7 +0.17 (28 pieces), s11 +0.04 (28 pieces); mean +0.11 +- 0.10 (range of the two seeds, n = 2, not a confidence interval). B wins 15, loses 11, ties 2 (tie band 0.1); both seeds agree beyond the band on 19; sign test over the 26 decided pieces p = 0.557.

### pooled pitch+onset F1

| piece | A s7 | A s11 | B s7 | B s11 | d s7 | d s11 | mean d +- sd | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 96.5 | 95.8 | 96.6 | 97.6 | +0.07 | +1.80 | +0.93 +- 1.22 | B wins |
| bach-italian-concerto-2 | 97.0 | 97.8 | 91.7 | 97.5 | -5.31 | -0.38 | -2.85 +- 3.49 | B loses (both seeds) |
| bach-prelude-873 | 97.1 | 96.8 | 99.4 | 99.4 | +2.23 | +2.59 | +2.41 +- 0.26 | B wins (both seeds) |
| beethoven-appassionata-1 | 90.3 | 91.5 | 90.9 | 92.6 | +0.63 | +1.05 | +0.84 +- 0.29 | B wins (both seeds) |
| beethoven-hammerklavier-4 | 90.1 | 88.8 | 90.6 | 90.2 | +0.53 | +1.41 | +0.97 +- 0.62 | B wins (both seeds) |
| beethoven-waldstein-1 | 93.8 | 93.6 | 95.5 | 95.0 | +1.65 | +1.43 | +1.54 +- 0.15 | B wins (both seeds) |
| chopin-etude-op10-4 | 93.8 | 94.5 | 93.8 | 94.4 | -0.02 | -0.05 | -0.03 +- 0.02 | tie |
| chopin-etude-op25-10 | 69.1 | 71.3 | 72.9 | 71.3 | +3.82 | +0.02 | +1.92 +- 2.69 | B wins |
| chopin-etude-op25-11 | 55.6 | 53.2 | 48.8 | 53.5 | -6.81 | +0.36 | -3.22 +- 5.08 | B loses |
| chopin-polonaise-op53 | 75.6 | 77.1 | 65.8 | 64.1 | -9.79 | -13.04 | -11.42 +- 2.30 | B loses (both seeds) |
| chopin-scherzo3 | 90.0 | 89.3 | 87.6 | 88.0 | -2.39 | -1.36 | -1.87 +- 0.73 | B loses (both seeds) |
| debussy-pour-le-piano-1 | 78.0 | 78.8 | 77.8 | 79.1 | -0.24 | +0.31 | +0.03 +- 0.39 | tie |
| debussy-reflets | 47.7 | 48.8 | 45.5 | 45.2 | -2.16 | -3.57 | -2.87 +- 0.99 | B loses (both seeds) |
| haydn-hob16-49-1 | 87.0 | 87.8 | 85.9 | 84.8 | -1.13 | -3.00 | -2.07 +- 1.32 | B loses (both seeds) |
| liszt-hr-6 | 81.3 | 80.9 | 78.8 | 79.1 | -2.55 | -1.78 | -2.16 +- 0.54 | B loses (both seeds) |
| liszt-paganini-6 | 62.6 | 62.6 | 67.1 | 64.9 | +4.50 | +2.32 | +3.41 +- 1.54 | B wins (both seeds) |
| liszt-sonata | 63.6 | 65.4 | 68.7 | 65.7 | +5.14 | +0.34 | +2.74 +- 3.39 | B wins (both seeds) |
| liszt-te-10 | 33.1 | 31.9 | 38.4 | 35.1 | +5.29 | +3.26 | +4.28 +- 1.43 | B wins (both seeds) |
| liszt-te-5 | 62.3 | 61.8 | 62.3 | 63.2 | +0.07 | +1.35 | +0.71 +- 0.91 | B wins |
| mozart-k475 | 69.6 | 71.5 | 68.0 | 68.2 | -1.65 | -3.31 | -2.48 +- 1.18 | B loses (both seeds) |
| prokofiev-toccata | 78.9 | 82.0 | 77.1 | 77.6 | -1.76 | -4.44 | -3.10 +- 1.90 | B loses (both seeds) |
| ravel-alborada | 60.8 | 60.4 | 59.6 | 59.9 | -1.22 | -0.50 | -0.86 +- 0.51 | B loses (both seeds) |
| schubert-impromptu-d899-4 | 98.5 | 98.2 | 97.9 | 97.9 | -0.62 | -0.34 | -0.48 +- 0.20 | B loses (both seeds) |
| schubert-wanderer-3-4 | 94.6 | 95.1 | 94.7 | 94.9 | +0.15 | -0.25 | -0.05 +- 0.28 | tie |
| schumann-kreisleriana-1 | 71.1 | 72.4 | 73.6 | 73.1 | +2.53 | +0.79 | +1.66 +- 1.23 | B wins (both seeds) |
| schumann-toccata | 81.0 | 82.6 | 80.3 | 80.9 | -0.73 | -1.66 | -1.20 +- 0.66 | B loses (both seeds) |
| scriabin-sonata-5 | 74.0 | 72.6 | 74.4 | 73.8 | +0.35 | +1.20 | +0.77 +- 0.60 | B wins (both seeds) |
| stravinsky-petrushka | 59.7 | 59.8 | 58.0 | 57.6 | -1.66 | -2.21 | -1.93 +- 0.39 | B loses (both seeds) |

Mean B - A per seed: s7 -0.40 (28 pieces), s11 -0.63 (28 pieces); mean -0.51 +- 0.17 (range of the two seeds, n = 2, not a confidence interval). B wins 12, loses 13, ties 3 (tie band 0.1); both seeds agree beyond the band on 21; sign test over the 25 decided pieces p = 1.000.

### pooled full F1

| piece | A s7 | A s11 | B s7 | B s11 | d s7 | d s11 | mean d +- sd | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 96.0 | 95.3 | 96.2 | 97.3 | +0.20 | +2.01 | +1.11 +- 1.27 | B wins (both seeds) |
| bach-italian-concerto-2 | 97.0 | 97.5 | 90.9 | 97.1 | -6.09 | -0.38 | -3.24 +- 4.04 | B loses (both seeds) |
| bach-prelude-873 | 96.8 | 96.5 | 99.2 | 99.2 | +2.39 | +2.67 | +2.53 +- 0.20 | B wins (both seeds) |
| beethoven-appassionata-1 | 89.4 | 90.5 | 90.2 | 91.7 | +0.85 | +1.26 | +1.06 +- 0.29 | B wins (both seeds) |
| beethoven-hammerklavier-4 | 89.5 | 88.0 | 89.8 | 89.5 | +0.36 | +1.54 | +0.95 +- 0.83 | B wins (both seeds) |
| beethoven-waldstein-1 | 93.1 | 92.9 | 94.9 | 94.5 | +1.79 | +1.61 | +1.70 +- 0.13 | B wins (both seeds) |
| chopin-etude-op10-4 | 93.6 | 94.3 | 93.5 | 94.0 | -0.11 | -0.27 | -0.19 +- 0.11 | B loses (both seeds) |
| chopin-etude-op25-10 | 64.7 | 67.4 | 68.7 | 66.5 | +3.94 | -0.89 | +1.52 +- 3.41 | B wins |
| chopin-etude-op25-11 | 52.4 | 50.0 | 45.3 | 50.3 | -7.09 | +0.21 | -3.44 +- 5.17 | B loses |
| chopin-polonaise-op53 | 71.7 | 73.8 | 60.5 | 58.6 | -11.13 | -15.26 | -13.19 +- 2.92 | B loses (both seeds) |
| chopin-scherzo3 | 89.1 | 88.5 | 86.7 | 87.2 | -2.36 | -1.28 | -1.82 +- 0.76 | B loses (both seeds) |
| debussy-pour-le-piano-1 | 77.2 | 78.1 | 76.8 | 78.0 | -0.45 | -0.04 | -0.24 +- 0.29 | B loses |
| debussy-reflets | 44.2 | 45.4 | 41.8 | 42.1 | -2.40 | -3.30 | -2.85 +- 0.64 | B loses (both seeds) |
| haydn-hob16-49-1 | 86.2 | 87.1 | 85.3 | 84.2 | -0.87 | -2.92 | -1.90 +- 1.45 | B loses (both seeds) |
| liszt-hr-6 | 80.5 | 80.2 | 78.1 | 78.4 | -2.36 | -1.74 | -2.05 +- 0.44 | B loses (both seeds) |
| liszt-paganini-6 | 59.5 | 60.1 | 64.8 | 62.6 | +5.34 | +2.54 | +3.94 +- 1.98 | B wins (both seeds) |
| liszt-sonata | 61.2 | 63.1 | 65.9 | 63.3 | +4.75 | +0.26 | +2.51 +- 3.18 | B wins (both seeds) |
| liszt-te-10 | 24.6 | 23.2 | 30.4 | 26.6 | +5.80 | +3.47 | +4.64 +- 1.65 | B wins (both seeds) |
| liszt-te-5 | 60.1 | 59.3 | 60.2 | 61.1 | +0.12 | +1.74 | +0.93 +- 1.14 | B wins (both seeds) |
| mozart-k475 | 66.4 | 68.1 | 65.0 | 64.9 | -1.38 | -3.13 | -2.26 +- 1.24 | B loses (both seeds) |
| prokofiev-toccata | 77.6 | 80.6 | 75.4 | 76.0 | -2.17 | -4.64 | -3.40 +- 1.74 | B loses (both seeds) |
| ravel-alborada | 58.2 | 57.8 | 57.1 | 57.6 | -1.07 | -0.22 | -0.64 +- 0.60 | B loses (both seeds) |
| schubert-impromptu-d899-4 | 98.5 | 98.2 | 97.9 | 97.9 | -0.60 | -0.32 | -0.46 +- 0.20 | B loses (both seeds) |
| schubert-wanderer-3-4 | 94.1 | 94.6 | 94.3 | 94.4 | +0.17 | -0.23 | -0.03 +- 0.29 | tie |
| schumann-kreisleriana-1 | 67.0 | 68.0 | 69.3 | 68.9 | +2.28 | +0.89 | +1.59 +- 0.99 | B wins (both seeds) |
| schumann-toccata | 79.5 | 80.8 | 78.9 | 79.6 | -0.58 | -1.26 | -0.92 +- 0.48 | B loses (both seeds) |
| scriabin-sonata-5 | 71.3 | 69.7 | 71.8 | 71.2 | +0.41 | +1.55 | +0.98 +- 0.81 | B wins (both seeds) |
| stravinsky-petrushka | 54.6 | 54.9 | 53.1 | 52.8 | -1.51 | -2.13 | -1.82 +- 0.43 | B loses (both seeds) |

Mean B - A per seed: s7 -0.42 (28 pieces), s11 -0.65 (28 pieces); mean -0.54 +- 0.16 (range of the two seeds, n = 2, not a confidence interval). B wins 12, loses 15, ties 1 (tie band 0.1); both seeds agree beyond the band on 24; sign test over the 27 decided pieces p = 0.701.

### dense-bar recall of pitches

| piece | A s7 | A s11 | B s7 | B s11 | d s7 | d s11 | mean d +- sd | verdict |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | 100.0 | 98.8 | 99.7 | 99.7 | -0.31 | +0.93 | +0.31 +- 0.88 | B wins |
| bach-italian-concerto-2 | 99.6 | 99.5 | 99.3 | 99.4 | -0.36 | -0.12 | -0.24 +- 0.17 | B loses (both seeds) |
| bach-prelude-873 | 98.5 | 98.5 | 99.2 | 99.2 | +0.77 | +0.77 | +0.77 +- 0.00 | B wins (both seeds) |
| beethoven-appassionata-1 | 98.8 | 98.8 | 99.0 | 99.1 | +0.24 | +0.24 | +0.24 +- 0.00 | B wins (both seeds) |
| beethoven-hammerklavier-4 | 94.6 | 92.9 | 93.9 | 93.7 | -0.70 | +0.76 | +0.03 +- 1.04 | tie |
| beethoven-waldstein-1 | 99.9 | 99.8 | 99.9 | 99.9 | +0.02 | +0.09 | +0.06 +- 0.05 | tie |
| chopin-etude-op10-4 | 95.8 | 96.1 | 96.3 | 96.2 | +0.50 | +0.15 | +0.33 +- 0.25 | B wins (both seeds) |
| chopin-etude-op25-10 | 96.2 | 97.0 | 96.6 | 97.2 | +0.47 | +0.19 | +0.33 +- 0.20 | B wins (both seeds) |
| chopin-etude-op25-11 | 87.8 | 88.3 | 90.4 | 90.4 | +2.57 | +2.12 | +2.35 +- 0.32 | B wins (both seeds) |
| chopin-polonaise-op53 | 89.9 | 90.5 | 88.1 | 89.0 | -1.78 | -1.46 | -1.62 +- 0.22 | B loses (both seeds) |
| debussy-pour-le-piano-1 | 83.5 | 85.2 | 87.5 | 90.7 | +3.93 | +5.56 | +4.74 +- 1.15 | B wins (both seeds) |
| debussy-reflets | 84.9 | 84.8 | 83.6 | 83.5 | -1.22 | -1.29 | -1.26 +- 0.05 | B loses (both seeds) |
| haydn-hob16-49-1 | 77.2 | 78.5 | 82.3 | 81.0 | +5.06 | +2.53 | +3.80 +- 1.79 | B wins (both seeds) |
| liszt-hr-6 | 89.7 | 90.2 | 89.4 | 90.1 | -0.34 | -0.08 | -0.21 +- 0.19 | B loses |
| liszt-paganini-6 | 84.8 | 84.2 | 80.7 | 84.0 | -4.10 | -0.29 | -2.20 +- 2.69 | B loses (both seeds) |
| liszt-sonata | 77.1 | 79.2 | 82.3 | 79.2 | +5.16 | -0.03 | +2.57 +- 3.66 | B wins |
| liszt-te-10 | 81.9 | 77.9 | 83.4 | 81.7 | +1.53 | +3.89 | +2.71 +- 1.67 | B wins (both seeds) |
| liszt-te-5 | 78.0 | 77.1 | 77.2 | 78.6 | -0.80 | +1.51 | +0.35 +- 1.64 | B wins |
| mozart-k475 | 93.3 | 92.8 | 92.7 | 93.8 | -0.58 | +0.96 | +0.19 +- 1.08 | B wins |
| prokofiev-toccata | 92.4 | 92.6 | 91.8 | 92.0 | -0.54 | -0.54 | -0.54 +- 0.00 | B loses (both seeds) |
| ravel-alborada | 77.9 | 76.9 | 77.4 | 77.7 | -0.59 | +0.78 | +0.10 +- 0.97 | tie |
| schubert-impromptu-d899-4 | 99.3 | 99.3 | 99.7 | 99.7 | +0.38 | +0.38 | +0.38 +- 0.00 | B wins (both seeds) |
| schubert-wanderer-3-4 | 95.8 | 96.0 | 95.8 | 95.8 | -0.08 | -0.12 | -0.10 +- 0.03 | tie |
| schumann-kreisleriana-1 | 95.8 | 95.8 | 95.8 | 95.8 | +0.00 | +0.00 | +0.00 +- 0.00 | tie |
| schumann-toccata | 89.7 | 90.3 | 88.6 | 88.1 | -1.07 | -2.20 | -1.64 +- 0.79 | B loses (both seeds) |
| scriabin-sonata-5 | 82.3 | 81.2 | 82.1 | 82.4 | -0.19 | +1.18 | +0.49 +- 0.97 | B wins |
| stravinsky-petrushka | 75.3 | 74.8 | 74.3 | 74.2 | -0.99 | -0.58 | -0.79 +- 0.29 | B loses (both seeds) |

Mean B - A per seed: s7 +0.26 (27 pieces), s11 +0.57 (27 pieces); mean +0.41 +- 0.22 (range of the two seeds, n = 2, not a confidence interval). B wins 14, loses 8, ties 5 (tie band 0.1); both seeds agree beyond the band on 16; sign test over the 22 decided pieces p = 0.286.

Seed noise, arm A: s11 - s7 pooled pitch over 28 pieces: mean +0.13, mean absolute difference 0.70, largest +2.62, pieces with |diff| >= 1 point: 5.
Seed noise, arm B: s11 - s7 pooled pitch over 28 pieces: mean +0.03, mean absolute difference 0.44, largest -1.96, pieces with |diff| >= 1 point: 4.

## 5. Missed notes in dense passages

Dense = reference bars (all staves together, visible notes) with at least 24 notes. Recall = share of the reference pitches found in the aligned bar (pooled alignment; Petrushka is per staff). Missed = number of reference notes not found.

| run | pieces | dense bars | dense reference notes | dense pitches missed | dense recall % |
|---|---|---|---|---|---|
| released | 28 | 2110 | 69957 | 8834 | 87.37 |
| A s7 | 28 | 2110 | 69957 | 8828 | 87.38 |
| A s11 | 28 | 2110 | 69957 | 8898 | 87.28 |
| B s7 | 28 | 2110 | 69957 | 8858 | 87.34 |
| B s11 | 28 | 2110 | 69957 | 8755 | 87.49 |

Per piece dense-bar recall % (pitches missed in brackets):

| piece | dense bars / notes | released | A s7 | A s11 | B s7 | B s11 |
|---|---|---|---|---|---|---|
| bach-fugue-873 | 13 / 323 | 100.0 (0) | 100.0 (0) | 98.8 (4) | 99.7 (1) | 99.7 (1) |
| bach-italian-concerto-2 | 30 / 829 | 99.5 (4) | 99.6 (3) | 99.5 (4) | 99.3 (6) | 99.4 (5) |
| bach-prelude-873 | 10 / 261 | 98.5 (4) | 98.5 (4) | 98.5 (4) | 99.2 (2) | 99.2 (2) |
| beethoven-appassionata-1 | 137 / 4587 | 98.7 (61) | 98.8 (57) | 98.8 (53) | 99.0 (46) | 99.1 (42) |
| beethoven-hammerklavier-4 | 50 / 1569 | 94.1 (92) | 94.6 (85) | 92.9 (111) | 93.9 (96) | 93.7 (99) |
| beethoven-waldstein-1 | 146 / 4295 | 99.8 (10) | 99.9 (5) | 99.8 (10) | 99.9 (4) | 99.9 (6) |
| chopin-etude-op10-4 | 69 / 1999 | 96.1 (77) | 95.8 (83) | 96.1 (78) | 96.3 (73) | 96.2 (75) |
| chopin-etude-op25-10 | 43 / 2134 | 95.7 (91) | 96.2 (82) | 97.0 (64) | 96.6 (72) | 97.2 (60) |
| chopin-etude-op25-11 | 89 / 3111 | 87.7 (383) | 87.8 (378) | 88.3 (364) | 90.4 (298) | 90.4 (298) |
| chopin-polonaise-op53 | 156 / 5666 | 89.4 (603) | 89.9 (574) | 90.5 (540) | 88.1 (675) | 89.0 (623) |
| chopin-scherzo3 | 0 / 0 | n/a | n/a | n/a | n/a | n/a |
| debussy-pour-le-piano-1 | 44 / 1476 | 87.2 (189) | 83.5 (243) | 85.2 (219) | 87.5 (185) | 90.7 (137) |
| debussy-reflets | 45 / 1393 | 82.0 (251) | 84.9 (211) | 84.8 (212) | 83.6 (228) | 83.5 (230) |
| haydn-hob16-49-1 | 2 / 79 | 86.1 (11) | 77.2 (18) | 78.5 (17) | 82.3 (14) | 81.0 (15) |
| liszt-hr-6 | 85 / 2618 | 89.1 (285) | 89.7 (269) | 90.2 (257) | 89.4 (278) | 90.1 (259) |
| liszt-paganini-6 | 58 / 2050 | 86.6 (275) | 84.8 (311) | 84.2 (323) | 80.7 (395) | 84.0 (329) |
| liszt-sonata | 123 / 3898 | 79.5 (800) | 77.1 (892) | 79.2 (811) | 82.3 (691) | 79.2 (812) |
| liszt-te-10 | 83 / 2290 | 82.2 (408) | 81.9 (414) | 77.9 (507) | 83.4 (379) | 81.7 (418) |
| liszt-te-5 | 115 / 4231 | 76.7 (984) | 78.0 (931) | 77.1 (969) | 77.2 (965) | 78.6 (905) |
| mozart-k475 | 61 / 2086 | 94.1 (123) | 93.3 (140) | 92.8 (150) | 92.7 (152) | 93.8 (130) |
| prokofiev-toccata | 71 / 2205 | 92.1 (175) | 92.4 (168) | 92.6 (164) | 91.8 (180) | 92.0 (176) |
| ravel-alborada | 63 / 2045 | 78.0 (449) | 77.9 (451) | 76.9 (472) | 77.4 (463) | 77.7 (456) |
| schubert-impromptu-d899-4 | 38 / 1064 | 99.5 (5) | 99.3 (7) | 99.3 (7) | 99.7 (3) | 99.7 (3) |
| schubert-wanderer-3-4 | 75 / 2599 | 96.0 (105) | 95.8 (108) | 96.0 (105) | 95.8 (110) | 95.8 (108) |
| schumann-kreisleriana-1 | 2 / 48 | 95.8 (2) | 95.8 (2) | 95.8 (2) | 95.8 (2) | 95.8 (2) |
| schumann-toccata | 151 / 4280 | 90.3 (416) | 89.7 (442) | 90.3 (417) | 88.6 (488) | 88.1 (511) |
| scriabin-sonata-5 | 99 / 3147 | 80.6 (612) | 82.3 (557) | 81.2 (592) | 82.1 (563) | 82.4 (555) |
| stravinsky-petrushka | 252 / 9674 | 75.0 (2419) | 75.3 (2393) | 74.8 (2442) | 74.3 (2489) | 74.2 (2498) |

## 6. What moved

Rule: pieces where the pooled pitch F1 changes by at least 1 point in the same direction in both seeds.

| piece | direction | d s7 | d s11 | A pooled (mean) | B pooled (mean) |
|---|---|---|---|---|---|
| liszt-te-10 | B better | +2.28 | +2.63 | 78.9 | 81.3 |
| debussy-pour-le-piano-1 | B better | +1.82 | +2.84 | 90.8 | 93.1 |
| chopin-etude-op25-11 | B better | +2.23 | +1.74 | 89.0 | 91.0 |
| prokofiev-toccata | B worse | -1.24 | -2.38 | 92.7 | 90.9 |
| chopin-scherzo3 | B worse | -2.06 | -1.34 | 92.0 | 90.3 |
| chopin-polonaise-op53 | B worse | -1.34 | -1.49 | 92.0 | 90.6 |
| stravinsky-petrushka | B worse | -1.31 | -1.09 | 79.1 | 77.9 |

## 7. Inference cost on the box (wall time per page from the saved per-piece times)

From `eval_run1/testset/<tag>/<piece>/wall_seconds.txt` (the `run_homr.py` call of the piece: segmentation, staff detection, transformer; merge and scoring not included) divided by the page count. Pieces are run one after the other by `res_eval.py`, but **the box is shared** with other agents' jobs, so these times are only indicative; a clean comparison needs a quiet box (`res_timing.py` on 5 pages, see `RESOLUTION_EVAL.md`, 'Final comparison').

| run | pieces with a time | pages | wall s per page (total / pages) | median of per-piece s/page |
|---|---|---|---|---|
| A s7 | 28 | 302 | 5.10 | 4.61 |
| A s11 | 28 | 302 | 6.17 | 5.38 |
| B s7 | 28 | 302 | 5.81 | 5.83 |
| B s11 | 28 | 302 | 4.61 | 4.70 |

Seed 7, 28 common pieces: B/A wall ratio 1.14 (summed), per-piece median 1.15, range 0.44-1.60. Spread of the same measure between A s7 and A s11 (same model size, different run) gives the noise of this timing.

Seed 11, 28 common pieces: B/A wall ratio 0.75 (summed), per-piece median 0.82, range 0.37-1.21. Spread of the same measure between A s7 and A s11 (same model size, different run) gives the noise of this timing.
Noise yardstick: A s11 / A s7 wall ratio per piece, median 1.27, range 0.39-2.76 over 28 pieces (the same architecture, so the ratio would be 1.0 on a quiet box).

