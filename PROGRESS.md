# Fork progress: octave brackets and real-scan testing

Living record of this fork (yiduoke/homr): what was built, tried and measured, and what
comes next. Written for people and coding agents picking up the work. Upstream is
liebharc/homr; its own docs (README.md, Training.md, IDEAS_FOR_CONTRIBUTORS.md,
AGENTS.md) still apply.

Last updated: 2026-11-15.

## Summary

The fork teaches homr's transformer to read octave brackets (8va, 8vb) on real printed
music. Five fine-tuning rounds were run; round 3 epoch 1 is published. It finds 244 of
the 322 hand-counted brackets on 73 real scan pages, with 14 false marks. Rounds 4 and 5
find 263 but double the false marks, so they were not published.

Upstream has since released model 566 (2026-11-13), which also reads octave brackets
(fewer than ours), reads beams, and is better at notes. Branch `octave-on-566` merges it
in. The main goal is now general note accuracy on 566 (see "Next"); octave rounds wait.

## State at handoff (2026-11-15, evening UTC)

- Running on the GPU box: regenerating training data with 566's converters (with beams).
  GrandStaff (45,635 staffs), PDMX (199,706) and Lieder (43,149) done; beam tokens
  present in sampled token files. The hard PDMX subset (complexity 2-3, scored test
  pieces excluded) failed at 20:00 UTC because MuseScore's logs had filled the disk
  (31 GB in `/root/.local/share/MuseScore/MuseScore4/logs`); logs deleted, rerun as
  `r6_hard2.sh` (tmux `r6hard2`, deletes those logs every 5 minutes), status ends with
  "ALL DONE HARD2". Box details and how to check progress: `run/HANDOFF_LOCAL.md`
  (laptop only).
- KernScores scan check done: usable after filtering (see "Real scans paired with
  transcriptions" under Next). Running since 20:40 UTC: recount of systems on every scan
  page with homr's own staff detection on the GPU (tmux `kerncount`,
  `/workspace/kern_check/homr_count.py`, results `homr_count.json`, staff positions saved
  as `.txt` next to each page PNG in `/workspace/kern_check/pages/`). Next: a cheap
  helper looks by eye at pieces where homr's count still disagrees with the .krn; then
  cut matching pieces into system/token pairs and have Sonnet check a sample bar by bar.
- Fixed: `homr --init` on this branch fetched 566 from the fork's release (404); upstream
  models now come from upstream's release (commit 5ecda33).
- No training is running. Nothing new is published; round 3 epoch 1 is still the
  fork's model.
- First things to pick up: verify the regenerated indexes (sizes, beam tokens), then
  the cheap post-decoding fixes and the time-signature round in "Next".

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
| Local only (git-excluded `run/`) | Test pages, scorers, results, reference transcriptions; on the owner's laptop, not on GitHub |

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

## Next

Agreed with the owner on 2026-11-15 (after review by Codex): general note accuracy is the
main project; time signatures are a bounded first improvement run alongside it; another
octave-only round is deferred. Keep experiments separate (one change each).

1. **Cheap note fixes after decoding, measured with `validation/score_notes.py` and
   `run/audit_note_errors.py` on the two references.** No training needed:
   - Tuplet repair: a beamed group whose durations do not fill its beat is a tuplet
     (Mazeppa's biggest loss, see the audit). Check upstream's existing triplet
     restoration (`homr/triplet_restoration.py`) first and extend it to 5, 6, 7.
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
