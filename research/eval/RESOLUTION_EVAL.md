# Evaluation harness for the input-resolution experiment (R7)

Prepared 2026-11-17 (Pacific) while res_B_s7 / res_B_s11 train. Spec: `../res_experiment_spec.md`. All new files are
`res_*` in this folder; the existing eval scripts are untouched. Code: worktree `../res_wt`, branch `resolution`, commit
4715ec5 (local only). Arm A = `run3_ctrl_s7` / `run3_ctrl_s11` (256x1280), arm B = `res_B_s7` / `res_B_s11` (384x1920).

## What every arm runs (identical except the model name, `HOMR_INPUT_SCALE` and the crop switch)

`res_eval.py` = `run_testset.sh` + the scorer, always with the code of `res_wt`: `HOMR_FIXED_MARGIN=1`, `HOMR_LOOP_GUARD=1`
(set explicitly, default on anyway), `eval_run1/run_homr.py` per piece, `merge_pages.py` (`HOMR_TRUST_PAGE_TIME=1`; the current
merger, so the three Schott scans are lined up per page, like the "after-merger" tables), `drop_minor_parts.py`,
`validation/score_notes.py --ignore-staff` (one JSON with staff-sensitive and pooled numbers, visible notes only; the file
is identical to `integration_wt`'s). It checks first that the encoder's input shape equals the canvas of `HOMR_INPUT_SCALE`
and writes `out/testset/RES-<tag>-settings.json` (commit, scorer/merger/ONNX hashes, switches, start time Pacific).
Test set = the 28 scans of the tables (manifest minus Islamey, which has no released-model score). The piece set and the
settings are the same for every tag. Checked: `res_A_s7` on Bach prelude/fugue 873 gives the same scores as the old
`r3ctrl_s7` outputs (fugue 99.65/96.54/95.99).

## Commands once the weights exist

```
cd /Users/yiduoke/Documents/homr/run; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
# 0. ONNX from the box (export per the spec; fp32 encoder/decoder + encoder .onnx.data are enough on the laptop)
for r in res_B_s7 res_B_s11; do mkdir -p models/$r; scp "vast-homr4:/workspace/homr_res/homr/transformer/*$r*" models/$r/; done
# 1. the four arms, same settings (about 50 min for an A arm, about 1.7 h for a B arm on the laptop CPU; run one at a time)
for a in A7 B7 A11 B11; do nice $PY eval_run1/res_eval.py --arm $a; done      # tags res_A_s7 res_B_s7 res_A_s11 res_B_s11
# 2. comparison 1a: the same pixels as arm A, enlarged to 384x1920 (B weights)           -> tags res_B_s7_enl, res_B_s11_enl
for a in B7 B11; do nice $PY eval_run1/res_eval.py --arm $a --mode enlarge; done
# 3. comparison 1b: B weights on 384x1920 crops cut from the 225 dpi render of the same pages -> res_B_s7_hi, res_B_s11_hi
#    (renders exist in eval_run1/pages_hires/225, 26 pieces; rebuild with res_render_hires.py). Control: arm A on the same renders.
for a in B7 B11 A7 A11; do nice $PY eval_run1/res_eval.py --arm $a --mode hires; done
# 4. tables
$PY eval_run1/res_summary.py res_A_s7 res_B_s7 res_B_s7_enl res_B_s7_hi --name seed7   # side by side
$PY eval_run1/res_paired.py                                                               # A vs B, seeds 7 and 11
$PY eval_run1/res_paired.py --a7 res_B_s7 --a11 res_B_s11 --b7 res_B_s7_hi --b11 res_B_s11_hi --name B_direct_vs_hires
$PY eval_run1/res_paired.py --b7 res_B_s7_enl --b11 res_B_s11_enl --name A_vs_B_enlarged
$PY eval_run1/res_curve.py --fetch && $PY eval_run1/res_curve.py                          # learning curves
# 5. timing, ~6 min, nothing else should run
nice $PY eval_run1/res_timing.py                                                          # A:run3_ctrl_s7  B:res_B_s7, 5 pages
```
Priority if time is short: step 1 for seed 7 (A7, B7), then 4/5, then seed 11, then 2 and 3 for seed 7. Existing outputs are
kept (use `--force` to redo); `--pieces P ...` runs a subset; `--score-only` re-scores without inference.

## 1. Same crops, two ways (`HOMR_ENLARGE_BASE_CROP`, `HOMR_HIRES_DIR`; both unset = no behaviour change)

How the crop boundaries are kept identical: staff detection, system repair and `_calculate_region` (the crop rectangle in
coordinates of the 1920-px-wide working page image, after autocrop, resize and CLAHE) never look at the model or the switches.
Everything after that only changes the pixels cut from that rectangle.

* **(a) `HOMR_ENLARGE_BASE_CROP=1`** (needs `HOMR_INPUT_SCALE=1.5`): the crop is cut, dewarped and laid out for the
  256x1280 canvas exactly as arm A does it, then the finished canvas is enlarged by `cv2.resize` to 384x1920, which is what
  training does to the stored crops. The point mapping back to the page starts with the inverse of that enlargement, so the
  attention coordinates still land on the right page position. Verified (`res_crop_check.py`, Bach fugue p. 18, 7 staves): the
  B canvas equals `cv2.resize(A canvas, 1.5x)` exactly on 7/7 staves, canvas corners and centre map to the same page position
  (0.00 px difference).
* **(b) `HOMR_HIRES_DIR=<folder>`**: a render of the same page at a higher dpi under the same file name (`res_render_hires.py`
  makes `pages_hires/225/<piece>/page-NN.png`; PDFs whose embedded scan is below 225 ppi are skipped: Wanderer 72 ppi,
  Kreisleriana 200 ppi, Petrushka has no PDF; the others are 300-600 ppi bilevel IMSLP scans). `homr/hires_page.py` cuts from it the
  part that covers the working page image (corners of the working image mapped to the input image through the existing
  `to_input_image`, then to the render by the size ratio per axis). `prepare_staff_image` scales the crop rectangle and the staff
  line coordinates (used for dewarping) by the same factors, computes the canvas size and padding from the unscaled rectangle
  (so layout and aspect are those of the other modes) and resizes the hi-res crop onto the 384x1920 canvas; `to_page` ends with
  the inverse of that scaling, so attention coordinates map back into working-page coordinates as before.
  Check on the same page: corner and centre positions agree with arm A's within 1.9 px of the 1920-px working page (mean 0.5 px;
  integer rounding of the canvas height), sharpness (mean |Laplacian|) A 30.0, B enlarged 12.2, B direct 15.7, B hi-res 22.5.
  The 150 dpi page is itself a 1.55x upsampling to 1920 px, the 225 dpi render (1860 px wide) is almost native, so this is where
  the finer grid can see new detail. The control `--arm A7 --mode hires` gives arm A the same renders (downsampled to 256x1280).
  If a render is missing the run fails loudly (no silent fallback); `res_eval.py` skips such pieces.
