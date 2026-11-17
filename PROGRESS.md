# Fork progress: octave brackets and real-scan testing

Living record of this fork (yiduoke/homr): what was built, tried and measured, and what
comes next. Written for people and coding agents picking up the work. Upstream is
liebharc/homr; its own docs (README.md, Training.md, IDEAS_FOR_CONTRIBUTORS.md,
AGENTS.md) still apply.

Last updated: 2026-11-16.

Related documents: [PAPER_NOTES.md](PAPER_NOTES.md) (the paper's story, final numbers only);
[EXPERIMENTS.md](https://github.com/yiduoke/homr-research/blob/main/EXPERIMENTS.md) in the private research repo
[yiduoke/homr-research](https://github.com/yiduoke/homr-research) (exact commands, commits,
checksums and outputs per result; local checkout `run/`); [Training.md](Training.md) (model
cards); release [meteracc_checkpoints](https://github.com/yiduoke/homr/releases/tag/meteracc_checkpoints).

## Summary

The fork teaches homr's transformer to read octave brackets (8va, 8vb) on real printed
music. Five fine-tuning rounds were run; round 3 epoch 1 is published. It finds 244 of
the 322 hand-counted brackets on 73 real scan pages, with 14 false marks. Rounds 4 and 5
find 263 but double the false marks, so they were not published.

Upstream has since released model 566 (2026-11-13), which also reads octave brackets
(fewer than ours), reads beams, and is better at notes. Branch `octave-on-566` merges it
in. The main goal is now general note accuracy on 566 (see "Next"); octave rounds wait.

## State at handoff (2026-11-16, ~2 am Pacific)

- **Best model: run 2** (branch `accidentals-run2`, `pytorch_model_acc_run2_657-2f4096d...pth`
  on the GPU box; ONNX in `/workspace/onnx/acc_run2/`). It is upstream 566 fine-tuned twice:
  run 1 = complete time signatures (C and cut C included, carried across pages), run 2 =
  printed accidentals (lift = the printed sign; code derives the sounding pitch).
  **Released** 2026-11-16 as `pytorch_model_meteracc-r2s7-afae0e3` (the seed-7 repeat):
  https://github.com/yiduoke/homr/releases/tag/meteracc_checkpoints; branch
  `accidentals-run2` uses it by default (`homr --init` downloads it). Model card in that
  branch's Training.md.
- Results (frozen pipeline, `run/eval_run1/`): run 2 beats 566 on 6 of 8 references (mean
  notes F1 79.3 -> about 80; Rachmaninoff +5.7, Campanella +4.1); notes sound right 98.8%
  (566 97.2%). Behind 566 on Mazeppa (33.7 vs 34.8, mostly page-16 variance) and K. 309
  (96.1 vs 96.9). Details under "Next phase" and in `run/EXPERIMENTS.md` R1, R2.
- Done: R2s7, a repeat of run 2 with FT_SEED=7 (`/workspace/onnx/acc_run2s7/`), reproduced
  run 2 (mean 80.1 both); run-to-run spread up to ~1.8 points per piece.
- Fixed in the evaluation: `run/merge_pages.py` keeps page-start time signatures for
  meter-carrying code (`HOMR_TRUST_PAGE_TIME=1`) and no longer "repairs" printed accidentals.
  Still open: it loses Mazeppa p. 11 and Rachmaninoff p. 5 (parts matched by id).
- Upstream answered our accidental question (discussions/226): they switched to sounding
  labels for simplicity. Our run 2 suggests printed labels help on accidental-heavy music.
- Listening room (artifact HQ1b6xu88PNQuWA6Nvwfzk, `run/out/compare/index.html`): one "Ours"
  column = our best model (now run 2) on all ten pieces, plus upstream 566, Copista,
  Audiveris, LEGATO, rokot, Transcoda v2.1 and references.
- Owner's open items: confirm the time signatures in the three Claude references (by Tue
  17 Nov); mark a meter test set (Petrushka, Pathetique, Pictures, Mazeppa pages; by Wed 18
  Nov); check the three Claude references bar by bar before the paper (mid-Feb 2027).
- Reference fixes needed (found by the run-2 diagnosis, `run/eval_run1/run2_diagnosis.md`):
  K. 309 printed reference misses cautionary naturals from m32; La Campanella printed signs
  have errors both ways; Mazeppa p. 14 bar 136.
- Timing audit (2026-11-16, `run/eval_run1/timing_audit.md`): of notes with the right pitch
  but wrong timing, 64% are tuplets (mostly unnumbered beamed groups), 17% bar length / meter
  (cadenza-like bars, one Mazeppa meter misread), 9% voices and rests. Validation staffs are
  99.2% fully right and contain only 2.5% tuplet notes. Tuplets are the next target: first a
  post-decoding repair (a voice that overfills its bar gets its beamed run rescaled as a
  tuplet, using the recognised meter), then a tuplet token plus training data with many
  (unnumbered) tuplets.
- Chopin Ballade No. 4 reference: MusicXML transcribed by Claude in another session, given by
  the owner on 2026-11-16 (unchecked; add to the owner's bar-by-bar check; by ear the owner
  judges it, and the other Claude references, roughly 99%+ right but not perfect), 96.8% pitch agreement with our PDF; released model 75.5 notes fully right vs 74.2
  for 566 (EXPERIMENTS "Ballade reference").
- Paper outline with final numbers: `PAPER_NOTES.md` (keep it current; PROGRESS stays the log).
- Mazeppa's notation is irregular by design (owner found it, 2026-11-16): Henle's blog
  "Gaps in the notation: Liszt's Mazeppa étude" (Peter Jost, 13 Feb 2023,
  https://blog.henle.de/en/2023/02/13/gaps-in-the-notation-liszts-mazeppa-etude/): in the
  1852 version the outer voices lack rests on beats 2 and 4 from the theme (m. 7 ff.; again
  31 ff., 80 ff., 114 ff.), judged intentional; the 1839 version is in 6/4 with unmarked
  triplets. Our Soviet edition (1852 text) also has bars like 29-30 holding six beamed groups
  under C (footnote: move smoothly from triplets to plain eighths). Plan: keep Mazeppa as the
  real-scan test, mark these bars as "free" and report timing with and without them; cite
  this in the paper as an example of why rhythm scoring on Romantic virtuoso music needs care.
- Pitch audit (2026-11-16, `run/eval_run1/pitch_audit.md`): 35% of pitch errors are bars
  lost to layout (ossia, four-staff systems), 11% octave (missed 8va brackets: the released
  model inherits 566's weaker bracket reading; round 3 found far more), 11% staff assignment
  (Bach fugue, staff-agnostic pitch F1 99.3). Candidate next steps besides tuplets: layout
  handling, and one octave round on the released model.
- Real-scan test set plan (draft, owner to edit): `run/test_set_plan.md`; ASAP references for
  ~25 virtuoso pieces + IMSLP scans; first IMSLP downloads opened for the owner.
- Speed: branch `speed`, merged into `accidentals-run2`: identical output, 1.6x faster on
  whole pieces under load, ~2.75x on a quiet machine (EXPERIMENTS.md S1).
- Next candidates (one change per run): fix the training mix (it costs up to 3.6 points on
  classical pieces vs 566); stop carrying a meter that bars don't fit; tuplet token;
  real-scan pairs from KernScores (168 pieces ready to cut); harder data (hard PDMX, ASAP,
  Scriabin are converted). Paper goal: ISMIR 2027 (abstract 9 Mar, paper 16 Mar 2027).
- Box details: `run/HANDOFF_LOCAL.md` (laptop only). Research workspace and experiment log:
  private repo yiduoke/homr-research (`run/`, `run/EXPERIMENTS.md`).

## Reproducibility and AI use (for the paper)

- Every number in this file should be reproducible from a commit in this repo (code) plus
  a commit in yiduoke/homr-research (scripts, data, outputs). From 2026-11-15 on, each
  new result gets an entry in `run/EXPERIMENTS.md` (homr-research): date, ID, homr
  commit, model file, training index and checksums, exact command, output path, result.
  Older results are traceable through this file and the session transcripts, less
  precisely.
- Before anything goes into a paper: rerun it from a script (not from a helper's report),
  and record the run in `EXPERIMENTS.md`.
- The Mazeppa, La Campanella and Rachmaninoff references were transcribed by Claude and
  checked only in part; the owner (a pianist) is to verify them bar by bar before they
  are used in a paper. The Bach, Mozart and Beethoven references are expert KernScores
  encodings converted by script.
- AI use, to be disclosed in any paper: Claude (Anthropic) and Codex (OpenAI) wrote most
  code and scripts, ran experiments, converted data, transcribed three references and
  drafted analyses; cheaper Claude models (Sonnet, Haiku) did searches and checks. The
  owner chose the direction, marked every octave bracket in the test set by hand, and
  checks the results.
- Double-blind review (ISMIR): publish an anonymized copy of the code and research repo
  for reviewers; make both public under the owner's name after acceptance.

## Where homr comes from

homr (liebharc/homr) adapts its segmentation networks from oemer and its transformer
from Polyphonic-TrOMR (NetEase; paper arXiv 2308.09370). Upstream's run 0 is the TrOMR
paper's weights; from March 2024 the author trained his own runs, first in a fork of
Polyphonic-TrOMR, then in homr; model 566 is the latest. TrOMR wrote accidentals as
printed (only visible ones); upstream switched to sounding accidentals in run 79 (April
2024) without recording why (details under Next, step 3). This fork forked homr.

## Where things are

| What | Where |
|---|---|
| Current branch | `octave-on-566`: upstream main (model 566, beams, octave tokens) merged on top of the octave work |
| Previous branch | `octave-shifts-lilypond`: octave rounds 1-5; published model `octave-r3e1-7ef6ff3` |
| Published octave models | GitHub release `octave_checkpoints` of this fork (round 3 epoch 1; round 2 epoch 2 kept) |
| Fine-tuning script | `training/transformer/finetune_octave.py` (warm start, new vocabulary rows copied by token name) |
| Octave training data code | `training/omr_datasets/augment_octave_shifts.py` (inserts brackets into MusicXML), `convert_lilypond.py` (LilyPond renders, one per page), `recrop_musescore_octave.py`, `training/transformer/build_round3_index.py` (training lists) |
| Held-out staff test | `training/transformer/octave_eval.py` |
| Individual-note scorer | `validation/score_notes.py`; definitions and usage in `validation/note_scoring.md` |
| Bracket-aware staff cutting | `homr/octave_bracket_rows.py`, used in `homr/staff_parsing.py`; `HOMR_FIXED_MARGIN=1` switches back to upstream's cutting |
| Research workspace `run/` | Its own private repo **yiduoke/homr-research** (since 2026-11-15): test pages and marked PDFs, source score PDFs (checksums in `scores/SOURCES.sha256`), scorers and scripts, reference transcriptions, engine outputs and audio, box scripts and logs (`box_scripts/`). Git-excluded from this repo; commit there after every experiment |

### Local `run/` layout (laptop only)

| Path | Contents |
|---|---|
| `run/scores/real/*.png` | 110 real test pages (150 dpi renders of the PDFs in `run/scores/real/pdf/`). Test only |
| `run/scores/real/verified_counts.csv` | Hand-checked bracket counts per page (8va, 8vb); `inventory.csv` lists every page with source and the earlier helper counts |
| `run/scores/real/system_counts.csv` | Bracket counts per system, from the owner's red-pen marks |
| `run/scores/marked/` | Copies of the PDFs with a red circle around every printed bracket |
| `run/scores/*.pdf` | Whole pieces used for listening: Bach BWV 848 prelude and fugue, Beethoven Pathétique mvt 1, Chopin Ballade 4, Liszt La Campanella, Mozart K. 309 mvt 1 and K. 331 theme, Rachmaninoff Op. 3 No. 2, Stravinsky Petrushka |
| `run/real_eval.py` | Bracket counts per page: `python run/real_eval.py <dir with encoder_*.onnx and decoder_*.onnx> <label>`. Copies the ONNX into the worktree's model slot, so run one at a time |
| `run/system_eval.py` | Same, per system and direction: a misplaced bracket counts as a miss and a false mark |
| `run/score_vs_ref.py` | Legacy mean per-bar pitch-inventory F1; not individual-note accuracy |
| `run/merge_pages.py` | Joins per-page MusicXML into one score (drops ossia-like parts, splits odd note lengths) |
| `run/render_wav.py` | Plain-synth WAV of a MusicXML at a steady 108 bpm |
| `run/models/octave/real_eval/<label>/` | Cached MusicXML per model and test page; `<label>.json` has per-page numbers |
| `run/out/compare/<piece>/` | Whole-piece transcriptions (MusicXML + audio) from ours and upstream 566, plus the references |
| `run/openscore_scans/` | Real-scan training experiment (see below) |

## Timeline

| Date | What |
|---|---|
| Aug 2026 | Fork created to explore a correction layer over OMR output; the working pipeline (page rendering, tempo map, page merging, WAV rendering) lives in `run/`, tested on Beethoven's Pathétique (Mutopia edition) |
| 3 Nov | Merged upstream (system repair, triplet restoration, dynamics, model 509) |
| ~11 Nov | Round 1: octave vocabulary added, 2 epochs from upstream checkpoint 465 |
| 12 Nov | Round 2: LilyPond renders in many bracket styles; published `octave-r2e2` |
| 13 Nov | Round 3: bracket-aware cutting, MuseScore staffs re-cut, brackets inserted into scores; published `octave-r3e1` |
| 13-15 Nov | The owner, a pianist, marked every printed bracket in red on five pieces; the test set grew from 39 scan pages with estimated counts to 73 hand-checked pages |
| 14 Nov | Round 4 (more 8vb and short brackets) |
| 15 Nov | Round 5 (no 8vb repeat, tight brackets); per-system scoring; Codex review |
| 15 Nov | Two reference transcriptions made by Claude; note accuracy measured for the first time |
| 15 Nov | Found upstream model 566 with octave tokens and beams; merged into `octave-on-566` |

## The test set

- Pages come from public-domain editions (IMSLP, archive.org) and two user-supplied
  scores; sources are in `inventory.csv` and in Training.md's round-three table.
- Counts first came from a helper's count by eye. The owner then marked every bracket in
  red on Mussorgsky's Pictures (Bessel 1886), Ravel's Jeux d'eau (Schott), Liszt's
  Hungarian Rhapsody No. 2 (Senff) and Mazeppa (Russian edition); Ravel's Scarbo is not
  done yet. Brackets the owner did not circle were counted by eye and noted in
  `verified_counts.csv`.
- Now: 73 scan pages with 322 printed brackets (307 8va, 15 8vb), plus 34 control pages
  with none, Chopin Ballade 4 (5 LilyPond pages) and La Campanella (6 MuseScore pages).
- Brackets on ossia staves are counted. homr's staff detection misses Mazeppa's small
  "Piano à 7 octaves" staff on two pages, so those brackets can't be found by any model.

## Reference transcriptions made by Claude

A separate Claude session transcribed two whole pieces by hand-like work:
- Liszt, Mazeppa (Transcendental Étude No. 4), 202 bars.
- Liszt, La Campanella, 147 bars.

Method, as reported by that session: a preparation tool found staves and barlines and
paired them into systems, checked against the full page (it miscounted systems on pages
5, 11 and 15). Notes were read from zoomed crops of one staff, half a bar at a time, with
pitch guide lines overlaid. Things spanning staves (folded three-staff systems, cross-staff
beams, 8va brackets, ties and slurs across barlines) were settled on the full page. The
result was rendered with Verovio and compared with the scan.

Use: test-only references for note evaluation (`validation/score_notes.py`). Their pitches are
trustworthy; their octave-bracket extents are the least checked part. Both pieces are in
the bracket test set, so they must never be used for training.

## Results

### Rounds 1-3 on the original test set (39 scan pages, estimated counts)

| Pages | Round 1 | Round 2 | Round 3 e1, upstream cutting | Round 3 e1, bracket-aware |
|---|---|---|---|---|
| Chopin Ballade 4, LilyPond, italic "8va" | 0 / 11 | 9 / 11 | 9 / 11 | 11 / 11 |
| La Campanella, MuseScore | 27 / 40 | 29 / 40 | 28 / 40 | 35 / 40 |
| Scans, 39 pages | 71 / 178 | 122 / 178 | 124 / 178 | 132 / 178 |
| Control pages with a false mark | 2 | 1 | 1 | 1 |

Validation accuracy on the regular datasets: 99.81% (round 1), 99.84% (round 2), 99.81%
(round 3). Details and held-out staff numbers are in Training.md.

### Brackets on the current test set (73 hand-checked scan pages, 322 brackets)

| Model | Found | False marks | 8vb found (of 15) | False 8vb | False marks on 34 clean pages |
|---|---|---|---|---|---|
| Round 3 epoch 1 (published) | 244 | 14 | 8 | 4 | 1 |
| Round 4 epoch 1 | 263 | 31 | 12 | 17 | 6 |
| Round 4 epoch 2 | 258 | 29 | 8 | 14 | 3 |
| Round 5 epoch 1 | 263 | 31 | 10 | 17 | 4 |

By piece, round 3 epoch 1: Hungarian Rhapsody 59/63, Jeux d'eau 36/42, Mazeppa 39/57,
Mussorgsky 21/55. Round 4 raised Mussorgsky to 34 and round 5 to 37.

Per system (four marked pieces, 217 brackets): round 3 152 correct, 65 missed, 13 false;
rounds 4 and 5 170, 47 and 22 (23). Only about 3 brackets per model land in the wrong
system, so page counts were a fair proxy.

Held-out synthetic staffs: rounds 4 and 5 reach 98-100% on 8va and 8vb, against 66-83%
for round 3 on the same harder staffs, with no invented brackets on 60 clean staffs.

### Notes against the references (pitches right per bar, upper / lower staff, all bars)

| Version | Mazeppa | La Campanella |
|---|---|---|
| Round 3, upstream's cutting | **80% / 77%** | 79% / 80% |
| Round 3, bracket-aware cutting (as published) | 72% / 73% | **84% / 80%** |
| Upstream 566 | 78% / **79%** | 76% / 78% |
| Upstream 509 (upstream's default at our 3 Nov merge) | 68% / 76% | n/a |

How far from correct upstream 566 still is on these two pieces (bars well read / badly
read, upper and lower staff):

| Piece | Bars | Bars at least 90% right | Bars under 50% right |
|---|---|---|---|
| Mazeppa | 202 | 93 / 107 | 18 / 16 |
| La Campanella | 147 | 72 / 67 | 18 / 11 |

These are mean per-bar pitch-inventory F1 scores, not the fraction of individual notes
correct; see the note-weighted rescore below. Only about half the bars reach 90% by the
legacy metric. These are dense virtuoso pieces (Mazeppa also a dirty scan); upstream's
own Polish-scores
benchmark puts 566 at a 14.6% error rate on cleaner scans. There is no reference yet for a
simpler piece, so it is unknown whether this rate holds outside such music.

Ignoring octave, La Campanella is about 87% for every version, so its differences are
octave brackets. On Mazeppa, ignoring octave, round 3 with upstream's cutting matches 509
on the upper staff (89%) and is a little behind on the lower (85% vs 88%).

### Individual-note rescoring (2026-11-15)

The new scorer counts every pitched notehead, including chord members, grace notes and
tied segments. It uses one bar alignment shared by both staves and includes notes in
missing/extra bars in the denominators. The old scorer averaged bars equally, aligned
each staff separately and did not penalize unmatched predicted bars. Its numbers are
not directly comparable. See [the scoring definitions](validation/note_scoring.md).

All figures below are **micro F1 percentages**, both staves combined, against the
existing references (Mazeppa: 7,213 noteheads; La Campanella: 4,250). They evaluate the
existing merged MusicXML, including `run/merge_pages.py` repairs, not the transformer
alone. No inference or training was run, and no input score was changed.

| Piece | Output | Pitch inventory | Pitch + onset | Pitch + onset + duration |
|---|---|---:|---:|---:|
| Mazeppa | Round 3, fixed cutting | 76.73 | 37.57 | 33.49 |
| Mazeppa | Round 3, published cutting | 70.66 | 34.41 | 29.54 |
| Mazeppa | Upstream 566 | 76.74 | 39.31 | 34.84 |
| La Campanella | Round 3, fixed cutting | 74.00 | 67.09 | 66.18 |
| La Campanella | Round 3, published cutting | 82.59 | 73.69 | 73.08 |
| La Campanella | Upstream 566 | 75.22 | 68.99 | 67.96 |

For upstream 566, full matches are 2,410/7,213 reference notes on Mazeppa and 2,903/4,250
on La Campanella. Those are recalls of 33.41% and 68.31%; precision is 36.40% and 67.62%.
The low Mazeppa timing score does **not** mean two-thirds of its pitches are wrong:
rhythm errors can displace many subsequent notes within a bar. Pitch inventory ignores
order and remains a lenient diagnostic, not a complete note-recognition score.

One example: reference Mazeppa bar 28 aligns to upstream output bar 31, with 108 versus
100 noteheads. There are 91 pitch matches, five pitch-and-onset matches and no full
matches. Its opening E5/E6 chord lasts 2/9 quarter notes in the reference and 1/2 in
the output; later onsets consequently diverge. Alignment is heuristic, especially near
cadenzas and split/merged bars, and the report exposes every pair for inspection.

Validation: the parser agrees with music21 on pitch, onset, duration and grace status
in every staff-measure of both references and both upstream566 outputs. Tolerance
0, 1/96 and 1/48 quarter notes gives the same Mazeppa score; La Campanella's full-match
F1 ranges only from 67.92% to 67.99%. The gap is not a floating-point rounding effect.

The scorer's 17 tests (plus 11 subtests), formatting, lint and type checks pass.
`make ci` was attempted; full CI remains blocked by unchanged training import-format
and type errors, and test collection requires the missing `augraphy` dependency.

Local reports: `run/out/compare/{mazeppa,la-campanella}/note-scores.json`, including
input hashes, per-staff counts and aligned/skipped bars. Reproduce from a checkout
containing the scorer, with `comparison_dir` pointing to the local comparison directory:

```sh
piece=mazeppa  # or la-campanella
python -m validation.score_notes "$comparison_dir/$piece-reference.musicxml" \
  "r3-fixed=$comparison_dir/$piece-ours-fixedcut.musicxml" \
  "r3-published=$comparison_dir/$piece-ours-published.musicxml" \
  "upstream566=$comparison_dir/$piece-upstream566.musicxml" \
  --json "$comparison_dir/note-scores.json"
```

Implication for training: general note reading remains a priority, but first distinguish
pitch/omission errors from onset, duration and merge errors. These results do not
isolate their causes. Develop on separate, aligned real scans with dense chords,
ledger lines, tuplets and multiple voices, retaining clean synthetic examples for
coverage. Check each staff crop against its labels before training. Keep these pieces
held out and report all three metrics; fixing meter alone cannot explain or guarantee
closing the note-level gap.

### Note-error audit (2026-11-15)

Where upstream 566's note errors come from, as a share of reference notes (grace notes
apart). Script `run/audit_note_errors.py`, results `run/out/compare/note-error-audit.json`;
bar alignment from `validation/score_notes.py`, one-to-one matching per bar and staff.

| Category | Mazeppa (6,873 notes) | La Campanella (4,234) |
|---|---|---|
| Fully right (pitch, onset, duration) | 32.7% | 68.3% |
| Right pitch, wrong onset | **35.9%** (1,676 of them tuplet notes) | 6.2% |
| Right pitch and onset, wrong duration | 4.5% | 1.1% |
| Wrong pitch at the right onset | 7.4% (octave 62, accidental 99, step 42, other 305) | **16.3%** (octave 263, accidental 216, step 31, other 182) |
| Missing | 13.2% (only 155 in chords of 3+) | 6.4% |
| In bars with no aligned output bar | 6.3% | 1.7% |
| Extra output notes | 430 | 334 |

- Mazeppa is mainly a rhythm problem: about 73% of its notes have the right pitch. The
  reference has 3,153 tuplet notes; 566 marks 1,288, so unmarked or misread tuplets shift
  every later onset in the bar.
- La Campanella's pitch errors are octaves (missed 8va brackets, which our octave data
  addresses) and accidentals.
- Page joining may lose notes on Mazeppa: 7,156 notes in the raw pages, 6,620 after
  `run/merge_pages.py`. About 280 are ossia parts dropped on purpose; the rest is
  unexplained and may be double counting at page edges. Check first.
- Missing notes are mostly single notes, not chord members.

### Rachmaninoff Prelude Op. 3 No. 2 (third reference, 2026-11-15)

A third Claude-made reference (redone after a first attempt was discarded): 62 bars, one
piano part, two staves (`run/out/compare/rachmaninoff-op3-2/rachmaninoff-op3-2-reference.musicxml`,
test only). Pitches right per bar (legacy measure, `run/score_vs_ref.py`), upper / lower:

| Version | All bars | Ignoring octave | Bars >= 90% / < 50% (upper; lower) |
|---|---|---|---|
| Round 3, upstream's cutting | 78% / 64% | 86% / 64% | 32 / 6; 23 / 17 |
| Upstream 566 | 78% / 64% | 87% / 64% | 34 / 6; 22 / 17 |

Ours and 566 are the same here (hardly any octave brackets). The lower staff is weak.

Individual notes (`validation/score_notes.py`, now aligning each staff separately when an
output's staves disagree on bar count): homr writes this piece on three staves (69, 69
and 43 bars; the third holds part of the four-staff climax). Scoring the two main staves
and counting the third staff's 290 notes as extras (so pessimistic): ours 52.3% notes
fully right (pitch alone 68.3%), upstream 566 57.2% (68.7%). A fairer score would assign
extra staves to the hand whose range they fit; not done yet.

### Page joining: ours vs upstream's (2026-11-15)

Upstream joins pages itself since PR #149 (`homr.main` with several images or a PDF,
`homr/relieur.py`). Same model 566, same pages, scored with `validation/score_notes.py`
(full match = pitch, onset and duration):

| Piece | Joining | Full match F1 | Recall | Precision |
|---|---|---|---|---|
| Mazeppa | `run/merge_pages.py` | **34.84%** | 33.41% | **36.40%** |
| Mazeppa | upstream relieur | **35.38%** | **34.06%** | **36.80%** |
| La Campanella | `run/merge_pages.py` | 67.96% | 68.31% | 67.62% |
| La Campanella | upstream relieur | **69.53%** | **69.88%** | **69.18%** |

Relieur is better on both pieces (47 more full matches on Mazeppa, 67 on La Campanella),
so `merge_pages.py` loses notes. (An earlier Mazeppa run looked doubled because homr's
own `*_teaser.png` preview images were passed in alongside the pages; homr.main does not
skip them or de-duplicate its inputs.) Relieur has one real bug: `homr/relieur.py:101-102`
pairs parts by position, not by name. On Mazeppa page 11 the small extra staff is the
first part, so it lands in the piano part and that page's 431 piano notes are dropped;
pages 4 and 5 have an extra part that is never joined. Fixing the pairing should raise
relieur's Mazeppa score further. Then retire `merge_pages.py`.

### Upstream 566 on our test set (2026-11-15)

| Version | Scan brackets found (of 322) | False marks | Chopin LilyPond italic "8va" (of 11) | La Campanella MuseScore (of 40) |
|---|---|---|---|---|
| Ours, round 3 e1, bracket-aware (published) | **244** | 14 | **11** | **35** |
| 566, upstream's cutting | 180 | **8** | 1 | 26 |
| 566, bracket-aware cutting | 159 | 10 | 1 | 32 |

Per system on the four marked pieces (correct / missed / false of 217): ours 152 / 65 /
13, 566 with upstream's cutting 114 / 103 / 5, with bracket-aware cutting 97 / 120 / 9.

Notes with 566 and bracket-aware cutting (legacy per-bar measure): Mazeppa drops to
67% / 73% (from 78% / 79%), La Campanella stays at 77% / 80%.

Reading: our data adds about 64 real brackets over 566, and 566 barely reads an italic
"8va" label (1 of 11), the same blind spot our round 1 had before the LilyPond styles.
566 makes fewer false marks. Bracket-aware cutting does not help 566 on scans and hurts
its notes on dense pages, so it should not be the default; at most, grow the region when
a bracket is detected. So step 3 below is worth one round.

## Rounds 4 and 5 (not published)

| Round | Change from round 3 | Start | Epochs |
|---|---|---|---|
| 4 | New inserted-bracket copies (`AUG_SUFFIX=oct4`): 8vb start chance 0.45, more single-note brackets and runs of short brackets; 8vb staffs repeated 3x (`R3_8VB_REPEAT=3`) | round 3 epoch 1 | 2 |
| 5 | Round 4 data without the extra 8vb repeat, plus a further 15% of scores rendered with tight brackets (`LILY_TIGHT_OTTAVA=0.35`) | round 3 epoch 1 | 2 |

## What we learned

- **Cutting is a trade-off.** Bracket-aware cutting helps on clean, sparse pages
  (La Campanella) and hurts note reading on dense, dirty ones (Mazeppa), because the
  taller staff image is squeezed into the same 256 px height. Idea: grow the region only
  when a bracket is detected above the staff.
- **False 8vb in rounds 4 and 5.** Per Codex's review: 8vb exposure was still about 3x
  round 3 (the general bracket repeat doubles every bracket staff), and there is a pitch
  confound: 8vb is inserted under low sounding pitches, which print an octave higher, so
  the original score never shows the same printed notes without a bracket and the model
  can learn note position instead of the bracket. Round 5 changed two things at once and
  was not a clean test. Planned fix: matched pairs (the same printed notes with and
  without a bracket) and 8vb exposure back to round 3's level.
- **Old engravings.** Mussorgsky's missed brackets are inside the staff crop; binarizing
  or upscaling the scan does not help. They are mostly short one-chord brackets over thick
  chords. The model sometimes emits a bracket's end without its start.
- **Engraving placement.** LilyPond already sets brackets tight over high chords; the
  tight-padding option only matters over notes inside the staff.
- **Limits checked.** The decoder's 608-token cap is never reached on Mazeppa (max 371);
  if it were, the staff would be cut off silently.
- **Layout.** homr reads a whole grand staff per image. Ossia and three-staff systems come
  out as extra parts; `run/merge_pages.py` now drops parts covering under half the piece
  and lines every page up with the main part.
- **Upstream.** PR liebharc/homr#204 (2026-11-13) added octave tokens; 566 finds fewer
  brackets than ours (Mazeppa 19 vs 30, La Campanella 53 vs 57) but reads beams and notes
  better. Before 566, homr read rhythm correctly but never wrote beam groupings.
- **Time signatures.** homr reads only the beat type and guesses the count, which breaks
  on 6/8, 3/2 and meter changes (Mazeppa's 6/8 from bar 114 is lost). This is the most
  audible remaining error in playback.
- **Real scans for training (`run/openscore_scans/`).** OpenScore Lieder transcriptions
  keep the source edition's system and page breaks and name their IMSLP source file. On
  two songs checked (Chaminade, Amoroso; Poldowski, L'heure exquise) systems per page
  match the scan exactly. 18 source PDFs for 19 random songs were downloaded by hand,
  because IMSLP blocks scripted downloads. Bar-level alignment is not checked yet. Songs
  rarely have brackets, so this would help general real-scan reading.
- **Not supported by homr at all:** pedal markings, glissando; cadenza notes are read as
  grace or ordinary notes.
- **Tuplet numbers are not recorded.** A tuplet is encoded only through note lengths
  (`note_24` = 1/24 of a whole note, `note_20`, `note_28`, ...). A sextuplet of
  sixteenths and two sixteenth-note triplets both become `note_24`, and the MusicXML
  writer groups them in threes, so a printed "6" comes out as two "3" groups (playback
  is right, the printed look is not). 4-in-the-time-of-3 cannot be encoded at all (same
  length as a dotted note). Keeping the number would need a tuplet group token and
  retraining, like the beam tokens in 566.

## Priorities (2026-11-15)

Overall accuracy matters more than new features:

| Problem | Cost on Mazeppa / La Campanella | Heard in playback |
|---|---|---|
| Wrong notes, octave aside | Legacy octave-free per-bar F1 about 85-89%; not an individual-note error rate | Everywhere |
| Wrong meter (6/8, 3/2, changes) | Every bar after the error is misplaced | Very |
| Missed octave brackets | About 5-8 points | In some passages |
| Missing features (glissando, pedal) | Rare, or not played at all | Hardly |

Post-training on 566 is suited to adding or sharpening specific things (brackets, meter);
it is not expected to make note reading on such pieces nearly right (566 gets about 35%
of Mazeppa's notes and 68% of La Campanella's fully right by the individual-note measure).
That would need much more varied real training data, or constrained decoding and a
render-and-compare check.

## Next phase: complete time signatures, then printed accidentals (2026-11-15)

Set by the owner's professor (email of 2026-11-15). Start from upstream 566. Prepare both
data changes now; train in two stages so each effect and any regression can be traced.
Keep tuplet changes, harder-data reweighting, octave experiments and RL out of both runs.

**Before either run (shared preparation)**
- P1. Beam tokens present in every regenerated set (done for GrandStaff, PDMX, Lieder,
  hard PDMX, ASAP, Scriabin: 2026-11-15 samples; re-check on the final indexes).
- P2. Deduplicate PDMX main (complexity <= 2) and PDMX hard (2-3): they share the
  complexity-2 pieces.
- P3. Remove evaluation pieces from every source: the 21 PDMX phrases, the five KernScores
  reference movements (Bach BWV 848 prelude and fugue, Mozart K. 331/1, K. 309/1,
  Beethoven Op. 13/1), every piece with pages in `run/scores/real` (scans and controls,
  as long as the controls stay in evaluation: Bach WTC, Beethoven sonatas Schirmer,
  Brahms Op. 116, Chopin Scherzo 1, ...), the listening-room pieces, Polish Scores and
  SMB. Match by composer + work in every index (GrandStaff, PDMX, Lieder, ASAP, Scriabin,
  KernScores scan pairs, LilyPond and MuseScore octave sets); write the exclusion list
  and the dropped counts into EXPERIMENTS.md.
- P4. Freeze the comparison pipeline: one commit of `validation/score_notes.py`, one page
  joiner, one cutting mode. Quantify the joining loss on the references first (relieur
  pairs parts by position: Mazeppa page 11 loses 431 notes; our merge_pages drops minor
  parts) and fix or report it, so it is not mistaken for a training effect.
- P5. Fixed elsewhere for both runs: staff cropping, dataset proportions, octave exposure.
  Owner (2026-11-15): keep the amount and mix of our octave-bracket training data unchanged
  (same LilyPond/MuseScore octave share as round 3). Those sets were made with the old
  converters and have no beam tokens although the images show beams: regenerate their
  tokens with the current parser (beams + full meter) from the same source MusicXML,
  keeping the images, after checking beams against crops (LilyPond may auto-beam).

**Run 1: complete time signatures**
- Tokens: `timeSignature_<num>/<den>` for every printed numeric signature (vocabulary
  from the counts in the data, plus `timeSignature_common` (C) and `timeSignature_cut`
  (cut C). Remove `timeSignature/<den>`. New rows initialised from the old denominator
  row of the same denominator (C from 4, cut from 2).
- Labels must describe the image: the renderer decides what is drawn.
  - MuseScore (PDMX, Lieder, ASAP, MuseScore octave): numeric unless
    `<time symbol="common|cut">`; check on rendered crops.
  - Verovio (GrandStaff kern): C only with `*met(c)` / `*met(c|)`; check on crops.
  - LilyPond (octave data): numbers unless the source marks a symbol (musicxml2ly writes
    `\numericTimeSignature`); the earlier assumption that it draws 4/4 as C was wrong
    (audit 2026-11-15, `run/audits/meter_report.md`). Images agree with the source in
    every dataset: regenerate tokens, no re-render. Label fixes from the audit: drop
    tokens of hidden signatures (`print-object="no"`, 246 staffs) and GrandStaff's
    default `/4` without `*M` (124); drop 435 GrandStaff samples that draw C on 3/4 or
    3/8. Vocabulary: 34 numeric meters + C + cut C (99.7% of printed signatures).
    Same-denominator changes are 60-73% of all meter changes (about 14,000 staffs).
  - Reuse renders; regenerate tokens only where agreement is verified on a sample of
    images per dataset and per case; otherwise fix the rendering.
  - Systems without a printed signature carry no time-signature token (already so for
    Lieder; PDMX windows always draw one). Pickups must keep their short first bar.
- Code: every parser (music_xml_parser, humdrum_kern_parser, music21_kern_parser,
  music21_xml_parser, convert_lieder, staff_merging, convert_lilypond), the vocabulary,
  `_remove_redudant_clefs_keys_and_time_signatures`, the decoder's rhythm head size, and
  the MusicXML writer (`build_time_signature`: write beats/beat-type and
  `symbol="common|cut"`). Carry the last recognised meter across systems and pages
  (also in the page joiner) until a new one is printed; use
  `find_division_and_time_signature_nominators` only when none was ever recognised.
  Meter changes with the same denominator (3/4 -> 4/4) must survive.
- Measures: exact meter recognition per printed signature, meter-change detection
  (precision/recall), and per-note precision, recall and F1 for pitch, onset and
  duration on every reference, with every page checked for regressions.

**Run 2: printed accidentals (from the run-1 checkpoint)**
- Labels: the printed sign (`#`, `b`, `N`, `##`, `bb`, or no sign), not the sounding
  alteration; "no sign" stays distinct from natural. The lift head's classes keep their
  names but change meaning (`#` used to mean "sounds sharp", now "sharp printed"): reset
  or re-initialise that head's output layer rather than trusting old weights, and record
  the choice.
- Label source, verified on images (absent source elements do not mean no sign):
  - MuseScore sets: the kept `rendered_scores/*.musicxml` is MuseScore's own export, whose
    `<accidental>` elements should match what it drew; check on crops incl. courtesy
    accidentals, ties across bars, and two voices on one staff.
  - GrandStaff: render the kern with Verovio to MEI and use written `@accid` (not
    `@accid.ges`); check on crops.
  - LilyPond: derive from LilyPond's default accidental rule and check on crops.
  - Audit (2026-11-15, `run/audits/accidental_report.md`): MuseScore sets and their
    Verovio renders: MuseScore's exported `<accidental>` (98-99.6% of bars exact by count;
    Verovio crops 6,462/6,462). GrandStaff: Verovio 6.4.1 MEI `@accid` plus kern `n`, with
    `X` (forced, 0.15% of notes) drawn and `y` hidden. LilyPond: neither rule (98%) nor
    XML (95%) exact; re-engrave and read the signs from LilyPond's SVG. Today's lift label
    differs from the printed sign on 24-48% of notes with a lift (mostly key-signature
    alterations with no printed sign). Bugs to fix in run 2, not run 1: printed `##`/`bb`
    become "none"; `strip_naturals` removes every printed natural.
- Asked upstream why run 79 switched to sounding alterations (owner approved;
  https://github.com/liebharc/homr/discussions/226, 2026-11-15). Answer (liebharc,
  2026-11-15 11:10 pm Pacific): switched "because it's simpler" - the training data and
  homr's MusicXML use sounding alterations, and the transformer learns the carry rules
  itself; a branch predicting staff positions instead of pitches added code without
  improving accuracy. So judge run 2 on printed signs (a new output) with no loss in
  sounding accuracy; if sounding accuracy drops, keep sounding labels and add printed
  signs as a separate output instead.
- Decoding: after the model, compute sounding pitch from key signature, accidentals
  carried within the bar (per staff and octave), and ties across bar lines; write both
  `<alter>` and `<accidental>` to MusicXML.
- Measures: printed-accidental precision/recall per class, plus everything from run 1.

**Run-1 data (2026-11-15)**: main sets relabeled for existing images in
`/workspace/homr566/datasets_meter/` (every label equal to the old one except time-signature
lines; kept: GrandStaff 43,437, PDMX 139,461, hard 90,744, Lieder 43,027, ASAP 5,491,
Scriabin 1,602; about 1% dropped for meters outside the vocabulary). Mix = round 3's recipe:
70,000 original staffs from GrandStaff, Lieder and PDMX only (PDMX with its complexity-2
scores, i.e. its original range; PrIMuS and musetrainer are gone in 566), plus the octave
sets relabeled with beams at round 3's exposure. Hard PDMX, ASAP and Scriabin wait for the
separate harder-data experiment. Control lists (same lines, old `timeSignature/<den>`
tokens) are built too, in case a control run is wanted.

**Run 1 result (2026-11-15 evening; details `run/EXPERIMENTS.md` R1, `run/eval_run1/`)**:
trained 2 epochs (~1 h); control run with identical data and settings but old tokens.
Notes (full-match F1, 566 / control / run 1): Mazeppa 34.8/33.6/35.8, Campanella
68.0/66.7/69.9, Rachmaninoff 57.8/59.0/58.9, Bach prelude 91.4/90.9/90.0, fugue
86.0/82.4/82.4, K. 331 99.6 all, K. 309 96.9/95.8/95.5, Pathetique 97.0/96.5/97.0.
The meter change itself is neutral to positive (run 1 vs control); the fine-tune recipe
costs up to 3.6 points on classical pieces (control vs 566) - check the mix before run 2.
Meter: run 1 writes C/cut C and full numerators (Pathetique 4/6 exact, 566 0/6; changes
5/5). Weakness: a misread is carried (Mazeppa 2/4 read as 3/4 at m129): bars in the right
meter 60% vs 82% for 566, which re-guesses per page. Ideas: drop a carried meter when
several bars in a row don't fit it; more meter-change data. The references hold only 18
printed signatures: the owner's meter test set (due Wed 18 Nov) decides.

**Run 2 result (2026-11-16; `run/EXPERIMENTS.md` R2 and its rescore, `run/eval_run1/`)**:
from run 1, lift head reset, same mix. After fixing the page joiner (it had overwritten printed
naturals): notes F1 Mazeppa 33.7, Campanella 72.1, Rachmaninoff 63.5, Bach prelude 92.6,
fugue 86.3, K. 331 99.6, K. 309 96.1, Pathetique 97.3 (566: 34.8, 68.0, 57.8, 91.4, 86.0,
99.6, 96.9, 97.0). Sounding pitch right on 98.8% of matched notes (566 97.2, run 1 96.3).
Printed signs read at roughly 86-99% F1 on most pieces; the low ones (K. 309 naturals,
Campanella sharps) are mostly reference errors. Step by step (control isolates the mix):
the round-3 mix costs up to 3.6 points on classical pieces, meter adds 2-3 on Liszt, printed
accidentals add 2-5 on accidental-heavy pieces. Mazeppa's remaining gap is mostly page-16
variance plus ~10 notes from one misread key signature (sounding pitch now depends on it).
Seed repeat R2s7 (FT_SEED=7) reproduces it: mean notes F1 80.1 for both runs (566 78.9),
sounding pitch 99.0%; single pieces vary up to ~1.8 points between identical runs, so judge
changes on two runs. Mazeppa stays ~1 point below 566 in both runs.

**Fix plan agreed with the owner (2026-11-16), from the timing and pitch audits**:

| Problem (audit share) | Fix | Kind |
|---|---|---|
| Tuplets (64% of timing errors) | Run 3: printed tuplet numbers; then a bar-fill repair for unmarked tuplets using the meter | training + code |
| Ossia staves (part of 35% layout loss; Mazeppa p. 11) | Ossias are alternatives (owner): drop them per page before joining, not after | code (branch `layout`) |
| Four-staff piano systems become a spurious third part (Rachmaninoff p. 5, ~290 extras) | Merge the extra staves into the two hands | code (branch `layout`) |
| Bach "wrong staff" (11% of pitch errors) | Not a reading error: the model writes notes on the printed staff, the reference files them by voice across staves. Add staff-agnostic scores | scoring |
| Octave brackets missed (11%; La Campanella 229 of 293) | First measure the released model on the 322-bracket test set (round 3: 244, 566: 180); then an octave round on the released model, or a writer fix if brackets are read but lost | training or code |
| Meter misread carried (Pathetique 60%, Mazeppa) | Drop a carried meter when several bars in a row don't fit it | code |
| Missing chord notes, accidentals | General reading quality: more varied and real-scan training data | training, later |

**Status of the fix plan (2026-11-16 afternoon)**:
- Code fixes done on branch `layout` (yiduoke/homr, head 4299394, pushed; not merged): ossia drop
  (`homr/system_repair.py`), four-staff piano merge (`homr/piano_staffs.py`), meter carry
  replacement after 4 misfit bars in the same denominator (`_repair_meter`), `score_notes.py
  --ignore-staff`. Full-match F1 vs run2s7: Rachmaninoff 61.7 -> 88.9 (bars 62/69 -> 62/62),
  Mazeppa 33.6 -> 37.8 (p. 11 scorable again, p. 16 42.9 -> 76.7), all other pieces identical.
  Rachmaninoff p. 1 "89.4 -> 86.9" is a scoring artefact (output byte-identical; the baseline used
  per-staff alignment because of the spurious parts); like-for-like both staves 74.8 -> 89.8.
  Known risk: a four-staff SATB/quartet system with G G F F clefs would be merged. The meter rule is
  deliberately strict (looser versions turned misread tuplets into 9/8, 13/16), so Pathetique's
  missed changes wait for run 3. Outputs `run/eval_run1/layout/`.
- Octave brackets measured (`run/eval_run1/brackets_released.md`): released model 254 found / 13
  false with bracket-aware cutting (round 3 244/14, 566 180/8); 238/4 with upstream cutting. La
  Campanella's octave errors are reading errors of bracket extent/continuation (bar 13 start+stop
  in one bar; bar 86 continuation missed) plus 33 false lower-staff starts. Scorer cache bug: page
  basenames collide between the Chopin and Campanella side sets (not the 322 scans).
- Real-scan test set (`run/test_set_plan.md`, swaps agreed with the owner for virtuosity): first
  five scored in `run/out/testset/` (full-match F1 ours/566: Chopin Op. 10/4 92.9/86.9, Prokofiev
  Toccata 81.5/43.8, Scherzo 3 88.8/85.0, Schumann Toccata 80.9/80.4, Islamey 54.3/51.0). 25 more
  scans in `run/scores/testset/` (Shostakovich Op. 87 in `private/`: non-PD in US/EU/Canada, not
  redistributed). Every test piece must be added to all training exclusion lists before the next run.

**Decisions of 2026-11-16 (afternoon, with the owner)**:
- **Next training order: pitch first, then tuplets.** Run 3 = harder data (hard PDMX, ASAP, Scriabin;
  all test pieces excluded) on top of the released model, measured on pitch over the ~50-piece test set.
  Run 4 = printed tuplet numbers. Reason: a wrong pitch is the more jarring error for a pianist, even
  though timing costs more full-match F1 (Islamey pitch 87.2 vs full 54.3). Octave-bracket extent is a
  separate, smaller round, kept out of run 3 so the effect of the data is visible alone. Pitch
  F1 with octave errors ignored (old 9 pieces, released model, pre-layout): pooled 89.6 -> 91.0
  (only errors under missed 8va brackets) or 91.4 (all octave errors); only La Campanella gains much
  (85.2 -> 91.2). Dense pieces stay at 82-92 pitch F1: the gap is dropped and invented notes.
- **Merge plan (owner's fork only, nothing upstream):** wait for the ASAP batch (released model,
  worktree acc_wt), merge `layout` into `accidentals-run2`, rerun the new pieces with the layout
  code (regression check on ~30 real scans), then merge `accidentals-run2` into the fork's `main`.
- **Tuplet ratio procedure (run 3/4 code):** the model emits the printed number, the written note
  values (flags) and group start/end; code lists candidate ratios (3: 3:2; 5: 5:4 or 5:6; 7: 7:4,
  7:6, 7:8), keeps the one that makes the group fill the beat grid and the bar, and breaks ties with
  the default (largest power of 2 below n in simple meter, 3-based in compound). Beat size from the
  meter: simple (2/4, 3/4, 4/4, 2/2) beat splits in 2; compound (top 6, 9, 12 over 8 or 16) beat holds
  3; odd meters (5/8, 7/8, 11/16) grouping comes from the beams, fallback the bar total. 3/4 and
  6/8 have the same bar length but different beats, which is why run 1 reads the full time signature.
  Wikipedia (Tuplet): septuplets are usually 7:4 (7:6 in compound), sometimes 7:8; usage is inconsistent.
- **Professor's review of run 3 (2026-11-16, agrees: harder-data pitch run first, tuplets after).**
  Design: control = continue training the released model on the existing mixture; candidate = same
  checkpoint with the harder material added; same budget, two seeds each; vocabulary, cropping,
  decoding and accidental interpretation unchanged. Details: (1) report pitch precision and recall
  separately (omissions vs additions); octaves stay in the primary metric, octave-free scores are
  diagnostic only; keep reporting onset and duration F1 so a pitch gain can't hide worse rhythm.
  (2) Verify the actual training crops contain the troublesome cases (dense chords, ledger lines,
  rapid runs, cross-staff writing, several voices) and that their labels are right under the current
  meter and printed-accidental formats. (3) Keep enough ordinary material (the control run showed the
  recipe can damage familiar repertoire); choose mixture and checkpoint on separate development
  pieces, then evaluate the held-out set (to do: split the ~50 test pieces into about 12 development
  and the rest held-out). (4) Establish the corrected layout baseline first so a recovered page isn't
  read as a training gain; add a safeguard so the four-staff merge doesn't fire on SATB/quartet systems
  before merging it generally. Octave round stays deferred; no architecture changes until this
  experiment answers something. If harder data helps broadly, expand it; if not, look at image
  resolution, capacity or decoding. Immediate deliverable: a verified mixture and a controlled run.
- **Findings from the 29 scans (details `run/EXPERIMENTS.md` T1 follow-up):** rare or fast-changing meters
  are read badly (Debussy Reflets 4/8 read as 4/4, Ravel Alborada 6/8-3/8-9/8-3/4 with invented 12/8, 5/8, 7/8);
  repeated notes in long beamed runs are dropped and the bar padded with rests (Prokofiev opening: audible pauses);
  sextuplets read as sixteenths (Polonaise bar 20); Schott Liszt pages fail staff pairing (hands become alternating
  bars). To do: fix Liszt pairing (code), keep these four as before/after examples for run 3 (pitch) and the tuplet run.
- **References corrected after a scan check (2026-11-16 evening, EXPERIMENTS T1 correction):** Ravel's third staff was
  an empty phantom, Rhapsody 6's reference carried two ossia mini-staves (now left out); both rescored with the normal
  scorer. Means over 29 scans: ours 85.3 / 70.9 / 69.1 vs upstream 82.5 / 67.3 / 65.5, ahead on 24 of 29. Petrushka
  really has 2, 3 and 4 staves per system; it stays scored staff-ignored and 3-staff systems are a layout to-do.
- **Meter checks (professor, EXPERIMENTS M1):** Alborada's 12/8, 5/8, 7/8 are raw decoder tokens chosen at only 18-23%
  with a flat distribution over 6/8, 9/8, 12/8, 5/8, 7/8 (clear cases: 3/4 84%, 3/8 70%); Reflets' printed 4/8 is below
  2% (top: common 33%, 4/4 18%), not a close second, so suspect the small glyph as well as the prior. Cheap fix without
  training: low-confidence meters fall back to the top candidate that fills the bars, or the carried meter.
- **Meter audit (box vast-homr4, 233,018 training staffs):** 4/8 has 86 time-signature examples (0.12%) vs 12,271 for
  4/4; 1/8 137; 5/8 196; 7/8 213; 11/16, 13/16, 15/16 under 12 each. Rare meters are nearly absent from training;
  next: oversample rendered rare meters (own run or part of run 3, question to the professor), check accuracy vs glyph
  size on the meter test set, consider a small separate meter reader. Upstream reads only the denominator.
- **Target (owner, 2026-11-17):** no paper until pitch is 97% or better on every piece (95% is the floor; 90% is "one wrong note in
  ten" and not acceptable). Today: mean pitch 85.3 over the 28 real scans (simple pieces 97-99, dense virtuoso 80-92, Liszt Schott
  pieces far lower because of layout). Plan consequence: after run 3 (control vs harder data) decide whether data alone can get there;
  if gains are modest, the next levers are input resolution, model capacity and decoding (the professor's fallback), then the meter,
  tuplet and real-scan arms. Report pitch per piece against the 97% line from now on.
- **Petrushka reference** (Claude transcription, unchecked, `run/out/testset/stravinsky-petrushka/`):
  first look full-match F1 ours 38.8 / 566 46.2, but not like-for-like; the reference has 3 staves per
  system, our output 2 (the layout merge handles only four-staff systems). Open question: 3-staff fix.

**Run 3 plan: printed tuplet numbers (agreed with the owner 2026-11-16)**. Today a tuplet is
only its resulting duration (`note_12` = triplet eighth); the printed number is not in the
labels, so the model ignores it (Pathetique 6 and 7). Same principle as run 2: the model reads
what is printed, code computes the meaning. Labels: the written note value plus a tuplet-start
token carrying the printed number (3, 4, 5, 6, 7, ...) on the group's first note and a
tuplet-end on its last (like beams); the bracket is optional (edition style) and not a label.
Code derives the ratio (3:2, 5:4, 6:4, 7:4 ...) from the number, the written values and the
meter (run 1), and writes MusicXML `<time-modification>` and `<tuplet>`. Only printed numbers
in this run; unmarked tuplets (most of Mazeppa and the Ballade) are the later bar-fill repair.
Steps as before: audit numbers drawn in the training images per renderer, code + tests,
relabel the same images with the same mix, train from the released model (two seeds), evaluate
(plus printed-tuplet recall/precision). Bonus: ASAP/Scriabin pieces dropped for unencodable
tuplets become usable.

**Order of work**: P1-P5 and the label audits (helpers, on the box) -> run-1 code +
tests -> regenerate run-1 tokens -> train run 1 -> evaluate -> run-2 code + tests ->
regenerate run-2 tokens -> train run 2 -> evaluate. Every result goes into
`run/EXPERIMENTS.md` (homr-research).

## Next (before 2026-11-15 professor's plan)

Agreed with the owner on 2026-11-15 (after review by Codex): general note accuracy is the
main project; time signatures are a bounded first improvement run alongside it; another
octave-only round is deferred. Keep experiments separate (one change each).

1. **Cheap note fixes after decoding, measured with `validation/score_notes.py` and
   `run/audit_note_errors.py` on the two references.** No training needed:
   - Tuplet repair: a beamed group whose durations do not fill its beat is a tuplet
     (Mazeppa's biggest loss, see the audit). Check upstream's existing triplet
     restoration (`homr/triplet_restoration.py`) first and extend it to 5, 6, 7.
     It does not use the meter today (it checks that voices meet); once run 1 recognises
     full time signatures, use "every bar adds up to its meter" as an extra constraint.
     Today the numerator is guessed from the median bar length, so a page full of misread
     triplets can also get a wrong meter.
   - Page joining: switch to upstream's relieur, after fixing its part pairing (by name,
     not position) so pages whose small extra staff comes first keep their piano notes;
     drop ossia-like parts with `run/drop_minor_parts.py`; score again; retire
     `run/merge_pages.py`. Candidate for an upstream issue if the owner wants one.
   - Accidentals: no output-only rule. The model already carries accidentals itself:
     training labels are each note's sounding alteration after the key signature and
     earlier accidentals in the bar (`_lift_from_pitch_or_accidental` in
     `training/omr_datasets/music_xml_parser.py`), and homr writes the model's value
     straight to `<alter>`. The output does not say whether an accidental was printed,
     so a rule cannot tell a printed natural from a forgotten sharp. Instead, first check
     whether La Campanella's 216 accidental errors come from misread key signatures on
     whole systems; if so, keep the key consistent across systems unless a change is
     visible.
   Before blaming training, compare raw per-page predictions with the merged MusicXML,
   and check a few reference passages against the scan too.
2. **Regenerate the training data with upstream 566's converters** on the GPU box (beam
   tokens; the box's datasets are 509-era). Needed before any training on 566.
3. **Time signatures: recognize them, and carry them across pages.** Decided
   2026-11-15: recognition is the fix, and it is the first training round on 566.
   - Tokens for the whole signature plus C and ¢ (below). Upstream's converters can
     rebuild only the token files (`only_recreate_token_files=True`), so the data being
     regenerated now does not have to be rendered again.
   - A signature is printed only at the start and where it changes; most pages have
     none, and homr reads each page alone. So carry the last recognized meter across
     systems and pages and switch where a new one appears (today
     `find_division_and_time_signature_nominators` in `homr/music_xml_generator.py`
     guesses one numerator per page from the median bar length, which is why Mazeppa
     stays in 4/4). Keep the guess only as a fallback when no signature was read.
   **Time-signature tokens (one controlled round on 566).** Today the parser keeps only the
   beat type (`timeSignature/4`); C and ¢ arrive as `/4` and `/2` with their `symbol`
   attribute dropped, and `homr/music_xml_generator.py` guesses the count from the
   median bar length. Plan: one token per whole signature (`timeSignature_3/4`,
   `timeSignature_6/8`, ... a fixed list of about 30-40) plus `timeSignature_common` and
   `timeSignature_cut`, keeping the old `/d` tokens as fallback and initialising new rows
   from them; written back to MusicXML with the C or ¢ symbol. Places to change:
   `homr/transformer/vocabulary.py`, `training/omr_datasets/music_xml_parser.py`,
   `humdrum_kern_parser.py`, `music21_kern_parser.py`, `convert_lieder.py`,
   `staff_merging.py`, `homr/music_xml_generator.py` (`build_time_signature`,
   `find_division_and_time_signature_nominators`). Trap: every engraver decides whether
   4/4 is drawn as C (LilyPond does by default), so renders must be forced to draw what
   the token says; check the engraver's own output (e.g. LilyPond source, Verovio MEI)
   for a sample before training. Keep cutting and octave data fixed in this round.
   Suggested: add a tuplet group token (e.g. "6 in the time of 4") in the same data
   regeneration, since both changes write what is printed and need the same new data;
   test them as separate variants.
   **"Transcribe what is printed, compute the meaning" (owner's proposal, 2026-11-15).**
   Today a note's accidental label is its sounding alteration, so the decoder itself must
   remember an accidental for the rest of the bar (a later B5 after a B#5 is output as
   B#5 by the model). Proposed: label only the printed accidental (or none) and apply the
   key signature and bar carry by rule after decoding (per pitch and staff, through ties
   across the bar line), writing both `<alter>` and the printed `<accidental>` to
   MusicXML. Same kind of change as the time-signature and tuplet-group tokens (label
   semantics, re-tokenized data, one round), so the three can share one data
   regeneration and be tested as separate variants. Measure first how many of La
   Campanella's 216 accidental errors are forgotten carries (same pitch altered earlier
   in the bar).
   MusicXML holds both: `<pitch><alter>` is the sounding pitch on every affected note
   (key signature, printed or carried accidental); `<accidental>` is the printed sign,
   only where one is printed (including courtesy accidentals). The Claude references do
   this; homr writes only `<alter>`, so whether an accidental was printed is lost and
   notation programs redraw accidentals their own way:

   | File | Notes | With sounding alteration | With printed accidental |
   |---|---|---|---|
   | Mazeppa reference | 7,213 | 2,634 | 2,053 |
   | La Campanella reference | 4,250 | 3,404 | 642 |
   | Rachmaninoff reference | 1,837 | 1,175 | 242 |
   | homr 566, La Campanella | 4,293 | 3,109 | 73 |

   The references' `<accidental>` elements can serve to measure printed-accidental
   accuracy once homr writes them.
   History (upstream Training.md): the original TrOMR (run 0, weights from arXiv
   2308.09370) wrote accidentals "depending on how they are placed", i.e. only visible
   ones (in D major: semantic C#, Cb, Cb written as C, Cb, C). Upstream switched to the
   semantic encoding in run 79 (April 2024); that run's entry shows 80.9 diffs against
   22.3 for run 77, not comparable (the Polyphonic-TrOMR log calls 80.9 a "manual
   validation result"). No reason for the 2024 switch is written down (Training.md,
   commits and issues checked); run 79 is described only as an attempt. The one
   discussion is issue liebharc/homr#49 (January 2026): PrIMuS labels dropped carried
   accidentals; the options were to encode "all pitches ... on how they sound" or, failing
   that, to "consider changing the training to work with the visible symbols" ("we had
   something similar in the past"); they fixed the data (PR #52). The old visible-symbol
   code was removed in a dead-code cleanup (commit fd1f1f8, September 2025). Upstream kept it: run 80 fixed accidentals in the data,
   run 81 (depth reverted) reached 13.1, better than run 77; courtesy accidentals came in
   June 2024 and uniform encoding across datasets in January 2026 (commit af59798,
   `strip_naturals`). Today's labels are mixed: a printed `<accidental>` wins, otherwise
   the sounding `<alter>`; printed naturals are dropped. Visible-only labels were never
   compared head to head with the current ones, so this would be a fair, separate
   experiment. Upstream
   trains its own runs for about 14-24 h each, so a from-scratch run is normal here
   (about 1-3 days on one RTX 3090); fine-tuning 566 with re-labelled accidentals (and a
   reset accidental head) is the cheaper first test.
4. **Note accuracy from real scans,** chosen by what step 1 leaves: if notes are missing
   from the crop, fix cropping; if recognition fails on dense chords and tuplets, build
   real-scan training examples for those cases (e.g. OpenScore scans, if bar alignment
   holds). Hand-checked pages and references stay test-only.
   **Harder music without real scans.** Upstream's `convert_pdmx.py` keeps only PDMX
   scores with complexity <= 2 and at most two tracks ("complexity 3 often has octave
   shifts (unsupported) and long sequences") and samples about 20,000 files. PDMX piano
   scores (1-2 tracks) by complexity: 0: 44,844; 1: 168,026; 2: 8,089; 3: 609. By composer
   (matched in composer/title, approximate), complexity 1 / 2 / 3: Chopin 25/100/48,
   Liszt 3/12/40, Beethoven 78/46/52, Debussy 2/26/26, Rachmaninoff 1/11/14, Scriabin
   2/10/4, Ravel 169/29/6. So most virtuoso repertoire is excluded or rarely sampled.
   Candidate round: fine-tune 566 with all complexity 2-3 piano scores (octave shifts are
   supported now), plus virtuoso piano from Mutopia (a clone is in `run/mutopia`),
   KernScores and possibly ASAP (PDMX and Mutopia are public domain or freely licensed).
   Must exclude every test piece (PDMX likely has La Campanella, Liebestraum, ...).
   Started 2026-11-15: `convert_pdmx.py` now takes `PDMX_MIN_COMPLEXITY`,
   `PDMX_MAX_COMPLEXITY`, `PDMX_TARGET_FILES`, `PDMX_SUBSET` and `PDMX_EXCLUDE`
   (`training/omr_datasets/pdmx_exclude_test_pieces.txt` lists phrases of our test
   pieces). Only pieces whose results we score are excluded: the bracket test pieces
   (scan pages, Chopin Ballade 4, La Campanella) and the note references (Mazeppa, La
   Campanella, Rachmaninoff Op. 3 No. 2). Pieces used only for listening or on the
   bracket control pages (Bach WTC, Beethoven sonatas, Brahms Op. 116) stay in training.
   Complexity 2-3: 21 scores excluded, about 7,190 kept, queued on the box into
   `datasets/pdmx/hard`.
   **Other hard sources (surveyed 2026-11-15, downloaded to the box at
   `/workspace/extra_scores/`, 1.3 GB, nothing converted yet):**

   | Source | Format | Piano scores | Hard composers | Scored test pieces inside (exclude) |
   |---|---|---|---|---|
   | KernScores (craigsapp repos) | Humdrum | 616 | Scriabin 207, Chopin 76, Beethoven 103 | Scriabin Op. 8 No. 12, Sonata No. 4 |
   | ASAP (fosfrancesco/asap-dataset) | MusicXML | 235 | Liszt 17, Chopin 36, Beethoven 63, Schumann 11, Ravel 4, Rachmaninoff 4 | La Campanella, Mephisto No. 1, Mazeppa, Chopin Ballade 4, Chopin Scherzo 1 |
   | Mutopia (`run/mutopia`, local) | LilyPond | about 770 | Chopin 50-67, Schumann 35, Rachmaninoff 10, Scriabin 7-9, Liszt 4 | Chopin Ballade 4, Rachmaninoff Op. 23 No. 2 and Op. 3 No. 2, Pictures |

   KernScores overlaps GrandStaff's sources (Beethoven, Mozart, Haydn, Scarlatti, Joplin,
   Chopin); its new value is Scriabin. ASAP is MusicXML and the most virtuoso. Mutopia
   needs a LilyPond to MusicXML step (python-ly; lossy, so keep only pieces whose engraved
   note counts per bar match).

   **Real scans paired with transcriptions (found 2026-11-15).** The KernScores repos
   ship the source editions as scanned PDFs (one raster image per page, no fonts; the
   READMEs call them the source editions), and the .krn files record line and page
   breaks (`!!LO:LB`, `!!LO:PB`) and the edition (`!!!SMS`). Scans / transcriptions:
   Beethoven sonatas 101/103 (nearly one-to-one), Mozart sonatas 69/69 and Chopin
   mazurkas 52/52 (one-to-one), Haydn 100/25, Scarlatti 545/65, Scriabin 65/207, Joplin
   52/47 (need matching). Plan: render scan pages, find systems with homr's staff
   detection, split the .krn at its line breaks, keep pages whose system counts match,
   and make each scanned system plus its tokens a training pair. First check on a few
   pieces that scans and transcriptions agree bar by bar. Check that our Beethoven control
   pages (Schirmer) are not the same edition. This is the first real-scan training data
   for homr.
   *Check (2026-11-15, Sonnet helper; scripts and results in `/workspace/kern_check/` on
   the box):* systems per piece counted on the scans with a simple left-edge detector
   (homr's segmentation was too heavy for the busy CPU; bar-line counting was too noisy
   and dropped), compared with the .krn's `g=original` line breaks + 1 (`g=z` is another
   layout). Only 10 Mozart and 4 Beethoven files have page breaks, so totals per piece
   were compared:

   | Repo | Pieces | With markers | Systems equal (no odd system heights) | Mismatch |
   |---|---|---|---|---|
   | Mozart | 69 | 69 | 66 (60) | 3 |
   | Beethoven | 101 PDFs | 101 | 75 (47) | 26 |
   | Chopin mazurkas | 52 | 12 | 7 (4) | 5 |

   Most mismatches are off by 1-2 systems (likely detector noise); Beethoven 29-4, 30-1,
   30-2 PDFs hold about twice the .krn (two movements); Mozart 12-2 and Chopin 7-3
   unexplained. Read by eye, 8 systems (Mozart 01-1, 14-1; Beethoven 15-1; Chopin 7-2):
   all notes, accidentals, rhythms, clefs and bar counts match. The scans carry fingering
   and pedal marks the .krn lacks (the model would see them unlabelled). Use: keep pieces
   whose counts match (about 110 so far), cut systems with homr's own staff detection
   when the box is free, convert the .krn (invisible rests `ryy`, spine splits, layout
   tags) to tokens.
   Planned mix for the first note round (to be tested): about 40% complexity 0-1, 30%
   complexity 2, 30% complexity 3 and the most virtuoso pieces from the sources above;
   fresh scores first, repeats at most about 2x. Judge on the references plus one simple
   piece (a reference for e.g. Mozart K. 331's theme would show forgetting).
   **Benchmarks for a paper (2026-11-15; never train on any of them):**
   - IMSLP-Piano-Scores (Hugging Face, gated, real pages, MusicXML ground truth), leaderboard
     by OMR-NED (lower is better): copista-28m 0.164, homr fine-tunes by another user about
     0.25, clefscan 0.35, LEGATO (ICLR 2026, 0.9B) 0.442, stock homr 0.905 (submitted by
     someone else; likely a setup problem), GPT-5 0.944. Active through mid-October 2026.
   - OLiMPiC (Prague, CC BY-SA): scanned dev 1,438 / test 1,493 systems from OpenScore
     Lieder; their best SER 17.7 on scanned test. **Lieder is in our training data**:
     remove OLiMPiC's test pieces from Lieder before training if we report on it.
   - SMT++ (Alicante, full page, **kern, MIT code, weights on HF): CER 10.5 Mozarteum and
     19.6 Polish Scores after fine-tuning on fewer than 100 pages each (5-fold), 27.7 / 53.2
     zero-shot; Audiveris 86.8 / 93.7.
   - Copista 28M (KobiMusic, leaderboard best 0.164; symbol detector + rules + 2M
     transformer, Apache-2.0, `github.com/kobimusic/copisteria`) run locally on our pieces
     (2026-11-15, outputs `run/out/compare/<piece>/*-copista.*`). Per-note F1 full / pitch
     alone: Mazeppa 27.6 / 68.8 (566: 34.8 / 76.7), La Campanella 39.4 / 65.6 (566: 68.0 /
     75.2). Rachmaninoff's four-staff pages come out as four parts (not scorable);
     Petrushka 539 of about 878 bars. On hard real piano music 566 is clearly ahead.
   - More references (2026-11-15) from KernScores, converted with music21
     (`run/kern_refs/scripts/build_refs.py`): Bach WTC I BWV 848 prelude (104 bars) and
     fugue (55), Mozart K. 331 theme (18) and K. 309/1 (155), Beethoven Op. 13/1 (312).
     **These five movements must stay out of all training data** (KernScores scan pairs,
     ASAP, PDMX). The scorer now maps extra staves to the nearest reference staff
     (commit 9d75cd0), so Rachmaninoff is scored. Per-note F1, all right (pitch alone):

     | Piece | Ours r3 | Upstream 566 | Copista 28M | Audiveris |
     |---|---|---|---|---|
     | Bach prelude 848 | 90.6 (90.9) | 91.4 (93.6) | 93.4 (93.7) | 93.2 (93.8) |
     | Bach fugue 848 | 80.4 (83.2) | 86.0 (86.5) | 83.4 (86.2) | 71.4 (85.4) |
     | Mozart K. 331 theme | 99.6 | 99.6 | 99.4 | 99.2 |
     | Mozart K. 309/1 | 96.7 (99.1) | 96.9 (99.2) | 97.2 (98.2) | 93.1 (98.0) |
     | Beethoven Op. 13/1 | 96.3 (98.1) | 97.0 (98.3) | 91.3 (95.7) | 76.1 (85.4) |
     | Rachmaninoff Op. 3/2 | 52.7 (68.4) | 57.8 (69.0) | 37.9 (58.1) | 57.7 (79.7) |
     | Mazeppa | 33.5 (76.7) | 34.8 (76.7) | 27.6 (68.8) | - |
     | La Campanella | 66.2 (74.0) | 68.0 (75.2) | 39.4 (65.6) | - |

     Classical scans are nearly solved for 566; the gap is virtuoso music. Chopin Op. 52
     exists as kern in pl-wnifc/humdrum-chopin-first-editions (not built yet).
   - Plan: report on IMSLP-Piano-Scores, OLiMPiC scanned test, Polish Scores and our own
     references; check each for overlap with PDMX, Lieder and KernScores training data.

5. **Octave work: one round on 566 at most,** later, with matched bracket/no-bracket
   pairs and 8vb exposure back to round 3's level.

**Idea for later: edit weights directly.** MIT CSAIL's "Sparks of Weight-Space
Programming" (blog post, 2026-11-02, https://rikiyat.github.io/blog/weight-space-programming;
logs at https://github.com/RikiyaT/lm_understand-logs) had GPT-6 Astra edit 0.016% of
Qwen3.5-0.8B's weights with a Python kernel and 10-50 forward passes of practice
problems: MATH-500 7.9% to 48.1%. No reasoning setting stated; little gain on a 270M
model; the authors say it "is not a method". For homr (75M) start simpler: adjust output
biases for narrow habits (false 8vb, plain sixteenths instead of tuplet lengths), tuned
on development data and judged on the references, never tuned on test pages. A frontier
model editing loop would come after that.

More reference transcriptions (e.g. one simpler piece such as the Beethoven) would show
whether the error rates hold outside dense virtuoso music; they are expensive to make,
and any piece transcribed for testing must never be trained on.

Operational details for this laptop and the GPU box (paths, model slot, box scripts)
are in the local, git-excluded `run/HANDOFF_LOCAL.md`.

## Rules

- Never train or tune on evaluation data: the real test pages, the reference
  transcriptions, Polish scores, SMB. Develop on other data.
- Real scans must not get worse page by page; a better average does not excuse a worse
  page.
- No pull requests to upstream unless the owner asks.
- Before any change to `homr/` goes upstream, run the Polish scores benchmark as
  AGENTS.md describes.
