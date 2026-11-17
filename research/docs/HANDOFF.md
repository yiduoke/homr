# Local handoff notes (not in git)

Operational details that stay off GitHub. The project record is `PROGRESS.md` on branch
`octave-on-566` (checkout: `run/octave_wt`).

## Checkouts on this laptop

| Path | Branch | Use |
|---|---|---|
| `/Users/yiduoke/Documents/homr` | `tempo-marking-direction` | Owner's main checkout; holds `run/` (git-excluded) |
| `run/octave_wt` | `octave-on-566` | Current work: upstream 566 + octave code + PROGRESS.md |
| `run/upstream_wt` | detached at upstream/main | Clean upstream 566 for comparisons |
| `run/note_scoring_wt` | `codex/note-level-scoring` | Codex's scorer branch (already merged into octave-on-566) |

Python: `/Users/yiduoke/Documents/homr/.venv/bin/python`. Run homr from a worktree:
`cd run/octave_wt && ../../.venv/bin/python -m homr.main page.png` (`HOMR_FIXED_MARGIN=1`
for upstream's cutting). The model slot is the ONNX named by `homr/transformer/configs.py`
(`model_name`, now 566). `run/real_eval.py` overwrites that slot with the model it tests,
so never run two real_eval jobs at once, and check which model is in the slot.

## GPU box (vast.ai)

- Instance 60703025, RTX 3090, 16 cores, about $0.30/h including 160 GB disk. Keep it
  running between rounds: a stopped box loses its GPU to other renters (that happened
  once). Never destroy it without the owner's explicit yes.
- SSH: `ssh vast-homr4` (alias in ~/.ssh/config). Never `pkill -f` over SSH; kill by PID.
- `/workspace/homr`: copy of the code as of round 5 (509-era), not a git checkout.
  `/workspace/homr/datasets/`: Lieder-main, pdmx, grandstaff, Corpus, musetrainer,
  lilypond (incl. round 4/5 copies), musescore_octave. These were converted with the old
  converters, so their tokens have no beams.
- `/workspace/ckpt/`: checkpoints (465, round1-5 safetensors). `/workspace/onnx/`:
  exported ONNX per round/epoch.
- Scripts: `restart.sh EPOCHS VAR=...` starts `train.sh` (finetune_octave.py) in tmux;
  `export.sh` makes ONNX; `r5_render.sh` / `r5_train.sh` / `auto5.sh` are the latest
  round's pipeline (render, build lists, train, test each epoch); `setup4.sh` reinstalls
  packages (also needs `pip install -e .[cuda]`, `onnxsim`, `x-transformers==2.16.1`
  with deps, and the dev dependency group; never install the rocm group).
- Logs: `/workspace/logs/r5/status.log`, `/workspace/logs/train.1.log`.

## Data regeneration for 566 (started 2026-11-15 09:37 UTC)

- `/workspace/r6_data.sh` (tmux `r6data`): fresh clone of `octave-on-566` in
  `/workspace/homr566` with its own `datasets/` (Lieder unzipped, GrandStaff untarred,
  PDMX and MuseScore symlinked from `/workspace/homr/datasets`), then converts
  grandstaff, pdmx and lieder with upstream's converters. Progress:
  `/workspace/logs/r6/status.log`, per-dataset `.out`/`.err` in the same folder.
- MuseScore (needed for Lieder) only runs on this box with
  `APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen xvfb-run -a` and the apt
  packages installed on 2026-11-15 (xvfb, libopengl0, libnss3, libegl1, libgl1, xcb
  libraries, libpipewire, libjack, libfuse2t64). `r6_data.sh` runs Lieder without them,
  so `/workspace/r6_lieder.sh` (tmux `r6lieder`) reruns Lieder with them if it fails.
- Overnight result: GrandStaff converted (45,635 staffs); PDMX and Lieder produced
  nothing, because MuseScore could not start without `APPIMAGE_EXTRACT_AND_RUN=1`, and
  the converters still reported success. `r6_lieder.sh` never retried (it only reacts to
  a reported failure).
- 2026-11-15 17:37 UTC: `/workspace/r6_data2.sh` (tmux `r6data2`) reruns PDMX then Lieder
  with the MuseScore settings and checks the index has more than 1,000 lines; status
  ends with "ALL DONE 2". Then check the index sizes and a few token files for beam
  tokens before any training.
- Post-decoding fixes for notes (tuplets, joining loss, accidentals): see PROGRESS.md.
- 2026-11-15 19:18 UTC: restarted as `/workspace/r6_data3.sh` (tmux `r6data3`) with
  `MUSESCORE_WORKERS=12 HOMR_CONVERT_WORKERS=14` (parallel MuseScore batches, commit
  4aad0fb); status ends with "ALL DONE 3". Queued after it: `/workspace/r6_hard.sh` (tmux
  `r6hard`), the hardest PDMX piano scores (complexity 2-3, test pieces excluded) into
  `datasets/pdmx/hard`; status ends with "ALL DONE HARD".
- 2026-11-15 19:46 UTC: PDMX done (199,706 staffs); Lieder started (12 MuseScore at once).
- 2026-11-15 19:55 Lieder done (43,149). 20:00 hard PDMX FAILED: disk full, 31 GB of
  MuseScore logs in `/root/.local/share/MuseScore/MuseScore4/logs`. Deleted them (disk
  82%), removed the partial `datasets/pdmx/hard`, reran as `/workspace/r6_hard2.sh`
  (tmux `r6hard2`; background loop deletes those logs every 5 min); ends "ALL DONE HARD2".
  Any future MuseScore job on this box needs the same log cleanup.
- 2026-11-15 ~22:30 UTC disk cleanup (owner approved), 97% -> 55% (74 GB free): deleted
  PDMX SVG renders in `homr566/datasets/pdmx{,/hard}/rendered_scores` (MusicXML kept);
  old 509-era `homr/datasets/{pdmx/flat,pdmx/rendered_scores,Lieder-main/flat,
  Lieder-main/rendered_scores,Corpus,grandstaff}` (superseded by homr566's regenerated
  data; sources pdmx/mxl, Lieder-main/scores, *.zip, *.tgz kept); trainer states
  `round1-4_checkpoints`, `homr/current_training` (weights remain in `/workspace/ckpt`).
  Kept: lilypond*, musescore_octave, musetrainer, StringQuartets, all of `/workspace/ckpt`.
- New training sets: `homr566/datasets/asap/index.txt` (5,832 staffs) and
  `homr566/datasets/kern_scriabin/index.txt` (1,847); see `/workspace/logs/r6/extra_sources.md`.
- KernScores scan check (Sonnet helper): scripts and results in `/workspace/kern_check/`
  (step1.py, step1_results.csv/json). Repos in `/workspace/extra_scores/kern/`, ASAP in
  `/workspace/extra_scores/asap/`.
