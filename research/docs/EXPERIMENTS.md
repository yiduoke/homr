# Experiment log

One entry per result that may be cited. Code commits refer to yiduoke/homr (branch
`octave-on-566` unless noted); paths are relative to this repo (yiduoke/homr-research)
unless they start with `/workspace` (GPU box; copies of its scripts and logs are in
`box_scripts/`). The narrative and earlier results are in [PROGRESS.md](https://github.com/yiduoke/homr/blob/octave-on-566/PROGRESS.md) of yiduoke/homr; the
paper outline is [PAPER_NOTES.md](https://github.com/yiduoke/homr/blob/octave-on-566/PAPER_NOTES.md); local audits are in [audits/](audits/), the
frozen evaluation in [eval_run1/](eval_run1/README.md), box scripts in [box_scripts/](box_scripts/).
Started 2026-11-15; results before that are traceable through PROGRESS.md, less precisely.

## D1. Training data regenerated with model 566's converters (2026-11-15)

Box checkout `/workspace/homr566` at homr commit cd95322. Scripts:
`box_scripts/r6_data.sh`, `r6_data2.sh`, `r6_data3.sh`, `r6_hard2.sh`,
`box_scripts/r6_extra/` (ASAP, Scriabin). Status log: `box_scripts/status.log`.
Test pieces excluded via `training/omr_datasets/pdmx_exclude_test_pieces.txt` (homr) and
the list in `box_scripts/extra_sources.md`.

| Set | Staffs | index.txt sha256 (first 16) |
|---|---|---|
| grandstaff | 45,635 | 46622be209dc3715 |
| pdmx (complexity <= 2) | 199,706 | 121e19bacdc69f63 |
| pdmx/hard (complexity 2-3) | 92,984 | 328d1b1db28019ce |
| Lieder-main | 43,149 | 3255ae73804bfd31 |
| asap | 5,832 | 4ea80d824fd8f00d |
| kern_scriabin | 1,847 | 23555faac1092186 |

## E1. Copista 28M on the listening-room pieces (2026-11-15)

kobimusic/copisteria (GitHub, cloned 2026-11-15) with HF kobimusic/copista-28m weights,
`python -m copisteria.pipeline <pdf> --pdf --range ...`, CPU, Apple M4. Pages joined with
`merge_pages.py` + `drop_minor_parts.py`. Outputs `out/compare/<piece>/*-copista.*`.

## E2. KernScores references and per-note scores across engines (2026-11-15)

References: `kern_refs/scripts/build_refs.py` (music21), sources listed in
`scores/SOURCES.sha256`, outputs `out/compare/<piece>/<piece>-reference.musicxml`.
Scorer: homr `validation/score_notes.py` at commit 9d75cd0 (extra staves mapped to the
nearest reference staff), default options. Results per piece in
`out/compare/<piece>/note-scores.json` and `note-scores-v2.json`; table in PROGRESS.md
("More references"). Audiveris scored from `work/<slug>/audiveris/*.mxl`.

## E3. KernScores scans vs transcriptions (2026-11-15, running)

Rough check: `box_scripts/kern_check/step1.py`, `step1_results.csv`. Recount with homr's
staff detection: `box_scripts/kern_check/homr_count.py` -> `homr_count.json`.

E3 result (2026-11-15): homr staff detection (homr566 checkout, segnet fp16 on GPU) counted
systems on every scan page; `box_scripts/kern_check/homr_count.json`. Systems per piece equal
to the .krn line breaks (`g=original`): Mozart 65/69, Beethoven 92/101, Chopin mazurkas 11/52
(40 without line breaks). 168 pieces usable; the 14 that disagree are dropped (Beethoven
29-4, 30-1, 30-2 hold two movements; Mozart 12-2 and Chopin 7-3 far off; 9 off by 1-2).
Reference movements (Mozart K. 331/1 = sonata11-1, K. 309/1 = sonata07-1, Beethoven Op. 13/1
= sonata08-1) are excluded from any training use. Not used in the meter and accidental runs
(fixed data mix); kept for a separate real-scan round.

## E4. Other engines scored on all references (2026-11-15)

Transcoda rerun with v2.1 (HF btrkeks/transcoda-v2.1, 2026-11-13; `tools/transcoda_v21_*.py`,
run on the GPU box); Audiveris 5.11.0, LEGATO (guangyangmusic/legato) and rokot-omr-2b
(2026-07-17 weights) from the 2026-08-04 runs (still latest). ABC from LEGATO and rokot
converted with `tools/abc2xml_stack.py` (voices parsed separately, stacked into two staves;
rokot's voices drift in bar count when systems are joined). Scorer as in E2. Results in
`out/compare/<piece>/note-scores*.json` and the listening room page `out/compare/index.html`.

## T0. Starting point for runs 1 and 2 (2026-11-15)

Upstream model 566: `pytorch_model_566-ccd1cb311c368b5711dd238d2464c615397a3f2b.pth` from
liebharc/homr release `checkpoints` (asset uploaded 2026-11-13), on the box in
`/workspace/ckpt/`. Its vocabulary, built from upstream commit ccd1cb3, is identical to
`octave-on-566`'s: `/workspace/ckpt/vocab_566.json` (rhythm 285, articulation 96, pitch 72,
lift 7, position 5, slur 17). Run 1 (branch `meter-run1`, commits 8bff5b8, 44738bb, 10bc7e6)
grows rhythm to 311: 10 `timeSignature/<den>` rows dropped, 36 complete time signatures added,
initialised from the old row of their denominator (`training/transformer/meter_vocabulary.py`).
Clean training lists (duplicates and evaluation pieces removed): `index_clean.txt` next to
each index on the box; report `audits/` (copied from `/workspace/clean_index/`).

## R1. Run 1: complete time signatures (started 2026-11-16 00:15 UTC)

Code: yiduoke/homr `meter-run1` at 10bc7e6, checkout `/workspace/homr_meter`. Start: upstream
566 (T0), rhythm head grown 285 -> 311 by name (warm start: 322 tensors copied, 825 rows
remapped, 108 new rows = 36 tokens x 3 tensors). Data: `/workspace/run1/run1_train.txt`
(109,185 lines: Lieder 10,940, GrandStaff 10,794, PDMX 48,248, LilyPond 30,046, MuseScore
octave 9,157; 13,798 octave-bracket exposures = round 3) and `run1_val.txt` (3,998); built
by `box_scripts/build_run1.py`, counts in `box_scripts/run1_stats.json`. Labels: relabeled
for existing images (`datasets_meter/`), octave sets also with beams. Settings as round 3:
2 epochs, LR 2e-5, batch 16 x 2 accumulation, 6,826 steps (~1 h on the RTX 3090).
Launcher `box_scripts/train_run1.sh`; logs `/workspace/logs/run1/`.
Control run (planned right after): identical lines and settings, time-signature tokens
converted back to `timeSignature/<den>` (`/workspace/run1/control_*.txt`).

## R1 result: first evaluation (2026-11-15 evening Pacific)

Frozen pipeline for all three models (566, control, run 1): pdftoppm 150 dpi, one `homr.main`
call per piece on all pages, HOMR_FIXED_MARGIN=1, per-page MusicXML joined with
`merge_pages.py` + `drop_minor_parts.py`, `validation/score_notes.py` (octave_wt) defaults.
Commands, scripts and tables: `eval_run1/` (README.md, summary.md, results.json, meter_eval.py).
Control: `pytorch_model_meter_control` (homr566 checkout, old vocabulary), same lines/settings.

Notes, pitch+onset+duration F1 (566 / control / run 1): Mazeppa 34.8/33.6/35.8; La Campanella
68.0/66.7/69.9; Rachmaninoff 57.8/59.0/58.9; Bach prelude 91.4/90.9/90.0; Bach fugue
86.0/82.4/82.4; K. 331 99.6/99.6/99.6; K. 309 96.9/95.8/95.5; Pathetique 97.0/96.5/97.0.
Meter change effect (run 1 vs control): within about 1 point except Liszt (+2.2, +3.2).
Fine-tune recipe effect (control vs 566): Bach fugue -3.6, K. 309 -1.1, Mazeppa -1.2.

Meter: run 1 writes C/cut (Pathetique exact 4/6 vs 0/6 for 566), exact single signatures in
Rachmaninoff, Bach fugue, K. 309; Pathetique changes 5/5. Mazeppa: run 1 misreads 2/4 as 3/4 at
m129 and carries it (meter in effect 49.5% of bars vs 81.7% for 566).
Pipeline problems found: merge_pages drops page-start time signatures on later pages (hurts
only run 1) and loses Mazeppa p. 11 and Rachmaninoff p. 5 (part pairing; all models).
KernScores references lack `<time symbol>`; exact meter is scored against the printed symbol.

R1 rescore (same evening): `merge_pages.py` now keeps page-start time signatures for code
that carries the meter itself (`HOMR_TRUST_PAGE_TIME=1`, set by `eval_run1/join_score.sh`
for run 1 only; 566 and control write a made-up one per page, which is still dropped).
Note scores unchanged for every model and piece. Run 1 Mazeppa meter: exact 4/8 (was 3),
numeric 5/8, changes found 2/7 (566: 2/7), bars in the right meter 60.4% (566 81.7%).
Part matching by "most notes per page" was tried and reverted: it broke K. 309 (97 -> 65)
and the Pathetique (97 -> 27). The part-id loss stays: Mazeppa p. 11 (13 bars) and
Rachmaninoff p. 5 (11 bars), identical for all models. First tables kept as
`eval_run1/summary_v1.md`, `results_v1.json`.

## R2. Run 2: printed accidentals (started 2026-11-15 10:59 pm Pacific)

Code: yiduoke/homr `accidentals-run2` at 2f4096d (lift = printed sign; shared rule
`homr/accidentals.py`; decoding writes `<alter>` and `<accidental>`; `FT_RESET_LIFT`).
Start: run-1 model `pytorch_model_meter_run1_653-10bc7e6...pth` (325 tensors copied); lift head
and lift embedding re-initialised. Data: run 1's lists relabeled in the lift field only
(`box_scripts/relabel_run2.py`, `build_lists.py`, `verify_run2.py`): train 108,884 (0.28%
dropped: microtonal or slash accidentals, staff-mapping misses), val 3,996; every other field
identical to run 1 (checked on all 109,849 files). Label sources: MuseScore export
`<accidental>` (PDMX, Lieder, MuseScore octave), Verovio 6.4.1 MEI @accid (GrandStaff; differs
from the rule on 2.5% of staffs), the rule for LilyPond (97.7% of measures agree with
LilyPond's own SVG glyph counts; 92.5% of measures with any sign). Settings as run 1 (2 epochs,
LR 2e-5). Launcher `box_scripts/train_run2.sh`, logs `/workspace/logs/run2/`; ONNX exported
automatically to `/workspace/onnx/acc_run2/`.
Evaluation prepared (`eval_run1/`): printed references `out/compare/<piece>/<piece>-reference-printed.musicxml`
(rule + hand corrections on viewed pages), `accidental_eval.py`, `key_eval.py`. Baseline: 566
sounding pitch right on 97.2% of matched notes, run 1 96.3%; neither writes printed signs.

## R2 result (2026-11-16, ~1 am Pacific; tables `eval_run1/run2_summary.md`)

Same frozen pipeline as R1 (run 2 merged with HOMR_TRUST_PAGE_TIME=1 like run 1). Export of
run 2 needed a manual rerun (relative path in `train_run2.sh`, fixed).
Notes, pitch+onset+duration F1 (566 / control / run 1 / run 2): Mazeppa 34.8/33.6/35.8/33.3;
Campanella 68.0/66.7/69.9/70.9; Rachmaninoff 57.8/59.0/58.9/61.2; Bach prelude
91.4/90.9/90.0/92.1; fugue 86.0/82.4/82.4/85.7; K. 331 99.6 all; K. 309 96.9/95.8/95.5/95.3;
Pathetique 97.0/96.5/97.0/96.3; mean 78.9/78.1/78.6/79.3.
Sounding pitch correct on matched notes: 97.2 / 96.7 / 96.3 / 97.8%.
Printed signs, run 2 P/R/F1 pooled: # 87.6/84.2/85.9, b 84.9/94.3/89.3, N 83.1/82.6/82.9,
## 77.8/94.7/85.4, none 98.8/98.4/98.6 (run 1 about 0 for every sign; bb untested).
Weak: K. 309 naturals F1 27 (precision 22), La Campanella # 59. Key and meter not lost.
Concern: Mazeppa, the only real scan among the references, drops vs run 1 and 566 (notes
-2.5 / -1.5, sounding pitch 94.7%; pages 13-16 down 3-14 points). AGENTS.md: real scans must
not get worse - investigate before adopting run 2. Single runs, no seeds: differences of a
point or two may be noise.

## R2s7. Repeat of run 2 with another seed (started 2026-11-16 ~12:40 am Pacific)

Same as R2 with `FT_SEED=7` (homr `accidentals-run2` afae0e3 adds FT_SEED; it seeds the
Trainer and the re-initialised lift head; R2 used the default 42). Purpose: how much of R2's
differences (Mazeppa -2.5, sounding pitch +1.5 vs run 1) is chance. Launcher
`box_scripts/train_run2s7.sh`; ONNX to `/workspace/onnx/acc_run2s7/`.

R2 rescore after a joiner fix (2026-11-16 ~1:30 am Pacific): `merge_pages.py`'s "accidental
repair" (meant for models drifting back to the key mid-bar) overwrote run 2's printed signs
(about 160 notes per Liszt piece); it now skips notes with a printed `<accidental>`. 566,
control and run 1 write no printed signs, so their results are unchanged. Diagnosis:
`eval_run1/run2_diagnosis.md`. Run 2 after the fix: sounding pitch right on 98.8% of matched
notes (566 97.2, run 1 96.3); notes F1 Mazeppa 33.7, Campanella 72.1, Rachmaninoff 63.5,
Bach prelude 92.6, fugue 86.3, K. 331 99.6, K. 309 96.1, Pathetique 97.3. Printed-sign F1,
e.g. Mazeppa # 91.6 b 89.9 N 86.1; Campanella # 77.1; Pathetique # 99.2 b 92.8 N 94.2;
K. 309 N 60.9 (reference misses cautionary naturals the PDF prints). Mazeppa's remaining
notes gap vs run 1 (-2.1) is mostly page 16 variance (566/control/run1/run2: 66.6/40.8/56.2/
42.1) plus ~10 notes lost to one misread key signature; references need fixes (K. 309 from
m32, Campanella, Mazeppa p. 14 b. 136).

R2s7 result (2026-11-16 ~2:10 am Pacific; same frozen pipeline, `eval_run1/run2s7/`):
notes F1 Mazeppa 33.6, Campanella 71.8, Rachmaninoff 61.7, Bach prelude 94.0, fugue 86.0,
K. 331 99.6, K. 309 97.1, Pathetique 97.2; mean 80.1 (run 2 80.1 after the latest rescore:
K. 309 95.8, Pathetique 97.1; 566 78.9). Sounding pitch right on 99.0% (run 2 98.8%).
Run-to-run spread per piece up to ~1.8 points (Rachmaninoff 63.5 vs 61.7, Bach prelude
92.6 vs 94.0); Mazeppa ~1 point below 566 in both runs (consistent, small).

## Release meteracc-r2s7-afae0e3 (2026-11-16 ~8:45 am Pacific, owner approved)

R2s7 published as GitHub release `meteracc_checkpoints` on yiduoke/homr, target commit 0caa509
(`accidentals-run2`: configs.py model_name `pytorch_model_meteracc-r2s7-afae0e3`, download_weights
maps the `pytorch_model_meteracc` prefix to this release, Training.md model card). Assets: ONNX
encoder/decoder fp32 and fp16 zips, the .pth zip, SHA256SUMS (files in `release_meteracc/`,
git-ignored). Verified: a fresh clone's download_weights fetched the files; decoder sha256 matches.
https://github.com/yiduoke/homr/releases/tag/meteracc_checkpoints
Listening room "Ours" = the released model on all ten pieces (artifact version 24). `merge_pages.py`
got a guard for note slivers MusicXML can't write (Petrushka bar 194: a gap music21 fills with a
"2048th" while writing): fix too-short values, and on a write error quantize that measure and
split complex values, then write again. Rescoring 566 and the released model on all eight
references with the guard gives identical tables.

## Ballade reference (2026-11-16 morning Pacific)

Owner supplied `Chopin_Ballade_4_F-minor_Op52.musicxml`, transcribed by Claude in another session (MusicXML 3.1, no encoder info; 239 bars,
one part, two staves, 6,525 notes, 1,331 printed accidentals, 6/8 with a 27/8 bar at m134), now
`out/compare/chopin-ballade-4/chopin-ballade-4-reference.musicxml`. Our test PDF is a LilyPond
2.18.2 engraving. Edition agreement: 96.8% pitch-inventory F1 for the released model. Scores
(pitch inventory / pitch+onset / pitch+onset+duration): released model 96.8 / 77.3 / 75.5,
566 (frozen pipeline) 93.3 / 76.2 / 74.2, Copista 92.8 / 67.8 / 64.2, Audiveris 88.7 / 59.4 /
53.5. Results `out/compare/chopin-ballade-4/note-scores.json`.

## S1. Speed-ups without output changes (2026-11-16; branch `speed`, commits 1483fce, 03f0e29, 278ea93)

1) The staffs of a page are decoded concurrently on threads (one shared single-thread decoder
session; ONNX models have batch 1 and the fp32 decoder is int8-quantised, so tensor batching
would change results); `HOMR_DECODER_THREADS` (default min(cores, 6)). 2) Pages are recognised
on a process pool (`--workers` / `HOMR_WORKERS`, default min(4, cores)); writing (time-signature
carry, title) stays in page order. 3) Cached geometry in `_can_shapes_possibly_touch` plus a
NumPy prefilter (staff detection 3.6 -> 2.3 s on the profiled page).
Equivalence (`speed_check/compare.py`): 110 real test pages and the 8 reference pieces, 118/118
MusicXML outputs and 888/888 per-system token sequences identical to `accidentals-run2`.
Timings under heavy machine load (load average 13-40): one page 10.2 -> 7.7 s median; K. 309
(10 pages) 68 -> 49 s; Mazeppa (14) 168 -> 78 s; 8 pieces 477 -> 293 s; a 5-page piece alone
110 -> 40 s with 4 workers.

