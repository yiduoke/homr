# Virtuoso real-scan pairs, batch 2, 2026-11-17

Second batch of verified (scan crop of one piano system, tokens) pairs from IMSLP scans, labels from ASAP MusicXML. Same method as the pilot (`../README.md`) plus the fixes learned since. Laptop only (released weights
`pytorch_model_meteracc-r2s7-afae0e3`, homr `integration_wt` code, `HOMR_FIXED_MARGIN=1`; labels with the fixed tuplet converter of `run/tuplet_wt`, branch `tuplet-fix`); **no homr code changed, the PDFs are untouched, the frozen pilot lists are untouched**.
Built 5:10-6:00 pm Pacific, 2026-11-17. Cloud boxes were not used.

## What is new against the pilot

1. **Labels** come from `training.omr_datasets.tuplet_tokens.fixed_tuplets(typeless_rests=True)`: printed tuplet values are kept (4:3 becomes plain, 5:3 becomes 5:4, ...), bar rests without `<type>` are bar rests (not `rest_8`), tuplets with no token are rejected. Rounded groups are listed in the manifest (`rounded_groups`); only 2 kept crops have one (`lists/batch2_train_rounded.txt`).
   Extra rhythm checks on every crop: MusicXML bar longer than the meter (cadenza) and token sum differing from the MusicXML outside a rounded group both quarantine the crop (the pilot audit found 12 % of its labels failing such checks).
2. **Octave handling**: label and the model's read must agree on whether the system carries an 8va/8vb; the pitch-class-agree-octave-differs case is treated the same. Disagreeing crops (47) are in `lists/batch2_*_octave_unverified.txt` (every one, also the admitted), were **reviewed by eye** (scan region with margin above, Verovio engraving of the label measures, per-note octave deltas against the read; `octave_review.md`, `octave_review.csv`, sheets in `work/sheets/oct`), and only verified ones are admitted: 7 label right as is, 27 with corrected tokens (`octave_review/tokens_corrected/`, originals in `tokens_uncorrected/`), 16 quarantined. Three more crops of the kept tiers whose label bracket extent differs from the print were found by an extent check and quarantined (`lists/*_octave_quarantine_final.txt` has all of them). Nothing octave-unverified is in a training or validation list.
3. **Clef/key**: kept crops whose first-measure clef or key signature in the tokens differs from the model's read are listed in `lists/clef_key_disagree.txt` (62; 52 clef, 10 key). They stay in the lists (sensitivity list). By eye 3 of 3 checked (N10_p-15_s1, NR2_p-03_s4, N1_p-03_s4) were label errors (the print has the clef the model read).
4. **Edition checks**: pages of the selected work only (found on contact sheets, `work/sheets`), systems from homr's detector (the staff-relation model found the grand staffs on every page, no pairing fallback was needed).

## Counts (crops)

