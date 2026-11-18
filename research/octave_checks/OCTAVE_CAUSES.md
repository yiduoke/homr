# Where do the octave errors come from? (D32)

Laptop only, released weights (`pytorch_model_meteracc-r2s7-afae0e3`; the reads are the ones the pair builders stored), written 9:26-9:55 pm Pacific, 2026-11-17. Analysis of existing outputs, no model run, no training, nothing pushed, vast-homr4 not touched, vast-homr5 not used.
Development data: the verified scan-pair crops (pilot lists, batch 2) with the released model's free-generation read. The 28 real scans are evaluation data: used here only to describe causes, never to tune or train. Nothing of this feeds a training list.
Scripts (all in this folder): `octave_causes_crops.py` (task 1, per crop), `octave_causes_tables.py`, `octave_causes_gap.py` and `octave_causes_ledger.py` (tables, counts), `make_eye_sheets.py`, `prev_right_montage.py` (by-eye sheets), `octave_causes_realscans.py` and `octave_causes_realscans_tables.py` (task 2), `make_scan_event_sheets.py`. Data: `octave_causes_crops.csv`, `octave_causes_notes.json` (per crop, per affected note), `eye_verdicts.csv`, `eye_sample_auto.json`, `octave_causes_realscans.json`, `octave_causes_tables.json`, `octave_causes_gap.json`. Figures: `causes/`.

## Causes and how they are told apart

Token convention (checked before): label and read write the printed pitch plus `octaveShift_8va/8vb` + `octaveShiftStop`; the sounding pitch is the written pitch plus the shift. For every aligned note (letters aligned per staff and time slice, chord order ignored) the script has the written octave difference `wd` and the sounding difference `sd = wd + shift_label - shift_read`.