## A1. Timing-error audit of the released model (2026-11-16; `eval_run1/timing_audit.md`)

Notes with the right pitch but wrong timing, one cause each, 9 scored pieces (5,517 notes):
tuplets 64%, bar length / meter 17% (693 cadenza-like bars, 234 from Mazeppa's last-page
2/4-vs-4/4 misread), voices 6%, grace/cue 4%, rests 3%, alignment 3%, duration only 1%, other
2%. Tuplet notes are 44% of Mazeppa's reference notes, 27% Rachmaninoff, 24% Chopin, 9%
Campanella, <1% elsewhere; mostly unnumbered beamed groups in print (Beethoven: printed 6 and 7
ignored). Training-style validation (300 staffs: PDMX, Lieder, GrandStaff): 99.7% pitch F1,
99.2% full-match F1, only 2.5% tuplet notes. So the model has no general timing weakness; the
loss is tuplet-heavy and cadenza-like real music the training data barely contains.

Accidental scorer fix (2026-11-16): `eval_run1/accidental_eval.py` read only the first part (right
hand) and aligned bars itself; it now uses score_notes' parser and alignment (both hands). Sounding
pitch right on matched notes: 566 96.7%, control 96.1%, run 1 95.9%, run 2 98.8%, released 99.0%
(about 16,500 matched notes each). Printed-sign F1 (released): # 92.5, b 93.4, N 90.0, ## 94.3, none 99.0.

## A2. Pitch-error audit of the released model (2026-11-16; `eval_run1/pitch_audit.md`)

4,548 pitch-inventory errors over 9 pieces: bars lost to layout 35% (Mazeppa p. 11 ossia page,
Rachmaninoff p. 5 four-staff systems), extra notes 14% (Rachmaninoff spurious third part ~290),
octave 11% (La Campanella 229 of 293 under printed 8va brackets the model missed; Chopin 21 of
24), right pitch on the other staff 11% (almost all Bach fugue: voices crossing staves; staff-
agnostic pitch F1 fugue 87.6 -> 99.3, prelude 94.0 -> 99.8), whole event missing 11%, chord
member missing 9% (Rachmaninoff 4-6-note chords), accidental 6% (Chopin bars 121-123, 166),
step 2%, clef 0.3%.

## B1. Octave brackets, released model (2026-11-16; `eval_run1/brackets_released.md`)

322 brackets on 73 real scan pages, same scorer as rounds 1-3 (`eval_run1/real_eval_acc.py`). Released model
(meteracc-r2s7): 254 found / 13 false with bracket-aware cutting (default), 238 / 4 with upstream's cutting.
Round 3: 244 / 14. Upstream 566: 180 / 8. Chopin italic 8va 11/11 (bracket-aware). La Campanella octave
errors are reading errors of bracket extent and continuation (bar 13: start and stop in one bar; bar 86:
continuation missed) plus 33 false starts on the lower staff; writing and scoring are correct. Scorer cache
collides on page basenames between the Chopin and La Campanella side sets (not the 322 scans).

## L1. Layout fixes (branch `layout`, yiduoke/homr, head 4299394; 2026-11-16)

Ossia drop (`system_repair.py`), four-staff piano merge (`piano_staffs.py`), meter carry replacement after
four misfit bars in the same denominator (`_repair_meter`), `score_notes.py --ignore-staff`. Frozen pipeline,
full-match F1 released model -> layout: Rachmaninoff 61.7 -> 88.9 (bars 62/69 -> 62/62), Mazeppa 33.6 -> 37.8,
all other pieces identical. Rachmaninoff page 1 "89.4 -> 86.9" is a scoring artefact (output byte-identical;
the baseline used per-staff alignment because of the spurious parts); like-for-like 74.8 -> 89.8. Risks: a
four-staff SATB/quartet system with clefs G G F F would be merged (safeguard to do); the meter rule is
strict on purpose (looser versions made 9/8, 13/16 out of misread tuplets). Outputs `eval_run1/layout/`.

## T1. Real-scan test set, released model vs upstream 566 (2026-11-16; `out/testset/SUMMARY.md`)

29 pieces (IMSLP scans, 150 dpi; ASAP expert MusicXML references, Claude transcription for Petrushka, unchecked).
Same frozen pipeline for both models; released model = `accidentals-run2` without the layout branch.
Mean over 29 pieces, pitch / +onset / fully right: ours 85.3 / 70.9 / 69.1, upstream 82.5 / 67.3 / 65.5 (after the Ravel and Rhapsody 6 reference corrections below);
ours ahead on fully right in 24 of 29. Upstream ahead on Chopin Op. 25/11 and the Polonaise, Debussy
Reflets, Haydn, Liszt Etude 10, Ravel. Strong (fully right): Schubert Impromptu 95.7, Bach fugue 93.3 and
Italian Concerto 93.7, Wanderer 93.0 (566 77.5), Chopin Op. 10/4 92.9, Waldstein 89.6, Prokofiev 81.5 (566 43.8).
Not model errors: (a) Liszt Sonata, Etudes 5 and 10 (Schott): the staff-relation model says "same system"
(1.00) and "grand staff" (0.00) for every hand pair, so the hands become separate parts and the joiner
chains them into one part with about twice the bars (604 vs reference 305); both models fail the same way;
(b) Ravel Alborada, Hungarian Rhapsody 6, Petrushka: references use 3-4 staves, ours 2; staff-ignored pitch
F1 80.9 / 90.9 / 79.1 (566 78.5 / 83.3 / 77.3) instead of 56.9 / 64.7 / 58.4; bar content matches (Ravel
bars 1 and 11 identical note for note); (c) Appassionata reference: 12 of 264 measures (69, 71, 73, 76, 138, 142, 144, 146, 156, 158, 160, 162) carried a
playback-expanded trill as voice 2 with `<forward>` jumps of about 665 beats; repaired by removing that voice and
rebuilding the backups (original kept as `-reference-asap-original.musicxml`). Rescored: ours 85.8 -> 88.5, 566 84.8 -> 87.5 fully right. Still unexplained: Bach prelude 873 recall 71 / precision 100, Hammerklavier fugue recall 69 /
precision 90 (page range or dropped notes), Reflets audio twice as long as the reference. Petrushka with
the same pipeline: ours 38.8, upstream 36.3 (the earlier 46.2 for upstream was a per-staff alignment artefact).
Exclusion list for training: `run/test_set_exclusions.txt` (76 lines). Listening room v34 shows all of it.

### T1 follow-up: why some pieces score low (2026-11-16 evening)

- **Debussy Reflets (fully right 44.8, upstream 46.9; pitch 85.5 vs 83.5).** The scan prints a small 4/8; ours reads
  4/4 (and 3/8 at bar 11 as 1/8), upstream reads 4/8. Note values in bar 1 are right (sixteenths); homr pads bars
  to the read meter. Whole-time-signature reading of rare meters fails here (the meter test set is for this); dense
  tuplets add to the drop. Share of each cause not separated (a timing audit on this piece would do it).
- **Chopin Polonaise Op. 53 (ours 66.2, upstream 73.8).** Pitch is better for ours (87.4 vs 85.4), timing worse
  (+onset 70.2 vs 76.4). Bar 20: sextuplets read as plain sixteenths; bars 13-14: wrong note lengths. Why upstream
  is better on timing here is open; the control run (same data, old tokens) can show whether the time-signature
  retraining cost rhythm reading.
- **Prokofiev Toccata, opening (audible pauses at bar ends).** The scan has eight repeated sixteenth D's per bar in
  the upper voice; our bars 2 and 3 have 4-5 of them (some read as sixth-of-a-beat tuplets) and homr pads the bar
  with a rest (1 beat in bar 2, 0.75 in bar 3). Dropped repeated notes in long beamed runs plus rest padding. A
  before/after example for the harder-data run (run 3).
- **Ravel Alborada (ours pitch 56.9, staff-ignored 80.9; fully right 33.4, upstream 34.4).** The piece changes
  between 6/8, 3/8, 9/8 and 3/4 (18 changes in the reference). Ours finds 13 changes but many are wrong (12/8, 5/8,
  7/8 where the reference has 6/8 or 9/8) and only 137 of 229 bars have the usual 3-beat length (reference 182);
  upstream carries 9/8 too long (49 bars of 4.5 beats). Mixed meters, dropped notes or tuplets, and a 3-staff
  reference (2 staves in ours) together; pitch in bars 1 and 11 matches note for note.
- **Liszt Sonata, Etudes 5 and 10 (Schott):** staff-relation model says "same system" 1.00, "grand staff" 0.00 for each
  hand pair, so two parts are written and the joiner chains them (about 2x bars); to fix in homr's staff pairing or
  the joiner. Listening room shows "layout issue, not scored" (6 cells).

### T1 correction: staves of the 3-4 staff references (helper audit, commit bc3db54)

Checked on the scan pages, not assumed. **Ravel Alborada:** 2 staves in every system; the reference's third staff held
only 249 voice-7 rests (a phantom), moved to staff 2. **Liszt Rhapsody 6:** 2 staves per system except two 4-bar ossia
mini grand staves on page 3 (bars 58-61, 66-69); the reference's old staves 1-2 held only whole-bar rests plus those
ossia notes, so the scored reference is now the main system only (ossia in `-reference-ossia.musicxml`; ossias are
alternatives and left out, as decided). **Petrushka:** a real mix of 2, 3 and 4 staves per system plus small ossia
staves (3 staves on pp. 1-7, 11-13, 16, 18, 21-23, 27-31, 35-37; 2 on pp. 8-10, 14, 17, 19-20; 4 in places on pp.
32-33); the reference stays as is and is scored staff-ignored (ours 79.1 / 57.4 / 52.8, upstream 77.3 / 54.2 / 49.6),
because the scorer cannot take a per-system staff layout. Our output has 2 parts, so 3-staff systems are a layout case
still to handle (the `layout` merge only covers four-staff systems). Standard scores after correction: Ravel ours
80.5 / 56.2 / 53.9 (upstream 77.9 / 55.4 / 53.0), Rhapsody 6 ours 91.6 / 81.6 / 81.0 (upstream 83.9 / 73.0 / 72.2).
This replaces the earlier statement that the references used a third staff "for some voices": Ravel's was empty.

## M1. Meter reading: where the wrong meters come from (2026-11-16 evening; `eval_run1/meter_topk/`)

Professor's two checks, released model. `topk_ts.py` hooks `ScoreDecoder.generate` (no repo change), runs homr
in-process and records the softmax of the rhythm head at every step where a time-signature token is chosen or any has
more than 15%. **Alborada** (pages 33, 36, 38, 44; printed 6/8, 3/8, 9/8, 3/4): the odd meters are raw decoder tokens
(not downstream inference), but chosen with low confidence: 12/8 at 20% (6/8 at 19%, 9/8 at 18%, 3/8 at 18%), 9/8 at
20%, 5/8 at 22%, 7/8 at 18%, 5/8 at 23% and 19%, with a nearly flat distribution over 6/8, 9/8, 12/8, 5/8, 7/8. Clear
cases are confident: 3/4 at 84%, 3/8 at 70%. So the model knows a meter is printed but not which. **Reflets** (printed
4/8): `common` 33%, 4/4 18%, 7/8 7%, 1/8 6.5%, 1/4 6%, 12/8 4.5%; 4/8 is below 2%, not a close second, and the
distribution is diffuse (lower systems: `common` 19%, 7/8 13%, 1/8 13%). By the professor's rule that points to the
small glyph (the 4/8 is printed small) and not to the prior alone, although `common` also has 5,313 training examples
against 86 for 4/8. Consequence: a decision-time fix needs no training: where the best meter has low probability (for
example under 50%), choose among the top candidates the one that makes the bars add up (or keep the carried meter).

## D2. Exclusion of the 29 new test pieces from the training indexes (2026-11-16 night)

Phrase list `run/pdmx_exclude_new_phrases.txt` (150 phrases, "a & b" = all parts; matched against PDMX title, song name
and composer, so other uploads of a piece are caught) plus the old 71 lines = `pdmx_exclude_v2.txt` (221, on the box
in `training/omr_datasets/`). 258 PDMX scores match (`/workspace/exclude_hashes_v2.txt`, Qm hashes). New indexes
`datasets_meter/<set>/index_excl_v2.txt` on vast-homr4 (originals kept): GrandStaff 43,437 -> 40,458 (Beethoven sonatas
21, 23, 29, 8 removed), PDMX 139,461 -> 139,159 (-302), PDMX hard 90,744 -> 89,096 (-1,648), ASAP 5,491 -> 4,241
(-1,250, whole works by ASAP name), Lieder and kern_scriabin unchanged. Over-matching is accepted (e.g. 56 "wanderer"
scores); under-matching is the risk. The control and the candidate must both be rebuilt from the filtered indexes.

### Meter check of the Claude references (owner, 2026-11-16 night)
Ballade 4: the printed score has one 6/8 throughout. The Claude reference had a 27/8 time signature at bar 134 (the fermata run
of the second system on scan page 9, written as 27/8 of note values in one bar) and 6/8 again at bar 135; both `<time>` elements
removed (`out/compare/chopin-ballade-4/chopin-ballade-4-reference.musicxml`, original kept as `-reference-original.musicxml`).
Bar 134 still contains 27/8 of written values (a fast run in the time of one 6/8 bar, unmarked tuplets), so it overfills its bar.

Mazeppa (helper reading all 16 scan pages, `out/meter_check/mazeppa_printed_meters.md`): the scan prints six meters (bar 1 C, 28 3/2,
29 C, 114 6/8, 136 2/4, 182 C) and the Claude reference has all of them; it also invented 10/4 at bar 177 (a free bar under fermatas)
and 2/4 at bar 178 (one half-note chord). Both `<time>` elements removed in `out/compare/mazeppa/mazeppa-reference.musicxml`,
original kept as `-reference-original.musicxml`. The reference has 202 bars, the scan 201 (the extra bar after bar 182 is not located).

Petrushka (helper reading all 37 scan pages, `out/meter_check/petrushka_printed_meters.md`): the scan prints 48 meter changes; of the
reference's 61 entries 47 were right, 1 wrong (bar 284: 12/8, printed 9/8) and 13 invented (the four cadenza bars 220-223: 43/16, 49/32,
15/8, 65/32; the one-beat Lento bars 225 and 227: 1/4; 5/4 at 331; 3/8 at 399; five restatements or relabels at 190, 226, 295, 332, 401).
No hidden `<time>` elements. Corrected: the 13 `<time>` elements removed and 284 set to 9/8 (48 entries left); original kept as
`-reference-original.musicxml`. The scan has no rehearsal or bar numbers; counted 624 bars against the reference's 627 (the cadenza is one
unmetered bar that the reference spreads over four; the reference is one bar early from 172 to 213 and +3 from ref 474; unlocated).
The reference is unchecked beyond meters. All five Claude references now match their printed meters.

## D3. Run 3 data: control and candidate (2026-11-17 night; `box_scripts/run3/`, lists in `/workspace/run3/` on vast-homr4)