| pid | piece | group | strong | hard | octave-verified | quarantined | pitch F1 | pitch+onset F1 |
|---|---|---|---|---|---|---|---|---|
| N1 | Liszt Concert Etude S.145/1 Waldesrauschen | train | 37 | 2 | 3 | 3 | 0.957 | 0.464 |
| N2 | Liszt Concert Etude S.145/2 Gnomenreigen | val | 41 | 1 | 2 | 1 | 0.968 | 0.904 |
| N3 | Liszt Venezia e Napoli 1 Gondoliera | train | 26 | 0 | 0 | 7 | 0.968 | 0.727 |
| N4 | Chopin Etude Op.10/5 | val | 20 | 0 | 1 | 3 | 0.979 | 0.612 |
| N5 | Chopin Etude Op.10/7 | train | 18 | 0 | 0 | 0 | 0.988 | 0.986 |
| N6 | Chopin Etude Op.10/8 | train | 21 | 0 | 7 | 3 | 0.991 | 0.981 |
| N7 | Chopin Etude Op.25/8 | train | 14 | 0 | 0 | 3 | 0.977 | 0.715 |
| N8 | Chopin Berceuse Op.57 | train | 21 | 0 | 4 | 5 | 0.973 | 0.792 |
| N9 | Chopin Sonata 2 mvt 1 | train | 32 | 0 | 2 | 8 | 0.961 | 0.750 |
| N10 | Chopin Sonata 2 mvt 3 Marche funebre | train | 15 | 1 | 0 | 2 | 0.977 | 0.897 |
| N11 | Beethoven Op.81a mvt 3 | val | 40 | 0 | 6 | 7 | 0.991 | 0.954 |
| N12 | Beethoven Op.81a mvt 1 | val | 30 | 0 | 4 | 3 | 0.979 | 0.938 |
| N13 | Beethoven Op.7 mvt 1 | train | 61 | 0 | 0 | 5 | 0.996 | 0.946 |
| N14 | Beethoven Op.27/1 mvt 4 | train | 52 | 0 | 0 | 3 | 0.995 | 0.961 |
| N15 | Beethoven Op.31/1 mvt 1 | train | 36 | 0 | 0 | 46 | 0.993 | 0.964 |
| N16 | Rachmaninoff Prelude Op.23/4 | train | 19 | 0 | 1 | 1 | 0.982 | 0.584 |
| N17 | Rachmaninoff Prelude Op.32/5 | train | 17 | 0 | 0 | 2 | 0.982 | 0.238 |
| N18 | Rachmaninoff Prelude Op.32/10 | train | 13 | 0 | 0 | 4 | 0.991 | 0.645 |
| N19 | Ravel Miroirs 3 Une barque sur l'ocean | demets | 42 | 1 | 4 | 37 | 0.937 | 0.412 |
| N20 | Schubert Impromptu D.935/3 | train | 28 | 0 | 0 | 21 | 0.996 | 0.677 |
| N21 | Schumann Arabeske Op.18 | train | 35 | 0 | 0 | 2 | 0.962 | 0.887 |
| NR1 | Chopin Etude Op.10/10 (reserve) | train | 23 | 0 | 0 | 1 | 0.986 | 0.755 |
| NR2 | Schubert Impromptu D.935/1 (reserve) | train | 62 | 0 | 0 | 10 | 0.991 | 0.953 |

| group | strong | hard | octave-verified | quarantined | kept | pitch F1 | pitch+onset F1 |
|---|---|---|---|---|---|---|---|
| train | 530 | 3 | 17 | 126 | 550 | 0.982 | 0.811 |
| val | 131 | 1 | 13 | 14 | 145 | 0.980 | 0.886 |
| demets | 42 | 1 | 4 | 37 | 47 | 0.937 | 0.412 |

all kept crops 742: pitch F1 0.979 (median 1.000), pitch+onset F1 0.801 (median 0.981)


Splits (by composition): validation extension = Liszt Gnomenreigen (N2), Chopin Etude Op.10/5 (N4), Beethoven Op.81a mvts 1 and 3 (N11, N12) (octave brackets 15-20 each in ASAP, repeated notes); `lists/batch2_val*.txt`, never train. Ravel Une barque (N19, Demets reprint of the book of the Alborada test scan) only in `lists/batch2_train_demets_unebarque*.txt`.
All other pieces: `lists/batch2_train_*.txt`. `batch2_train_all.txt` = train strong + hard + octave-verified (550, without Demets). The two reserves (NR1 Op.10/10, NR2 Schubert D.935/1) are included in train (85 kept).
Test exclusion check (done again per piece against `run/test_set_exclusions.txt` and `run/test_set_plan.md`): no composition here is listed (the Op.10/4, Op.25/10-11, Op.23/2, D.899/4, Miroirs 4, Waldstein/Appassionata/Hammerklavier, Schumann Toccata/Kreisleriana 1 entries are different works; the Demets scan is not the Alborada test scan). Note: Chopin Sonata 2 is split as in the pilot (pilot val = mvt 2, pilot train = mvt 4, batch 2 train = mvts 1 and 3).