* `python eval_run1/res_crop_check.py PAGE.png --hires-dir DIR` repeats the check on any page and saves the crops of one staff
  to `eval_run1/res_crop_check/`.

## 2. Metrics per piece (`res_summary.py`, `out/testset/RES-<tag>.md`)

Bars ours / reference; staff-sensitive pitch, +onset, full; pooled pitch (pitch counted on either staff of the aligned bar),
+onset, full; and at the bottom the number of pieces at 97+ (pooled and staff-sensitive) and with equal bar counts. A piece
whose parts have different bar counts has no pooled score; its staff-sensitive per-staff numbers stand in (marked `*`), as in
the earlier tables.
**Dense bars**: reference bars (all staves together, visible notes) with at least 24 notes (`res_lib.DENSE_NOTES`). For them:
number of bars and reference notes, recall of the reference pitches (pooled alignment and pitch inventory, the headline metric),
the count of reference notes missed, and the recall with pitch and onset. Bars that the alignment leaves unmatched count as fully
missed (`dense_bars_unaligned` in `res-dense-<tag>.json`). Both are computed with the scorer's own alignment and matching.

## 3. Timing (`res_timing.py`)

Each arm in its own process on the same 5 pages (Chopin op. 10/4 p. 13, Liszt Paganini 6 p. 14, Waldstein p. 5, Bach fugue 873
p. 18, Debussy Reflets p. 5; fixed in `SAMPLE`), a warm-up page then 2 repeats each, median. Reports wall per page (`recognize_page`:
segmentation, staff detection, dewarping, transformer; title OCR and XML writing off), staff-reading time (`parse_staffs`),
summed encoder and decoder time, staffs, decoded tokens, and the ratios to arm A. fp32 ONNX on the CPU, same threads. Pass
`--arm NAME:MODEL:SCALE[:enlarge]` to time other models.

## 4. Paired seeds and learning curve

