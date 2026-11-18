# Pilot comparison: rendered twins vs scanned crops of the same passages (spec, prepared 2026-11-17 about 4:55 pm Pacific, NOT launched)

Question (advisor): do real engravings add value beyond the notes themselves? The SAME passages are given to the model in two arms with equal exposure:
**CTRL_RENDER** = the passage rendered from its label MusicXML (like the existing rendered training data), **SCAN** = the scanned crop. Both start from the released
`run2s7` weights, same recipe as run3 / the resolution runs, the pilot passages are mixed into the existing mixture at a fixed share, same number of updates, seeds 7 and 11.
Everything below is built resolution-agnostic: the choice 256x1280 or 384x1920 is one variable (`RES=1|1.5`) made later by the resolution experiment.

## 1. Rendered twins (laptop, done)

Code: `scripts/twin_render.py` (render + checks), `scripts/twin_compare.py` (side-by-side sheets), `scripts/build_pilot_lists.py` (paired lists), `scripts/clef_disagree.py`. Output `twins/<pid>/<name>.png`
(32 MB, not in git), per-crop record `twins_report.json`, drop list `lists/pilot_dropped.txt`, counts `pilot_pairs_summary.json`. Runs in 3.7 min on the laptop (8 workers).

How a twin is made (same label tokens as the scan, `tokens/<name>.tokens`, no new labels):
- Source: the ASAP MusicXML of the manifest's measure range (`asap_measure_range` a+1..b, 0-based [a,b)), the file the tokens came from. Engraver: **Verovio** (the second renderer of the existing
  data, `training/omr_datasets/verovio_staffs.py`; MuseScore is not installed on the laptop or on the cloud box 5, so the MuseScore share of the existing data is not reproduced), `select measureRange`
  so that clef, key and octave brackets that begin before the range are kept (a crop that starts inside an 8va shows the continuing bracket, checked on A2_p-071_s2 and A9_p-58_s4). One system, scale 40, one of the five fonts
  per piece (hash of the piece: Leipzig, Bravura, Gootville, Leland, Petaluma, as in `verovio_staffs.py`).
- Conventions of the scan tokens reproduced: a time signature only where the first measure of the range declares one (earlier ones are `print-object=no`); no part name ("Pno."), no automatic measure
  number; ASAP/MuseScore trill and tremolo realisations are notes with `print-object="no"` (the token converter does not count them, Verovio still draws their beams): they become invisible rests.
