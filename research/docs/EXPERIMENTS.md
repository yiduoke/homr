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
