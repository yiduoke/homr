# Fork progress: octave brackets and real-scan testing

Living status of this fork (yiduoke/homr), kept for people and coding agents picking up
the work. Upstream is liebharc/homr; its own docs (README.md, Training.md,
IDEAS_FOR_CONTRIBUTORS.md, AGENTS.md) still apply. Newest state first; update this file
when something changes.

Last updated: 2026-11-15.

## Where things are

| What | Where |
|---|---|
| Current branch | `octave-on-566`: upstream main (model 566, beams, octave tokens) merged on top of the octave work |
| Previous branch | `octave-shifts-lilypond`: octave rounds 1-5 on top of model 509; published model `octave-r3e1-7ef6ff3` |
| Published octave model | GitHub release `octave_checkpoints` of this fork (round 3 epoch 1) |
| Octave training data code | `training/omr_datasets/augment_octave_shifts.py` (inserts brackets into MusicXML), `convert_lilypond.py` (LilyPond renders), `recrop_musescore_octave.py`, `training/transformer/build_round3_index.py` (training lists) |
| Bracket-aware staff cutting | `homr/octave_bracket_rows.py`, used in `homr/staff_parsing.py`; `HOMR_FIXED_MARGIN=1` switches back to upstream's cutting |
| Local only (git-excluded `run/`) | Test pages, scorers, results, reference transcriptions. Present on the owner's laptop, not on GitHub |

### Local `run/` layout (laptop only)