`res_paired.py` pairs A s7 with B s7 and A s11 with B s11. Per piece and metric (pooled pitch, staff-sensitive pitch, pooled
+onset, pooled full, dense recall): the four values, d = B - A per seed, mean +- sample std over the two seeds (n = 2: a range, not
a confidence interval), win / loss / tie from the seed-mean d with a +-0.1 point tie band (`--tie`), whether both seeds agree,
macro means, the paired difference per seed, and an exact two-sided sign test over the non-tied pieces. The same script compares any
two tag pairs (`--b7 res_B_s7_enl ...`), so 1a and 1b use it too.
`res_curve.py` reads the trainer logs (`/workspace/logs/res/res_B_s<seed>.<attempt>.log`, control logs
`/workspace/logs/run3/run3_ctrl_s<seed>.1.log`; `--fetch` copies them with scp to `eval_run1/res_logs/`): training loss every 100 steps
(mean of those steps), validation dict at each epoch end (only 2 points per run: `eval_strategy="epoch"`). It writes
`out/testset/RES-curve.md/.png`: loss per quarter of the run, gap B - A per quarter, the slope of the training loss over the last half
epoch and of the gap (matched steps), the evaluation points and their change from epoch 1 to 2. Read "still improving at the cutoff" as:
the gap B - A still closing and a larger epoch-2 gain in eval loss/accuracy for B than for A. The learning rate follows a cosine
to zero, so every curve flattens at the end; a flat B curve at a higher loss than A means "converged worse in 6,716 steps", not
"finer grid hurts". Run it also during training on the partial log (it handles a log that stops early).

## Test without the trained model

`res_make_warmstart.py` builds `models/res_warm15` (the released run2s7 with its positional embeddings resampled to 24x120,
untrained, CPU export; needs timm, x-transformers, torchvision, einops, onnxscript next to torch, installed with
`uv pip install --target <dir> --no-deps ...` and passed as `PYTHONLIBS=<dir>`). Its scores mean nothing; it was used to run
`res_eval.py` in all three modes, `res_timing.py` and `res_paired.py` end to end. Do not report numbers from `res_warm15*` tags.

## Notes

* `res_wt/homr/transformer/*.onnx` are symlinks into `run/models/<name>/` made by `res_eval.py` (git-ignored); the first run in
  `res_wt` downloaded the segmentation and staff-relation models into the worktree (git-ignored).
* The page folders `eval_run1/pages/<piece>/` of some pieces hold stray `page-NN_teaser.png` files; `res_eval.py` and
  `res_render_hires.py` only use `page-<digits>.png` (the older `run_testset.sh` globs `page-*.png`).
* Not used for training or tuning: nothing here trains; the 28 scans and their references are only read.

## Final comparison (advisor's specification, prepared 2026-11-17 6:10 pm Pacific)

Target metric: 97 % pooled sounding-pitch F1 on every held-out piece. Seeds 7 and 11 on the same GPU pipeline (tags `res_A_s7_gpu`, `res_A_s11_gpu`,
`res_B_s7_gpu`, `res_B_s11_gpu`), same layout, merger, scorer and loop guard, edition-corrected references for every arm. `res_final_table.py` re-scores
Schubert D. 899/4 against `schubert-impromptu-d899-4-reference-edition.musicxml` (files `note-scores-<tag>-edition.json`, `out/pooled/<piece>/<tag>-edition.json`,
`res-dense-<tag>-edition.json`; existing outputs untouched, nothing is re-run on a GPU), reads the other 27 pieces from `res-scores-<tag>.json`, and writes
`out/testset/RES-FINAL-table-<date>.md`: per piece pooled / staff-sensitive / +onset / full per arm and seed, summary lines (means, worst piece, pieces at
97 pooled, bar-count equality), paired B - A per seed (mean and spread over the seeds, wins/losses, sign test), dense-bar recall and missed notes, "what moved"
(|B - A| >= 1 point pooled pitch in the same direction in both seeds) and wall time per page. A missing tag or piece is listed as missing and left out, never filled in.
Check of the A arms: before the edition fix `res_A_s7_gpu` reproduces 89.98 / 91.70 / 76.78 / 74.68 (staff-sensitive / pooled / +onset / full); the released baseline reproduces
92.0 / 77.0 / 75.0 and 6 of 28 at 97 pooled on the edition-corrected references.