## Verification (by eye)

- **strong: 46 random crops (2 per piece, 23 pieces, seed 20261118): 0 wrong** (95 % Clopper-Pearson upper bound 7.7 %). Sheets `work/sheets/eye_strong`.
- **hard: all 7 hard crops that survived the guards checked: 2 wrong** (N9_p-04_s0: label 7 bars, print 6; N11_p-15_s1: ASAP has an 8va over bar 1 where the print writes the notes at pitch). Both are quarantined (`eye` column); 5 hard crops kept (4 train, 1 val). Hard rate 2/7 = 29 % (95 % interval 3.7-71 %). Strong + hard pooled 2/53 = 3.8 % (0.5-13 %).
- octave review: 50 crops viewed or analysed (see above); the 27 corrected ones also pass an automatic check: after the correction 92-100 % (mostly 100 %) of the aligned notes equal the model's read of the scan.
- Verovio label renderings can show a bracket that the XML never closes (ASAP Schubert D.935/3 has unmatched octave-shift directions); the tokens, not the rendering, are the label.

quarantine reasons (a crop can have several; total 177):
- not music of the piece (before start / after end): 52
- duration/tuplet not representable (no token): 31
- rhythm: token sum differs from MusicXML (volta/repeat split, cadenza): 22
- ledger lines > 5 (trainer filter): 21
- octave review: not admitted (label wrong / edition difference / partial): 20
- rhythm: MusicXML bar longer than the meter: 12
- bar mismatch: 10
- alignment ambiguous: 9
- trainer filter (vocabulary/length): 6
- edition/key mismatch: 3
- crop not one grand staff: 2
- wrong by eye: 2

octave roles of kept crops:
train {'kept': 550, 'has_8va_token': 73, 'start_inside_8va': 28, 'continue_through_8va (starts inside, no stop)': 12, 'end_an_8va (starts inside, stop in crop)': 16, 'open_at_end (continues into next system)': 29, 'bracket starts and stops in the crop': 30}
val {'kept': 145, 'has_8va_token': 62, 'start_inside_8va': 30, 'continue_through_8va (starts inside, no stop)': 13, 'end_an_8va (starts inside, stop in crop)': 17, 'open_at_end (continues into next system)': 33, 'bracket starts and stops in the crop': 21}
demets {'kept': 47, 'has_8va_token': 20, 'start_inside_8va': 4, 'continue_through_8va (starts inside, no stop)': 3, 'end_an_8va (starts inside, stop in crop)': 1, 'open_at_end (continues into next system)': 4, 'bracket starts and stops in the crop': 15}
ALL {'kept': 742, 'has_8va_token': 155, 'start_inside_8va': 62, 'continue_through_8va (starts inside, no stop)': 28, 'end_an_8va (starts inside, stop in crop)': 34, 'open_at_end (continues into next system)': 66, 'bracket starts and stops in the crop': 66}


"not music of the piece" = systems before the piece starts or after it ends on the extra pages kept for safety (mostly N15 Op.31/1 pages 10-13 after the end of mvt 1, Ravel title/neighbours, Op.81a mvt 2 on p8). Without them the quarantine is 125.

## Octave brackets in the kept crops (for the multi-system continuation weakness)

From the final tokens and the XML bracket state ("starts inside" = the bracket began in an earlier system and is re-opened at the system start by the cutter):

| | kept | with an 8va/8vb token | start inside an 8va | continue through (start inside, no stop) | end an 8va (start inside, stop in crop) | open at the end (continues into the next system) | start and stop in the crop |
|---|---|---|---|---|---|---|---|
| train (A) | 550 | 73 | 28 | 12 | 16 | 29 | 30 |
| validation | 145 | 62 | 30 | 13 | 17 | 33 | 21 |
| Demets (Une barque) | 47 | 20 | 4 | 3 | 1 | 4 | 15 |
| all | 742 | 155 | 62 | 28 | 34 | 66 | 66 |