| Path | Contents |
|---|---|
| `run/scores/real/*.png` | 110 real test pages (150 dpi renders of the PDFs in `run/scores/real/pdf/`). Test only, never train or tune on them |
| `run/scores/real/verified_counts.csv` | Hand-checked bracket counts per page (8va, 8vb); `inventory.csv` has the rest |
| `run/scores/real/system_counts.csv` | Hand-checked counts per system, from the owner's red-pen marks |
| `run/scores/marked/` | Copies of the PDFs with red circles around every bracket (the owner's annotations) |
| `run/real_eval.py` | Bracket counts per page for a model: `python run/real_eval.py <dir with encoder_*.onnx and decoder_*.onnx> <label>`. Copies the ONNX into the worktree's model slot, so run one at a time |
| `run/system_eval.py` | Same, scored per system and direction, so a misplaced bracket counts as a miss and a false mark |
| `run/models/octave/real_eval/<label>/` | Cached MusicXML per model and page |
| `run/out/compare/<piece>/` | Whole-piece transcriptions (MusicXML + audio) for ours and upstream 566, plus references |
| `run/out/compare/*/<piece>-reference.musicxml` | Careful Claude-made transcriptions of Mazeppa (202 bars) and La Campanella (147 bars). Test only |
| `run/merge_pages.py`, `run/render_wav.py` | Join per-page MusicXML into one score; render a plain-synth WAV |
| `run/openscore_scans/` | Real-scan experiment: 18 IMSLP source PDFs of 19 random OpenScore Lieder songs (`songs.csv`), downloaded by hand, plus three OpenScore `.mscx` files. Not used for training or testing yet |

History of the octave rounds 1-3 (data, settings, per-epoch results) is in
[Training.md](Training.md#octave-shifts-round-three-epoch-1-octave-r3e1-7ef6ff3). Rounds 4
and 5 are summarized below and were not published.

## Current results

### Octave brackets on real scans (73 scan pages, 322 printed brackets, page counts)

| Model | Found | False marks | 8vb found (of 15) | False marks on 34 clean pages |
|---|---|---|---|---|
| Round 3 epoch 1 (published) | 244 | 14 | 8 | 1 |
| Round 4 epoch 1 | 263 | 31 | 12 | 6 |
| Round 5 epoch 1 | 263 | 31 | 10 | 4 |

Per system (four hand-marked pieces, 217 brackets): round 3 152 correct / 65 missed /
13 false; rounds 4 and 5 170 / 47 / 22. Only about 3 brackets per model land in the
wrong system.

### Notes against reference transcriptions (pitches right per bar, upper / lower staff)

| Version | Mazeppa | La Campanella |
|---|---|---|
| Round 3, upstream's cutting | **80% / 77%** | 79% / 80% |
| Round 3, bracket-aware cutting | 72% / 73% | **84% / 80%** |
| Upstream 566 | 78% / **79%** | 76% / 78% |
| Upstream 509 (our starting point) | 68% / 76% | n/a |

Ignoring octave, all versions are within a few points on La Campanella (about 87%), so
differences there are octave brackets.

## What we learned

- Bracket-aware cutting helps on clean, sparse pages (La Campanella) and hurts on dense,
  dirty ones (Mazeppa): the taller staff image is squeezed into the same 256 px height.
  Idea: grow the region only when a bracket is detected above the staff.
- Rounds 4 and 5 found about 18 more brackets in the right place but doubled the false
  marks, mostly false 8vb. Cause per Codex's review: inserted 8vb data with 8vb exposure
  still about 3x round 3 (the general bracket repeat doubles it), and a pitch confound
  (8vb is inserted under low sounding pitches, which print an octave higher, so the
  model can learn note position instead of the bracket). Round 5 changed two things at
  once, so it was not a clean test.
- Missed brackets on old engravings (Mussorgsky, Bessel 1886) are inside the staff crop;
  binarizing or upscaling the scan does not help. Mostly short one-chord brackets over
  thick chords.
- The decoder's 608-token cap is never reached on Mazeppa (max 371).
- homr reads a whole grand staff per image, not one staff. Ossia and three-staff systems
  come out as extra parts; `run/merge_pages.py` now drops parts covering under half the
  piece.
- Upstream added octave tokens (PR #204, 2026-11-13) and model 566 outputs octave
  shifts, finding fewer than ours (Mazeppa 19 vs 30, La Campanella 53 vs 57).
- Upstream's time-signature handling reads only the beat type and guesses the count,
  which breaks on 6/8, 3/2 and meter changes; this is the most audible remaining error.
- Real scans for training: OpenScore Lieder transcriptions keep the source edition's
  system and page breaks, and each song names its IMSLP source file. On two songs checked
  (Chaminade, Amoroso; Poldowski, L'heure exquise) the systems per page match the scan
  exactly. IMSLP blocks scripted downloads, so scans have to be fetched by hand; bar-level
  alignment is not checked yet. Songs rarely have octave brackets, so this helps general
  real-scan reading more than brackets.

## Rounds 4 and 5 (not published)

| Round | Change from round 3 | Start | Epochs |
|---|---|---|---|
| 4 | New inserted-bracket copies (`AUG_SUFFIX=oct4`): 8vb start chance 0.45, more single-note and run-of-short brackets; 8vb staffs repeated 3x | round 3 epoch 1 | 2 |
| 5 | Round 4 data without the extra 8vb repeat, plus copies rendered with tight brackets (`LILY_TIGHT_OTTAVA=0.35`) | round 3 epoch 1 | 2 |

Both reach 98-100% on held-out synthetic staffs and gain about 18 real brackets, but
double the false marks (see above). Neither replaces the published model.

## Next

1. Finish testing 566 on our pages (brackets per page and system, notes vs references,
   both cutting modes).
2. If our data still adds brackets over 566: regenerate the octave training data with
   the merged parser (it now emits beam tokens), add matched bracket/no-bracket pairs,
   set 8vb exposure back to round 3's level, and fine-tune 566 with one change per round.
   Judge on brackets and notes.
3. Time signatures: read the printed numerator instead of guessing.

## Rules

- Never train or tune on evaluation data: the real test pages, the reference
  transcriptions, Polish scores, SMB. Develop on other data.
- Real scans must not get worse page by page; a better average does not excuse a worse
  page.
- No pull requests to upstream unless the owner asks.
- Before any change to `homr/` goes upstream, run the Polish scores benchmark as
  AGENTS.md describes.