**Control** = run 2's training list (108,884 staffs) without the 29 new test pieces by name (D2) and without 27 PDMX scores found by a
note-sequence leak check (below): 107,444 staffs, validation 3,942. **Candidate** = control + harder data with run-2 labels, no octave-bracket
staffs added (octave exposure unchanged, as agreed): 19,909 hard PDMX staffs (sampled by whole score, density-weighted, a quota of 400 staffs per rare meter),
3,754 ASAP, 1,216 Scriabin listed twice; 131,488 staffs (added share about 19.5%), validation 5,285 = control validation + a held-out hard list
(1,343 staffs held out by whole score or piece: hard PDMX 72 scores, ASAP 7 pieces, Scriabin 9 pieces). Labels: lift = printed sign; ASAP and Scriabin MuseScore
exports regenerated (MuseScore 4.6.5); by-eye check 0 errors in 45 staffs per set; automatic sounding-pitch check disagrees on 0.05% (hard PDMX), 0.08% (ASAP), 0.34%
(Scriabin) of notes (upper bounds). Trainer filters (vocabulary, length, at most 5 ledger lines) applied before sampling; this drops the densest 8% of hard PDMX and
15.5% of Scriabin. Crop audit (added vs control sample): notes per staff median 66 / 51 / 59 (hard PDMX / ASAP / Scriabin) vs 38; chords of 4+ notes 17 / 11 / 17% vs 11%;
second voice 46 / 63 / 70% vs 26%; runs of 8+ short notes 45 / 51 / 16% vs 34%; all clean MuseScore or Verovio renderings, no scans.
**Leak check** (`leakcheck2.py`, name-independent): 12-note pitch sequences (6+ distinct pitches, 4+ direction changes) of all 38 references against every training staff;
59 staffs of the first candidate list and 36 of the control list shared 12 or more 12-grams with a reference (Chopin Op. 25/10 octave patterns, Schumann Toccata,
Ravel Alborada, ...), which means PDMX uploads under other titles; the 27 scores were removed from every list (`exclude_leak_hashes.txt`). About 0.8% of staffs still
share 3+ 12-grams (weak coincidences; 37 of the candidate with 10+, same rate in the control). **Training**: continue the released model (run2s7), lr 2e-5, effective batch 32,
**6,716 steps for both arms** (the control's two epochs; the candidate stops at 1.63 epochs of its larger list), last weights (no best-checkpoint selection), seeds 7 and 11,
order ctrl-7, cand-7, ctrl-11, cand-11, one after the other on the RTX 3090 ($0.299 an hour, about 68 minutes each). Trainer patch `finetune_octave_FT_MAX_STEPS_FT_LAST.patch`
(FT_MAX_STEPS, FT_LAST). Started 2026-11-16 23:13 Pacific.

## D4. Meter arm data (helper, 2026-11-17 00:15-02:35 Pacific; `box_scripts/run4_meters/`, lists in `/workspace/run4/meters/final/` on vast-homr4)

Mining of the run-3 lists (128,439 staffs): 22.8% print a time signature, 5,581 have a mid-staff change. Staff space 11.76 px (MuseScore sets), 10.0
(Lieder); no existing set has small-print signatures (MuseScore 4.6.5 and Verovio draw default size only; digits about 3.7 staff spaces). Main
meters (staffs / scores / composers): 3/4 7,919/2,992/1,087; 4/4 7,658/4,941/1,971; 2/4 4,745/1,492/580; 6/8 2,795/1,471/542; 5/8 778/449/219; 7/8
523/407/180; 1/8 572/374/185; 4/8 58/32/19. **Finding: most printed rare meters in the real scores are bars that do not fit** (scores with two
consecutive bars adding up vs scores printing the meter: 5/8 33 vs 449, 7/8 42 vs 407, 1/8 9 vs 374, 4/8 28 vs 32), i.e. cadenza or irregular-bar encodings,
so real rare-meter examples are scarce and partly wrong labels in the original data. Built: windows of 2-26 real bars, every bar checked to fill its meter;
operations: real bars, same-duration relabels (3/4<->6/8, 2/4<->4/8, 4/4<->2/2, 6/4<->3/2<->12/8, C and cut-C), all values halved or doubled with the beat type
(4/4->4/8, 5/8->5/16), 2-3 bars joined (5/4x2->10/4), real meter changes, splices of 2-6 segments of different scores (same staves and clefs); 17/16 and 19/16
synthetic. Renderers Verovio 6.4.1 (5 fonts, scale 30-45, signature size by SVG edit) and MuseScore 4.6.5 (5 fonts, signature scale in the mscx); labels from the
homr_acc parser. MuseScore ignores the per-job style key, so older MuseScore renders probably all use Leland. Lists: train 15,000 / val 1,500 (737 held-out source
scores, none shared); 20% without a signature; 47.9% with a change; small print 32.5%, large 10.4%; every one of the 36 labels has at least 151 staffs from at least 8
scores (tightest: 5/16 151; 11/8 and 11/16 8 scores); validation thin for rare meters (13/8, 15/8 none, 13/16 one). By eye 7/480 errors (1.5%, 95% bound 2.9%):
swapped clefs, bar counts, a barline inside a bar. Caveats: the arm is deliberately unrealistic (48% change staffs vs about 4% in the control; 59.8% of start
signatures common vs about 85% in real data), so it must enter run B as a share, not whole; LilyPond skipped; before training repeat the by-eye check on the real mixture
and test Reflets 4/8 and Alborada plus a common-meter regression check.

## D5. First read of run 3 (seed 7): control vs harder data (2026-11-17 morning)

28 real scans, layout code of the `integration` branch for all rows (`eval_all.sh r3ctrl_s7 / r3cand_s7`, `compare_tags.py`), mean pitch / +onset / full match:
baseline (released weights, tag layout1) 85.3 / 71.6 / 69.7; **control seed 7** (continued on the old mixture, 6,716 steps) 84.8 / 71.3 / 69.5;
**candidate seed 7** (+ harder data) 85.3 / 71.5 / 69.7; upstream 566 82.5 / 67.8 / 66.0. Candidate minus control +0.5 pitch; candidate better than the
baseline in 16 pieces, worse in 10 (-0.00 mean); control worse than the baseline in 14 (-0.43). Pieces with pitch >= 97: 3 of 28 in all three. Biggest movers
(cand vs baseline): Scriabin sonata +1.5, Chopin Op. 25/10 +3.8 onset, Debussy Pour le piano -1.4, Haydn -0.3, Liszt Rhapsody 6 +0.3, Chopin Op. 25/11 -5.9 onset.
**Staff-level free generation on held-out rendered staffs** (`hard_eval.py`, 450 staffs): released model pitch precision/recall 0.998 / 0.998 on held-out hard
(PDMX, ASAP, Scriabin) and 0.999 / 0.998 on ordinary validation staffs; exact meter sequence only 0.75 on hard staffs that carry a signature (0.964 ordinary), invented
signatures 0. **Reading:** on clean renderings the model is already at the ceiling, even for dense virtuoso writing, so more rendered hard data cannot move
the real-scan score much; the gap between 99.8% on renderings and 85% on scans is the domain (scans and photos), plus layout and meter. This does not support
"insufficient exposure to difficult notation" for clean renderings. Note: validation staffs get the usual training distortions too (`distort_image`, Augraphy noise, fixed seed per staff), so 0.998 is on degraded
rendered staffs; more of the same synthetic noise is unlikely to help. The gap must come from what the synthetic data lacks: the engraving styles of real
editions (fonts, historical plates, spacing, hand-corrected plates), scan resolution and binarisation, and page layout. Next: real-scan pairs (KernScores) first, more
engraving styles second (fonts in Verovio, MuseScore and LilyPond), and the staff-level read of the released model on verified real-scan staffs (isolates the transformer from page layout); seed 11 will give the noise level.

## D6. Real-scan pairs for run B and a staff-level read of the scan domain (helper, 2026-11-17 00:20-03:30 Pacific; `box_scripts/run4_scans/`, lists in `/workspace/run4/scans/`)

KernScores source scans cut with homr's own detection and `prepare_staff_image`, paired with the .krn split at `!!LO:LB:g=original` (a piece is used only if homr's
system count equals the .krn line breaks), labels in the current format. Lists: train 3,480 pairs (Beethoven sonatas 2,352 from 75 pieces, Mozart 982 from 49, Chopin mazurkas 146
from 10), validation 230 (whole pieces: 7 / 4 / 1), quarantine 341 (octave shifts 98, repeat sign at a system start 68, failed verification about 97, over 5 ledger lines 39,
conversion errors 18, one suspect piece); "strong" lists without 49 medium pairs. Left out: Haydn and Scarlatti (line breaks are another layout), Joplin (scans not
matched), Scriabin (no line breaks), 40 of 52 mazurkas. Test pieces excluded by composition. Verification: bar count of a barline counter (2,646 agree) and a free-generation read by the released
model (strong: pitch F1 >= 0.8, same bars, notes within 10%); 978 pairs accepted on the model alone; by eye 192 pairs, 0 mislabelled (95% upper bound about 1.6% pooled). Bias: the
verification keeps what the model already reads, the quarantine holds correct but hard cases. GrandStaff already contains rendered snippets of the same pieces. **Staff-level read of the
released model on all judged real-scan staffs: pitch F1 0.988 (3,866 staffs; Beethoven 0.985, Mozart 0.995, Chopin 0.997; 95% of staffs at 0.97 or better), 0.997 when the bar count
agrees and nothing else is wrong.** Scans differ from renderings mainly by extra marks (fingerings, pedal signs, page numbers, stamps), neighbouring-system fragments in the crop (ink extent
31.8 vs 24.2 staff spaces) and crops filling the full canvas height; resolution, paper, ink and line thickness are comparable. **Consequence:** the real-scan gap of the 28 test pieces (pitch
85.3) is not a scanning gap for classical music (the KernScores pieces Pathetique, K. 331, K. 309 score 99.4-99.7 at page level too); it comes from the specific editions, dense virtuoso engraving,
octave brackets, layout and the page pipeline. Adding these 3,480 classical scans to training is therefore an anchor against regressions, not the lever. Next: error attribution by cause on the 28 pieces
(`pitch_audit_28.md`), labelled real virtuoso scans (ASAP pieces with IMSLP scans are the candidate source).

## D7. Where the pitch error of the 28 real scans comes from (helper, `eval_run1/pitch_audit_28.md`, script `pitch_audit_28.py`; 2026-11-17)

Earlier classifier reused unchanged on the layout1 outputs; 25 pieces without the three Liszt Schott pieces (44-49% of their loss is doubled bars; reading-only F1 67-70).
Mean pitch F1 89.4 (91.0 with Scriabin and Petrushka staff-ignored); **reading-only F1 (aligned bars) 91.9; only 1.0 of the 9.0 lost points (11%) are bars that never aligned**
(28-piece means 85.3 / 87.1 audited / 89.5 reading-only). Shares of the loss: octave 27%, missing notes 29% (chord member 10%, whole event 19%), lost bars 11%, accidental 11%,
wrong staff 7%, extra 6%, step 4%, other 4%, clef 0.3%. **Density is not the driver** (aligned-bar F1 92-93 up to 23 notes per bar, 88 at 36-59); octave costs at most 2.7 points
(pitch-class F1 93.7). **Octave events are whole passages** (84% in blocks of 4+ same-direction shifts, 4% single notes); a third (1,011 of 3,219) are bars where only our output has
a bracket: on the pages checked the print has the 8va and the REFERENCE lacks the octave-shift (Schubert Impromptu p. 29, Chopin Scherzo pp. 4 and 12), the opposite (model keeps
printed pitch, misses the bracket) on Wanderer p. 31 and Rhapsody 6, undecided for Ravel pp. 42-44 and Scriabin p. 14. **Many "missing notes" are the references' written-out
trills** (Hammerklavier: 18.8% of reference notes are trill-like runs, 1,562 of 2,123 missing events; Bach prelude 873: 203 trill-run notes, 67 grace notes, 90 very short notes
of 486 missing events), a lower-bound floor of 0.65 points on the mean. Layout failures are few but large: Scriabin p. 18 dropped entirely (706 notes; the page has two parts, `merge_pages`
matches parts by id and `drop_minor_parts` removes the music part), Petrushka loses two minor parts of 69 measures, bar-splitting in Schumann Toccata, Hammerklavier p. 31, Rhapsody 6 p. 5
(cadenza). Edition does not separate good from bad pages (Breitkopf 87.4-96.7, Peters 78.3-95.9); 8va brackets and ornaments do. If the 1,011 only-output-bracket events were reference-side
and trill runs removed, the 25-piece mean would be 92.4. **Recommended:** (1) report bracket-normalised and trill-collapsed scores next to the raw ones; (2) real-scan pairs with
8va/8vb including multi-system brackets (the KernScores pairs quarantined these: 98 pairs, about 166 recoverable with octave tokens in the converter); (3) code: robust part matching in
`merge_pages` for pages with a small extra staff (K. 309 regression check), octave-shift direction written into the part that carries the shifted notes, no pseudo-bars out of unbarred
cadenza runs. Limits: octave statements outside the 16 viewed pages are inferred; the trill detector is a five-note two-pitch proxy (lower bound).


## D8. Evaluations moved to the box (2026-11-17, from 10:08 am Pacific)

Run B real-scan evaluation and the 28 rendered-piece evaluation run on `vast-homr4` (see
`PROGRESS.md`, status of 10:45 am). Upload by tar over ssh (rsync is refused). Rendered
pieces use layout1 code with the released weights (comparable with the laptop run);
run B uses tag `r3B7`. Logs: `eval_run1/eval_rendered_box.log`, `eval_r3B7_box.log`
(on the box). First result: Bach fugue 873 rendered, 99.21 pitch inventory, 94.87
pitch+onset. A first run B attempt hit an intermittent empty-message page error under CPU
overload (both jobs at once); rerun after the rendered job finishes. Results to follow.


## D9. Run B on the real scans, rendered vs scanned, and the hidden-note scoring problem (2026-11-17, noon)

Run B (harder data + meters + scans; 6,716 steps, seed 7): real-scan mean pitch/+onset/full
84.0 / 71.2 / 69.4 vs run2s7 85.3 / 71.4 / 69.6 and 566 82.5 / 67.8 / 66.0; no gain, and
Debussy Pour le piano 1 drops 91.6 -> 82.8. Rendered-from-reference pages with the same code and
weights: mean pitch 92.9 (scan 85.3), 12 of 28 at or above 97; Scriabin rendered 61.5 -> 70.6
after removing a stray 47-note second part from the reference before engraving. The three Schott
Liszt scans show +39 to +46 because the scan output has about twice the bars. Reference notes
marked `print-object="no"` (ornament realisations, e.g. 484 of 1,801 in the Bach prelude) were
counted as missed; the model never learns them (the training parser skips them), so this is a
scorer error. Rescoring with hidden notes excluded is the next step; all numbers above are
uncorrected. Details and open items: `PROGRESS.md`, status of 12:30 pm.


## D10. Corrected scoring, decoder loops and the loop guard (2026-11-17, afternoon)

Hidden notes (`print-object="no"`, invisible noteheads) are no longer counted by `validation/score_notes.py`
(`SCORE_COUNT_HIDDEN=1` restores the old behaviour); 195 existing score files were rescored without inference
(`eval_run1/rescore_visible.py`, originals in `out/scores_before_hidden_fix/`). Corrected real-scan means
pitch / +onset / full: released 86.5 / 72.7 / 70.9, run B 85.3 / 72.3 / 70.6, harder data s11 86.5 / 72.8 / 71.0
(null against the released model, as with seed 7). A bar of 274-538 repeated notes (a decoder loop to the 608-step
limit) appears on real scans in both controls and run B on Debussy Pour le piano and Hungarian Rhapsody 6. The
released and harder-data outputs checked on those scans avoided the loop. A repetition guard (cycle of up to 4 symbols repeated for 64 symbols; real
maximum is 24) recovers Debussy 85.5 -> 90.2 and Hungarian Rhapsody 6 89.5 -> 91.6 on the control. The 97 %
target is on pitch inventory, which ignores timing; on pitch+onset scans average 72.7. Full table:
`out/testset/CORRECTED-table-2026-11-17.md`.

## D11. Visual comparison of 29 scan/render pairs (2026-11-17)

Released weights, layout1, visible notes. We inspected matched passages in 23 pieces and opening systems in six. Holding bar alignments fixed and pooling pitches across staves raises whole-piece scan F1 from 89.5 to 95.9 on Hammerklavier and from 94.2 to 99.5 on Waldstein. The respective renders move from 97.7 to 97.8 and remain at 99.0. The editions visibly assign the same figure to different staves in both sampled bars.

The released model also repeats on **rendered** Hungarian Rhapsody No. 6. Page 8, fourth output bar, has 414 consecutive G5s. That bar accounts for 578 of the piece’s 902 unmatched predictions. The existing guard’s effect on this render is unmeasured. The proposed resolution experiment compares a finer spatial grid with fixed data and decoder. [Passages, images and scoring method](eval_run1/scan_render_audit.md)