| class | rule (automatic) | what it means | fix |
|---|---|---|---|
| (a) start | `wd = 0`, bracket differs, the label bracket lies inside the crop: read has none, starts late or early, wrong direction, or a read bracket where the label has none | missed / misplaced / invented start | more starts, hard negatives |
| (b) stop | same, the read bracket ends too early, too late (or never: no stop token), or stray `octaveShiftStop` | wrong stop | more stops |
| (c) continuation | the label bracket crosses a system or page break: open at the crop start (the previous system's label is open at its end, measure ranges contiguous) or open at the crop end; any bracket error on such a span | multi-system bracket | multi-system data |
| (d) wrong register | `wd != 0`, same shift state on both sides | note read an octave off (ledger lines, clef change) with no bracket involved | high/low passages, clef changes |
| (e) edition / reference | `wd != 0` and bracket differs but `sd = 0` (print at pitch vs 8va with lowered notes: same sound) | label and print notate it differently | do not train on it unreviewed; correct the reference |
| mixed | `wd != 0`, brackets differ, `sd != 0` | register and bracket both | counted with the bracket classes in bounds |

Limit of the rules: a read bracket where the label has none (`spurious bracket`) cannot be told from "the reference lacks the print's bracket" (Schubert D.899/4 type) without the print; the by-eye check below measures how often that is (e).

## Task 1: development crops (pilot + batch 2)

Population: 2,153 manifest crops; 1,965 have a label token file, a read and a reliable label (120 have no label; 57 are quarantined for an unreliable label: alignment, bar mismatch, edition/key mismatch, label shifted; 11 more, Liszt TE1 `A1` and two Ballade crops, are known wrong labels from the octave review); 125 more differ from the read by more than octaves (pitch-letter F1 below 0.8, mostly strong-tier crops with chord/ornament differences) and are not analysed. **Analysed: 1,840 crops.** Quarantined crops with reliable labels (octave disagreement, ledger lines, rhythm, tuplets) are in.

### T1 crops with an octave or bracket difference

| group (never mixed) | manifest | label+read reliable | analysed | flagged | share | affected notes |
|---|---|---|---|---|---|---|
| pilot train (A, Peters/Schott etc.) | 948 | 876 | 810 | 347 | 43 % | 3,383 |
| pilot train, rendered-mixture pieces (B) | 164 | 161 | 152 | 40 | 26 % | 433 |
| **pilot validation (C)** | 122 | 117 | 114 | 51 | 45 % | 500 |
| batch 2 train | 676 | 605 | 566 | 209 | 37 % | 2,136 |
| batch 2 Demets (Une barque) | 84 | 55 | 48 | 31 | 65 % | 502 |
| **batch 2 validation** | 159 | 151 | 150 | 62 | 41 % | 587 |
| all | 2,153 | 1,965 | 1,840 | **740** | **40 %** | 7,541 |

Strict case "all pitch letters agree, written octave differs": 54 crops, 591 notes. Crops where the numbers of bracket start/stop tokens of label and read differ: 287.

### T2 causes (automatic class; crop = class with most affected notes)

| cause | crops, training groups | crops, validation groups | crops total | share | notes affected | of them sounding pitch differs |
|---|---|---|---|---|---|---|
| (a) start | 70 | 11 | 81 | 11 % | 1,964 | 1,964 |
| (b) stop | 59 | 14 | 73 | 10 % | 890 | 890 |
| (c) continuation | 27 | 7 | 34 | 5 % | 762 | 762 |
| (d) wrong register | 394 | 61 | 455 | 61 % | 2,323 | 2,323 |
| (e) edition / reference | 74 | 20 | 94 | 13 % | 1,542 | 0 |
| mixed | 3 | 0 | 3 | 0 % | 60 | 60 |
| total | 627 | 113 | 740 | | 7,541 | 5,999 |

Crops containing at least one event of the class: (a) 105, (b) 99, (c) 42, (d) 510, (e) 138, mixed 19. Sub-classes (T3, in `octave_causes_tables.json`): (a) 1,686 of its 1,964 notes are a read-only bracket (label none): invented, or the reference lacks the print's bracket, resolved by the eye sample below; missed bracket 219 notes; (b) 870 notes are a read bracket that is never closed or closes late, 20 notes a stop that is too early, 16 crops a stray stop with no note affected, 15 crops a missing stop token with no note affected (label stops at the crop end); (c) 551 of 762 notes are "bracket continued from the previous system, read does not stop where the label stops".

### Per bracket span: what the released model gets right (all analysed crops, original labels)

| label bracket | spans | all notes under it with the right shift | start right | stop right (stops inside the crop) |
|---|---|---|---|---|
| starts and stops inside | 282 | 72 % | 75 % | 60 % of 228 |
| continues from the previous system | 114 | 82 % | 87 % | 60 % of 72 |
| starts inside, runs into the next system | 78 | 76 % | 77 % | n/a |

Where a stop is wrong (120 spans with a stop inside): the read bracket never closes in the crop in 74 of them (55 + 19), closes later in 45 (1 other), so the dominant dev-set failure is the stop, not the start. Validation groups alone: all-notes-right 19 of 22, 32 of 36, 37 of 48 spans.

### T4 by-eye check (51 crops, stratified random, seed 20261132; crop + label engraving + full page)

Sheets `make_eye_sheets.py` (header shows label and read bracket events, not the class). 9 (a), 9 (b), 9 (c), 12 (d), 8 (e), 3 mixed; one (Liszt TE1) turned out to have a known shifted label and is not assessable. Verdicts: `eye_verdicts.csv`.

| auto \ eye | a | b | c | d | e | n/a | n |
|---|---|---|---|---|---|---|---|
| a | 6 | 0 | 1 | 0 | 2 | 0 | 9 |
| b | 0 | 9 | 0 | 0 | 0 | 0 | 9 |
| c | 0 | 0 | 8 | 0 | 1 | 0 | 9 |
| d | 0 | 0 | 0 | 11 | 1 | 0 | 12 |
| e | 0 | 0 | 1 | 0 | 7 | 0 | 8 |
| mixed | 1 | 2 | 0 | 0 | 0 | 0 | 3 |

**Agreement 41 of 50 = 82 %** (95 % interval about 69-91 %). The 9 disagreements: read-only bracket (auto a) that is a reference gap (the print has the 8va, the reference none: Ravel Une barque p. 25, Schubert D.935/3 p. 20; 2 of the 4 read-only crops of the sample, the other 2 are invented brackets: an 8vb on the lower staff, hand brackets read as 8vb); an (a) that is a continuation (Liszt Ballade 2 p. 14: 8va over the whole system, runs on); a continuation whose bracket in the print ends inside the system while ASAP runs it on (e); a (d) that is a printed-register difference (e); an (e) that is a continuation (Chopin Scherzo 2 p. 19); the 3 mixed crops are a (1) and b (2). Caution learned: **a single crop cannot tell a start from a continuation.** My first by-eye calls on the crop alone put 6 continuations under (b); the previous system's right end (`prev_right_montage.py`) showed the 8va still open there in all 6 (Liszt TE3 p. 14, Gnomenreigen p. 7 and p. 9, Liszt TE9 p. 77, Chopin Op.10/10 p. 36, Chopin Scherzo 2 p. 13), so the neighbour check of the tokens was right and the verdicts were changed (`eye_verdicts.csv`). Calibrated to the eye confusion (rough, small sample): about 55 (a), 75 (b), 51 (c), 417 (d), 142 (e) of the 740 flagged crops. The earlier octave reviews (110 crops by eye, `octave_review.md`) agree: edition/reference decisions are (e) in 43 of 54 usable crops, "label right" cases are (a) 22, (b) 2, (c) 5, (d) 5.

Examples (figures `causes/`): `fig1_a_missed_start_A4_p-10_s4.png` (print and label: 8va over bars 2-3, read none), `fig2_b_stop_early_or_missing_A9_p-58_s1.png` (two short brackets: first stop 3 notes early, second never stopped), `fig3_c_continuation_C1_p-014_s3.png` (previous system ends in an open 8va; this one: label re-opens it, read opens it and never closes), `fig4_d_wrong_register_C3_p-16_s3.png` (low left-hand ledger-line notes read 1-2 octaves off, no bracket), `fig5_e_edition_N11_p-16_s3.png` (print writes the high notes at pitch, ASAP has an 8va), `fig6_real_scans_WinterWind_c_and_Hammerklavier_e.png` (task 2).

Findings for the training mix: (1) stops, not starts, are where the model fails on the dev crops (60 % right); (2) a bracket that is open from the previous system is started correctly 87 % of the time but closed correctly only 60 %; (3) register errors are 61 % of the flagged crops but only 31 % of the affected notes (2,323 of 7,541): they come in 1-3 notes, 4 times more often on notes with 4 or more ledger lines (67 per 1,000 notes against 17 for notes inside the staff, `octave_causes_ledger.py`) and 1.7 times more often in crops with a clef change (25 against 15 per 1,000 notes); (4) 19 % of the flagged crops (the calibrated (e) share) are notation or reference differences where the model is right; 1,542 notes have the same sound under another notation (print at pitch vs 8va).

## Task 2: note level on the 28 real scans (description only)

Basis: the audit of `eval_run1/brace_models/audit_relbrace3_gpu.md` (27 scans, Petrushka is not in it; relbrace3, GPU, merger by role): 3,557 octave events = note pairs (reference note, predicted note, same letter, octave differs by 1-2) = 3.02 micro F1 points. For each event the exact bracket state of the reference note and the predicted note (start/stop positions in the files, Schubert D.899/4 with its edition reference as in the audit), the print's system breaks (from the predicted file's `new-system`, mapped to reference bars through the audit alignment) and the bar's bracket profile on that staff are used. The attribution reproduces 3,557 events and 3.017 points. The task text names the page-xml of the layout1 run; the 3.02 points belong to relbrace3_gpu, so its merged MusicXML (`out/testset/<piece>/<piece>-relbrace3_gpu.musicxml`, with the `print new-system` of homr's layout) is used.

