# Candidate brace (staff-pairing) models on the 28 real scans, full page pipeline, common merger (D28)

Run 2026-11-17, 7:23-9:00 pm Pacific, vast-homr5 (Titan RTX, GPU, nothing set), one evaluation at a time. Plan item: `PLAN.md`, "In parallel", item 1.
Nothing was adopted, trained or tuned; the three Schott scans and all other test scans were only scored. The candidate models were chosen after seeing the Schott scans (D14, D24), so none of the Schott gains below is an unbiased estimate.

## Setup (identical for the three arms)

* Code `run/rel_wt` (branch `staff-relations-real`, integration + `HOMR_STAFF_RELATION_MODEL`), released transcription weights `pytorch_model_meteracc-r2s7-afae0e3` (as tag `layout1`), `HOMR_LOOP_GUARD=1`, `HOMR_FIXED_MARGIN=1`, GPU (fp16), 4 page workers.
* Merger `run/merge_wt/merge_pages.py` (branch `merge-by-staff-role`, sha256 16 `3581cc08549f06d1`), `HOMR_TRUST_PAGE_TIME=1`, `drop_minor_parts.py`.
* Scorer `validation/score_notes.py` of `rel_wt` (visible notes only), `--ignore-staff` (staff-sensitive and pooled in one JSON); edition-corrected references (Schubert D. 899/4 against `-reference-edition.musicxml`, Scriabin's reference without the stray part); `hand_sync.py` for the hands.
* Tags and relation models: `shipped_merge_role_gpu` (shipped pdmx2 pairing = the control), `relbrace2_gpu` (`staff_relations_realbrace-2.onnx`, sha 282194a93bc486b9), `relbrace3_gpu` (`-3`, sha 10317017d3407b3d). 28 pieces each, 330 pages, 20-26 min each. Settings per tag: `out/testset/BRACE-<tag>-settings.json`.
* Driver `eval_run1/brace_eval.py` (like `res_eval.py`), pulling `brace_pull.sh`, tables `brace_table.py` -> `brace_models/table.md` (all per-piece numbers), pair decisions `pair_replay.py` / `pair_diff.py` -> `brace_models/pair_diff.md` (one segmentation per page, the three models side by side, 302 pages), eye review `pair_view.py`, `pair_montage.py` (`brace_models/eye/`), note-error audit `pitch_audit_brace.py`, `brace_audit_summary.py` (`brace_models/audit_<tag>.md`).
* Check of the replay: its pair-call counts equal the `Staffs i and j` lines of the real runs for 81 of 84 piece/model pairs (three differ by one pair: GPU segmentation noise).

## 1. Result in short

* **On the 24 non-Schott, non-Petrushka scans nothing changes.** Both new models make exactly the shipped model's pair decisions on all 232 pages (0 of 2,360 pairs differ); the final MusicXML is identical to the control on 23 of 24 pieces for realbrace-3 and 24 of 24 for realbrace-2 (Hammerklavier p. 35 and p. 45 differ by one note: GPU run-to-run noise, scores unchanged). So there is no regression there, by construction.
* **Schott (test, chosen after seeing it):** pooled pitch 80.5 / 78.0 / 77.9 (Sonata / Etude 5 / Etude 10, control) -> realbrace-2 86.9 / 79.5 / 91.2, realbrace-3 88.3 / 79.5 / 88.7. Hands in the same reference bar 79 / 71 / 67 % -> 93 / 88 / 95 % (rb2), 96 / 92 / 91 % (rb3). Bars (reference 305 / 134 / 182): control 307 / 134 / 181, rb2 306 / 134 / 182, rb3 304 / 133 / 182.
* **Petrushka regresses badly with both**, through the merger: control 79.2 pooled, rb2 44.8, rb3 58.8 (per-staff, no pooled score defined); bars 598 -> 475/390/390/286/286 (rb2, five parts) and 516/499/499 (rb3, three parts) against 627. Cause in section 4.
* Means (pooled pitch): 28 pieces control 91.94, rb2 91.46, rb3 91.92; without Petrushka (27) 92.41, 93.19, 93.15. Pooled +onset (28) 76.77 / 76.95 / 77.32, full 74.72 / 75.08 / 75.43. Pieces at 97 or more pooled: 7 of 28 for all three (staff-sensitive 5); no piece crosses 97 with either model.
* Verdict: neither model may be adopted as the default (section 6).

## 2. Per piece, the pieces that change (pooled pitch / staff-sensitive / pooled +onset / pooled full; bars per part; hands in the same bar)

| piece | model | pooled | staff-sens. | +onset | full | bars (ref) | hands % |
|---|---|---|---|---|---|---|---|
| Sonata | control | 80.48 | 79.96 | 64.6 | 62.4 | 307x2 (305) | 79 |
| | rb2 | 86.86 | 86.46 | 74.5 | 72.6 | 306x2 | 93 |
| | rb3 | 88.25 | 87.85 | 76.5 | 74.6 | 304x2 | 96 |
| Etude 5 | control | 77.98 | 77.16 | 61.6 | 59.7 | 134x2 (134) | 71 |
| | rb2 | 79.48 | 79.35 | 65.1 | 63.8 | 134x2 | 88 |
| | rb3 | 79.49 | 79.38 | 66.5 | 65.4 | 133x2 | 92 |
| Etude 10 | control | 77.94 | 77.27 | 31.2 | 22.4 | 181x2 (182) | 67 |
| | rb2 | 91.17 | 91.05 | 49.8 | 43.0 | 182x2 | 95 |
| | rb3 | 88.65 | 88.55 | 45.3 | 38.5 | 182x2 | 91 |
| Petrushka | control | 79.21 | 58.56 | 59.1 | 54.2 | 598x2 (627, 1 part of 3 staves) | n/a |
| | rb2 | 44.83* | 44.83 | 32.2 | 29.5 | 475/390/390/286/286 | n/a |
| | rb3 | 58.85* | 58.85 | 43.7 | 40.2 | 516/499/499 | n/a |

`*` per-staff numbers (parts of different lengths, no joint bar list). Hands for Petrushka are not meaningful (three reference staves). The other 24 pieces: every column equal to the control; all 28 rows are in `brace_models/table.md`. The control reproduces the earlier CPU box numbers (Sonata 79.95 / Etude 5 77.04 / Etude 10 76.90 staff-sensitive) to within 0.4. Bar counts equal to the reference: 14 (control), 15 (rb2, gains Etude 10), 14 (rb3, gains Etude 10, loses Etude 5 by one bar) of 28. Hands in the same bar over the 27 two-staff pieces: 95.9 / 98.0 / 98.1 %.

## 3. Where the pair decisions differ from the shipped model (`pair_diff.md`)

Pages with at least one different call (of 302 pages): rb2 39, rb3 39 (Sonata 13 / 14, Etude 5 9 / 8, Etude 10 10 / 9, Petrushka 7 / 8, none elsewhere); pairs changed 98 (rb2) and 108 (rb3) of 3,050. After the layout repair the layout differs on 47 (rb2) and 53 (rb3) pages (Petrushka 27 / 31, where the calls stay `grand staff` for two pairs and the choice of the pair is made by group_staffs from the probabilities).

Schott, all systems are two-staff grand staffs with a brace (checked by eye on six pages), so a within-system pair is right if called grand staff, wrong if `same system`; no between-system pair is ever joined (no false merge, 136 of 136 separate for every model). Within-system pairs called grand staff: Sonata 1 of 76 (control), 39 (rb2), 48 (rb3); Etude 5 0 of 45, 21, 24; Etude 10 0 of 48, 30, 26. Pages with every system right: control 0 of 33, rb2 1, rb3 2.

### Eye review (13 pages, crop and print side by side; `brace_models/eye/m1-m4.png`, `stravinsky-petrushka_page-35.png`; bars at the left of each page: shipped | rb2 | rb3, green grand staff, orange same system)

| page (file name) | printed | control | rb2 | rb3 | verdict |
|---|---|---|---|---|---|
| Sonata page-02 (4 systems) | opening page, "Piano", braces | 0 grand | 0 | 2 (systems 1, 3) | improvement (rb3), unchanged (rb2); the missing systems remain lost grand staffs |
| Sonata page-07 (printed 12, 6 systems) | six braced systems | 0 | 4 | 6 | improvement, rb3 complete |
| Sonata page-09 (printed 14, 6 systems) | six braced systems | 0 | 2 | 5 | improvement |
| Etude 5 page-029 (title page, 5 systems) | braces | 0 | 4 | 4 | improvement |
| Etude 5 page-033 (5 systems) | braces | 0 | 4 | 3 | improvement; rb3 loses systems 2 and 3 |
| Etude 10 page-076 (printed 78, 4 systems) | braces | 0 | 1 | 1 | improvement, 3 of 4 systems still lost |
| Petrushka page-32 | sys. 1 three staves, sys. 2 and 3 four staves (treble, treble, bass, bass), one brace each | sys. 2, 3 `same system` x3 (no pair) | bass pair of sys. 2, 3 joined | same as rb2 | partial improvement (lower hand paired, upper two staves not) |
| Petrushka page-33 | sys. 1 four staves, one brace | G, S, S | G, S, G | G, S, G | improvement: two hands, two staves each |
| Petrushka page-34 | ossia pair, then two three-staff systems | `G+s` in both three-staff systems | s+G in both | s+G in both | layout change only, defensible; the ossia pair stays a separate grand pair in all |
| Petrushka page-35 | sys. 1 three staves; top two treble staves interlock (rests in one where the other plays) = one hand; bass = other | 0-1 grand | 1-2 grand | 1-2 grand | **wrong for the new models on this system**: the top two staves belong together; the other four systems are two-staff grand in all models |
| Petrushka page-07 | four three-staff systems | s+G (1-2) | same | rb3 calls 0-1 `same system` | no change of layout; rb3's call is the more accurate one (top melody staff alone) |
| Petrushka page-11 | four three-staff systems | alternates s+G / G+s (inconsistent within the page) | s+G in all | s+G in all | improvement in consistency |
| Petrushka page-12 | four three-staff systems | G+s in all | s+G in all | s+G in all | layout change; by eye top staff = right-hand melody, so pairing the lower two is the more plausible one, not certain |

Summary of the verdicts: improvement 8 (Schott 6, Petrushka p. 33 and p. 11), partial 1 (p. 32), layout change without clear verdict 3 (p. 7, 12, 34), wrong 1 (p. 35 system 1). No lost grand staff in the sense of a grand pair turned into `same system` on any Schott page (relative to rb2, rb3 calls two systems of Etude 5 page-033 `same system` where rb2 called one; these are missed grand staffs that the control missed too), no false merge on any page.

### Petrushka's three-staff systems

* Printed: a braced system of three staves (treble, treble, bass), on two pages four (treble, treble, bass, bass); the reference (unchecked) writes one three-staff part. There is no single correct pair: the hands go over staves in different ways (page 2 and 12: top staff the right-hand line, the lower two the left hand; page 35 sys. 1: the top two staves one hand). The representation (grand staff = a pair of two staves, anything else a separate part) cannot hold a brace over three staves; a correct pairing keeps all staves of a system in one system and pairs by hand: `s+G` where the top staff is alone, `G+s` where the top two interlock, `G+G` (or the bass pair alone) for four staves.
* Chosen pair in the 81 three-staff systems (`replay_all.json`): shipped 0-1 (`G+s`, treble + treble) 69, 1-2 (`s+G`, treble + bass) 12; rb2 1-2 71, 0-1 10; rb3 1-2 81, 0-1 0. Four-staff systems (3): shipped `s+s+s+s` x2 and `G+s+s`, rb2/rb3 `s+s+G` x2 and `G+G`. So the models move to the pair that is usually the musically better one and never join two systems.
* Does the output keep all hands? On the pages yes: 15,342 notes (control), 15,238 (rb2), 15,158 (rb3) against 15,483 in the reference. After the merge no: the control keeps 12,448 (the single third staff is a sparse minor part, dropped by `drop_minor_parts`), rb3 12,433 (and the seven two-staff pages, 142 bars, are dropped as a minor part), rb2 15,244 but in five parts that do not share bar numbers.

## 4. Why Petrushka regresses (merger, not pairing)

The merger names the parts of a page by staff role only for a page that is one uniform stack (`P1-Staff1..k` or k parts `Voice`). A three-staff page is `[grand part, single]` for the shipped pairing (ids `P1-Staff1/2` + `P2`: the grand part carries the same ids as the two-staff pages, which are `[grand]`) and `[single, grand part]` for the new models (ids `P1`, `P2-Staff1/2`): not a uniform stack, so matched by id, and the new three-staff pages no longer share any part with the two-staff pages. rb2: 5 parts of 475, 390, 390, 286, 286 bars (for example pages 8-9, 18-21 and 32-34 are appended at the same offset); rb3: the seven two-staff pages form a part of 142 bars, below 50 % of 516 and dropped. Page XML is complete in both. A merger that treats a three-staff page and a two-staff page of the same piece consistently would need a rule for which staff of the three is missing on the two-staff pages: not done, no heuristic added.

## 5. Remaining note errors (task 3): audit of the best model, rb3, on the aligned passages

Method: `pitch_audit_28.py` attribution (the categories of `pitch_audit.md`: lost bars, octave, accidental, step, clef, wrong staff, chord member missing, whole event missing, extra, other), tag `relbrace3_gpu`, 27 pieces (Petrushka cannot be audited with rb3: parts of different lengths; the control row is below). Test scans: the categories are described, nothing is tuned on them; the "development scans only" rule for choosing changes stands. F1 points lost, micro over 235,812 reference + output notes (staff-sensitive, so wrong staff counts; 8.53 points in total):

| category | events | F1 points lost | share |
|---|---|---|---|
| octave | 3,557 | 3.02 | 35 % |
| missing bars (lost, unaligned) | 52 bars of 6,031 | 1.14 | 13 % |
| accidental | 1,198 | 1.02 | 12 % |
| extra notes | 1,795 | 0.76 | 9 % |
| wrong staff | 883 | 0.75 | 9 % |
| dropped whole events | 1,270 | 0.54 | 6 % |
| missing chord members | 1,197 | 0.51 | 6 % |
| step 0.38, other 0.38, clef 0.04 | | | 9 % |

* Repeated-note runs (four or more equal events on a staff in one bar): 6,579 reference notes in such runs; 7 % of the missed notes (173 of 2,467 in the two missing categories) fall in them, 0.07 points. Not the main loss on these 27 pieces.
* Octave concentrates on few pieces: Etude 5 12.6, Ravel 11.0, Op. 25/11 7.8, Sonata 6.1, Paganini 5.6, Reflets 5.4, Scherzo 5.1 points. Missing events and chord members together (1.05) are second only to octave and bars, and live in Hungarian Rhapsody 6, Reflets, Debussy, Polonaise, Waldstein.
* Restricted to the nine pieces whose bars equal the reference and whose hands are in the same bar at least 99 % of the time (Bach x3, Appassionata, Waldstein, Op. 10/4, Op. 25/10, Polonaise, Schubert D. 899): loss 4.35 points: accidental 0.86, octave 0.74, chord members 0.70, wrong staff 0.68, unaligned 0.51, step 0.23, extra 0.21, whole events 0.20. In the cleanest pieces accidentals and chord members dominate, octave errors are a property of particular pieces.
* Control, Petrushka (staff-ignored alignment): 79.2 audited, loss mostly chord members missing 6.2 (the dropped third staff, section 3), octave 4.8, lost bars 4.1 (50 of 627 bars).
* Control over all 28 for comparison: 10.65 points, octave 3.41, lost bars 1.67 (113 of 6,658), chord members 1.13.

## 6. Verdict (task 4)

* Regressions against the shipped control (pooled pitch lower by 0.5 or more, or bars or hands worse): **Petrushka, both models** (-34.4 and -20.4 pooled; five parts and three parts; hands not defined). **Etude 5 with realbrace-3**: one bar fewer (133 of 134), pooled +1.5, hands 92 % against 71 %: a small flag, not a score loss. No other of the 28 pieces changes; none of the 25 non-Schott scans other than Petrushka differs at all.
* The pairing models themselves do not harm any non-Schott scan; the damage is confined to the one piece whose systems have three staves, and it is a merger-and-pairing interaction. A pairing that moves the grand pair of a three-staff system from staves 0-1 to 1-2 needs a merger that matches such pages with two-staff pages.
* Not adopted. The candidates were chosen after seeing the Schott pieces, and the other 25 scans contain no thin-brace edition, so they say only that nothing else breaks. A held-out edition test is still needed (the same-volume Schott etudes and a transfer edition, `run/brace_collection/`; D30 for the newer models trained on the Schott series).
