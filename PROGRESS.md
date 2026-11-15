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
in. The plan is to fine-tune 566 with our bracket data, after testing how much that
still adds.

## Where things are

| What | Where |
|---|---|
| Current branch | `octave-on-566`: upstream main (model 566, beams, octave tokens) merged on top of the octave work |
| Previous branch | `octave-shifts-lilypond`: octave rounds 1-5; published model `octave-r3e1-7ef6ff3` |
| Published octave models | GitHub release `octave_checkpoints` of this fork (round 3 epoch 1; round 2 epoch 2 kept) |
| Fine-tuning script | `training/transformer/finetune_octave.py` (warm start, new vocabulary rows copied by token name) |
| Octave training data code | `training/omr_datasets/augment_octave_shifts.py` (inserts brackets into MusicXML), `convert_lilypond.py` (LilyPond renders, one per page), `recrop_musescore_octave.py`, `training/transformer/build_round3_index.py` (training lists) |
| Held-out staff test | `training/transformer/octave_eval.py` |
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
| `run/score_vs_ref.py` | Pitches right per bar against a reference MusicXML: `python run/score_vs_ref.py REF.musicxml name=OUT.musicxml ...` |
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

Use: test-only references for note accuracy (`run/score_vs_ref.py`). Their pitches are
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

So about one pitch in five is wrong and only about half the bars are nearly right. These
are dense virtuoso pieces (Mazeppa also a dirty scan); upstream's own Polish-scores
benchmark puts 566 at a 14.6% error rate on cleaner scans. There is no reference yet for a
simpler piece, so it is unknown whether this rate holds outside such music.

Ignoring octave, La Campanella is about 87% for every version, so its differences are
octave brackets. On Mazeppa, ignoring octave, round 3 with upstream's cutting matches 509
on the upper staff (89%) and is a little behind on the lower (85% vs 88%).

### Upstream 566 on our test set (2026-11-15)

| Version | Scan brackets found (of 322) | False marks | Chopin LilyPond italic "8va" (of 11) | La Campanella MuseScore (of 40) |
|---|---|---|---|---|
| Ours, round 3 e1, bracket-aware (published) | **244** | 14 | **11** | **35** |
| 566, upstream's cutting | 180 | **8** | 1 | 26 |
| 566, bracket-aware cutting | 159 | 10 | 1 | 32 |

Per system on the four marked pieces (correct / missed / false of 217): ours 152 / 65 /
13, 566 with upstream's cutting 114 / 103 / 5, with bracket-aware cutting 97 / 120 / 9.

Notes with 566 and bracket-aware cutting: Mazeppa drops to 67% / 73% (from 78% / 79%),
La Campanella stays at 77% / 80%.

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

## Priorities (2026-11-15)

Overall accuracy matters more than new features:

| Problem | Cost on Mazeppa / La Campanella | Heard in playback |
|---|---|---|
| Wrong notes, octave aside | About 11-15% of pitches per bar | Everywhere |
| Wrong meter (6/8, 3/2, changes) | Every bar after the error is misplaced | Very |
| Missed octave brackets | About 5-8 points | In some passages |
| Missing features (glissando, pedal) | Rare, or not played at all | Hardly |

Post-training on 566 is suited to adding or sharpening specific things (brackets, meter);
it is not expected to lift general note accuracy on such pieces from about 78% to 95%.
That would need much more varied real training data, or constrained decoding and a
render-and-compare check.

## Next

In order of priority:

1. **Time signatures.** Read the printed numerator instead of guessing the beat count
   from bar lengths. Mostly code, cheap, very audible (one wrong meter misplaces every
   later bar), and nobody upstream is working on it. Measure on the two references.
   Today the parser keeps only the beat type (`timeSignature/4`), and C and ¢ arrive as
   `/4` and `/2` with their `symbol` attribute dropped. Plan: one token per whole
   signature (`timeSignature_3/4`, `timeSignature_6/8`, ... a fixed list of about 30-40)
   plus `timeSignature_common` and `timeSignature_cut`, written back to MusicXML with the
   C or ¢ symbol. Trap: every engraver decides on its own whether 4/4 is drawn as C
   (LilyPond does by default), so the training renders must be forced to draw exactly
   what the token says, and a sample of images checked against their tokens before
   training. Needs one fine-tuning round on 566.
2. **Note accuracy on real scans, on top of 566.** Real-scan training data, e.g. the
   OpenScore scans if bar alignment holds; our hand-checked pages and the references stay
   test-only. The bigger project, and where this fork has an edge.
3. **Octave work: one round on 566 at most,** only if the 566 test shows our data still
   adds enough brackets. Regenerate the octave training data with the merged parser (it
   now emits beam tokens), add matched bracket/no-bracket pairs, set 8vb exposure back to
   round 3's level, change one thing, and judge on brackets and notes. Then stop.

## Rules

- Never train or tune on evaluation data: the real test pages, the reference
  transcriptions, Polish scores, SMB. Develop on other data.
- Real scans must not get worse page by page; a better average does not excuse a worse
  page.
- No pull requests to upstream unless the owner asks.
- Before any change to `homr/` goes upstream, run the Polish scores benchmark as
  AGENTS.md describes.