| cause | events | notes | points | share |
|---|---|---|---|---|
| (a) start (missed 271, started late 261, other 45) | 577 | 1,154 | 0.49 | 16 % |
| (b) stop | 46 | 92 | 0.04 | 1 % |
| (c) continuation: bracket crosses a print system break (reference bracket not read 416, read bracket runs on 217, other 54) | 687 | 1,374 | 0.58 | 19 % |
| (d) wrong register, brackets equal or absent in both bars | 1,651 | 3,302 | 1.40 | 46 % |
| read-only bracket: spurious start or (e) the reference lacks the print's bracket | 132 | 264 | 0.11 | 4 % |
| mixed (bracket differs and the octave differs by another amount) | 464 | 928 | 0.39 | 13 % |
| total | 3,557 | 7,114 | 3.02 | |

Bracket-related (a, b, c, read-only, mixed): 1,906 events = 1.62 points (54 %); register (d): 1.40 points (46 %). Because the audit pairs each missed note with the nearest extra note of the same letter, a bracket that starts or stops at the wrong place in a dense bar shows up as mixed octave pairs; the bar profile (reference bracket against read bracket on the staff) was used to move such events from (d) to (a), (b), (c); 93 events of (d) sit in bars whose bracket extents agree.

**By-eye checks on the print (10 bars of the top pieces, `make_scan_event_sheets.py`):** Winter Wind bars 85-86 (24 events each): the 8va of the print runs on from the previous system over the whole system and the read has none: (c) confirmed (`fig6`). Hammerklavier mvt 4 bar 247: the print has 8va brackets over the right-hand figures, the reference has no octave-shift at all and the read follows the print: **(e) confirmed** (21 events; the same pattern as Schubert D.899/4, where the edition reference already removes the loss). Schubert Wanderer bar 473-474: the print has two short 8va brackets, the reference only orphan stops: (e) (16 events). Scriabin Sonata 5 bars 299 and 301 (the read-only bracket events, 50 in all): the print has no bracket there and the read invented an 8vb on the right-hand chords: spurious (a), not (e). Ravel Alborada bar 179 (read-only, 18): no bracket visible in the print there: spurious. Debussy Reflets bar 32 (register): a cross-staff run with a treble clef in the lower staff, the read puts two notes of it 1-2 octaves too high: real (d), clef change. Scriabin bar 312 (32 register events): the reference engraves the chords below the staff (printed D4-B4 from the file), the scan shows them inside the treble staff, the read agrees with the scan: a reference register difference, so (e) inside the (d) bucket. Five more large (d) bars (Ravel 206, Liszt Sonata 204, Chopin Polonaise 54, Liszt TE5 78, Paganini 193) could not be decided by eye at 150 dpi from an approximate system band (chord octaves in the middle of the staff could not be read reliably; the Sonata band missed the system), so the (d) share that is a reference difference is **unknown**; of the 2 decidable (d) bars one is model, one reference. (d) is therefore an upper bound for pure register reading.