(The pilot had 122+2 crops with a bracket of 864, 47 starting inside.) Batch 2 adds 62 start-inside crops, 28 of them continuing through the whole system, but the Demets/train share of continuations is small: 12 + 3 train/Demets crops continue through, 13 are in the validation lists.
Of the 27 corrected crops, 20 are edition differences (Op.81a, Op.10/8, Berceuse, Sonata 2: the print writes the notes at pitch, ASAP has 8va): bracket removed, notes raised, as the print shows; 7 add a bracket that the ASAP label lacks and the print has over whole bars (Waldesrauschen 1, Op.10/5 1, Op.81a mvt 1 1, Une barque 4; notes lowered where ASAP held sounding pitch). Quarantined after review (16): 7 Schubert D.935/3 variation crops whose printed 8va covers part of the system and is missing in ASAP (partial spans, not corrected), 2 that exceed 5 ledger lines once raised, 1 time-signature difference (Op.25/8), 6 with unclear or partial bracket extent.

## Caveats

- Ravel Une barque: the ASAP file has an empty third staff (removed, script only: `labels2.xml_text`), voices a few ticks short of their backup (tolerance 12 ticks of 480 per quarter, note values come from `<type>`), many 13:8-like tuplet groups with no token: 24 conversion errors and 37 quarantined of 84 systems. Gondoliera: ASAP has 4 staves, the first two empty (removed, staves 3,4 renumbered). Schubert D.935/3 has one 256th note (read as a 128th; its crop is quarantined by the rhythm check).
- Chopin Op.25/8: the print has 12/8 eighths where ASAP has 4/4 with triplets (same music); one crop with the time signature was quarantined, the rest keep triplet kerns.
- Schubert D.935/3: 11 crops quarantined because a repeat sign sits inside a measure (token bar structure differs from the XML).
- Rachmaninoff Op.32/10: the 3-page PDF holds the first 48 of the 62 ASAP measures; Op.31/1: only mvt 1 is paired, the pages after its end are 'not music of the piece'.
- Chopin Etude Op.10/5: page 19 was added after a first run ended at measure 72 of 85.
- ASAP text differs from the print in places (Klindworth, Breitkopf Serie 16 print high notes at pitch where ASAP has 8va: handled above).

## Files

`images/<pid>/<crop>.png`, `pages/<pdf>/p-NN.png` (150 dpi, pages with systems of the kept crops), `tokens/` (final tokens), `tokens_uncorrected/` (originals of the 27 corrected), `octave_review/tokens_corrected/`, `manifest.csv`
(crop, page_image, page_bbox_xyxy, system_index, piece, pid, edition, group T/V/D, asap_measure_range, tier strong|hard|octave_verified|quarantine, verification, pitch_f1 (aligned), read_pitch_f1, read_onset_f1 (against the final tokens), bar_counter_groups, label_bars, rounded_groups, octave_roles, octave_review, clef_key_disagree, eye, reasons),
`quarantine.txt` (`image,tokens,reasons`), `lists/` (`image.png,tokens.tokens` per line, paths relative to `run/`, same format as the pilot), `report.md/json`, `octave_review.md/csv`, `scripts/`, `work/` (reads, assignments, per-system records `export/`, detection crops, sheets).

## Reproduce

`scripts/render_pages.sh`; `scripts/run_detect.sh pdf:pages`; `scripts/queue_reads.sh pdf...`; `scripts/run_all.sh N1 ... NR2` (align + export2 with the fixed converter); `scripts/octave_delta.py all`, `stack_sheets.py`, `octave_decide.py` (decisions); `scripts/assemble2.py`; `scripts/report2.py`.
Interpreter `/Users/yiduoke/Documents/homr/.venv/bin/python`. Piece pages: `scripts/pieces2.py`.
