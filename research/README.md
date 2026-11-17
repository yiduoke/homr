# Research workspace

Scripts, notes and result tables for the experiments on this fork of homr (dense virtuoso piano
music, real scans, time signatures, octave shifts, evaluation). Code changes to homr itself
(`homr/`, `validation/`, `training/`) are ordinary commits in this repository; this folder holds
the experiment around them.

- `docs/`: `EXPERIMENTS.md` (the experiment log), `PROGRESS.md` (the living status and plan),
  `PAPER_NOTES.md`, the test-set plan and the lists of pieces excluded from training.
- `scripts/`: rendering, joining pages, evaluation, dataset building and training helpers
  (absolute paths point at the author's machine; edit them before use).
- `eval/`: the one-command evaluation (`eval_all.sh`), summaries, error audits, rescoring.
- `results/`: summary tables of the test-set runs, including `CORRECTED-table-2026-11-17.md`.
- `box_scripts/`: scripts that ran on the rented GPU machine.

## What is not here

The test-set scans, the reference MusicXML files, rendered pages, per-run outputs, datasets and
model weights. Several of them come from sources with their own terms (the ASAP and KernScores
data are CC BY-NC; IMSLP scans have their own copyright status; one score is not free to share),
and together they are tens of gigabytes. The scripts and notes record how they were made. The
released model weights are on the fork's releases page.

## Licence

Code in this folder is under the repository's AGPL-3.0 licence. Third-party data used for
evaluation and training keeps its own licence and is not redistributed here.

Scores in `results/` are F1 values of pitch, pitch with onset, and pitch with onset and
duration. Notes marked `print-object="no"` in a reference (ornament realisations stored for
playback) are not counted since 2026-11-17; older tables counted them.