### Top 8 pieces by octave loss (relbrace3; points are the audit's)

| piece | octave points | events | a | b | c | d | read-only | mixed | bracket-related | dominant cause (largest single class) |
|---|---|---|---|---|---|---|---|---|---|---|
| Liszt TE5 | 12.6 | 562 | 153 | 6 | 122 | 192 | 4 | 85 | 66 % | (d) register 34 %, but (a)+(c) 49 %: missed starts and bracket continuations over several systems (the print repeats the 8 at every system) |
| Ravel Alborada | 11.0 | 505 | 29 | 0 | 95 | 262 | 18 | 101 | 48 % | (d) 52 %; run figures above/below the staff with `8 bass`/8va brackets on both staves; (c) 19 % |
| Chopin Etude 25/11 (Winter Wind) | 7.8 | 248 | 61 | 11 | 93 | 61 | 0 | 22 | 75 % | (c) continuation 38 %: 8va crossing system and barline breaks |
| Liszt Sonata | 6.1 | 398 | 119 | 0 | 53 | 166 | 11 | 49 | 58 % | (d) 42 %; (a) 30 % |
| Liszt Paganini 6 | 5.6 | 246 | 50 | 3 | 100 | 61 | 1 | 31 | 75 % | (c) 41 % |
| Debussy Reflets | 5.4 | 118 | 28 | 1 | 32 | 47 | 3 | 7 | 60 % | (d) 40 % (clef change in the lower staff), (c) 27 % |
| Chopin Scherzo 3 | 5.1 | 274 | 16 | 0 | 84 | 146 | 2 | 26 | 47 % | (d) 53 %, (c) 31 % |
| Liszt TE10 | 4.2 | 174 | 35 | 0 | 22 | 55 | 3 | 59 | 68 % | mixed 34 % (bracket and register together), (d) 32 % |

Next: Scriabin Sonata 5 3.4 ((d) 68 %, read-only 50 events), Chopin Polonaise 2.9 ((d) 72 %).

## Task 3: what the next training mix should contain

### Verified examples we already hold (admitted lists: pilot A+B strong, hard and octave-verified, batch 2 train; validation never trained)

| list | crops | no bracket | with a start inside (spans) | with a stop inside (spans) | continuing from the previous system | continuing into the next | lower-staff spans |
|---|---|---|---|---|---|---|---|
| pilot train (A+B strong) | 864 | 738 | 104 (129) | 107 (129) | 33 | 33 | 3 |
| pilot train hard + octave-verified | 48 | 26 | 20 (22) | 17 (18) | 2 | 6 | 0 |
| batch 2 train (strong + hard + octave-verified) | 550 | 477 | 49 (62) | 48 (62) | 28 | 29 | 4 |
| batch 2 Demets (Une barque) | 47 | 27 | 17 (46) | 16 (45) | 3 | 4 | 11 |
| **training lists together** | **1,509** | **1,268** | **190 (259)** | **188 (254)** | **66** | **72** | **18** |
| pilot validation (C) | 104 | 92 | 10 | 10 | 2 | 2 | 0 |
| batch 2 validation | 145 | 83 | 44 | 41 | 30 | 33 | 3 |

(Note: the pilot README's "47 crops continue from the previous system" counts crops whose bracket opens at the first note; with the previous system's label as check, 33 of them are continuations, 14 are fresh starts at the first note.) Middle systems (both open at the start and at the end): 22 crops in the training lists (batch 2 validation alone: 24). Crops with 4 or more ledger lines: 366 in the training lists (231 + 13 + 103 + 19); crops with a clef change inside the system: 480 of the 1,509. Hard negatives (read invents a bracket, label none, admitted after review): 26.