- **Spacing (the owner's readability rule):** tightest rung of a ladder of 8 (spacingLinear, spacingNonLinear) = (0.18, 0.42) ... (0.52, 0.92) at which no two notes of different columns touch: note
  heads, accidentals and dots of different onsets that are less than 0.5 staff spaces apart vertically must be at least 0.25 staff spaces apart horizontally (bounding boxes from Verovio, `readable()`).
  Rung chosen: the tightest for 529 of 867, rungs 1-6 for the rest. A crop that still fails at the loosest rung is dropped.
- Cut and size like a scan crop (homr `_calculate_region` / `prepare_staff_image` / `get_tr_omr_canvas_size` for a grand staff): 4 staff spaces above the top and below the bottom staff line, extended to hold
  stems, beams, ledger notes, brackets, dynamics (+1 space; needed in 802 of 867), 1 space left of the brace, 2 right of the staff lines; scaled to the 256x1280 canvas rule (height 256, or
  width 1280 if wider), stored WITHOUT canvas padding and without a crop JSON, i.e. exactly like `images/*`. The data loader applies the model's canvas later, so the same files serve 256x1280 and 384x1920
  (the scans are also stored at scale 1 and upsampled by 1.5 in the second case: no arm gets extra detail).
- Token check: number of note heads and presence of an octave bracket in the rendering must equal the token file.

**Counts.** 982 crops (train strong 864 + hard 14, validation strong 104) -> 965 twins; 17 dropped, dropped from BOTH lists:
train 11 (10 where notes touch at the loosest spacing: Liszt TE11 3, Liszt Ballade 2 2, Chopin Op.25/5 2, Ballade 1 1, Barcarolle 1, Ballade 2 (group B) 1; 1 head count, Op.25/5: tokens 123, rendering 122), validation 6 (all notes touch, Chopin Sonata 2 mvt 2).
**Lists (same line order, same token file in each pair):** `lists/pilot_twin_render.txt` and `lists/pilot_scan.txt`: **867 passages** (A 716 from 19 pieces, B 151 from 4 pieces; 853 strong, 14 hard);
`lists/val_twin_render.txt` and `lists/val_scan.txt`: **98 passages** (C, 3 pieces, never trained on, kept separate; C1 19, C2 26, C3 53). `lists/box/*` = the same with `/workspace/pilot/...` paths.
`lists/pilot_clef_key_disagree.txt`: 78 of the 965 whose initial clefs (69) or key signature (15) in the label differ from the released model's read of the scan (see risks).

**By-eye check:** 36 pairs (30 train + 6 validation, random, seed 20261118) in `twins_check/sheet_00..11.png` (scan above, twin below, 3 per sheet; all 12 sheets viewed): no touching or squeezed notes found; accidentals,
chord seconds and beamed 16th runs are clean; the twin spacing is looser than the print in dense passages. Differences scan vs twin found: Verovio numbers every triplet ("3"), the Schubert print has none;
wavy trill lines where the print has "tr"; pedal signs overlap a little in one crop; tempo words differ; twin widths vary (p10/p50/p90 707 / 1016 / 1280 px) while scans fill the line (929 / 1019 / 1147; 0.8 %
reach the 1280 limit, twins 31 %), median staff space on the canvas equal (8.8 px), twin p10 6.6 px; no fingerings, page numbers, neighbouring-system fragments or paper in the twin.

## 2. Mixture and equal exposure (box vast-homr4, `/workspace/run3/` lists)

Base list: `/workspace/run3/run2_train_excl_v3.txt` (107,444 staffs; the list of run3 `ctrl` and of resolution arm A, so the comparison also sits next to those baselines; val list
`/workspace/run3/run2_val_excl_v3.txt`, 3,942 rendered staffs, unchanged, so the epoch evaluations are comparable with `run3_ctrl_*` and `res_*`). The candidate list `cand_train_nooct_v3.txt` (132,415, harder PDMX,
ASAP, Scriabin) is NOT used: it would add a second change.
`build_pilot_mix.py` writes `mix_CTRL_RENDER_R8.txt` and `mix_SCAN_R8.txt`: base lines + **R = 8 copies** of the 867 passages (6,936 pilot lines), shuffled with seed 20261120; line i of both files is the same
passage at the same position (identical tokens, only the image differs), base lines identical. With the same `FT_SEED` and list length the trainer shows the same passage in the same step in both arms
(assuming the HF seeded random sampler; the augmentation draws are not seeded, so runs are not bit-identical, as with every earlier repeat).

| | value |
|---|---|
| list length N | 107,444 + 6,936 = 114,380 |
| updates (FT_MAX_STEPS) x batch | 6,716 x 32 = 214,912 samples (as run3 ctrl: 2.00 passes of the base list) |
| passes over the list | 1.879 (base lines 1.88 times each, 6 % fewer than ctrl) |
| pilot share | 6.06 % of the list and of the samples (about 13,030 pilot samples) |
| **exposure per passage** | **8 x 1.879 = 15.0 passes over the 867 (distinct augmentations)** in each arm; per pass 8 |

`R` (env `R`, `--repeat`) and `--groups A` (drop the 4 group-B pieces: they are already in the rendered mixture, so CTRL_RENDER sees their notes twice; 151 passages) are the knobs if a
smaller or cleaner share is wanted (list name gets `_A`). The extra arm "no pilot data, 1.88 passes" is not needed: `run3_ctrl_s7/s11` (2.0 passes, no pilot data) are the nearest no-pilot baseline.

## 3. Scripts (prepared, not launched) in `run/research_wt/research/box_scripts/pilot/`

`train_pilot.sh ARM SEED` (copy of `run3/train_run3.sh` / `res_wt/training/train_resolution.sh`: same hyper-parameters, `FT_CKPT` = run2s7, vocab, lr 2e-5 cosine, warm-up 3 %, bf16, last weights, batch 16 x 2,
13 workers, 3 retries with resume; `RES=1` code `/workspace/homr_acc`, `RES=1.5` code `/workspace/homr_res` with `HOMR_INPUT_SCALE=1.5`), `chain_pilot.sh` (4 runs interleaved: CTRL_RENDER 7,
SCAN 7, CTRL_RENDER 11, SCAN 11; waits until no `finetune_octave.py` runs; builds the mixes if missing), `build_pilot_mix.py`, `upload_pilot.sh` (laptop), `pilot_val_eval.py` (held-out read, tested on the laptop
with the released model on 6 crops). No pkill anywhere; vast-homr4 was not touched while preparing (no ssh).

**Upload (when approved; the box is training: it only creates `/workspace/pilot`):**
```
cd /Users/yiduoke/Documents/homr/run && bash research_wt/research/box_scripts/pilot/upload_pilot.sh --dry-run   # 2,895 files, 109 MB
bash research_wt/research/box_scripts/pilot/upload_pilot.sh      # mkdir /workspace/pilot/{lists,mix,scripts}; tar over ssh of images/, twins/, tokens/, lists/box/*, scripts; verifies every path
```
**Size: 109 MB of images and tokens (114 MB with 4 KB blocks): scans 75 MB (867 + 98), twins 31 MB, tokens 2.4 MB; the two mix lists written on the box add about 40 MB (114,380 lines each): about 150 MB in total, 1.7 % of the 8.7 GB free.** Each training run peaks at about 3 GB of checkpoints
(`current_training`, deleted by the script when the weights exist; `KEEP_CKPT=1` keeps it) and leaves 287 MB of weights (+ 230 MB ONNX): 4 runs add 1.2 GB if the weights stay; copy each `.pth` to the laptop
and delete it on the box after the ONNX export. Resolution runs (`tmux res`) and the pilot must not share the GPU: the chain waits for them.

Start (when approved and RES decided): `ssh vast-homr4`, then `tmux new -s pilot 'RES=1 /workspace/pilot/scripts/chain_pilot.sh'` (or `RES=1.5`). Status: `/workspace/logs/pilot/status.log`, run logs `/workspace/logs/pilot/pilot_<ARM>_s<seed>.1.log`.

## 4. Cost and time (box $0.30/h; Pacific time; box clocks are UTC, 8 h ahead)

6,716 updates: 256x1280 about 0.62 s/step with real data = 1.15 h + start-up (75 s loader) + two epoch evaluations = **1.2-1.5 h per run, 4 runs 4.8-6 h, $1.4-1.8**. 384x1920 at 0.72 s/step (res B
measurement; 0.68 s GPU only) = 1.35 h + overhead = **1.6-2.1 h per run, 4 runs 6.4-8.4 h, $1.9-2.5**. Pilot images cost no extra loader time (PNG of 28-79 KB). ONNX export about 2 min per model on the CPU.
Earliest start: after `res_B_s11` (expected about 6:45-7:00 pm 2026-11-17) and the resolution decision, i.e. realistically the morning of 2026-11-18; the chain then ends 5-8 h later.

## 5. Evaluation plan (no test composition is used for training, selection or tuning; validation stays separate)

Models: `pilot_CTRL_RENDER_s{7,11}`, `pilot_SCAN_s{7,11}` (names get `_r15` for 384x1920); references: released `run2s7`, `run3_ctrl_s{7,11}` (= `res_A_s{7,11}`, no pilot data) and, for 1.5, `res_B_s{7,11}`.
1. **Training-time check** (in the logs): epoch evaluations on the control validation list (3,942 rendered staffs): accuracy must not fall below `run3_ctrl` by more than seed noise; guards against the pilot share hurting rendered music.
2. **Held-out validation crops** (primary, `pilot_val_eval.py`): the 98 passages of validation group C (Liszt TE3, Chopin Sonata 2 mvt 2, Schubert D.899/2), once as `val_scan.txt` and once as `val_twin_render.txt`,
   free generation, per crop pitch-multiset F1, (pitch, rhythm) F1, bar count agreement, exact multiset match. Primary contrast: SCAN vs CTRL_RENDER on `val_scan`, per-crop paired difference, seeds averaged,
   bootstrap 95 % interval over crops; secondary: both models on `val_twin_render` (does the scan arm keep rendered-domain skill), and each against `run3_ctrl`/released. 98 crops from 3 pieces: report intervals, expect noise.
3. **28 real test scans end to end** on vast-homr5 (GPU path, tags `res_<model>_gpu` like the controls; one evaluation at a time; `res_eval.py --tag pilot_SCAN_s7_gpu --model pilot_SCAN_s7 --scale 1`): pooled and
   staff-sensitive pitch per piece, pieces at 97, dense-bar recall, paired seeds, against `res_A_s{7,11}_gpu`. Hard rule of AGENTS.md: original scans must not get worse; a page-level regression is reported even
   if the mean improves. This set is read, never used to choose R, seeds or arms.
4. **Sensitivity:** repeat 2 without the 78 crops in `pilot_clef_key_disagree.txt` (label/print mismatch in the scan arm) and without group B.
Commands per model: ONNX export on box 4 (`cp training/architecture/transformer/pytorch_model_<name>_*.pth .../<name>.pth; HOMR_MODEL_NAME=<name> [HOMR_INPUT_SCALE=1.5] CUDA_VISIBLE_DEVICES="" python -m training.onnx.main --tromr --overwrite`),
`./cloud2_models.sh <name> [/workspace/homr_acc/homr/transformer]` to box 5, then `ln -sf .../run/models/<name>/* .../run/res_wt/homr/transformer/`, the val crops of the two lists are tarred to box 5 (small, 10 MB),
`HOMR_FORCE_CPU=1 PYTHONPATH=.../run/res_wt HOMR_MODEL_NAME=<name> python pilot_val_eval.py lists/val_scan.txt out.json`; compare with `pilot_val_eval.py --compare A.json B.json`.

## 6. Open risks

1. **Small and noisy.** 867 training passages from 23 pieces, 98 validation crops from 3 pieces, two seeds: only a large effect will show; run-to-run spread of earlier repeats was up to 1.8 points per piece.
2. **The contrast is engraving + print, not engraving alone.** The twin has Verovio's fonts and spacing (looser than the print; 31 % width-limited, p10 staff space 6.6 px against about 8 px), no fingerings, page
   numbers, neighbour fragments or paper; both arms get the same trainer distortions and Augraphy noise on top. A positive SCAN effect cannot separate "print style" from "scan degradation"; a degraded twin would be a later third arm.
3. **Scan-arm label noise the twin does not have.** The tokens follow the XML, the twin follows the tokens, the scan follows the print. Seen by eye: first-measure clefs (Chopin Ballade 1 m. 1 and Scherzo 2 m. 1: XML bass clef in the upper staff, print treble clef; Sonata 3 finale p. 15 lower staff), and what looks like no key signature printed in the scan of Liszt Ballade 2 p. 12 system 4 where the label has four sharps. 78 of 965 crops flagged by comparing the label with the
   released model's read (a model error also triggers it): this biases against SCAN; sensitivity analysis 4 handles it. Verified-pair checks (D13) covered bars and pitches, not clefs or key signatures.
4. **Group B already in the rendered mixture** (151 passages, Chopin Op.10/12, Ballade 2, Sonata 2 mvt 4, Beethoven Op.31/2): CTRL_RENDER sees those notes rendered twice; `--groups A` removes them.
5. **Selection:** the 17 dropped crops are the densest ones (Liszt TE11, Ballade 2, Op.25/5; validation Chopin Sonata 2 scherzo), removed from both arms; the metric is strict (also drops a few
   staggered arpeggio chords that were not squeezed). Sets are 878 -> 867 and 104 -> 98; the 14 hard crops are all kept.
6. **Exposure:** 15 passes over 867 images (and over 28 KB-79 KB PNG with 3 augmentation draws each) can overfit or memorise in either arm; R = 4 is the fallback. Base lines get 1.88 passes (6 % fewer than `run3_ctrl`).
7. **Resolution.** Not fixed yet; the scans are stored at 256 px height (like all scan data), so at 1.5 both arms are upsampled equally (no extra detail). A true 1.5 render of the twin would favour CTRL and is deliberately not done.
8. **Box.** One GPU: the chain waits for the resolution runs; disk is tight (see 3); the loader start-up has hung before (`FT_START_METHOD=forkserver`; 3 retries with resume); equal sample order depends on the seeded sampler (check the first logged losses of the two arms agree in trend).
9. Verovio only (no MuseScore), so the twin is not the exact renderer mix of the existing data (existing ASAP images are MuseScore renders); fonts per piece are random.
10. Frozen lists: `lists/train_octave_verified.txt` (34 octave crops admitted by the D17 eye review) and the second batch (D20) are NOT in this pilot; `twin_render.py` takes any list in the same format, so a second pilot can reuse everything.

## 7. v2 lists (D23, 2026-11-17, 6:40 pm Pacific; sections 1-6 describe the frozen v1 lists, the v2 numbers below replace them)

Lists are resolution-agnostic: the 256x1280 / 384x1920 choice (`RES`) is still pending, nothing here depends on it. Frozen v1 lists untouched; new files next to them. Code: `scripts/build_pilot_v2.py` (lists), `scripts/build_batch2_v2.py` (batch 2),
`scripts/twin_render.py` (new options `--lists`, octave bracket patch, range fallback), `scripts/twin_check_v2.py`, `scripts/scan_sheet.py` (by-eye sheets in `twins_check_v2/`, `audit_printed/`).

| | v1 | v2 |
|---|---|---|
| pilot train passages (both arms, same lines, same tokens) | 867 | **881** = 796 kept v1 + 26 Sonata 2 mvt 2 (moved) + 30 octave-verified + 29 tuplet-fixed |
| validation passages (`val_*_v2.txt`, separate, never trained) | 98 (C1 19, C2 26, C3 53) | **72** (C1 19, C3 53) |
| passages still on the old token file | 78 train + 6 val | 0 (all 80 remaining ones use the corrected file; 4 of the 84 were removed by 7.3/7.4) |
| clef/key flagged crops in the lists | 78 | 12 key-only (kept) |
| printed-notation mismatches | not checked | 7 removed |
| batch 2 train (`batch2_train_all`) / val / Demets | 550 / 145 / 47 | 520 / 145 / 26 (51 printed-notation candidates removed) |

**7.1 Stale labels (claim verified).** Diffing every list line against `tokens_typeless_rest_fixed/`: 78 of 867 pilot and 6 of 98 validation passages (same in the twin lists) pointed to the old file (bar rest written `rest_8`); no other corrected file (tuplet, octave) was in the v1 lists. v2 points all of them to the corrected file; 187 rest tokens change.
The twins needed no new render: Verovio draws a typeless whole-bar rest as a bar rest, so the old twins already showed what the corrected tokens say. Re-rendering the 84 gives pixel-identical PNGs; 83 of 84 contain at least as many measure rests (`mRest`) as changed tokens (A16_p-18_s0: 5 for 6, one changed rest is in a secondary voice and not drawn). By eye 22 changed twins (16 train, 5 validation, plus A16_p-18_s0): all bar rests right. Seen: A16_p-19_s4 has a voice-1 bar rest in the label that neither scan nor twin shows (same in both arms); A16_p-18_s0 twin has a font box artifact ("E5 20") from a text direction; A2_p-078_s4 twin is very wide and small (cadenza).
**Added crops.** 34 octave-verified + 30 tuplet-fixed: 64 of 64 twins rendered (`twins_report_v2add.json`, heads and bracket match the tokens). For the 7 octave labels corrected to the print (ASAP has no 8va, print has it, notes lowered) the twin XML gets an `octave-shift` direction derived from the corrected tokens (`octave_patch`), checked by eye on all 7 (`twins_check_v2/oct_corrected_*`); the open bracket of A15_p-10_s2 ends in the next measure of the XML. A10_p-03_s5 had a bar rest typeless (`tokens_v2/`). Three tuplet crops have their measure range from `work/tuplet/conv_*.json`. Tuplet numerals: the twin shows the XML's numerals where the label keeps the rounded value (declared in `manifest_tuplet_fixed.csv`).

**7.2 Chopin Sonata 2.** Before: mvt 2 validation (C2, 26 twinned passages, 32 scans), mvt 4 (B3 25) in the pilot train, mvts 1 and 3 (N9 34, N10 16) in batch 2 train. Moving mvt 2 to the train side costs 26 validation passages (98 to 72) and loses no training data; moving mvts 1, 3, 4 to validation would remove 25 + 34 + 16 = 75 training passages. **Chosen: all four movements on the train side** (v2: pilot train C2 26 + B3 17; batch 2 train N9, N10; no Sonata 2 in any validation list). Cost: the held-out set has two pieces (Liszt TE3, Schubert D.899/2); `batch2_val_v2.txt` (145, four works) is the larger independent validation set.
Other works: Beethoven Op.81a mvts 1 and 3 both in batch 2 val; Op.110 mvts 3-4 both train; every other work appears with one movement only. No other movement split. Sets of independent pieces split across sides (kept, treated like the Etudes, listed for the advisor): Schubert D.899 (no. 1 train, no. 2 val), Liszt Concert Etudes S.145 (Waldesrauschen train, Gnomenreigen val), Chopin Etudes Op.10 (1, 10, 12 train; 5 val); against the test set: Kreisleriana 3 (train) vs 1 (test), Ravel Miroirs 3 (Demets, train list only) vs 4 (test), Rachmaninoff Op.23/4 (train) vs 2 (test).

**7.3 Printed notation vs ASAP encoding.** Four classes found by comparing the first-measure time signature of the tokens with the model's read (all 1,724 crops; 17 disagreements) and with the print (by eye on every disagreement, 40 more crops, zoomed time signatures of 12 first systems):
A meter differs: print compound/other meter, ASAP simple meter with triplets (same sound). Pilot: none found. Batch 2: Chopin Op.25/8 (print 12/8, ASAP 4/4; 14 crops), Sonata 2 mvt 1 (print 6/4 in two sections, ASAP 2/2 with triplet quarters; 13 crops, 10 by eye), Ravel Une barque (print 6/8 over 2/4, ASAP 2/4; 21 crops, Demets list only, 1 by eye).
S meter symbol: same meter, different symbol (print C or cut, label 4/4 or 2/2 or the reverse): pilot A5_p-01_s0, B1_p-50_s0, A7_p-05_s0, A9_p-57_s0, A10_p-10_s4 (added octave crop); batch 2 N9_p-01_s0, NR2_p-01_s0, N21_p-06_s4.
M time signature printed but missing in the label (pilot A15_p-02_s3, A18_p-11_s3).
B implied (unnumbered) tuplets: print has plain eighths/quarters in the right meter (Chopin Sonata 2 finale, Etudes Op.25/1 and 25/2, Schubert D.899/1 and /2, ...), ASAP the true triplets; same meter, so no meter mismatch; the model reads plain values (D18). Not removed (it is the class the converter fix is for); the twin shows tuplet numerals the print lacks (known difference, section 1). Sensitivity: crops with a tuplet kern are not listed separately.
**Pilot:** the 7 crops of classes S and M are removed from both arms (`lists/pilot_printed_notation_mismatch.txt`); no relabelling. **Batch 2:** `lists/batch2_printed_notation_candidates.txt` (51 crops, printed meter, encoding, evidence); corrected tokens under `batch2/tokens_printed/` only where unambiguous (17: the 3 symbol crops, 10 of Op.25/8 and 4 of Sonata 2 whose every note and rest is a triplet kern and whose print is eye-checked; triplet kern 12, 6, 24, 3 becomes 8, 4, 16, 2, bar sums go from 1.0 to 1.5 in all 60 complete voice-bars; originals in `batch2/tokens/`). Not admitted anywhere (v2 train/val lists exclude them).

**7.4 Clef/key flagged crops (78).** Eye check of 24 (random, seed 20261118; crop start enlarged): of 19 crops with a clef disagreement, **19 label errors** (the ASAP XML has the other clef; the print agrees with the model); of 5 key-only crops 1 label error (A14_p-03_s5, print 2 sharps, label -3) and 4 label right (Liszt Ballade 2 x3 five sharps, TE11 five flats; the model misread). Decision: the 64 crops with a clef flag (a 65th, A9_p-57_s0, is removed under 7.3), plus A14_p-03_s5 and 4 added crops with the same clef flag, are removed from both arms (`lists/pilot_clef_key_removed.txt`, 69 passages, all on the train side; flags in `lists/pilot_clef_key_flags_v1.json`); the 12 other key-only crops stay. Passages remaining: 881 train, 72 validation.

**7.5 Held-out read of the v2 validation lists (released model, laptop CPU, `pilot_val_eval.py`, results in `research/results/pilot_v2/`; 72 crops; pitch F1 and (pitch, rhythm token) F1 as defined in that script, not the onset metric):** scan: pitch 0.991, pitch+rhythm 0.717, bar count right 97.2 %, exact 19.4 %; rendered twin: pitch 0.996, pitch+rhythm 0.991, bars 98.6 %, exact 77.8 %. By piece (pitch) scan C1 0.989, C3 0.991; twin C1 0.993, C3 0.997. The gap sits in rhythm (the unnumbered triplets of D.899/2, class B), not in pitch.

**7.6 Upload and mixture (v2).** `upload_pilot.sh` takes the v2 lists and installs them on the box under the old names (`lists/pilot_scan.txt` ...): dry run **2,859 files, 107.5 MB** (v1 2,895 files, 109 MB). Mixture, R = 8 as before: 107,444 + 881 x 8 = **114,492 lines**, pilot share 6.16 %, 214,912 samples = 1.877 passes, exposure per passage 15.0. `build_pilot_mix.py` default groups are now `A,B,C` (C2 is train side; the old default `A,B` would have dropped it); `--groups A,C` removes the four B pieces (Sonata 2 mvt 4 is in the rendered mixture). Cost and time estimates of section 4 stand.
