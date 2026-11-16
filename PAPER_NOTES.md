# Paper notes: reading virtuoso piano scores with homr

The current story for a paper (target: ISMIR 2027, abstract 9 Mar, paper 16 Mar 2027; or its
late-breaking/demo session, about Aug 2027), with final numbers only. Day-by-day history, failed
attempts and superseded numbers are in [PROGRESS.md](PROGRESS.md); exact commands, commits, data
checksums and outputs are in [EXPERIMENTS.md](https://github.com/yiduoke/homr-research/blob/main/EXPERIMENTS.md) of the private research repo
[yiduoke/homr-research](https://github.com/yiduoke/homr-research) (experiment IDs below, e.g. R2s7).
Model card: [Training.md](Training.md); weights: release
[meteracc_checkpoints](https://github.com/yiduoke/homr/releases/tag/meteracc_checkpoints). Last updated 2026-11-16.

## 1. Claim in one paragraph

Optical music recognition (OMR) of printed piano music is close to solved for plain classical
textures (96-99.6% of notes fully right on Bach, Mozart, Beethoven) but not for dense Romantic
virtuoso music (34-76% on Liszt, Rachmaninoff, Chopin). Starting from homr's model 566, we
(1) teach the model to read what is printed rather than what it means - complete time
signatures and printed accidentals - and compute meaning in code, (2) evaluate every change
with a control run, seed repeats and a frozen pipeline, and (3) show where the remaining loss
is: 64% of notes with correct pitch but wrong timing are tuplets, mostly unmarked in print.
The released model beats 566 on 7 of 9 scored pieces (mean notes F1 80.1 vs 78.9 on the eight
older references) and writes printed signs that 566 cannot. Missing notes and timing errors (mostly tuplets) remain
the main loss.

## 2. Contributions

1. Complete time signatures (34 numeric meters + C + cut C) carried across systems and pages
   (run 1; homr previously predicted only the denominator and guessed the numerator).
2. Printed-accidental labels ("#", "b", natural, "##", "bb", none) with rule-based decoding of
   the sounding pitch (key signature, carry within the bar per staff and octave, ties) and
   MusicXML output with both `<accidental>` and `<alter>` (run 2).
3. Label-versus-image audits before every relabeling (time signatures, beams, accidentals) for
   each renderer (MuseScore, Verovio, LilyPond): labels must describe what the image shows.
4. An evaluation protocol: one frozen pipeline for every model, a control run that isolates the
   label change from the fine-tuning recipe, seed repeats, page-level regression checks, and
   meter / key / printed-sign metrics alongside per-note F1.
5. An error analysis of timing (tuplets, meter, voices) on real virtuoso music, including a
   documented case of intentionally irregular notation (Liszt, Mazeppa; Henle 2023).
6. Released weights, code, references and audio (fork of homr, AGPL-3.0).

## 3. Model and training

- Architecture (unchanged from upstream 566): ConvNeXt-tiny encoder (first three stages,
  ImageNet-initialised by upstream), 16x80 grid of 512-d image tokens with factorised position
  codes, 8-layer transformer decoder (width 512, 8 heads, cross-attention), six output heads per
  symbol (rhythm, pitch, lift/accidental, staff position, articulation, slur/beam); greedy
  decoding, up to 608 symbols per system; input one system, 256 x 1280 px. About 13M encoder
  and 47M decoder parameters at run time. Upstream trains it for 30-35 epochs from scratch.
- Lineage: Polyphonic-TrOMR (NetEase, ICASSP 2023; ResNet+ViT encoder, 4+4 layers, width 256;
  released checkpoint from epoch 47) -> homr (liebharc/homr, own from-scratch runs since 2024)
  -> model 566 (13 Nov 2026) -> our fine-tunes.
- Fine-tuning recipe (all runs): 2 epochs, LR 2e-5, batch 16 x 2 accumulation, one RTX 3090,
  about 1 hour per run. New vocabulary rows start from the old row of the same denominator;
  the accidental head is re-initialised when its label meaning changes.
- Training data (computer-rendered only): 70,000 staffs from GrandStaff, OpenScore Lieder and
  PDMX (licence-clean subset, original complexity range) plus the fork's octave-bracket staffs
  (LilyPond and MuseScore renders), 13,798 bracket exposures per epoch; total 108,884 staffs.
  Evaluation pieces were removed from every source; labels were regenerated for the same images
  and verified against them (`run/audits/`).

## 4. Evaluation set and protocol

| Piece | Source of test PDF | Reference | Notes |
|---|---|---|---|
| Liszt, Mazeppa (pp. 3-16) | real scan, Soviet edition (1852 text) | transcribed by Claude, partly checked | irregular notation, see section 7 |
| Liszt, La Campanella | MuseScore 2.3 engraving | Claude, partly checked | |
| Rachmaninoff, Prelude Op. 3 No. 2 | LilyPond 2.18 | Claude, partly checked | four-staff climax |
| Bach, WTC I Prelude and Fugue BWV 848 | LilyPond 2.9 | KernScores (humdrum-tools/bach-wtc) | different edition |
| Mozart, K. 331 theme; K. 309/1 | LilyPond 2.10 | KernScores mozart-piano-sonatas | |
| Beethoven, Op. 13/1 | LilyPond 2.12 | KernScores beethoven-piano-sonatas | |
| Chopin, Ballade No. 4 | LilyPond 2.18 | transcribed by Claude (another session), unchecked | 96.8% pitch agreement with our output |
| Stravinsky, Petrushka (3 movements, piano) | real scan (image PDF, 37 pp.) | none yet | many meter changes; candidate second real-scan reference |

Pipeline (frozen, identical for every model; `run/eval_run1/`): pages rendered at 150 dpi,
upstream's staff cutting, one homr call per piece, pages joined by `merge_pages.py` (keeps
page-start time signatures for meter-carrying models; leaves printed accidentals alone),
scored with `validation/score_notes.py`: per-note precision/recall/F1 for pitch inventory,
pitch+onset, pitch+onset+duration ("notes fully right"); plus meter (exact signature, changes
found, share of bars with the right meter), key signatures, and printed accidentals per class.
Known pipeline loss: two pages (Mazeppa p. 11, Rachmaninoff p. 5) lose their notes when parts
are matched by id, identically for all models.

## 5. Results (released model meteracc-r2s7-afae0e3 vs upstream 566)

Notes fully right (pitch + onset + duration F1, %):

| Piece | 566 | Ours | Copista 28M | Audiveris 5.11 | Transcoda v2.1 |
|---|---|---|---|---|---|
| Mazeppa | **34.8** | 33.6 | 27.6 | - | 16.7 |
| La Campanella | 68.0 | **71.8** | 39.4 | 36.5 | 52.5 |
| Rachmaninoff Op. 3/2 | 57.8 | **61.7** | 37.9 | 57.7 | 46.1 |
| Bach prelude BWV 848 | 91.4 | **94.0** | 93.4 | 93.2 | 93.1 |
| Bach fugue BWV 848 | **86.0** | **86.0** | 83.4 | 71.4 | 69.6 |
| Mozart K. 331 theme | **99.6** | **99.6** | 99.4 | 99.2 | 99.2 |
| Mozart K. 309/1 | 96.9 | **97.1** | 97.2* | 93.1 | 91.9 |
| Beethoven Op. 13/1 | 97.0 | **97.2** | 91.3 | 76.1 | 89.2 |
| Chopin Ballade No. 4 | 74.2 | **75.5** | 64.2 | 53.5 | - |
| Mean (first 8) | 78.9 | **80.1** | | | |

(*Copista slightly ahead on K. 309. Other engines were run with their own page handling and our
joiner; LEGATO and rokot-omr-2b scored lower, see EXPERIMENTS E4.)

- Accidental correctness on matched notes only (same letter, octave and onset as the reference,
  both hands; `run/eval_run1/accidental_eval.py` with score_notes' bar alignment): sounding pitch
  right on 99.0% of 16,494 matched notes vs 96.7% for 566 (run 1 95.9%). This excludes missed,
  extra and mistimed notes, so it is not transcription accuracy; that is "notes fully right"
  above. Never quote it without this qualifier.
- Printed accidentals (pooled over the eight older pieces; 566 writes none): sharp 92.5,
  flat 93.4, natural 90.0, double sharp 94.3, no sign 99.0 F1. Remaining errors are partly
  reference issues (cautionary naturals in K. 309, La Campanella). (An earlier version of the
  scorer read only the right hand and gave 99.0 / 97.2 on half the notes.)
- Time signatures: reads C and cut C (Pathetique 5 of 6 printed signatures exact; 566: 0).
  Weakness: a misread meter is carried until the next printed one (Pathetique: 3 of 5 changes,
  60% of bars in the right meter vs 100% for 566; Mazeppa: 83% vs 82%).
- Key signatures: unchanged on classical pieces (100%); Mazeppa 91% of bars.
- Speed (branch `speed`, identical output): 1.6x faster on whole pieces under load, ~2.75x on
  a quiet machine (Apple M4 CPU); ~7-9 s per page before.

## 6. Ablations (EXPERIMENTS R1, R2, R2s7)

| Step (one change each) | Mazeppa | Campanella | Rachmaninoff | Bach fugue | Mean of 8 |
|---|---|---|---|---|---|
| 566 | 34.8 | 68.0 | 57.8 | 86.0 | 78.9 |
| Control: fine-tuning recipe only (old labels) | 33.6 | 66.7 | 59.0 | 82.4 | 78.1 |
| Run 1: + complete time signatures | 35.8 | 69.9 | 58.9 | 82.4 | 78.6 |
| Run 2: + printed accidentals (seed 42) | 33.7 | 72.1 | 63.5 | 86.3 | 80.1 |
| Run 2 repeat (seed 7, released) | 33.6 | 71.8 | 61.7 | 86.0 | 80.1 |

The recipe alone costs up to 3.6 points on classical pieces; meter adds 2-3 on Liszt; printed
accidentals add 2-5 on accidental-heavy pieces. Identical runs differ by up to ~1.8 points on a
single piece, so conclusions use two seeds.

## 7. Error analysis (EXPERIMENTS A1)

Of notes with the right pitch but wrong timing (5,517 notes, 9 pieces): tuplets 64%, bar
length / meter 17% (cadenza-like bars; one Mazeppa meter misread), voices 6%, grace notes 4%,
rests 3%, alignment 3%, length only 1%. Tuplet notes are 44% of Mazeppa, 27% Rachmaninoff,
24% Chopin, under 1% of the classical pieces. Most are unmarked in print (beamed groups whose
number the reader infers from the beat); the model also ignores printed numbers (Pathetique
6 and 7). Training-style validation staffs score 99.2% fully right but contain only 2.5% tuplet
notes, so the gap is the data, not a general timing weakness.

Pitch errors (EXPERIMENTS A2; 4,548 errors): 35% are bars lost to page layout (ossia pages,
four-staff systems), 14% extra notes, 11% octave errors (mostly under printed 8va brackets the
model missed: La Campanella 229 of 293), 11% right pitch on the other staff (Bach fugue: voices
crossing staves; staff-agnostic pitch F1 99.3 vs 87.6, so report staff-agnostic scores too),
11% whole notes missing, 9% chord members missing, 6% accidentals. So the largest fixes are
layout handling (staff grouping, joining) and restoring the fork's octave-bracket strength,
not general note reading.

Mazeppa is irregular by design: in the 1852 version the outer voices lack rests on beats 2
and 4 from the theme on, which Henle judges intentional (Peter Jost, "Gaps in the notation:
Liszt's Mazeppa étude", Henle blog, 13 Feb 2023,
https://blog.henle.de/en/2023/02/13/gaps-in-the-notation-liszts-mazeppa-etude/); the 1839
version is in 6/4 with unmarked triplets. Our edition also has bars (29-30) holding six beamed
groups under C. Timing on such bars has no single correct answer; report with and without them.

## 8. Related work and comparisons (details PROGRESS "Benchmarks", EXPERIMENTS E1, E4)

- Sheet Music Transformer / SMT++ (Alicante; full-page, **kern; CER 10.5 Mozarteum and 19.6
  Polish Scores after fine-tuning on <100 pages).
- OLiMPiC (Prague; scanned Lieder test set 1,493 systems, SER 17.7). Overlaps our Lieder data:
  remove its pieces before reporting on it.
- LEGATO (ICLR 2026, vision-language model, ABC output); Copista 28M (KobiMusic, detector +
  rules, best on the IMSLP-Piano-Scores leaderboard, 0.164 OMR-NED); Audiveris; Transcoda v2.1;
  rokot-omr-2b.
- Benchmarks to report: Polish Scores (homr's required check), SMB (Alicante; access requested
  2026-11-15), MuseScore's OMR benchmark (1,077 synthetic-but-degraded pairs), IMSLP-Piano-
  Scores leaderboard (32 real pages), OLiMPiC scanned test. Not run yet.

## 9. Limitations (state in the paper)

- Seven of nine scored pieces are digital engravings; only Mazeppa is a real scan. The bracket
  test set (73 real scan pages, 322 hand-counted octave brackets) has no note references.
- Three references are Claude transcriptions checked only in part, a fourth (Ballade) unchecked;
  the owner (a pianist) listened and judges them roughly 99%+ right but audibly not perfect
  (2026-11-16), so scores near the top carry about a point of reference noise; KernScores references are
  other editions (and lack C / cut C symbols); the Ballade reference is also a Claude
  transcription (unchecked). Four of nine references are Claude-made.
- Single training runs except run 2 (two seeds). No experiment on real-scan training data yet.
- Meter carry propagates misreads; tuplets and cadenzas are unsolved.

## 10. Still to do before writing

1. Run 3: printed tuplet numbers (see PROGRESS, "Run 3"), then the bar-fill repair for unmarked
   tuplets.
2. More real-scan references (KernScores scans, the owner's meter test set), and the owner's
   bar-by-bar check of the three Claude references (due mid-February 2027).
3. Outside benchmarks above, with training-overlap checks.
4. Real-scan training pairs (168 KernScores pieces ready) as a separate experiment.
5. Disclose AI use (PROGRESS "Reproducibility and AI use").