### Recommendation per cause, bound on the value (real-scan points; staff-sensitive micro F1 on 27 scans)

| cause | what to put in | what we have | gap | max points if fully fixed |
|---|---|---|---|---|
| (c) continuation | crops that open and stop a bracket across 2-4 systems and across page breaks, **with the stop** in the last system; middle systems; Liszt/Chopin/Rachmaninoff pieces with long 8va passages; keep the repeated `8` at the system start as label | 66 + 72 crops, 22 middle systems; model: start 87 % but stop 60 % | proposed target 250 continuation crops incl. 80 middle systems: gap about 180 and 60 | **0.58** (+ part of mixed) |
| (b) stop | brackets with varied extent: ends at a barline, mid-bar, before an accidental, two brackets in one system, hook before a tuplet | 188 crops with a stop (254 stops); stop right 60 % | proposed target 500 stops incl. 150 multi-bracket systems (we have 62 crops with 2+ spans): gap about 250 and 90 | 0.04 on the 27 scans (most stop failures appear as continuation); 74 of the 99 stop failures on the dev crops are "never closes" |
| (a) start | starts of short brackets on runs/arpeggios, 8vb on the left hand (only 18 lower-staff spans, real references have 14 % 8vb), and hard negatives for hand brackets/phrase marks read as 8vb (Casella-type, Scriabin chords) | 190 crops (259 starts), 26 hard negatives; start right 75 % | proposed: 100 more lower-staff spans, 60 more hard negatives | 0.49 (0.07 of it spurious) |
| (d) register | passages high/low with no bracket: 4-6 ledger lines, clef changes in the middle of a bar, cross-staff runs, chords on ledger lines; balance so that ledger-line notes are not a small tail | 366 crops with 4+ ledger lines, 480 with a clef change; error rate 67 per 1,000 notes at 4+ lines | proposed target 800 crops with 4+ ledger lines (gap about 430); clef-change crops are already plentiful, add cross-staff runs | **1.40** upper bound (an unknown part is a reference register difference, e.g. Scriabin bar 312) |
| (e) edition / reference | nothing to train on: **do not use ASAP labels that differ from the print** (print at pitch vs 8va; printed 8va missing in ASAP); use the corrected tokens only after the eye review (110 crops reviewed: 68 admitted, of them 34 with corrected tokens, 42 quarantined); fix the evaluation references with printed brackets instead (as for Schubert D.899/4): Hammerklavier, Wanderer | corrected labels exist for 34 crops | the references of Hammerklavier (21 events), Wanderer (16) | 0.11 (read-only bracket events, part spurious; Scriabin 50 events are spurious per the eye) |
| mixed | no separate action, follows (a)-(d) | | | 0.39 |

What not to do: do not add the unreviewed octave-disagreement crops (the eye review found a label that differs from the print in 33 of 60 pilot and 43 of 50 batch-2 octave-disagreement crops: edition differences, printed brackets missing in ASAP, wrong labels); do not train on crops whose label bracket only agrees with ASAP and not with the print; do not pad with easy classical pieces without brackets or high passages; do not tune on the 28 scans (staff-sensitive points above are descriptions); a reference lacking the printed 8va (Schubert D.899/4, Hammerklavier) is an evaluation issue, correcting it costs nothing in training; keep the validation groups (pilot C, batch 2 V: 54 crops with starts, 32 with continuations from the previous system, 24 middle systems) out of every training list.
Estimate of the order: brackets (a)+(b)+(c) bound 1.11 points (1.50 with mixed), register 1.40, reference 0.11. Only part of each bound is reachable: on the dev crops the model already reads 72-87 % of the spans right, so the continuation and stop experiments have the larger remaining error (stop 40 % wrong), the register experiment the larger and less certain bound.

## Caveats

* The automatic classes agree 82 % with the eye on a stratified sample of 50; (a) read-only brackets are the weak point (2 of 4 turned out to be reference gaps).
* Real-scan (d) cannot be split between model and reference without a per-bar reading of the print: 7 bars viewed, 2 decidable (one model, one reference), 5 undecided. A 40-bar by-eye pass is the next step if the (d) bound is to be used as a number.
* The sample is stratified by class, so class shares in the sample are not population shares; calibration used the class-wise confusion.
* Dev-crop counts treat every crop once; continuation detection needs the previous crop's label (contiguous measure range or manifest order); crops after a quarantined predecessor without a label count as starts.
