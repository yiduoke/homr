# Same-edition training of the staff-pairing CNN on real thin-brace pages (D30)

Written 2026-11-17, 8:20 pm Pacific (work 7:27-8:20 pm). Everything is in `run/staff_rel_realbrace/` (`d30/`, `models2/`, `scripts/`). Nothing pushed.
Models: `realbrace2-<arm>-s<seed>.onnx` (A, B, C; seeds 0, 1; also in `models2/`); the shipped model and `staff_relations_realbrace-{1,2,3}.onnx` are untouched.

## Read this first

**The three Schott test scans (Liszt TE 5, TE 10, Sonata) come from the same engraving and the same scanning series as the training pages (B. Schott's Soehne 1917-18, Schmid-Lindner, Sibley scans).
Results on them show same-edition learning, not transfer.** The held-out evidence is: the reserved Mazeppa pages and the held-out pieces of the same volume (same edition, other music: it shows the model reads the brace
on unseen compositions, still not on another edition), the held-out curved-brace editions (the shipped model already reads them at 99.6 %, so this is a no-regression check, not evidence of improvement) and the three
transfer scans (Cappi 1802, Eder 1800, Reichardt 1819), where the effect is **weak and comes with more false joins**. There is still no second public thin-brace edition with this brace (D26).

## Result in one table

Pairing decisions (argmax; missed grand / false grand / separate pair joined). Shipped model and arms; seeds 0 | 1.

| set (grand pairs / pairs) | status | shipped | A (control, no Schott pages) | B (+ real Schott pages) | C (B + Schott-guided variations) |
|---|---|---|---|---|---|
| Mazeppa pages (43 / 78) | reserved, same edition | 43 / 0 / 0 | 32/0/0 \| 27/0/0 | **0/0/0 \| 0/0/0** | 0/0/0 \| 0/0/0 |
| held-out Schott pieces XI, XII, Waldesrauschen, Gnomenreigen + Concert-Etudes S.144 (189 / 341) | validation, same edition | 187 / 0 / 0 | 102/0/0 \| 76/0/0 | **0/0/0 \| 0/0/0** | 0/0/0 \| 0/0/0 |
| 3 Schott test scans, grand calls among 169 within-system pairs (separate pairs kept separate 136 / 136 for all models) | TEST, same edition, not transfer | 1 | 71 \| 98 | **169 \| 169** | 169 \| 169 |
| opening pages of the 3 scans (13 systems) | same | 0 | 4 \| 7 | 13 \| 13 | 13 \| 13 |
| 22 held-out curved editions (720 / 1,317) | negative controls, never trained | 3 / 0 / 2 | 1/1/1 \| 1/1/1 | 2/0/0 \| 1/1/1 | 1/0/0 \| 1/0/1 |
| Cappi 1802 Op. 27/2 (46 / 82) | transfer, weak scan | 40 / 0 / 10 | 12/0/12 \| 11/1/12 | 15/0/15 \| 9/0/16 | 12/1/13 \| 13/0/15 |
| Eder 1800 Op. 13, 2 pages (9 / 16) | transfer, tiny | 7 / 0 / 3 | 3/0/3 \| 1/0/2 | 1/0/2 \| 1/0/2 | 1/0/2 \| 1/0/4 |
| Reichardt 1819 songs (56 / 153) | transfer | 53 / 0 / 6 | 53/0/9 \| 52/0/9 | 35/0/11 \| 35/1/13 | 34/0/13 \| 43/0/16 |

Full pipeline (box GPU, merger by staff role, saved page XML re-merged on the laptop; staff-sensitive / pooled pitch F1; bars out / reference; hands in the same reference bar). Control = shipped model on the same GPU pipeline and the same merger (its output is the same as with the old merger).

| piece | control (shipped) | A s0 \| s1 | B s0 = s1 = C s0 = C s1 |
|---|---|---|---|
| Sonata | 80.0 / 80.5; 307 / 305; 79 % | 87.0 / 87.4; 93 % \| 87.9 / 88.3; 93 % | **88.9 / 89.3**; 304 / 305; 98 % |
| Etude 5 | 77.2 / 78.0; 134 / 134; 71 % | 81.1 / 81.2; 90 % \| 79.4 / 79.5; 88 % | **81.6 / 81.6**; 132 / 134; 95 % |
| Etude 10 | 77.3 / 77.9; 181 / 182; 67 % | 89.4 / 89.5; 92 % \| 91.1 / 91.2; 95 % | **93.8 / 93.9**; 182 / 182; 100 % |
| mean of the three | 78.1 / 78.8 | 85.8 / 86.1 \| 86.1 / 86.3 | **88.1 / 88.3** |
| Mazeppa (reserved; provisional reference, see below) | 73.0 / 77.0; 212 / 202; 76 % | 76.4 / n.a.; parts 224 and 209 bars; 4 % \| 76.3 / n.a.; same | **82.2 / 82.6**; 190 / 202; 99 % |

* **Which arm helps.** B (real thin-brace pages) helps: it moves every same-edition pair from "missed" to right on pieces it never saw (Mazeppa 43 of 43, held-out pieces 189 of 189, test scans 169 of 169), and the pipeline gains
  +10.0 pitch points over the shipped control on the three test scans (+2.3 / +2.0 over A, seed 0 / 1), +9.2 on Mazeppa (+5.8 over A), the hands stay in the same bar 95-100 % (control 67-79 %). Arm A, the first-round recipe
  (variations only) with the merger fix, is already +7.7 / +8.0 (seed 0 / 1) over the control on the three scans, because the merger fix makes partial recognition harmless (D24); on Mazeppa its two parts differ in length (224 and 209 bars,
  4 % hands in the same bar) and the score is not comparable. **C (Schott-guided variations on top of B) adds nothing**: pairing, pipeline output and scores are the same as B for both seeds, the pairing sets are saturated for B and C alike,
  and on the transfer sets B and C do not differ beyond seed noise (Cappi missed 15 / 9 vs 12 / 13, false joins 15 / 16 vs 13 / 15; Reichardt missed 35 / 35 vs 34 / 43). The seed spread of A is 1-2 pitch points per piece, B and C do not vary between seeds on these pages.
* **No regression on other editions.** Held-out curved editions (22, 1,317 pairs; missed grand / false grand / joins): shipped 3 / 0 / 2, B 2 / 0 / 0 and 1 / 1 / 1, C 1 / 0 / 0 and 1 / 0 / 1: unchanged within one or two pairs.
  Relation model only on the saved crops of the 26 other scan sets (2,905 pairs, `d30/pairing_changes.md`): for B (seed 0 / 1) and C, 8-10 pairs on 6-7 pages change, **all on Stravinsky Petrushka** (3-4 staves under one brace; p. 2, 8 (A/C), 12, 32, 33, 34, 35: same
  pages as realbrace-1, -2, -3 in D14); no pair of the 25 other scan sets changes. The Petrushka pipeline score is the open point (the 25-scan pipeline run by another agent, `eval_run1/brace_models_25scans.md`, did not exist yet).
* **Transfer is weak and unsafe.** On Cappi 1802 and Reichardt the new models call more grand staffs (Cappi missed 40 -> 9-15, Reichardt 53 -> 34-43) but also join more separate pairs (Cappi 10 -> 12-16 of 36, Reichardt 6 -> 9-16 of 41). A (no Schott pages) already
  gives Cappi 11-12 missed, so that gain comes from the variations of the first round; only Reichardt separates A (52-53 missed) from B and C (34-43), i.e. on a different thin brace the real Schott pages help a little and the false joins rise. Cappi 1802 is a straight bracket with hooks on a grey scan (different shape), Eder has 2 labelled pages.

## Data and split (nothing of the test or reserved material is in any training set)

Mixture of the first round (`mixture_B.npz`: real piano 2,418 pairs, real songs 1,450, rendered Lieder/SATB/duos 9,419, brace variations 2,978) with the **Reichardt pairs removed** (transfer test now), plus:

| source | train | validation / held out | note |
|---|---|---|---|
| real thin brace (Schott), arms B, C | volume pieces I, II, III, VI, VII, VIII, IX (220 grand pairs of the volume) + Piano Concertos 1 and 2 (496 grand, 248 same system, 165 separate): 127 pages, 1,305 pairs (341 separate / 248 same / 716 grand) | pieces XI, XII, Waldesrauschen, Gnomenreigen of the volume and the Concert-Etudes S.144 file: 37 pages, 341 pairs | split by piece / work, never pages of one piece on both sides |
| curved-brace editions, all arms | 17 editions of 13 works: Brahms Op. 1, Rhapsodies Op. 79 (2), Chopin Nocturnes Op. 9, Sonata 2 (2), Liszt Consolations, HR 2 (2), HR 12, Mephisto (2), Kinderszenen, Scriabin Sonata 3, Berg, Lyapunov (2): 1,115 pairs | 22 editions of the other works (Op. 110, Op. 27/1 Cappi 1801, Op. 27/2 Cranz, Op. 31 x2, Ballades, Mendelssohn, Op. 12 x3 incl. Henle, Papillons x3, Schubert x3, Liszt Sonata x4 incl. Salabert, Islamey, Paganini 2): 1,317 pairs | split by work; editions of test compositions (Sonata, Islamey), Henle 1987 and Salabert 1949 are never trained on (the two non-public-domain files stay on the owner's machines) |
| Schott-guided variations, arm C | 2,978 pairs on the 291 training pages of the first round | - | `scripts/vary_braces_schott.py` |
| never used | Mazeppa pages, TE 5, TE 10, Sonata, Cappi 1802, Eder 1800, Reichardt | | tests only |

**Does the old variation generator cover the real shape?** Measured on the labelled Schott pool (ink at 35 / 50 / 65 % of the gap): stroke about 0.2-0.5 unit wide (median extent 0.47 unit), leftmost ink 0.2-0.45 unit left of the staff start (point depth up to about 1 unit), a nearly
straight spine with a short point at the centre and hooks toward the staff at both ends, no connecting line across the gap in most systems (figures: `brace_collection/figures/labelcheck_schott_pool.png`, D25). The generator of the first round draws a spine that bulges over the whole
middle (a bow, not a point), thickness 0.25-1.1 unit, depth 0.5-2.2 units, distance 0.25-1.6 units: the Schott brace is in its corner and a point shape did not exist (only a few percent of the draws came near the Schott corner). Widened in `vary_braces_schott.py`: 70 % of the braces are point shaped
(spine = base + a sharp peak, thickness 0.14-0.4, depth 0.7-1.4, hooks), 30 % are the old bowed shape with curvature 0-0.45, depth 0.35-1.1, thickness 0.14-0.45; distance from the staff 0.1-0.6 unit; the connecting line is removed in 60 % of the systems (kept 25 %, added 15 %); brackets for
systems of separate parts as before. Variations are drawn on the page image before the segmentation net runs, as in D14, on the training editions only.

## Arms, training

Same network and input as the shipped model (not changed), fine-tuned from the shipped weights (batch norms folded, `finetune2.py`), 12 epochs x 150 steps x batch 64, AdamW lr 1e-4 one-cycle, the first-round augmentations, seeds 0 and 1, identical in all arms; sampling
weight per source (split over the three classes): real piano 3, songs 2, rendered 2, varied 3, curved 2, Schott 3, Schott-guided 3. **A** = first-round recipe (realbrace-2: variations, no Reichardt) + curved training editions; **B** = A + real Schott pages; **C** = B + Schott-guided variations.
The curved training editions are in every arm so that the arms differ only in the thin-brace data. Trained on the laptop (MPS, about 3 minutes per run), validated on the held-out sets above each epoch; no model selection, no tuning on any evaluation set; the recipes were fixed before the first run. Validation at epoch 12 (all arms):
real piano 0.998-1.0, songs 1.0, rendered 0.993-0.995 (grand recall 0.984-0.987), curved 0.9985-0.9992, Schott pieces held out 1.0 (B, C).

## Why the 3 test scans are not evidence of generalisation, and what is

* Same publisher series, same scanner, same page geometry and the same brace as the 127 training pages: 169 of 169 is what learning that engraving looks like; the earlier models (D14) reached 56-98 of 169 only because the variations came near it.
* Mazeppa and the held-out pieces are other music of the same edition: they show that B reads the brace on notes it never saw, nothing about other editions.
* The independent evidence is the curved editions (all fine before, still fine) and the transfer sets (weak: some real gain on missed grand, more false joins). There is no second thin-brace edition to test generalisation; a library scan of another Schott or Peters volume would be the first honest test.
* Selection note: the three scans were looked at in D14 and D24 when the recipes A and the merger fix were made; B and C were fixed before the first run and are not tuned on them.

## Caveats

* **Mazeppa pipeline numbers are provisional.** The only Mazeppa reference (`out/testset/liszt-te-4-schott/liszt-te-4-schott-reference.musicxml` = `out/compare/mazeppa/mazeppa-reference.musicxml`) is a hand transcription of another scan (Musicaneo, 202 bars); it is not checked against
  the Schott print (three-staff systems, other editorial marks), so bars out (190, control 212) and scores can include edition differences. The comparison between models on the same reference holds, the absolute value does not.
* Only 4 of the 13 Mazeppa pages were labelled (k = 2 systems); the pipeline run uses all 13, including three-staff systems that the pairing sets do not test.
* Arm A's Mazeppa result (parts of 224 and 209 bars) is a merger output with unequal parts, not a pitch result.
* One seed pair; B and C are identical on these pages, so the seed spread is not estimable for them; A varies by 1-2 points.
* The pipeline runs used the GPU path (fp16 transformer) with the shipped transformer weights; the earlier CPU numbers differ by up to 2 points (D14 note).
* The curved held-out set contains 4 editions of the Liszt Sonata (a test composition) and Henle / Salabert: they are tested, never trained on.

## Reproduce (all paths absolute on the laptop; box = vast-homr5)

`scripts/vary_braces_schott.py` (like `vary_braces.py`; 5 processes, 10 minutes) -> `scripts/build_mixture2.py d30` (`d30/mixture2_{A,B,C}.npz`) -> `scripts/train_arms2.sh` (`scripts/finetune2.py`) -> `scripts/eval2.py d30/eval_X.json LABEL=MODEL ...` (held-out sets, transfer, test scans)
-> `scripts/pipeline_arm2.sh TAG MODEL` on the box (tags `relbrace2_<arm>_s<seed>_gpu`, control `relbrace2_ctl_gpu`; `chain_d30.sh`) -> `scripts/pull_d30.sh`, `scripts/merge_score_d30.py TAG` (merger `run/merge_wt/merge_pages.py`, scores in `eval_run1/merge_by_role/d30/`)
-> `scripts/table_d30.py > d30/tables.md` (all tables, per-edition and per-piece detail) -> `scripts/pairing_changes.py NAME=MODEL ... > d30/pairing_changes.md` (task e). Logs: `d30/train_*.log`, `d30/collect.log`.