The scan outputs for *Winter Wind* m. 20 and Schubert D. 899 No. 4 m. 64 disagree with the reference in sounding octave even after staff pooling. The rendered outputs match all 33 and 14 reference pitches, respectively. Verify the printed bracket endpoints against the XML and render before attributing those discrepancies to recognition. Correct and rescore any verified reference errors, with the edition and benchmark version recorded. [Render and reference XML checks](eval_run1/scan_render_audit.md#render-and-reference-xml-corrections)


## D11. Pooled pitch, Scriabin reference, loop replay (2026-11-17, evening)

Pooled-staff pitch inventory (a pitch counts on either staff, `staff_agnostic` block of the scorer) lifts the released model from
87.2 to 89.3 over the 28 scans and the scans at 97 from 4 to 5; Waldstein 94.2 -> 99.5. Scriabin was mis-scored all along
(stray 47-note second part in the reference): 69.6 -> 89.1 scan, 71.1 -> 95.7 rendered after dropping it (original kept). The
released model loops on rendered Hungarian Rhapsody 6 (bar 87: 608 notes, 484 G5); the loop guard removes 509 notes on that
page and gives no false trigger on Prokofiev Toccata (0 of 11 pages). Tables: `out/testset/POOLED-table-2026-11-17.md`,
`CORRECTED-table-2026-11-17.md`. Petrushka's pooled score (79.2) rests on a different bar alignment and is unverified.


## D12. Page merger after the Schott fix: hands lined up per page (2026-11-17)

Three scans (Liszt Sonata, Transcendental Etudes 5 and 10) come out of homr as two single-staff parts per page, both named `Voice`, because the staff
pairing model does not read the Schott brace as a grand staff. `merge_pages.py` joined them by name and so poured both hands into one part (604, 261
and 358 bars for references of 305, 134 and 182). Commit cd3b639 keeps the n-th same-named part of a page separate (two parts of 298/306, 132/129, 176/182 bars).
Aligning each hand to the reference shows that both hands cover the same reference bars on every page and that a hand differs only by bars lost inside a
page output (Sonata p. 2, 7, 12, 15: 1, 1, 2, 4 bars; right hand loses reference bars 292-296 on p. 15; Etude 5: 7 bars on six pages; Etude 10: p. 81, 85: 4, 2).
`merge_pages.py` now gives the part with fewer bars on a page rests for the missing bars at the end of that page (only for same-named simultaneous parts), so both
hands have the same bars per page (306, 134, 182 bars; reference 305, 134, 182). The two hands then point to the same reference bar in 85 / 72 / 76 % of the output bars
(without padding 1.4 / 4.9 / 39 %; `eval_run1/hand_sync.py`). Same parts, bars and notes as before on the other 26 scan sets (of 29) and 28 of 29 rendered sets; rendered Petrushka gets 10 padded
bars and keeps its score (73.3 / 56.8). Pairing is untouched and no heuristic was added (the two-staff rule was reverted).

Rescored from the saved page outputs of the released model and of both controls and both harder-data runs (no inference, visible notes, `eval_run1/remerge_after_merger.sh`,
`score_after_merger.py`, `after_merger_tables.py`). Released model, pitch staff-sensitive / pooled: Sonata 81.0 / 81.5 (was 48.8), Etude 5 77.0 / 77.8 (53.3), Etude 10 79.1 / 79.8 (52.3).
The per-staff alignment of the unpadded parts gave 84.6 / 82.6 / 86.0 because each hand is aligned on its own; those figures hide the drift and are not used. Means over 28 scans, released:
staff-sensitive pitch 90.2 / +onset 75.5 / full 73.6; pooled pitch 91.9 / 76.9 / 74.9; scans at 97: 4 and 5; bars equal to the reference on 14 of 28. Controls 89.7-89.9 / 91.5-91.6,
harder data 90.1-90.4 / 91.8-92.1; run B 86.0 / 88.2 is not re-merged (only its final files are local). Petrushka remains provisional (staff-sensitive 58.3 is per-staff aligned, pooled 79.2 jointly).
Tables: `out/testset/POOLED-table-2026-11-17-after-merger.md`, `CORRECTED-table-2026-11-17-after-merger.md`. Limits: lost bars sit mid-page and cannot be placed by the merger;
the Schott scans still lack the grand staff (pairing handled separately; the reverted heuristic reached 84.6 / 81.6 / 93.5 on Sonata / Etude 5 / Etude 10).

## D14. Staff relation model for the Schott brace: real scans, brace variations, controlled comparison (helper, 2026-11-17, 3:30-6:25 pm Pacific; `staff_rel_realbrace/README.md`; code branch `staff-relations-real`, worktree `run/rel_wt`, commit a769705)

Question: can the staff-pairing model (`homr/staff_relations.py`, 5 x 96 x 96 crops, 3 classes) learn the thin, nearly straight Schott brace without any rule in the pairing?
Data: 19 IMSLP piano PDFs (250 pages, 2,418 pairs; pages of test pieces removed by eye), 18 OpenScore-Lieder source scans (1,603 pairs, voice + piano = same-system negatives),
386 MuseScore Lieder pages sampled from the box (9,419 pairs, SATB, duets, voice+piano), labels from the page structure checked by barlines which cross the gap (no look at the
brace). No real edition has the Schott style; only Reichardt (1819, 23 pages) has a thin nearly straight brace, and the shipped model already reads every other real edition (Op. 31 Schirmer:
17 of 59 grand pairs missed, staff start cut off). Brace variations (curvature, centre point, thickness, distance, connecting line kept / removed / added; brackets on systems of separate
parts) were drawn on 327 training page images before segmentation (2,978 pairs).
Results (two seeds, fixed budget 12 x 150 x 64, lr 1e-4): arms A0 (no variations, Reichardt held out), B (A0 + variations), C (B + Reichardt). Held-out real editions (7 editions, 890 pairs): 0 missed,
0 false merges for all arms and the shipped model. Held-out thin edition (Reichardt): shipped misses 53 of 56 grand pairs, A0 53 / 55, B 53 / 51 (variations did not transfer there; false joins 14 vs 7-9).
Schott scans (TEST), grand staff calls among 169 within-system pairs: shipped 1, A0 21 / 33, realbrace-1 (A0 + Reichardt) 56, B 90 / 91, C 98 / 78; opening pages 0, 1, 2, 5-6, 7 / 4 of 13; no separate pair
joined. 25 of the other 26 scan sets: no pair changes for any model; Petrushka (3-4 staffs under one brace): 8 pair decisions on 6 pages change for realbrace-1, none a false merge, the grand pair chosen
in 3-staff systems moves from staffs 0-1 to 1-2 on 25 of 37 pages (needs a pipeline score).
Full pipeline (box CPU, merger as it is; staff-sensitive pitch): control 79.95 / 77.04 / 76.90 (Sonata / Etude 5 / Etude 10); realbrace-1 44.5 / 71.0 / 62.0; B0 61.5 / 43.0 / 79.9; C0 59.9 / 67.0 / 73.7. Hands in the
same reference bar 79 / 72 / 70 % (control), best 96 % (Etude 10, B0), but pages with a mix of grand and single-staff systems lose bars (output 62-188 bars against 134-305) and give 4 parts.
Conclusion: recall rose from 1 to about 98 of 169 pairs but not to all, and partial recognition is worse than none for the current merger; not ready to ship. Models `staff_rel_realbrace/staff_relations_realbrace-{1,2,3}.onnx`
(`HOMR_STAFF_RELATION_MODEL`), tables `pipeline_summary.txt`, `eval_*.json`. Open: a held-out real thin-brace edition (none found), more or more varied drawn braces, a merger that tolerates mixed pages.

## D15. Octave-bracket checks: Winter Wind m. 20 and Schubert D. 899 No. 4 m. 64 (2026-11-17, 3:45 pm Pacific; `octave_checks/REPORT.md`)

Procedure from the scan/render audit (D11). Encoding: reference = sounding pitch + `<octave-shift>` (`down` = 8va); the model writes the same; `score_notes.py` does not re-apply shifts.
**Chopin Op. 25/11 bars 19-20 (scan p. 34):** the print's 8va (bar 19 note 17 to bar 20 note 12), the reference (`down` before A6, `stop` before D#6) and the render agree; the released model starts the bracket at the right note but stops it after note 20 of bar 19, so bar 19 notes 21-24 and bar 20 notes 1-12 come out an octave low (scan bar 20 20/33 pitches, render 33/33). Verdict: model misread, recorded, reference unchanged.
**Schubert D. 899/4:** the Breitkopf print has an 8va over the right hand of bars 57-64 (scan p. 29) and 231-236 (p. 35); the ASAP reference has no octave-shift at all and the written pitches, an octave below the sounding pitch the print asks for. The model reads the bracket correctly. Edition copy `schubert-impromptu-d899-4-reference-edition.musicxml` (original kept; shift pair plus 12 semitones on 132 right-hand notes), all 9 saved tags rescored: released 96.7 -> 99.2 pitch (95.8 -> 98.6 +onset), run B 96.3 -> 98.8, controls 96.5-96.7 -> 98.9-99.2, 566 96.1 -> 98.6; the 14 bars concerned go from 5/13 (4/14) to full. Test-set means move by 0.1 (released staff-sensitive 90.2 -> 90.3, pooled 91.9 -> 92.0; scans at 97 or more 4 -> 5, pooled 5 -> 6). New tables: `out/testset/POOLED-table-2026-11-17-after-merger-octave-edition.md`, `CORRECTED-table-2026-11-17-after-merger-octave-edition.md` (old ones kept); `eval_run1/after_merger_tables_octave.py`. The rendered Schubert copy is still scored against the original reference it was made from.
**Same pattern elsewhere** (`octave_checks/shift_inventory.md`, nothing fixed): references without shifts but with shifts in the released scan output: Hammerklavier (14), Kreisleriana (2); references with orphan stops (no start): Wanderer 14, Rhapsody 6 15, Pour le piano 4, Petrushka 3; many brackets cross barlines (Scherzo 3: 39). Chopin 25/11 spans 37-38 and 83-87 lose many scan pitches and may show the Winter Wind error again.


## D16. Second cloud machine vast-homr5 for evaluation and pair building (2026-11-17, 3:40-4:25 pm Pacific; `cloud2_README.md`)

vast.ai instance 61144905 (`ssh vast-homr5`), Titan RTX 24 GB, 28 vCPU (Xeon E5-2680 v4), 31 GB RAM, about $0.134/h; the training box vast-homr4 is not used for this.
Env `/venv/main` (onnxruntime-gpu 1.32, opencv 5.0.0.93, numpy 2.4.6, rapidocr 3.9.2: the laptop's versions), laptop paths mirrored, `run/integration_wt`, `run/res_wt`
(clean, 4715ec5), `run/models/run3_ctrl_s7|s11`, scan pages, references and scripts copied (about 1 GB, tar over ssh); helpers `cloud2_push.sh`, `cloud2_pull.sh`,
`cloud2_models.sh` (box 4 to box 5 through the laptop; no key on the boxes). Check: Bach fugue 873, released model, `HOMR_FORCE_CPU=1`: the scorer JSON equals the laptop's
`note-scores-layout1.json` in every metric and alignment entry; GPU (fp16) gives 99.48 instead of 99.55 pooled pitch (one note). So CPU runs are laptop-exact, GPU runs are a separate
setting (tags `res_<arm>_gpu`). Speed: box CPU 2.6-3x slower than the laptop per piece (A11 vs A7: Op. 10/4 60 vs 21 s, Prokofiev 130 vs 52, Scherzo 3 187 vs 71);
box GPU about 1.9 s/page on 22 inputs (41 s) vs about 7 s/page on the box CPU. Moved: `res_eval.py --arm A11` (laptop chain killed before A11 started; laptop A7 had finished all 28 pieces)
runs on the box in tmux `a11` (CPU, `HOMR_FORCE_CPU=1`, log `/root/logs/res_eval_A11.log`, results pulled with `./cloud2_pull.sh res_A_s11`); tmux `after` then re-runs failed pieces
and the GPU arms `res_A_s7_gpu`, `res_A_s11_gpu` (the baselines for the B arms on the GPU). Problem met: two evaluations plus another agent's 8 workers filled the 31 GB and OOM-killed pool
workers (pieces FAILED in the log); the GPU run was stopped and everything is re-run one at a time, finished pieces are kept. ONNX hashes of `run3_ctrl_s11` on the box equal the laptop's.

## D17. Eye review of the 60 training-side octave-bracket disagreements of the pilot scan pairs (2026-11-17, 4:30-5:00 pm Pacific; `scan_pairs_virtuoso/octave_review.md`, `.csv`)

Each of the 60 crops (groups A and B; the 6 validation crops were not touched) was put above an engraving of its label measures (Verovio, bracket re-opened at the window start) and compared with the print and the released model's read; token convention checked on the ASAP XML: pitch tokens are written pitch, shift tokens carry the shift.
**Result: 27 label right (13 bracket in label and model missed, 14 model invented a bracket or stop), 7 label wrong and corrected (ASAP XML lacks the printed `<octave-shift>`, notes at sounding pitch: bracket added, notes lowered; 0 octave differences to the model's read afterwards), 6 label wrong and quarantined (Liszt TE1 x2 shifted label, TE11 orphan stops, Ballade 2 and Ballade 1 bar-count mismatches hidden behind the octave reason, Ballade 3 bracket extent), 20 edition differences (the print writes the high notes at pitch without 8va, ASAP has 8va; Muzgiz Scherzo 2, Schirmer Schubert/Ballade 2, Buelow Op.111, Scharwenka Ballade 3), 0 undecided.**
Admitted `lists/train_octave_verified.txt`: 34 (14 without any bracket, 20 with one: 19 bracket starts, 1 crop inside a continuing bracket, 16 stops, 5 continuing into the next system; no crop holds the end of a bracket opened in an earlier system); quarantine `lists/octave_quarantine_final.txt` 26; 16 of the edition crops have a corrected tokens candidate (`lists/octave_edition_corrected_candidates.txt`, not admitted).
Training total with the pilot: 878 + 34 = 912. The multi-system continuation gap is not closed by this review. Evidence: 18 side-by-side sheets in `octave_review_images/`; code `octave_review_scripts/`; originals and frozen lists untouched; corrected tokens in `octave_review/tokens_corrected/`.

## D18. Tuplet and duration conversion errors, re-admission of 30 crops, and rhythm audit of the 864 training strong crops (helper, 2026-11-17, 4:00-5:00 pm Pacific; `scan_pairs_virtuoso/rhythm_audit.md`; code branch `tuplet-fix`, worktree `run/tuplet_wt`, commit 3356196)

**Why 59 crops were quarantined (39 irregular tuplet, 20 duration errors).** The training path writes kern = round(written x actual/normal) and raises for a non-integer value (17 crops of 4:3, 4 of 5:3, ...); 20 crops have a kern with no token in the vocabulary (note_76 = 19 in the time of 4, note_14 = 7:4 eighths, note_52, note_80, dotted triplet rests `rest_24.`); 7 failed only because of hidden tuplet notes. **Fix** (new module `training/omr_datasets/tuplet_tokens.py`, used only inside `fixed_tuplets()`, parser and homr untouched, 12 tests): exact kerns stay, a notes of the printed value are read as a in the time of prior_power_of_two(a) (4:3 eighths become plain eighths, 5:3 becomes 5:4, 9:4 becomes 9:8), rests without a token get the token of the same length, notes whose MusicXML duration disagrees with type x ratio or which have no token are rejected, a report lists every non-exact note. With the new option for bar rests off, 1,153 other crops give token files byte-identical to the frozen ones.
**Result: 30 admitted** (`lists/train_tuplet_fixed.txt`; 6 exact, 24 with a declared rounded group; 10 of them also sum to the meter, `lists/train_tuplet_fixed_meter_exact.txt`), **30 rejected** (`lists/tuplet_quarantine_final.txt`: 18 not representable, 4 nested tuplets with an inconsistent XML (Kreisleriana 3), 2 cadenza bars longer than the meter, 2 pitch F1/bar count, 2 ledger lines, 1 octave bracket, 1 two-octave shift). Bar count equal in 30 of 30; token sums equal the true durations in the 6 exact crops and differ only in declared rounded bars in the others (+1/4 in the 6/8 bars of Sonata 3 finale, which keep the printed plain eighths); printed value and meter total cannot both hold for 4:3 and 5:3. Released model, free read, mean of the 30: pitch F1 0.966, duration F1 0.916, pitch+onset 0.652, full-note 0.639. By eye 33 crops viewed (all 30 admitted): 32 right, 1 wrong and rejected (Op.25/5 cadenza written as quarter notes). Never group C.
**Rhythm audit, strong tier (864).** Label rhythm wrong by eye in 5 of 60 random crops (8.3%, 95% CI 2.8% to 18.4%); the automatic check (token durations vs true MusicXML durations per bar and voice, bar vs meter) flags 105 of 864 (12.2%, CI 10.0% to 14.5%): **79 bar rests without `<type>` written as rest_8** (MuseScore export; fixed tokens in `tokens_typeless_rest_fixed/`; 7 more in the validation group, listed separately), 14 MusicXML bars longer than the meter (cadenzas), 13 nested tuplets with inconsistent durations (Kreisleriana 3, 13 of 23 crops); 31 crops with a flag other than the bar rest are listed in `lists/train_strong_rhythm_suspect.txt`. Model vs label on all 864: pitch F1 0.980, pitch+onset 0.836, full-note 0.810, duration 0.862; on the 244 crops with a tuplet kern in the label the full-note F1 is 0.58 against 0.90 elsewhere. Pieces with pitch >= 0.95 but full-note F1 at least 0.2 lower: Liszt TE9 (0.959/0.375), Op.25/1 (0.962/0.308), Op.25/2 (0.991/0.334), Kreisleriana 3 (0.983/0.497), Liszt Ballade 2 (0.981/0.658), TE11, Barcarolle, Schubert D.899/1, Sonata 2 finale. In most the label is right and the model misses an implied tuplet (71 of 114 crops with pitch >= 0.9 and rhythm F1 < 0.6); Kreisleriana 3 labels are wrong; Liszt TE9 (12/8) the model invents triplets. Evidence: 8 sheets in `scan_pairs_virtuoso/work/tuplet/evidence/`, 20 audit sheets `work/tuplet/audit_eye/`. Recommended list: train_strong with the 79 fixed files, without the 31 suspect crops (833) + 30 tuplet crops.

## R7. Input-resolution experiment, prepared 2:35 pm, LAUNCHED 2:55 pm Pacific 2026-11-17 (spec `res_experiment_spec.md`)

Question: finer grid (384x1920 canvas, 24x120 tokens) vs 256x1280 (16x80) from released run2s7, same list (`run2_train_excl_v3`, 6,716
updates, batch 16x2, lr 2e-5 cosine, seeds 7/11). Code: yiduoke/homr-local branch `resolution` (worktree `run/res_wt`, e0fc61b, from `integration`):
`HOMR_INPUT_SCALE` (default 1, bit-identical), `HOMR_MODEL_NAME`, positional embeddings resampled at warm start, ONNX context length from config.
Stored training images are ~1290 px wide (canvas 1:1), so arm B upsamples ~1.5x on the fly (no new detail; true re-render not possible: PDMX SVGs deleted,
LilyPond/GrandStaff raster only, disk). Arm A = existing run3_ctrl_s7/s11. Smoke on vast-homr4: B fits batch 16x2 (17.8 GiB worst case), 0.68 s GPU step vs 0.36 s,
0.72 s with real data; est. 1.6-2.1 h and ~$0.55 per B run. Result: none yet. Box: `/workspace/homr_res`, logs `/workspace/homr_res/logs`.


**R7 update (3:05 pm Pacific).** Owner approved option 1 (arm B only, seeds 7 and 11, lr 2e-5, 6,716 updates; controls reused). Running in tmux `res` on vast-homr4 since 2:55 pm; first result expected about 4:45-5:00 pm, second about 6:45-7:00 pm. The advisor's evaluation plan: same held-out crops A vs B (B on the enlarged pixels), then B on native-detail crops from higher-dpi scans; paired seeds, pooled pitch per piece, pieces at 97, dense-bar recall, end-to-end timing, learning curves; a null result applies to this recipe and the stored rasters. Schott diagnosis and the merger fix are in `PROGRESS.md` (3:05 pm block).

## D13. Pilot set of verified real-scan pairs of virtuoso piano music (helper, 2026-11-17, 3:20-4:30 pm Pacific; `scan_pairs_virtuoso/`, README there)

IMSLP scans of 26 pieces (19 group A + 4 group B for training, 3 group C held out for validation) paired with ASAP MusicXML labels: homr detection and `prepare_staff_image` cut one crop per grand-staff system, the systems of a piece are aligned
to consecutive ASAP measure ranges by Viterbi over cumulative bar counts (bar-by-bar similarity of the released model's read + barline counter; all 26 pieces end at the last measure), labels by `MeasureCutter` (current token format). Strong = bar count
agrees and released-model pitch F1 >= 0.8; hard = bar count agrees and F1 < 0.8, with shift/anchoring guards. **Counts: train strong 864 (A 712, B 152), hard 14; validation C strong 104; quarantine 252** (ledger lines >5: 59, octave-bracket
disagreement between label and the model's read: 66 (kept in `*_octave_unverified.txt`), irregular tuplets rounded by the converter 39, conversion errors 21, edition/key mismatch 16, ambiguous alignment 11, other). **Training total 878, below the target of about 1,500**: the 23
pieces have 208 pages and 1,112 systems; the extra works should supply multi-system octave-bracket continuations, unnumbered tuplets, repeated notes and cross-staff passages (47 of the 864 start inside an 8va). Released-model pitch F1 on the kept crops: strong mean 0.981, hard mean 0.73; by piece 0.95-1.00 (lowest Schubert
D.899/1 0.949). By eye: 36 random strong crops 0 wrong (95% upper bound 9.7%); all 16 hard crops that survived the guards checked, 2 wrong (Liszt TE1 label shifted: whole piece dropped; Ballade 2: ASAP writes out trills), 14 kept; pooled 2/52 = 3.8%, upper bound 13.2%. Only 14-16 hard crops exist, so the
40-crop hard sample asked for was not possible; before the guards 3 of 25 hard crops were wrong (shifted labels in Liszt TE1 and Chopin Op.25/12), which is why the bar-by-bar alignment score and shift check were added. Bias: strong is what the model already reads. Schott Ballade 3 and the Op.31/2 spreads needed no homr change (pairing fallback in the script only; Op.31/2 PDF pages are two-page spreads with one half upside down, split and rotated by `split_b4.py`). The 5-ledger-line limit, irregular tuplets and 8va-sign disagreements are the main losses.

## D20. Second batch of verified-pair material: 21 candidate works chosen and 17 IMSLP PDFs downloaded (helper, 2026-11-17, 4:00-4:50 pm Pacific; `scan_pairs_more_candidates.md`, `scan_pairs_downloads_batch2.md`)

Goal: about 150 more pages for the pilot's 878 crops (target about 1,500). Method: ASAP `metadata.csv` minus pilot pieces, test compositions and Bach/Haydn/Mozart; predictors computed from the ASAP MusicXML (octave-shift brackets and spans, notes in tuplets, runs of repeated notes, cross-staff bars); rendered-training status read from copies of `index.txt`, `cand_train_nooct_v3.txt`, `cand_val_hard_v3.txt` (scp from vast-homr4, no remote compute); IMSLP file lists read from the work pages (curl, HTML only); then each downloaded PDF viewed as a 36 dpi contact sheet (page ranges, movements) and brace crops at 90 dpi.
Result: **21 entries (plus 2 reserves) in 17 PDFs, about 137 pages (about 152 with reserves), 46 MB, all public domain.** Octave-rich: Ravel Une barque (75 brackets in 139 bars; Demets reprint file; Miroirs 4 is a test piece and the test scan is a different file), Liszt Waldesrauschen, Gnomenreigen, Gondoliera (Cotta, Trautwein, Schott), Chopin Etudes Op.10/5 and /8 (Bote & Bock/Klindworth), Beethoven Op.81a (Breitkopf Serie 16); repeated notes: Beethoven Op.7, Op.27/1, Op.31/1 (UE Schenker, Peters Pauer, Ullstein Lamond), Etude Op.10/7, Schubert D.935/3; cross-staff: Schumann Arabeske (157 of 231 bars), Op.10/8; unnumbered tuplets: Rachmaninoff Op.23/4, 32/5, 32/10 (Gutheil), Chopin Berceuse (Peters), Etude Op.25/8 (Schott Pachmann), Sonata 2 mvt 1 (Augener). Eight of the 21 entries are not in the rendered training mixture (status A), the rest are (B). Expected yield about 570 crops at 4.2 per page (about 1,450 in total), less for Une barque (3-staff systems) and the grey Liszt library scans.
Limits: no edition with a straight bracket or no connecting line was found for these works (all 17 files show a curly brace; thinnest in Peters Pauer, Gutheil, Schott, UE); no Jurgenson or Belaieff files for them. Edition agreement with ASAP is not tested (pairing must check pitch agreement). Two downloaded files had the wrong content and are not used (IMSLP45201 Berceuse for violin, IMSLP07349 Une barque orchestral score). Nothing was paired. Owner decision wanted: use of the Demets Miroirs reprint (a different file of the same book as the Alborada test scan, pages 14-30 only).


## D19. Pilot comparison, prepared not launched: the same passages as rendered twins and as scanned crops, equal exposure (helper, 2026-11-17, 4:00-4:55 pm Pacific; `scan_pairs_virtuoso/PILOT_SPEC.md`, `box_scripts/pilot/`)

Question (advisor): do real engravings add value beyond the notes? Arms CTRL_RENDER (passage rendered from its label MusicXML) and SCAN (scanned crop), same tokens, same positions in the training list, both from run2s7 with the run3 recipe, 6,716 updates, seeds 7 and 11,
pilot passages mixed into `run2_train_excl_v3` (107,444 staffs) as R = 8 copies (6,936 lines, 6.06 % of the samples; 1.88 passes over the list, **15.0 passes over each passage in each arm**, same order). Resolution a variable (`RES=1|1.5`), decided by the resolution experiment.
**Twins** (laptop, 3.7 min): Verovio `select measureRange` of the ASAP MusicXML of each crop's measure range, one system, fonts per piece, time signature only where the token file has one, no part name or measure number, ASAP's invisible written-out trill notes turned into invisible rests;
readability rule: tightest of 8 spacing rungs at which no two notes of different columns touch (heads/accidentals at least 0.25 staff spaces apart); cut like a homr grand-staff crop, stored at canvas scale 1 without padding and without crop JSON, like the scans (same files serve 256x1280 and 384x1920).
Token check: note heads and octave brackets equal the tokens. **982 crops -> 965 twins; 17 dropped from both arms (16 notes touch at the loosest spacing, 1 head count). Lists: 867 training passages (A 716, B 151; 14 hard kept), 98 validation passages (separate), same line order and token files:
`lists/pilot_twin_render.txt`, `pilot_scan.txt`, `val_twin_render.txt`, `val_scan.txt`.** By eye: 36 side-by-side pairs (30 train, 6 validation; `twins_check/`) show no touching or squeezed notes; twins are looser than the print (31 % reach the 1280 width limit against 0.8 % of the scans; median staff space equal, p10 6.6 px).
Found on the way: **the scan arm carries label noise the twin does not**: tokens follow the XML, e.g. first-measure clefs differ from the print (Ballade 1 m. 1, Scherzo 2 m. 1), and one Ballade 2 system prints no key signature; 78 crops flagged by comparing label clefs/key with the released model's read (`lists/pilot_clef_key_disagree.txt`), used for a sensitivity analysis.
**Prepared, not launched:** `train_pilot.sh`, `chain_pilot.sh` (4 runs interleaved, waits for other training), `build_pilot_mix.py`, `upload_pilot.sh` (109 MB of images and tokens plus about 40 MB of mixes onto 8.7 GB free; vast-homr4 not touched), `pilot_val_eval.py` (held-out read, tested on 6 crops with the released model).
Cost: 1.2-1.5 h per run at 256x1280 (4 runs 4.8-6 h, $1.4-1.8), 1.6-2.1 h at 384x1920 (6.4-8.4 h, $1.9-2.5). Evaluation: control-validation accuracy per epoch, the 98 held-out passages as scans and as renderings (paired per crop, bootstrap), the 28 test scans end to end on box 5 (GPU tags), sensitivity without the 78 flagged crops and group B. Open risks (small n, engraving + print not separable, label noise, group B already rendered in the mixture, strict dropping of dense crops, Verovio instead of MuseScore): PILOT_SPEC.md section 6.


## D21. Second batch of verified real-scan pairs: 742 crops from 23 virtuoso pieces, with octave review and the fixed tuplet converter (helper, 2026-11-17, 5:10-6:00 pm Pacific; `scan_pairs_virtuoso/batch2/`, README there)

Method of the pilot (D13) on the 17 PDFs of D20 (21 works + 2 reserves; homr detection with the released weights, Viterbi alignment to ASAP measures, tiers strong/hard, laptop only, no homr code changed, PDFs untouched), plus the follow-ups: labels from the fixed tuplet converter (`run/tuplet_wt`, `fixed_tuplets(typeless_rests=True)`; printed tuplet values kept, bar rests as bar rests, no token = reject) with extra rhythm checks (MusicXML bar longer than the meter, token sum differing from the MusicXML outside a rounded group: quarantine); label/read octave disagreements go to `lists/*_octave_unverified.txt` and were reviewed by eye (50 crops): 7 admitted as is, 27 admitted with corrected tokens (20 edition differences: print at pitch where ASAP has 8va, bracket removed and notes raised; 7 printed brackets missing in ASAP added), 16 quarantined; first-measure clef/key disagreements with the read flagged in `lists/clef_key_disagree.txt` (62 crops, 3 of 3 checked are label errors).
**Counts (crops): kept 742 = train 550 (530 strong + 3 hard + 17 octave-verified, 21 pieces incl. the 2 reserves), validation extension 145 (131 strong + 1 hard + 13 octave-verified: Liszt Gnomenreigen, Chopin Etude Op.10/5, Beethoven Op.81a mvts 1 and 3; never train), Demets Ravel Une barque 47 in its own list (`lists/batch2_train_demets_unebarque*.txt`); quarantined 177 (52 are pages beyond the piece)**; pilot 878 + 550 gives 1,428 train crops (+47 Demets). Released-model pitch F1 on the kept crops 0.979 (train 0.982, val 0.980, Demets 0.937), pitch+onset F1 0.801 (train 0.811, val 0.886, Demets 0.412); per piece in the README (pitch 0.94-1.00; pitch+onset lowest Rachmaninoff Op.32/5 0.24, Waldesrauschen 0.46, Rach Op.23/4 0.58, Ravel 0.41, Op.10/5 0.61).
Quarantine reasons: not the piece 52, tuplet/duration without a token 31, rhythm sums differ from the MusicXML 22 (11 are Schubert D.935/3 volta splits), ledger lines > 5 21, octave review not admitted 20, MusicXML bar longer than the meter 12, bar mismatch 10, alignment ambiguous 9, trainer vocabulary 6, edition/key 3, other 4.
**By eye: 46 random strong crops (2 per piece): 0 wrong (95 % upper bound 7.7 %); all 7 hard crops that survived: 2 wrong (bar count 6 vs 7; an 8va the print does not have), hard crops kept 5; pooled 2/53 = 3.8 % (upper 13 %).**
Octave roles (kept crops, 155 with a bracket): 62 start inside an 8va (28 continue through the whole system, 34 end it), 66 open at the end; train 28 start inside (12 continue through), validation 30 (13), Demets 4 (3). Found on the way: ASAP Gondoliera has 4 staves (two empty), Ravel Une barque 3 (one empty) and voices a few ticks short of their backups (script-side fixes in `labels2.py`); Breitkopf Serie 16, Klindworth and Scholtz editions print high notes at pitch where ASAP has 8va; the Schubert D.935/3 variations and Une barque bars 98-102 have printed 8vas that ASAP lacks. Not done: GPU runs, MuseScore twins, correcting partial-span brackets (7 Schubert crops quarantined).

## D22. Final resolution comparison: tooling and first results (2026-11-17, 5:40-6:20 pm Pacific; `eval_run1/res_final_table.py`, `out/testset/RES-FINAL-table-2026-11-17.md`; section 'Final comparison' of `eval_run1/RESOLUTION_EVAL.md`)

Advisor's specification: arms A (256x1280, `run3_ctrl_s7/s11`) and B (384x1920, `res_B_s7/s11`), seeds 7 and 11, the GPU harness (`res_*_gpu` tags: same layout, merger, scorer, loop guard), edition-corrected references for every arm (Schubert D. 899/4 against `-reference-edition.musicxml`, Scriabin without the stray part), target 97 % pooled sounding-pitch F1 on every piece. `res_final_table.py` re-scores Schubert from the saved outputs (`note-scores-<tag>-edition.json`, `out/pooled/<piece>/<tag>-edition.json`, `res-dense-<tag>-edition.json`), reads the other 27 pieces from `res-scores-<tag>.json`, lists missing runs as missing, and writes the per-piece tables (pooled, staff-sensitive, +onset, full, bars), summary lines, paired B - A per seed with mean and spread, dense-bar recall (reference bars with >= 24 notes), a what-moved list and wall time per page. Options `--a7 --a11 --b7 --b11 --label-a --label-b --name --no-baseline` also serve the enlarge and hires comparisons (commands prepared in RESOLUTION_EVAL.md; the extra GPU runs are not started, owner to approve). `cloud2_pull_min.sh` pulls outputs, scores and wall times of a tag in a few minutes (the full `cloud2_pull.sh` took over 15 minutes for one tag because of the per-page files).
Checks: `res_A_s7_gpu` before the edition fix gives 89.98 / 91.70 / 76.78 / 74.68 (as recorded); the released baseline on the edition references gives 91.99 pooled, 77.05 +onset, 75.00 full, 6 of 28 at 97 pooled, 14 of 28 bar counts equal (as in the table of D15).
**Result (28 pieces each; staff-sensitive / pooled / +onset / full; at 97 pooled; worst piece pooled): released 90.25 / 91.99 / 77.05 / 75.00; 6; Liszt TE 5 77.8. A s7 90.07 / 91.79 / 76.88 / 74.78; 6; TE 5 78.7. A s11 90.22 / 91.92 / 77.22 / 75.13; 8; TE 10 77.8. B s7 90.24 / 91.92 / 76.48 / 74.36; 7; Petrushka 78.0 (TE 5 78.2).** No arm approaches 97 on every piece: the pieces at 97 are the Bach, Beethoven Appassionata and Waldstein and Schubert D. 899/4 in all three GPU runs (plus Hammerklavier for B s7, Etude 25/10 and Kreisleriana for A s11). Seed 7, B - A: pooled +0.13, staff-sensitive +0.17, pooled +onset -0.40, full -0.42, dense recall +0.26 points; B wins 14 / loses 11 / ties 3 pieces on pooled pitch (p = 0.69), 10 / 14 / 3 on dense recall; missed pitches in the 2,110 dense bars (69,957 notes): A s7 8,828, A s11 8,898, B s7 8,858, released 8,834. Seed noise (A s11 - A s7, pooled): mean absolute 0.70, 5 of 28 pieces differ by >= 1 point, largest 2.6; so a single-seed difference of 1 point is within noise. Single-seed moves of 1 point or more: B better on Liszt sonata +4.2, TE 10 +2.3, Etude 25/11 +2.2, Debussy Pour le piano +1.8; worse on Scherzo 3 -2.1, Reflets -1.6, Polonaise -1.3, Petrushka -1.3, Prokofiev -1.2; the +onset and full scores of B s7 are lower on Italian Concerto (-5.3), Polonaise (-9.8), Etude 25/11 (-6.8). Reading: at seed 7 the finer grid gives no net gain in pitch and a small loss in rhythm; the decision needs seed 11 and the same table.
Learning curves (`res_curve.py`, trainer logs copied read-only from vast-homr4 at 5:49 pm): B s7 starts above A in training loss (+0.014 in the first quarter) and the gap closes to +0.0006 in the last quarter; validation loss falls from epoch 1 to epoch 2 by 0.0042 for B s7 against 0.0035 for A s7 (accuracy +0.00009 against +0.00004); the final validation loss is 0.9330 (B s7) against 0.9326 (A s7). B s11 is partial (epoch 1.13 at 6:00 pm). With a cosine learning rate every curve flattens at the end, so this is not evidence of continued gains beyond the cutoff.
Cost: the per-piece wall times on the shared box are not clean (A s11 / A s7 per-piece ratio median 1.27, range 0.39-2.76; B s7 / A s7 median 1.15), so no ratio is claimed; the earlier harness measurement was 2.0x wall and 2.8x staff-reading time with an untrained B start. A clean measurement (laptop `res_timing.py`, 5 pages, or a quiet box) is in the commands.
Not done: B s11 (not trained), enlarge and hires runs (need the owner's approval), the clean timing, and `res_B_s7`'s fp32 ONNX on the laptop (the copy from the box ran at about 0.2 MB/s). Pulling B s7 results with the full `cloud2_pull.sh` was stopped and the A s7 per-page copy is incomplete (a truncated `joined.musicxml` was deleted).

## D23. Pilot label lists v2: corrected tokens, Sonata 2 split, printed notation, clef labels (2026-11-17, 6:00-6:45 pm Pacific; `scan_pairs_virtuoso/PILOT_SPEC.md` section 7)

Advisor's findings acted on before the scan-versus-render pilot launches (laptop only; vast-homr4 and vast-homr5 not touched; frozen v1 lists unchanged, new `*_v2.txt` next to them).
1. **Stale tokens verified:** 78 of 867 pilot and 6 of 98 validation passages (scan and twin lists alike) pointed to the old token file (bar rest as `rest_8`); v2 uses `tokens_typeless_rest_fixed/` for all. Twins already show bar rests (Verovio draws a typeless rest as a measure rest): the 84 re-rendered PNGs are pixel-identical, 22 viewed. Added in both arms with twin renders (64/64 ok, `twins_report_v2add.json`): 34 octave-verified (7 corrected-to-print labels: twin XML gets an `octave-shift` patch, all 7 viewed) and 30 tuplet-fixed.
2. **Sonata 2 split:** all four movements on the train side (moving mvt 2 costs 26 validation passages; the alternative would remove 75 training passages). No other movement split; independent pieces of one set split across sides are listed in the spec (Kreisleriana 3 train / 1 test, Miroirs 3 / 4, Op.23 no. 4 / 2).
3. **Printed notation vs ASAP:** pilot: 7 crops removed (meter symbol C/cut/4/4 differs from the print in 5, time signature missing in the label in 2), no compound-versus-simple meter mismatch in the pilot; batch 2: 51 candidates (Op.25/8 print 12/8, Sonata 2 mvt 1 print 6/4 in two sections, Ravel print 6/8 over 2/4, three symbol cases), 17 with unambiguous corrected tokens in `batch2/tokens_printed/`, none admitted. Implied (unnumbered) tuplets in the right meter are a different class and stay.
4. **Clef/key flagged crops:** 24 of 78 viewed: 19 of 19 clef-flagged are label errors (ASAP clef differs from the print), key-only 1 of 5. 69 passages removed from both arms.
**Counts:** pilot train 867 to 881 (796 kept + 26 moved + 30 octave + 29 tuplet), validation 98 to 72, batch 2 train 550 to 520, val 145 unchanged, Demets 47 to 26. Upload 2,859 files 107.5 MB; mix 114,492 lines (6.16 % pilot, 15.0 exposures per passage). Released-model held-out read of the v2 validation lists (72 crops): scan pitch F1 0.991 / pitch+rhythm 0.717; rendered twin 0.996 / 0.991 (`research/results/pilot_v2/`). Resolution choice still pending; lists are resolution-agnostic. Commands: `python scripts/build_pilot_v2.py`, `python scripts/build_batch2_v2.py`, `twin_render.py --lists train_octave_verified train_tuplet_fixed`.

## D27. Bar-rest label audit of the main training data: the typeless-rest bug is not in it (helper, 2026-11-17, 6:30-7:00 pm Pacific; `barrest_audit/REPORT.md`, detector `barrest_audit/detect_barrest.py`)

Question: the pilot found a bar rest without `<type>` written as `rest_8` in 79 of 864 strong crops (D18); is it in the main data? Read-only on vast-homr4 (token files and MusicXML, `nice`, 3 processes, outputs in `/workspace/audit_barrest/`, nothing trained, vast-homr5 not used). **Detector** on token files (bar = lines between barlines; track = position tag; bar length from `timeSignature_*`, else inferred from the staff's other bars, else unknown): flags a primary track that is one `rest_8` in a longer bar, a bar of only rests that does not fill it, and a lone `rest_8` in a bar of unknown length. Validation: 86 of 86 known pilot crops flagged (frozen tokens), 0 of 86 on the fixed tokens, 0 of 100 random and 0 of 785 other strong crops; it also finds 2 hard crops of `pilot_scan_v2.txt` that still have the bug (`A13_p-11_s4`, `A10_p-12_s2`). **Main lists** (`/workspace/run3/B_train.txt` 149,891 staves, `B_val.txt` 7,012): 820 staves (0.55 %) and 891 bars (0.14 %) flagged in training, 29 (0.41 %) in validation, per source 0.02 % (GrandStaff) to 1.4 % (Lieder) of staves; 60 % of the flagged bars are the first bar of the staff, 19 % the last. **They are not the bug:** a regex scan of the source MusicXML of 56,441 scores (all MuseScore 4.6.5 exports) finds 0 typeless rests (the original ASAP XML has them: 138 of 211 files, 4,465 against 70 `measure="yes"`); the XML of 52 of 55 sampled flagged staves shows a typed eighth rest in a pickup bar or a rest in a second voice. Converter paths: MuseScore-XML sets go through `music_xml_parser._process_note` (`measure="yes"` becomes a typed rest of the bar by `_measure_rest_rhythm`; rest_1 where it has no token), the kern sets (GrandStaff, KernScores scan pairs) through `humdrum_kern_parser` (typed kern rest, `2.r` = `rest_2.`); **the model vocabulary has no `measureRest` token** (decoder and writer symbol only). **Impact:** 0 training staves change; the released model reads a single bar-rest token in 170 of 190 pilot label bars that have `rest_8` (`rest_2.` 110, `rest_1` 36, `rest_4.` 24), never `rest_8`; on the 29 saved test-scan pages the writer output has 29 of 227 rest-only staff bars with the wrong length (24 longer, 21 of them one whole rest in a 3/4 bar; 4 shorter; Petrushka's meter changes excluded; 0.23 % of the measures), no effect on pitch scores. Side finding: `rest_1` is written for bar rests in meters without a token (3/2, 9/8, 5/4, 5/8): 592 of 14,878 single-rest bar tracks with a known meter. **Plan, not run** (`REPORT.md`, Task 4): no regeneration of the main sets (expected diff 0 files); put the pilot rule into the parser with tests; fix the 2 pilot hard crops from `work/tuplet/regress_*.tokens`; run the detector and `xml_scan.py` on every new source before building lists; the writer-side measure rest for a lone rest in a known meter is the cheap fix for the `rest_1` residual; a change of the bar-rest convention would need a matched control and is not recommended. Timings on the box: detector over 157,000 token files 20 s, XML scan of 56,000 files about 3 min.

## D24. Where bars disappear on mixed pages: the merger keys parts by writing form, not by staff (helper, 2026-11-17, 6:30-7:15 pm Pacific; code branch `merge-by-staff-role`, worktree `run/merge_wt`; scripts `eval_run1/merge_by_role_eval.py`, `merge_by_role_regress.py`, `merge_by_role_table.py`, `staff_rel_realbrace/trace/`; tables `eval_run1/merge_by_role/table.md`)

Question (professor's step 1): on Etude 5 the shipped model gives 134 bars of 134, realbrace-2 (B0, the model that finds more braces) 62 bars in four parts: where does a system get lost?
**Method.** Replay of every page (laptop, same code as `rel_wt`): staff detection, pair decisions of the four models, `group_staffs`, `repair_systems` (`trace/trace_stages.py`; the replay's layout after the repair (grand staff or two staves per system) equals the box page XML on 33 of 33 pages for the shipped model and realbrace-2, 32 of 33 for realbrace-1, 30 of 33 for realbrace-3: borderline probabilities, laptop CoreML against box fp32 segmentation; the stage tables use the box page XML); the box's page XML (parts, bars, notes per page), the merger's keys, the merged and the final parts (`trace/trace_pipeline.py`, tables `trace/table_*.md`).
**Result: nothing is lost before `merge_pages.py`.** All pages have 10 (Etude 5) staffs for every model; the pair calls of a half-joined page (e.g. G-s-s-G-s) are made uniform by `repair_systems` (it converts the minority systems to the majority layout: 2 staves per system or one grand staff per system), so no page reaches the writer mixed (no log line 'The layout changes on the page'); the writer gives, per page, either ONE part with two staves (`P1-Staff1`, `P1-Staff2` in music21) or two parts called `Voice`. The sum over pages of the bars of the fullest part is the same for every model (Sonata 307/307/306/304, Etude 5 134 x 4, Etude 10 182 x 4 for shipped, realbrace-1, -2, -3): all bars are in the page XML.
**First stage where it goes wrong: `merge_pages.py`, part keys.** The merger matches parts by music21 id (`Voice`, `Voice#2`, `P1-Staff1`, `P1-Staff2`), so the right hand of a page written as a grand staff (`P1-Staff1`) does not continue the right hand of a page written as two `Voice` parts: a score whose pages are written both ways gets four parts. Etude 5 with B0: pages 29, 33, 35, 36 are grand-staff pages (17 + 13 + 16 + 16 = **62 bars**, the first part created, which is the 'measures=' the merger prints), pages 30, 31, 32, 34, 37 are Voice pages (71 / 69 bars, padded to 72): four parts of 62, 62, 72, 72 bars; `drop_minor_parts` keeps all (62 > 50 % of 72); MusicXML positions measures only by their order, so the grand-staff pages' bars are concatenated without the gaps and sit at the wrong times (hands in the same bar 73 %, pitch 43.0). Second failure, same cause: the merger's own minor-part rule drops a part with fewer than 50 % of the bars of the longest, so when one writing form dominates the pages of the other form are dropped whole (merge log 'dropped minor part'): B0 Etude 10 the 27 bars of two Voice pages (155 of 182 bars left), C0 Etude 5 the 42 bars of three Voice pages (92 left), C0 Etude 10 47 bars (135 left), realbrace-1 Etude 5 the one grand-staff page, 16 bars (118 left); realbrace-1 Etude 10 and Sonata stay at 4 parts (121 and 178 bars; `drop_minor_parts` removed one of four parts on Etude 10: 58 of 120 bars). Parts with different bar counts per page in the same writing form (a lost bar inside a page, e.g. 16 against 17) are padded as before and unrelated.
**Fix (merger only, no model or pairing change, no heuristic):** a page which is one stack of k staves (a multi-staff part split by music21 into `P1-Staff1..k`, or k parts with the same id) names its n-th part by the n-th staff from the top (`staff_stack()`, key of the first page with k staves and role n; pages with another k, a single part or an ossia are matched by id as before). Etude 5 B0 is then two parts of 134 bars.
**Results, Schott test scans, saved page XML only, no new transcription** (staff-sensitive / pooled pitch F1, bars out / reference, hands in the same reference bar; old = merger as it was, which reproduces the earlier table to the digit):
| piece | model | old | new |
|---|---|---|---|
| Sonata (305 bars) | shipped | 79.95 / 80.48, 307, 79 % | identical |
| | realbrace-1 / -2 (B0) / -3 (C0) | 44.5 / n.a., 4 parts 178 / 61.5 / n.a., 4 parts 183 / 59.9 / n.a., 4 parts 188 | 86.15 / 86.55, 307, 86 % / 86.67 / 87.04, 306, 93 % / 87.75 / 88.15, 304, 96 % |
| Etude 5 (134) | shipped | 77.04 / 77.86, 134, 72 % | identical |
| | realbrace-1 / -2 / -3 | 71.0 / 71.9, 118 / 43.0 / n.a., 62 x 4 parts / 67.0 / 67.1, 92 | 75.53 / 76.34, 134, 70 % / 79.25 / 79.39, 134, 88 % / 80.07 / 80.23, 134, 90 % |
| Etude 10 (182) | shipped | 76.90 / 77.62, 182, 70 % | identical |
| | realbrace-1 / -2 / -3 | 62.0 / n.a., 121 x 4 parts / 79.9 / 80.0, 155 / 73.7 / 73.8, 135 | 83.00 / 83.65, 182, 85 % / 90.14 / 90.31, 182, 96 % / 87.65 / 87.79, 182, 92 % |
With the fix every new model is at or above the shipped model on all three pieces except realbrace-1 on Etude 5 (-1.5) (best: B0 on Etude 10 +13.2, C0 on Sonata +7.8, C0 on Etude 5 +3.0), and the hands stay in the same bars as well as or better than with the shipped model (shipped 70-79 %, new 85-96 %, except realbrace-1 Etude 5 70 % against 72 %). **This reverses the D14 conclusion that partial recognition is worse than none: that came from the merger.** What is not shown: the new models on any non-Schott piece through the pipeline (D14 changed pair decisions only on Petrushka, 3-4 staves under one brace, grand pair moves from staves 0-1 to 1-2 on 25 of 37 pages: needs a pipeline score), the recipes were tried after seeing these scans (realbrace-1, -2, -3), the merger rule was written after seeing these outputs. The Schott pieces stay test data.
**Regression** (`merge_by_role_regress.py`, result `eval_run1/merge_by_role/regress.tsv`): 220 saved page sets (tags layout1 with the rendered twins, 566, run2s7, r3ctrl_s7, r3cand_s7, res_A_s7_gpu = the 26 other scan sets and rendered twins, plus relctl, relbrace, relB0, relC0, schottfix, mergefix) re-merged with the old and the new merger and dropped with `drop_minor_parts`; final MusicXML compared with the random part ids normalised: **210 identical (same parts, bars and notes, byte for byte after normalising), 10 different: the 9 sets of realbrace-1/-2/-3 on the three Schott pieces and the old `schottfix` Sonata (a reverted pairing rule with mixed pages; 271 to 304 bars)**. No page set of the 25 other scans changes under the shipped or earlier models. (An earlier first version of the fix, which also mixed pages with a different number of staves per system, changed rendered Petrushka; it was replaced by the per-k keys before this run.) Not run: tags r3ctrl_s11, r3cand_s11, res_A_s11 (same merger path, other seeds). Commit `5f2b4f7` on branch `merge-by-staff-role` of the research repo (worktree `run/merge_wt`, sparse), not merged; `run/merge_pages.py` itself is unchanged.

## D25. What the staff-pairing classifier gets of the Schott brace (helper, 2026-11-17, 6:45-7:20 pm Pacific; `staff_rel_realbrace/INPUT_INSPECTION.md`, figures in `staff_rel_realbrace/input_inspection/`)

Question (professor's step 3): does the 96 x 96 crop (4 px/unit, 10 units margin, 5 channels, no brace layer) lose the thin straight brace?
Method: crops of the 13 printed systems of the three opening pages, 5 pairs of two working scans and 16 grand pairs of the held-out Reichardt volume, rebuilt as `page_inputs` does, next to the native-resolution margin, the five channels and the probabilities of the shipped model and rb1-3; the brace peak over the gap rows at 4, 8 and 12 px/unit.
Result: **the brace survives.** Schott, 13 systems: gray-ink peak 0.74 (min 0.62) at 4 px/unit, 0.86 at 8, 0.88 at 12; symbols channel 0.53, 0.76, 0.82; the working scans 0.50 / 0.52 at 4. The brace is in the gray-ink and symbols channels only. The difference is its shape in the *symbols* channel (segmentation has no brace class): one continuous wavy curve over both staves on the working scans (tallest connected structure 0.73 of the crop height), a thin straight line broken at the point on Schott (0.38: it looks like the start of each staff). The shipped model calls all 13 'same system' (mean p(same) 0.99); diagnostic on its crops: copying the gray line into the symbols channel changes nothing, erasing the symbols margin moves 3 of 13 to grand staff and leaves the 5 working pairs grand. Reichardt: a heavy double line runs through the three staves, the small brace of the piano lies inside it; the margin line is as strong on the voice/piano 'same system' pairs (gray peak 0.64, symbols 0.69) as on the grand pairs (0.56, 0.53), the shipped, A0 s0 and B s0 models miss the same 13 of 16 sampled grand pairs (labels by chain position, 4 of 16 crops with a weak line: qualitative).
No higher-resolution crop was trained: the resize does not remove the brace, the problem is what the symbols channel shows, and it would need new crops of every training page. Recommendation: train the same CNN on broader real examples first (thin straight braces with a point and no connecting line, other Schott etudes), and check the segmentation net's symbols output for the break at the point; a cheap ablation on the stored crops (symbols channel zeroed) shows whether the model needs that channel. No training, no GPU job, vast-homr4 and vast-homr5 untouched.

**D27 follow-up (2026-11-17, about 7:20 pm Pacific): the two pilot hard crops fixed.** `A13_p-11_s4` and `A10_p-12_s2` now take `scan_pairs_virtuoso/tokens_typeless_rest_fixed/<name>.tokens` (copies of `work/tuplet/regress_*.tokens`; they differ from the frozen tokens only in rest tokens; originals in `tokens/` kept) in `lists/pilot_scan_v2.txt`, `lists/pilot_twin_render_v2.txt` and `lists/box/*_v2.txt` (old lists kept as `*.before_D27`). The twin images show the bar rests as bar rests. Detector on the four v2 lists (laptop and box copies): 0 flagged of 881 / 881 / 72 / 72. Token files hashed pair by pair, scan list against twin list: 0 differences in 953 pairs. Box: only `/workspace/pilot/tokens_typeless_rest_fixed/` (2 files) and `/workspace/pilot/lists/` (4 lists) written, all list paths exist, counts 881 / 881 / 72 / 72; no training touched.

## D26. Collection of real thin-brace examples: the Schott series, 46 screened editions, labels and splits (helper, 2026-11-17, 6:30-7:30 pm Pacific; `brace_collection/README.md`, `downloads.md`, `split.tsv`, `table_raw.txt`)

Question (professor's step 2): collect real examples of the thin, nearly straight brace of the Schott scans of Liszt's Transcendental Etudes 5 and 10 and the Sonata (test pieces), for training and testing the staff-pairing CNN; reserve a different thin-brace edition for a transfer test.
Identification: the Etudes volume is IMSLP #964191, Schott, Mainz 1917, plate 30341, ed. August Schmid-Lindner, 121 pp. (TE 5 = pdf pp. 29-37, TE 10 = pp. 76-85, the other ten pieces in the same volume); the Sonata is IMSLP #364674, Schott 1917, plate 30373, same editor (Sibley Mirroring Project scans). Same series on IMSLP: Concert-Etudes S.144 (#04424, 1918), Piano Concertos 1 and 2 for two pianos (#977987, #977999, 1918); the Schott 1913 Schubert Impromptus (#936502) is another engraving with a curved brace.
Method: 49 PDFs (175 MB, `downloads.md`) downloaded through Brave (owner-authorised), 3 of the Schott series and 46 independent editions of 1800-1987 chosen from IMSLP pages (Liszt, Beethoven, Chopin, Schumann, Brahms, Mendelssohn, Schubert, Lyapunov, Berg ...); pages rendered at 150 dpi, staff detection and crops with the code of `staff_rel_realbrace/scripts/extract_pairs.py` (worktree `run/rel_wt`), labels from the page structure with the barline check of `label_pairs.py` (plus a gap check for pages without a barline in some gap; k = 4 for the two-piano scores), decisions of the shipped relation model per pair (`brace_collection/analyze.py`). 135 labelled crops of the Schott pool, concertos, Concert-Etudes and Cappi 1802 looked at one by one: 0 wrong labels (`figures/labelcheck_*.png`).
Result: **Schott series (same brace, other compositions than the test pieces)**: Etudes volume, 86 pages (78 labelled), 394 grand pairs, **392 missed by the shipped model**, 0 false joins; Concert-Etudes 15 of 15 missed (3 labelled pages); Concerto 1 68 of 214 (36 of 44 pages labelled, braces marked I and II), Concerto 2 68 of 282 (47 of 54). Train-candidate total: 194 pages, 164 labelled, 905 grand pairs. Reserved: the Mazeppa pages of the volume (Etude 4, test composition; 13 pages, 43 grand pairs, 43 missed), the three test scans, Reichardt 1819. **Independent editions**: 37 editions with a curved (thin to medium) brace and a connecting barline, 292 pages sampled, 250 labelled, 1,332 grand pairs, 2 missed, 1 false grand, 2 false joins: not hard, negative controls. The only other failing edition is **Beethoven Op. 27/2, Cappi, Vienna 1802** (#15808): a straight line with short hooks (square bracket), no separate connecting line; 10 of 16 pages labelled, 46 grand pairs, 40 missed, 10 false joins (binding shadow); weak grey scan. Eder 1800 Op. 13 fails 7 of 9 on 2 labelled pages (of 21). Seven early or blurred files (1800-1822) give no usable staffs. No second thin straight brace with a point exists in the public IMSLP scans looked at.
Split (`split.tsv`): train candidates = the four Schott groups above; reserved/test only = test scans, Mazeppa pages, Cappi 1802, Eder 1800, Reichardt; negative controls = the 37 curved editions (must stay at 100 %). Same-edition caveat: the Schott pool shares the scanner and page geometry with the test scans, so a model trained on it shows that the brace can be learned from real examples, not that it generalises; hold out whole pieces, not pages (suggested: train Etudes 1-3, 6-9 and the concertos, validate on 11, 12 and the Konzert-Etueden). Limits: 6-12 sampled pages per edition, style read from rendered crops, two non-public-domain files (Henle 1987, Salabert 1949; negative controls only). No training, no GPU box, vast-homr4 and vast-homr5 untouched; the La Campanella single edition (#930921) went through a Petrucci Library Canada terms page, its "I understand" click was not made, the file is not used.

## D29. Automation of the pilot evaluation (four models) and the final-table tooling (helper, 2026-11-17, 7:20-8:15 pm Pacific; `eval_run1/pilot_auto.sh`, `eval_run1/pilot_auto_scripts/`, `eval_run1/pilot_final_table.py`)

Question: evaluate each of the four pilot models (`pilot_CTRL_RENDER_s7`, `pilot_SCAN_s7`, `pilot_CTRL_RENDER_s11`, `pilot_SCAN_s11`, RES=1, 256x1280, chain `/workspace/pilot/scripts/chain_pilot.sh` started 7:21 pm) as soon as it is trained, without touching the chain.
What runs: `nohup caffeinate -i bash run/eval_run1/pilot_auto.sh` on the laptop (log `eval_run1/pilot_auto.log`, Pacific time; stdout `pilot_auto.out`; state markers `eval_run1/pilot_auto_state/`, finished steps are skipped on a restart; every step retried 3 times, a failed step is logged as FAILED and the script goes on to the next model). Per model, when `<NAME> DONE` is in `/workspace/logs/pilot/status.log` on vast-homr4:
1. **Export** on vast-homr4, tmux `pexp_<NAME>`, `/workspace/pilot_auto/pilot_export.sh` (CPU only, `CUDA_VISIBLE_DEVICES=""`, `nice -n 10`, idle I/O class, 2 threads, refuses below 1.5 GB free; code = `git archive HEAD` of `/workspace/homr_acc` in `/workspace/export_<NAME>`, the weights only symlinked, work dir removed afterwards; result `/workspace/onnx/<NAME>/`, 4 files, about 220 MB, removed only if the box has under 2.5 GB free and the copies are verified). Recipe = the run3 `export_run.sh` (the `homr_acc` Config has a fixed model name and ignores `HOMR_MODEL_NAME`; that variable is for inference in `res_wt`). Test: exporting the `run3_ctrl_s7` weights this way took 30 s and gives the four ONNX files **byte-identical** (sha256) to `/workspace/onnx/run3_ctrl_s7`; the script also checks the four sizes against run3_ctrl_s7. No remote command line contains the training script's name (the chain waits with `pgrep -f` on it).
2. **Copy** to vast-homr5 through the laptop (`cloud2_models.sh <NAME> /workspace/onnx/<NAME>`, `LAPTOP_COPY=1`: also `run/models/<NAME>/` on the laptop); file sizes compared on box 4, box 5 and the laptop.
3. **Wait for vast-homr5 to be idle** (no python/pdftoppm/ffmpeg/rsvg process of anybody else, three readings 20 s apart, at least 14 GB available; the other agent's `brace_eval`/replays were running at preparation time), a marker `/root/logs/pilot_auto.busy` while a job of the automation runs.
4. **Held-out read** (tmux `pilot_val_<NAME>`, `eval_run1/pilot_val_box.sh`, GPU path, `pilot_val_eval.py`): the 72 v2 validation passages as scan and rendered twin, and the independent 145-crop extension `batch2_val_v2` as scan, plus (new) its rendered twins and the scan crops of the same 134 crops. Results `eval_run1/pilot_val/<NAME>/{val_scan_v2,val_twin_v2,b2_scan,b2_scan_matched,b2_twin}.json` (laptop and box 5). Baselines read once with the same script: `released` (integration_wt), `run3_ctrl_s7`, `run3_ctrl_s11`.
5. **28-scan GPU evaluation** (tmux `pilot_eval_<NAME>`, `eval_run1/pilot_eval_box.sh` -> `res_eval.py --tag <NAME>_gpu --model <NAME> --scale 1`, tags `pilot_CTRL_RENDER_s7_gpu`, `pilot_SCAN_s7_gpu`, `pilot_CTRL_RENDER_s11_gpu`, `pilot_SCAN_s11_gpu`; `start`/`end ... exit=` lines in `/root/logs/gpu_chain.status` in the earlier format; a pass with FAILED pieces is repeated up to 3 times), then `cloud2_pull_min.sh <tag>` to the laptop (`out/testset/<piece>/...-<tag>...`, `out/testset/RES-<tag>.md`).
**Dry run** (7:31-7:55 pm, model `dry_s7` = the run3_ctrl_s7 weights, one piece, cleaned up afterwards): export, copy with size check, held-out read and a one-piece evaluation (Bach fugue 873: 99.65 / 96.54 / 95.99, identical to `res_A_s7_gpu`) all went through without a retry; the held-out numbers of the exported copy equal those of `run3_ctrl_s7` (same weights, deterministic). Held-out read of one model takes about 9 min on the shared box 5 (about 4 min on an idle one).
Twins of the extension: new option `twin_render.py --batch2 batch2/lists/batch2_val_v2.txt` (own manifest and piece table): 134 of 145 rendered (`batch2/twins/`, `batch2/twins_report.json`), 11 dropped (9 octave-bracket mismatch, 2 touching notes); lists `batch2/lists/batch2_val_v2_twin.txt` and `batch2_val_v2_scan_matched.txt`. Evaluation data only, never trained on.
Box 5 got 645 files (24 MB: validation crops, token files, lists, the three scripts and `pilot_val_eval.py`) via tar; the box-5 scripts are in `eval_run1/` there.
**Expected times** (training 1.84 it/s, about 65-70 min per run incl. evaluations): DONE about 8:30 pm, 9:40 pm, 10:50 pm and 12:00 am; per model export 1 min, copy 3 min, held-out read 4 min, evaluation 25-45 min if the box is free (longer if the other agent's jobs hold it). All four evaluations should be finished by about 1 am Pacific; results appear as the tags above and `pilot_val/`.
**Final table (prepared, not run):** `python eval_run1/pilot_final_table.py` (laptop venv python) -> `out/testset/PILOT-final-table-<date>.md`: per seed SCAN - CTRL_RENDER on the 28 scans (staff-sensitive and pooled pitch, +onset, full, pieces at 97 pooled / staff-sensitive / on every staff, per-piece paired differences, sign test, dense-bar recall, regressions of 1 point or more, edition-corrected references, imports `res_final_table.py`), the run3 controls and the released model as context, the seed spread, and the held-out lists by work (pitch and pitch+rhythm, both seeds, spread, per-crop paired difference with bootstrap interval). Machinery tested with the resolution tags (`--ctrl7 res_A_s7_gpu ... --name TEST --no-heldout`; reproduces 0.70 mean absolute seed difference of the controls). One run per arm and seed: the table says plainly when a difference is inside the seed spread.


## D30. Staff-pairing CNN trained on real thin-brace pages of the Schott series: same-edition experiment (helper, 2026-11-17, 7:27-8:20 pm Pacific; `staff_rel_realbrace/SAME_EDITION.md`; scripts `staff_rel_realbrace/scripts/{build_mixture2,finetune2,eval2,vary_braces_schott,pairing_changes,table_d30,merge_score_d30}.py`, `pipeline_arm2.sh`, `chain_d30.sh`, `collect_d30.sh`, `train_arms2.sh`; models `staff_rel_realbrace/realbrace2-<arm>-s<seed>.onnx`; tables `staff_rel_realbrace/d30/tables.md`, `d30/pairing_changes.md`)

Question (plan, 'In parallel' item 2): can the same CNN (5 x 96 x 96 input, not changed) learn the thin Schott brace from real pages of the same series, on pieces it never saw, and does that carry over to other editions? Data: first-round mixture (real piano 2,418, songs 1,450, rendered 9,419, variations 2,978) without Reichardt (transfer test now); + 17 curved-brace training editions (13 works, 1,115 pairs, all arms; 22 other editions, 1,317 pairs, held out by work; Henle 1987, Salabert 1949 and editions of test compositions never trained on); + real Schott pairs (arms B, C): volume pieces I, II, III, VI, VII, VIII, IX and Piano Concertos 1 and 2 (127 pages, 1,305 pairs: 341 separate, 248 same system, 716 grand), validation = pieces XI, XII, Waldesrauschen, Gnomenreigen and the Concert-Etudes S.144 file (37 pages, 341 pairs); never used: Mazeppa pages, TE 5, TE 10, Sonata, Cappi 1802, Eder 1800, Reichardt. Arms (A control = realbrace-2 recipe + curved; B = A + real Schott; C = B + 2,978 pairs of Schott-guided variations), seeds 0 and 1, fixed budget 12 x 150 x 64, AdamW lr 1e-4 one-cycle from the shipped weights, laptop MPS (3 min per run), no selection. Variation generator check: measured the real brace on the pool (stroke 0.2-0.5 unit, point depth up to about 1 unit, hooks, no connecting line); the first-round generator drew bows (not a point) with thickness 0.25-1.1 and depth 0.5-2.2 units, the Schott corner was rarely reached; `vary_braces_schott.py` draws 70 % point-shaped braces (thickness 0.14-0.4, depth 0.7-1.4), 30 % narrowed bows, distance 0.1-0.6 unit, connecting line removed in 60 %.
Result (pairing, missed grand / false grand / separate joined, seed 0 | 1): **Mazeppa pages (reserved, 43 grand) shipped 43/0/0, A 32/0/0 | 27/0/0, B 0/0/0 | 0/0/0, C 0/0/0 | 0/0/0; held-out Schott pieces (189 grand) shipped 187, A 102 | 76, B 0 | 0, C 0 | 0; the 3 Schott test scans, grand calls among 169 within-system pairs (same edition, NOT transfer): shipped 1, A 71 | 98, B 169 | 169, C 169 | 169 (opening pages 0, 4 | 7, 13 | 13, 13 | 13; separate pairs kept 136 of 136 for all).** Held-out curved editions (720 grand): shipped 3/0/2, A 1/1/1 | 1/1/1, B 2/0/0 | 1/1/1, C 1/0/0 | 1/0/1. Transfer (weak, and more false joins): Cappi 1802 (46 grand) shipped 40/0/10, A 12/0/12 | 11/1/12, B 15/0/15 | 9/0/16, C 12/1/13 | 13/0/15; Eder 1800 (9) shipped 7/0/3, B 1/0/2 | 1/0/2, C 1/0/2 | 1/0/4; Reichardt (56) shipped 53/0/6, A 53/0/9 | 52/0/9, B 35/0/11 | 35/1/13, C 34/0/13 | 43/0/16.
Full pipeline (box GPU, tags `relbrace2_<arm>_s<seed>_gpu`, control `relbrace2_ctl_gpu` on the same pipeline; merger by staff role, merge on the laptop; staff-sensitive / pooled pitch F1, bars, hands in the same bar): Sonata control 80.0 / 80.5, 307 bars, 79 %; A 87.0 / 87.4 | 87.9 / 88.3, 93 %; B = C (both seeds identical) **88.9 / 89.3**, 304 bars, 98 %. Etude 5 control 77.2 / 78.0, 71 %; A 81.1 | 79.4; B = C **81.6 / 81.6**, 132 bars, 95 %. Etude 10 control 77.3 / 77.9, 181 bars, 67 %; A 89.4 | 91.1; B = C **93.8 / 93.9**, 182 bars, 100 %. Mean of the three (staff-sensitive): control 78.1, A 85.8 | 86.1, B = C 88.1 (+10.0 over control, +2.3 / +2.0 over A). Mazeppa (provisional reference: hand transcription of another scan, 202 bars): control 73.0 / 77.0, 212 bars, 76 %; A 76.4 | 76.3 with parts of 224 and 209 bars (4 %); B = C 82.2 / 82.6, 190 bars, 99 %.
Regression (relation model only on the saved crops of the 26 non-Schott scan sets, 2,905 pairs): B s0 / s1 change 9 / 9 pairs on 7 / 6 pages, C 10 / 8 on 7 / 7, A 9 / 10 on 7: all on Stravinsky Petrushka (p. 2, 8, 12, 32, 33, 34, 35; same pages as realbrace-1, -2, -3), no pair of the 25 other scan sets changes.
Conclusions: the real thin-brace pages (B) fix the pairing of the Schott edition on pieces never trained on (Mazeppa 43 of 43, held-out pieces 189 of 189, test scans 169 of 169) and give +10.0 pitch points on the three scans and +9.2 on Mazeppa over the shipped control through the pipeline; A (no Schott pages) with the merger fix already gives +7.7 / +8.0; **Schott-guided variations (C) add nothing to B**. The three test scans share the engraving and the scanning series with the training pages, so they and Mazeppa show same-edition learning; the held-out evidence for other editions is the curved editions (no regression, but already 99.6 % before) and the transfer sets, where B / C call more grand staffs but also join more separate pairs (Cappi false joins 10 -> 12-16 of 36, Reichardt 6 -> 9-16 of 41): weak, no second public thin-brace edition exists. Open: Petrushka pipeline score; a library scan of another Schott or Peters volume as a real transfer test; a Schott-checked Mazeppa reference; the box was shared (pipeline runs one at a time, 7 runs of 4 pieces, GPU path confirmed in every log); vast-homr4 untouched, nothing pushed.

## D28. Candidate brace models through the full page pipeline on the 28 real scans, common merger (helper, 2026-11-17, 7:20-9:20 pm Pacific; `eval_run1/brace_models_25scans.md`, tables `eval_run1/brace_models/`; vast-homr5 GPU; code `rel_wt` branch `staff-relations-real`, merger `merge_wt` branch `merge-by-staff-role`)

Question (PLAN, "validate grand-staff pairing and page assembly", item 1): what do the retrained pairing models do on the other 25 scans, and what is left after the merger fix?
Method: `eval_run1/brace_eval.py` (res_eval-style, GPU, released transcription weights, loop guard, fixed margin, merger by staff role, scorer with visible notes and edition-corrected references, `hand_sync.py`), tags `shipped_merge_role_gpu` (control), `relbrace2_gpu`, `relbrace3_gpu`, 28 pieces each, 20-26 min each. Pair decisions of the three models on all 302 pages from one segmentation per page (`pair_replay.py`, `pair_diff.py`; matches the real-run log counts in 81 of 84 cases), eye review of 13 pages, note-error audit (`pitch_audit_brace.py`, `brace_audit_summary.py`).
Results. **Nothing changes on the 24 pieces other than the three Schott scans and Petrushka**: identical pair decisions on 232 of 232 pages, identical final MusicXML (23 of 24 for rb3: one note on one page of Hammerklavier, GPU noise), same scores. Schott pooled pitch (Sonata / Etude 5 / Etude 10): control 80.5 / 78.0 / 77.9, rb2 86.9 / 79.5 / 91.2, rb3 88.3 / 79.5 / 88.7; hands in the same bar 79 / 71 / 67 % -> 93 / 88 / 95 (rb2), 96 / 92 / 91 (rb3); no between-system pair is ever joined (136 of 136). **Petrushka regresses with both**: control 79.2 pooled (598 bars, 12,448 of 15,483 reference notes, third staff dropped as a minor part), rb2 44.8 (five parts, 475 / 390 / 390 / 286 / 286 bars), rb3 58.8 (three parts, 516 / 499 / 499; the seven two-staff pages dropped as a minor part). Cause: the new models pair staves 1-2 of three-staff systems (81 of 81 for rb3, 71 for rb2; shipped 69 times 0-1), so the three-staff pages are `[single, grand]` instead of `[grand, single]` and no longer share part ids with the two-staff pages; the merger matches non-uniform pages by id. Page XML is complete (15,158-15,342 notes of 15,483). Means pooled 28: 91.94 / 91.46 / 91.92; without Petrushka 92.41 / 93.19 / 93.15.
Eye review (13 pages): 8 improvements, 1 partial, 3 layout changes without clear verdict, 1 wrong (Petrushka p. 35 system 1: the top two staves are one hand, the new models pair 1-2); correct pairing in Petrushka: one system per brace, pairs by hand (`s+G`, `G+s`, `G+G` for four staves), not expressible as one grand staff.
Remaining errors (rb3, 27 pieces, 8.53 F1 points staff-sensitive): octave 3.02, lost bars 1.14 (52 of 6,031), accidental 1.02, extra 0.76, wrong staff 0.75, dropped events 0.54, missing chord members 0.51; repeated-note runs hold 7 % of the missed notes (0.07 points); on the nine pieces with equal bars and aligned hands 4.35 points (accidental 0.86, octave 0.74, chord members 0.70).
Regressions: Petrushka (both), Etude 5 with rb3 one bar short (133 of 134, pooled +1.5); no other piece. Not adopted: candidates chosen after seeing the Schott pieces; held-out edition test still needed (`brace_collection/`, D30). Open: a merger rule for mixed three- and two-staff pages (no heuristic added). vast-homr4 untouched, nothing pushed, box tmux sessions finished.

## D32. Where the octave errors come from: five causes on development crops and on the real scans (helper, 2026-11-17, 9:26-9:55 pm Pacific; `octave_checks/OCTAVE_CAUSES.md`, scripts and data `octave_checks/octave_causes_*.py|csv|json`, `eye_verdicts.csv`, figures `octave_checks/causes/`)

Question (advisor, before choosing the next training mix): how many octave errors come from (a) missed starts, (b) missed or wrong stops, (c) bracket continuations across system or page breaks, (d) wrong register with no bracket, (e) edition or reference differences? Different fixes. Laptop only, existing outputs only (no model run, no GPU, vast-homr4/5 untouched), nothing pushed, nothing fed back into training lists.
Method: `octave_causes_crops.py` reads, for all 2,153 pilot and batch-2 crops, the original label tokens and the released model's stored read, aligns notes per staff and time slice (chord order ignored), computes written and sounding octave differences and bracket states, classifies every affected note and crop (rules in the md; continuation = label bracket open at the crop start by the previous system's label, or open at the crop end); 1,840 crops analysed (labels reliable, letter F1 >= 0.8), validation groups kept apart. By eye: 51 stratified random crops (crop, Verovio label engraving, full page; `make_eye_sheets.py`), neighbouring system checked for continuations. Real scans: `octave_causes_realscans.py` reproduces the audit's 3,557 octave events (3.02 points, relbrace3_gpu) and gives each the exact reference and read bracket state, print system breaks (from the read file's `new-system`) and the bar's bracket profile.
Results. Dev crops: 740 of 1,840 crops (40 %) have an octave or bracket difference (pilot val 45 %, batch-2 val 41 %). By crop: (a) 81, (b) 73, (c) 34, (d) 455, (e) 94, mixed 3; by affected notes 1,964 / 890 / 762 / 2,323 / 1,542 (same sound under another notation) / 60. Eye agreement with the automatic class 41 of 50 = 82 % (calibrated crops about 55 / 75 / 51 / 417 / 142). The model reads a bracket span right in 72-82 % of cases, its start in 75-87 %, **its stop only in 60 %** (74 of 120 stop failures: the bracket never closes); register errors are 4 times more frequent on notes with 4+ ledger lines (67 vs 17 per 1,000) and 1.7 times in crops with a clef change. Real scans (27 pieces, 3.02 points): (d) 1.40 (46 %), (c) 0.58 (19 %), (a) 0.49 (16 %), mixed 0.39 (13 %), read-only bracket 0.11 (4 %), (b) 0.04; bracket-related in all 1.62 (54 %). Eye on the print: Winter Wind bars 85-86 are (c) (8va runs on from the previous system, read has none), Hammerklavier mvt 4 (21 events) and Wanderer (16) are (e) (print has 8va, reference none), Scriabin Sonata 5 read-only brackets (50) are spurious, a Reflets register bar is a clef-change error, a Scriabin register bar is a reference register difference; five large (d) bars could not be decided from the 150 dpi bands. Top pieces: TE5 12.6 (register 34 %, starts + continuations 49 %), Ravel Alborada 11.0 (register 52 %), Winter Wind 7.8 (continuations 38 %), Liszt Sonata 6.1 (register 42 %), Paganini 6 5.6 (continuations 41 %), Reflets 5.4, Scherzo 3 5.1, TE10 4.2.
Gap in the verified pool (training lists, 1,509 crops): starts inside 190 crops (259 spans), stops 188 (254), continuation from the previous system 66, into the next 72, middle systems 22, lower-staff spans 18, no bracket 1,268, 4+ ledger lines 366, clef change 480, hard negatives 26; validation groups hold 54 / 51 / 32 / 35 / 24 of the same. Recommendation: more multi-system continuations with the stop, stop variety, 8vb, ledger-line passages without brackets; no unreviewed ASAP labels (a label differs from the print in 33 of 60 pilot and 43 of 50 batch-2 octave crops); fix evaluation references (Hammerklavier, Wanderer) instead of training. Bounds in real-scan points: (c) 0.58, (a) 0.49, (b) 0.04, (d) 1.40 (upper bound, part is reference), (e) 0.11, mixed 0.39. Caveats: stratified eye sample (n = 50), (d) on the real scans not split between model and reference.

## D33. Reference hygiene for octave brackets: the suspect pieces are model errors, not reference gaps; one shared list of edition-corrected pieces (helper, 2026-11-17, about 10:10 pm Pacific; `octave_checks/REFS_REPORT.md`, scripts `octave_checks/{refs_lib,bar_octave_diff,notes_dump,locate,view,crop_render2,make_refs_evidence,rescore_edition}.py`, figures `octave_checks/refs/`, shared list `eval_run1/edition_refs.py`, rescored files `octave_checks/edition_scores/`)
Question. D32 named Hammerklavier (reference has no octave-shift, output 14) and Wanderer (orphan stops) as reference gaps of the Schubert D. 899/4 type, and listed orphan stops in Liszt HR 6 (15), Debussy Pour le piano (4), Petrushka (3), an unexplained shift in Kreisleriana and spurious brackets in Scriabin Sonata 5. For each: does the print have an 8va/8vb the reference lacks (write an edition-specific reference), do the editions differ, or did the model err?
Method. Per piece `bar_octave_diff.py` flags the bars where moving the upper (or lower) staff of the released output (`layout1`) by an octave gains 3+ pitch matches against the reference (pooled alignment); each flagged cluster was located on the scan (page XML systems, `locate.py`), the reference and the output engraved with Verovio (`crop_render2.py`, grand staff kept) and compared with the print by eye. Laptop only, no training, no model run; the references and scans are evaluation data.
Results. 12 decisions with side-by-side figures (`octave_checks/refs/`: Hammerklavier 246-249, 365-368, 402-406; Wanderer 114-118, 438-444, 471-476; HR 6 35-42; Debussy 44-52; Kreisleriana 1-4; Scriabin 297-306, 305-314, 322-333) plus 3 more by page view: **all are (c) model errors** (stops too late or never closed, stops one bar early, a bracket not read, a note misread under a glissando 8va, invented 8vb/8va); **no case (a) or (b)**. In Hammerklavier, Wanderer, HR 6, Debussy and Scriabin the reference holds the sounding pitch under every printed bracket that was checked; it lacks only the directions (none in Hammerklavier, orphan stops 14 / 15 / 4). The orphan stops checked on the print (Wanderer 94, 472, 474, 439, 446; Debussy 50, 51) all have the sounding pitch under the lost start, so they are pitch-neutral and a better model is not penalised. D32's (e) verdicts for Hammerklavier bar 247 and Wanderer bars 473-474 are corrected to model errors (the 8va of the print is shorter than the model's). Undecided and left: Wanderer 423-424 (tremolo, bar alignment slip), the ossia pages of HR 6, Petrushka (3 reference staves against 2, 627 against 598 bars); not viewed: Debussy 141-142, Scriabin 1-4 (LH), 279-280, 350-351, 430-432. Limit: only bars where output and reference differ by an octave are flagged, a bracket missing from both would not show.
Rescoring. No new edition reference, so the 28-piece numbers do not change; the edition list is now one place (`eval_run1/edition_refs.py`, imported by `res_final_table.py`, `after_merger_tables_octave.py`, `brace_eval.py`, `merge_tracking_eval.py`, `pitch_audit_brace.py`, `brace_audit_summary.py`, `pilot_final_table.py`) and `octave_checks/rescore_edition.py` rescored all 23 saved Schubert tags against the edition reference (staff-sensitive and pooled; 10 new: pilot_CTRL_RENDER_s7_gpu, ctl_slots[_nodrop], rb2/rb3_slots[_nodrop], relbrace2/3_gpu, shipped_merge_role_gpu; later tags: run it again). New tables `RES-FINAL-table-2026-11-17-edition2.md`, `POOLED-...-after-merger-octave-edition2.md`, `CORRECTED-...-edition2.md` equal the `-edition` ones (diff checked). Effect of the Schubert correction on the 28-piece pooled mean (original reference to edition): released 91.90 to 91.99 (pieces at 97: 5 to 6), res_A_s7 91.70 to 91.79 (5 to 6), res_A_s11 91.83 to 91.92 (7 to 8), res_B_s7 91.83 to 91.92 (6 to 7), res_B_s11 91.87 to 91.96 (7 to 8); worst piece unchanged (liszt-te-5 77.8 for the released model).

## D31. Part tracking across pages in the merger: one fixed list of staff slots (helper, 2026-11-17, 9:35-11:15 pm Pacific; `eval_run1/merge_tracking.md`, scripts `eval_run1/merge_tracking_{diagnose,eval,table,regress}.py`, tables and logs `eval_run1/merge_tracking/`; code `run/merge2_wt`, new branch `merge-staff-slots` from `merge-by-staff-role`: `merge_pages.py` sha256 16 `f1e4a7260a1e846b`, `slot_tracking.py` `65ff6dcde8ffb813`, `tests/test_slot_tracking.py`)

Question (advisor, "layout blocks release"): fix how the merger tracks the parts of a piece across pages (Petrushka moves between 2, 3 and 4 staves per system; the retrained pairing models fall to five parts of 286-475 bars or three of 499-516 against 627), then rerun the whole piece before any default changes. No transcription: the saved page XML of D28 (`shipped_merge_role_gpu`, `relbrace2_gpu`, `relbrace3_gpu`) re-merged on the laptop; nothing adopted, no default changed, nothing pushed, vast-homr4 untouched.
Diagnosis (`merge_tracking/diagnose_stravinsky-petrushka.md`, 37 pages x 3 runs): staves per system 2, 3 or 4 on the same pages for all models (largest system 3 staves on 30 pages, 2 on 5, 4 on 2; 21 of 37 pages mix system sizes); the writer fills a hidden staff of a smaller system with rests and which staff is hidden depends on the pairing (`G+s` hides the bottom staff of a two-staff system, `s+G` the top one); 3 / 4 / 2 pages (control / rb2 / rb3) are read as one long voice (`The layout changes on the page`). The D24 merger names the parts of a page by role only for a uniform stack, so `[grand, single]` and `[single, grand]` pages share no part with each other or with the two-staff pages: five keys in every run (`P1-Staff1/2`, `Voice`, `P2-Staff1/2`).
Rule: one ordered list of staff slots per piece; a page with as many staves as established slots (given a staff by at least half of the pages so far) continues them by position, otherwise order-preserving match by register (median pitch), clef and place in the stack, surplus staves open new slots in place, absent slots get rests for the page's bars, a late slot gets rests for the earlier bars, the merger's minor-part rule counts real staves; constants fixed a priori (12 semitones for another clef, 1 per place, 8 notes). 18 tests on synthetic 2/3/4-staff and half-paired page sets (the D24 merger fails four of them). Faults found by the identity regression and corrected before the scores were read: slot proliferation (Islamey page of two grand pairs), a spurious three-staff page splitting the bass (`liszt-te-4-schott`), an unwritable bar now reaching a main part (blanked after five repair attempts).
Result (pooled / staff-sensitive pitch F1, D24 -> slots): **Petrushka** control 79.2 / 58.6 (598x2) -> 84.1 / 71.8 (647x3), rb2 44.8* / 44.8* (475/390/390/286/286) -> 80.7 / 63.1 (676x3), rb3 58.8* / 58.8* (516/499/499) -> 82.2 / 61.9 (661x3), reference 627 bars, three staves, unchecked (scorer: three slots compared staff to staff, two parts remapped bar by bar to the nearest mean pitch, unequal parts per staff; the Petrushka columns are provisional). **28 scans, mean pooled** 91.94 -> 92.20 (control), 91.46 -> 92.83 (rb2), 91.92 -> 92.85 (rb3); staff-sensitive 90.21 -> 90.66, 90.53 -> 91.15, 90.99 -> 91.07; pooled +onset 76.77 -> 76.96, 76.95 -> 78.02, 77.32 -> 78.01; full 74.72 -> 74.92, 75.08 -> 76.10, 75.43 -> 76.10; bars equal to the reference 14 -> 15, 15 -> 16, 14 -> 15 of 28. Only Petrushka and Scriabin Sonata 5 change (page 18 has a small extra staff above the piano: 432 -> 456 bars, pooled +2.47, **staff-sensitive -0.7, hands in the same bar 97 -> 95 %** because the page that D24 left out is read badly); the three Schott scans are identical to D28. Regression over all 425 saved page sets: 392 identical to D24 after normalising ids, 33 differ (Petrushka 13, Scriabin 13, `liszt-te-4-schott` 7 sets of the D30 arms, not scored).
Candidate against the evidence: plain top alignment (staff n to slot n, surplus staves at the bottom; same fill and padding) has the same pooled pitch and 1.5 to 2.3 points better staff-sensitive on Petrushka (rb2 64.7, rb3 62.6; control 74.4 without the drop) and Scriabin (90.7); not adopted as the rule, since test data must not choose it; the large gains come from the fixed slots and the rest fill, not from register matching.
Conclusions: the part-tracking fault is fixed (three parts of equal length in all three runs; D24 -34.4 / -20.4 pooled against the control becomes -3.5 / -2.0). **The retrained models are not adoptable by the D28 criteria**: on the same slot merger rb2 / rb3 are 3.5 / 2.0 pooled points below the control on Petrushka and have more bars (676 / 661 against 647, reference 627); every other piece is equal or better (Schott +1.5 to +13.3 pooled; Etude 5 with rb3 one bar short). What remains on Petrushka is on the transcription side (hidden-staff placement on mixed pages, collapsed pages) and in the unchecked reference; the held-out edition test of D28 is still open. Test-data rule: Petrushka, the Schott scans and Scriabin were only diagnosed and scored once with the finished rule.