```
cd /Users/yiduoke/Documents/homr/run; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
# 1. B11 on the box (after seed 11 has finished training and its ONNX is on the box: ./cloud2_models.sh res_B_s11)
ssh vast-homr5 "tmux new-session -d -s b11 'cd /Users/yiduoke/Documents/homr/run && nice /Users/yiduoke/Documents/homr/.venv/bin/python eval_run1/res_eval.py --tag res_B_s11_gpu --model res_B_s11 --scale 1.5 2>&1 | tee /root/logs/res_B_s11_gpu.log'"
#    (one evaluation at a time on the box; about 45 min; check "done in" for 28 pieces, repeat the command for FAILED pieces)
# 2. pull (small and fast; cloud2_pull.sh also fetches every per-page file and takes more than 10 minutes)
./cloud2_pull_min.sh res_B_s11_gpu
# 3. final table (rescoring of Schubert included, 10 s)
$PY eval_run1/res_final_table.py                      # -> out/testset/RES-FINAL-table-<today>.md
# 4. learning curves (the log of seed 11 is complete after about 6:45 pm Pacific; copies the trainer logs read-only with scp)
$PY eval_run1/res_curve.py --fetch && $PY eval_run1/res_curve.py
# 5. inference cost, quiet machine only (the per-piece wall times in section 7 of the table come from a shared box and are not clean: the same A model
#    differs by a factor 0.4-2.8 between seeds). Laptop CPU, 5 pages, about 6 min, nothing else running:
mkdir -p models/res_B_s7 && scp "vast-homr5:/Users/yiduoke/Documents/homr/run/models/res_B_s7/*res_B_s7.onnx*" models/res_B_s7/   # fp32 files; or from vast-homr4
nice $PY eval_run1/res_timing.py                      # A: run3_ctrl_s7  B: res_B_s7, writes out/testset/RES-timing.md
```
Extra GPU runs for the owner to approve (not started): the same B weights on the original crops enlarged (`--mode enlarge`, tag suffix `_enl`) and on crops from the
225 dpi renders (`--mode hires`, suffix `_hi`, 26 pieces; arm A on the same renders as control). Each about 45 min on the box, one at a time:
```
# on vast-homr5, in tmux, one after the other (prefix every python command with: cd /Users/yiduoke/Documents/homr/run && nice /Users/yiduoke/Documents/homr/.venv/bin/python)
eval_run1/res_eval.py --tag res_B_s7_gpu  --model res_B_s7  --scale 1.5 --mode enlarge     # -> res_B_s7_gpu_enl
eval_run1/res_eval.py --tag res_B_s11_gpu --model res_B_s11 --scale 1.5 --mode enlarge     # -> res_B_s11_gpu_enl
eval_run1/res_eval.py --tag res_B_s7_gpu  --model res_B_s7  --scale 1.5 --mode hires       # -> res_B_s7_gpu_hi
eval_run1/res_eval.py --tag res_B_s11_gpu --model res_B_s11 --scale 1.5 --mode hires       # -> res_B_s11_gpu_hi
eval_run1/res_eval.py --tag res_A_s7_gpu  --model run3_ctrl_s7  --scale 1 --mode hires     # control, -> res_A_s7_gpu_hi
eval_run1/res_eval.py --tag res_A_s11_gpu --model run3_ctrl_s11 --scale 1 --mode hires     # control, -> res_A_s11_gpu_hi
# on the laptop after ./cloud2_pull_min.sh <the tags>:
$PY eval_run1/res_final_table.py --a7 res_B_s7_gpu --a11 res_B_s11_gpu --b7 res_B_s7_gpu_enl --b11 res_B_s11_gpu_enl --label-a "B direct" --label-b "B enlarged" --name enlarge --no-baseline
$PY eval_run1/res_final_table.py --a7 res_B_s7_gpu --a11 res_B_s11_gpu --b7 res_B_s7_gpu_hi  --b11 res_B_s11_gpu_hi  --label-a "B direct" --label-b "B hires"    --name hires   --no-baseline
$PY eval_run1/res_final_table.py --a7 res_A_s7_gpu --a11 res_A_s11_gpu --b7 res_A_s7_gpu_hi  --b11 res_A_s11_gpu_hi  --label-a "A direct" --label-b "A hires"    --name hires_control_A --no-baseline
```
`res_final_table.py` options: `--a7 --a11 --b7 --b11` (tags of the two sides of a pair per seed), `--label-a --label-b`, `--name` (suffix of the output file), `--no-baseline`,
`--force-rescore`, `--pieces`, `--date`. Pieces without a render (hires) are listed as missing and the pairs use the common pieces.
