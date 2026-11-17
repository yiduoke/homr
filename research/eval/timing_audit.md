# Why run2s7 gets pitches right but timing wrong

Model: `pytorch_model_acc_run2s7_658-afae0e3` (released). Read-only analysis; no reference or result file was changed.
Scripts (all in `run/eval_run1/`): `timing_audit_a.py` (Part A classifier, writes `timing_audit_a.json` with one record per note),
`timing_audit_tables.py` (tables below), `timing_audit_crops.py` (maps a predicted bar to its page and crops it from the page PNG using the
`imgpos` comments in `page-xml/`), `timing_audit_b_decode.py` (GPU box, `/workspace/audit_val/`), `timing_audit_b.py` (Part B scoring),
`timing_audit_b_preds.jsonl` / `timing_audit_b.json` (Part B data).

## Headline

* On training-style validation staffs (Part B) run2s7 is almost perfect on timing: 99.7 % pitch F1, 99.2 % pitch+onset+duration F1.
  Timing is not weak in general.
* On the scored pieces the gap between pitch F1 and full F1 is large only for the pieces whose references contain many tuplets:
  Mazeppa 80.3 -> 33.6 (44 % of reference notes are in tuplets), Chopin 96.8 -> 75.5 (24 %), Rachmaninoff 72.4 -> 61.7 (27 %),
  La Campanella 85.2 -> 71.8 (9 %). Pieces with no tuplets (Bach, Mozart, Beethoven except one bar) lose at most 3 points
  (Bach fugue 1.6, Mozart KV309 2.6, Beethoven 2.2).
* 64 % of the pitch-matched but not fully matched notes are tuplet cases, 17 % bar length / cadenza-like bars, 9 % voice confusion plus rest shift.

## Part A - per-note cause of "pitch right, timing wrong"

Method. Alignment, matching and tolerance are those of `score_notes.py` (alignment taken from each `note-scores.json`; my per-bar match counts
equal the saved totals for all 9 pieces, check column `check_ok` in the json). A reference note is a target when it is matched in the pitch inventory
but not on pitch+onset+duration; it gets its pitch partner in the aligned prediction bar (same staff and pitch, nearest onset) and exactly one cause,
decided in this order: cadenza-like bar (ref bar > 1.5 x nominal or pred > 2 x nominal) -> 5; bar pitch overlap < 50 % -> 7; ref note in a tuplet, prediction note a
spurious tuplet, or a later note of the same voice after a tuplet error, or bar length explained by tuplets written plain -> 1; grace count mismatch or a grace/cue note -> 4;
time signature differs -> 5; over/under-long bar: tuplet notes missing -> 1, extra/missing rest or `forward` gap summing to the length error -> 3, voice count differs or rests in a
voice without notes -> 2, extra/missing notes -> 8, else 5; onset right -> 6; onset wrong: rest difference equals shift -> 3, voice count differs or onset equals another reference voice's
onset -> 2, extra/missing notes -> 8, else 8. Notes in unmatched bars are not pitch-matched; listed separately.
`forward` elements written by the generator are counted as rests.

| piece | F1 pitch / +onset / +duration | ref notes | pitch-matched, not fully matched | 1 tuplet | 2 voice | 3 rest | 4 grace/cue | 5 bar length/meter | 6 duration only | 7 alignment | 8 other | ref notes in unmatched bars |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mazeppa | 80.3 / 38.7 / 33.6 | 7213 | 3239 | 1936 | 159 | 19 | 158 | 822 | 31 | 70 | 44 | 429 |
| la-campanella | 85.2 / 73.5 / 71.8 | 4250 | 575 | 265 | 94 | 35 | 16 | 40 | 2 | 61 | 62 | 28 |
| rachmaninoff-op3-2 | 72.4 / 62.6 / 61.7 | 1837 | 195 | 112 | 24 | 6 | 0 | 0 | 0 | 49 | 4 | 28 |
| bach-prelude-848 | 94.0 / 94.0 / 94.0 | 822 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| bach-fugue-848 | 87.6 / 86.2 / 86.0 | 1471 | 23 | 0 | 0 | 10 | 0 | 0 | 0 | 4 | 9 | 0 |
| mozart-kv331-theme | 99.6 / 99.6 / 99.6 | 241 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| mozart-kv309-1 | 99.7 / 97.4 / 97.1 | 2387 | 61 | 0 | 4 | 21 | 30 | 0 | 6 | 0 | 0 | 0 |
| beethoven-pathetique-1 | 99.4 / 97.4 / 97.2 | 4394 | 94 | 60 | 0 | 22 | 0 | 0 | 6 | 0 | 6 | 0 |
| chopin-ballade-4 | 96.8 / 77.3 / 75.5 | 6224 | 1330 | 1133 | 43 | 37 | 0 | 78 | 28 | 5 | 6 | 29 |
| **all** | | 28839 | 5517 | 3506 (64 %) | 324 (6 %) | 150 (3 %) | 204 (4 %) | 940 (17 %) | 73 (1 %) | 189 (3 %) | 131 (2 %) | 514 |

Sub-causes:

| sub-cause | notes |
|---|---|
| 1a reference tuplet, prediction has plain notes | 2298 |
| 1b reference tuplet, prediction has a tuplet of another ratio or position | 606 |
| 1c spurious tuplet in the prediction (plain reference) | 271 |
| 1d later notes of the voice shifted by a tuplet error | 131 |
| 1e bar too long because tuplets were written plain (the note itself is plain) | 200 |
| 5a cadenza-like bar | 693 |
| 5b time signature differs from reference (Mazeppa last page, reference 4/4, prediction 2/4) | 234 |
| 5c other over/under length | 13 |

Notes: Bach prelude, KV331, Bach fugue and the KV309 differences are small (<= 3 points). Bach fugue and KV309 losses are extra/missing notes and gaps written as
`forward` in the prediction. KV309 grace notes written as 32nd notes (4) lengthen the bar by 0.375.

### Examples checked on the page images (top two categories)

Crops are in the session scratchpad; each was produced with `timing_audit_crops.py piece bar out.png`. Bar numbers are the 1-based bar of the joined prediction.

Category 1, tuplet:

| bar | what the page shows | what the model did | verdict |
|---|---|---|---|
| mazeppa 33 (page 6) | two runs of 9 and 6 eighth notes in one 4/4 bar under "poco rall.", no tuplet numerals | reference encodes 9:4 and 3:2; model wrote 8 + 7 plain eighths in two voices, so durations are wrong while all pitches are right | confirmed; tuplet is implicit in the print, the bar can only be filled by counting |
| chopin 214 (page 15) | 3/4 bar of sixteenth notes beamed in threes, no numerals | reference 3:2 (sextuplet style); model wrote plain sixteenths, bar 4.5 quarters instead of 3 | confirmed |
| beethoven 10 (page 1) | runs with printed "6", "6" and "7" | model wrote plain 16ths for the 6- and 7-groups, bar 4.875 instead of 4 | confirmed; printed numerals were ignored |
| la-campanella 41 (page 2) | 3/4 bar of sixteenths beamed in threes | model wrote 12 notes as 1/6 tuplets plus a 1-quarter rest (spurious triplet, bar still 3.0); reference plain | confirmed (type 1c) |
| la-campanella 100 (page 7) | long 8va run in one 3/4 bar | reference has 46 notes as 23:12 tuplets; the model wrote 24 plain 32nds | doubtful: the reference encodes a free run, note count also differs; not a tuplet-logic problem |

Category 5, bar length / meter:

| bar | what the page shows | what the model did | verdict |
|---|---|---|---|
| mazeppa 7 (page 3) | unmetered run of 32nd notes across a whole system | reference bar 21.4 q, prediction 7.4 q | confirmed cadenza-like; reference-specific encoding |
| mazeppa 107 (page 12) | "poco rallentando", more than 30 eighth-note chords | reference bar 32.5 q, prediction 12.8 q | confirmed |
| chopin 133 (page 9) | cadenza with fermata and grace notes | reference bar 13.5 q, prediction 14.25 q | confirmed |
| la-campanella 79 (page 5) | one 3/4 bar of about 40 32nd notes | reference 10 q, prediction 3.9 q | confirmed |
| mazeppa 187 (page 16) | one bar with two 8va chord figures | reference 4/4, prediction 2/4 | print is ambiguous; which signature is right is not verifiable from the crop |

Also checked: mazeppa bar 80 (bass staff quarters) was classified 5 by an earlier rule; the prediction put eighth rests in a voice that has no notes and
the generator inserted `forward` gaps, lengthening the bar by 1.5 q. The final rule files such bars under 2 (voice confusion).

## Part B - training-style validation staffs

300 lines of `run2_val.txt` drawn with seed 20261116; images prepared exactly as in validation (`DataLoader._prepare_image`, validation distortions), decoded
greedily with the released checkpoint through `Staff2Score`. 294 were scorable (6 skipped: labels without pitched notes). The val list contains only PDMX, Lieder and GrandStaff
(no lilypond or musescore_octave lines). Onsets: durations summed per voice (position token) from each barline; pitch is the sounding pitch after key signature
and in-bar accidentals; bar alignment and matching as in `score_notes.py`.

| set | staffs | pitch F1 | pitch+onset F1 | full F1 | share with full F1 < 80 % |
|---|---|---|---|---|---|
| all | 294 | 99.7 | 99.2 | 99.2 | 1.0 % (3 staffs) |
| pdmx | 210 | 99.9 | 99.2 | 99.1 | 1.0 % |
| Lieder | 44 | 99.8 | 99.6 | 99.6 | 0 % |
| GrandStaff | 40 | 99.0 | 98.9 | 98.8 | 2.5 % |

247 of 294 predictions are token-for-token identical to the label; 24 staffs have any full-match loss, 15 are below 95 %.

The 3 staffs under 80 %: two PDMX staffs lose 29 and 35 % of notes only because a note is put on `upper` instead of `upper2` (or `lower` instead of `lower2`):
same pitches and durations, but a different voice slot makes the onset calculation differ (category 2 voice confusion and 5 for the follow-on bar length); one GrandStaff
staff has pitch F1 75.8 (pitch errors, no timing cause). Over all 294 staffs, the pitch-matched but not fully matched notes are: PDMX voice 36, bar length 22, tuplet 10,
other 8, rest 1; Lieder other 2, voice 1; GrandStaff bar length 2. In the validation data 2.5 % of notes are in tuplets (288 of 11356); only 10 tuplet notes are lost.
Reference tuplet share of the scored pieces: Mazeppa 43.7 %, Rachmaninoff 26.8 %, Chopin 24.4 %, La Campanella 9.1 %, others <= 0.8 %.

So the timing errors on real pieces are not decoding noise on in-distribution staffs: the failures come from tuplet-rich, long-run material that the synthetic validation staffs
hardly contain (a gap in the training distribution), and from the way voices, rests and bars are assembled after decoding.

## Which causes to fix first

1. Tuplets (64 %, mostly 3:2 and 9:4/6:4 groups with no printed numeral). Cheapest fix: in the generator or a repair step, when a voice's summed durations exceed the bar
   length given by the time signature, re-scale the beamed run(s) as tuplets so the bar fills (this also resolves 1e/1d and the spurious-triplet case 1c by checking against bar length).
   Then add training data with unnumbered tuplets and groups of 3 in 3/4 (validation has only 2.5 % tuplet notes).
2. Voice / rest assembly (9 %): rests written into a voice that has no notes and `forward` gaps in `music_xml_generator.py` lengthen bars by whole rest values; the only errors on synthetic
   validation are upper/upper2 slot swaps. Normalise voices per bar before writing.
3. Time signature misreads (234 notes, Mazeppa last page) and cadenza-like bars (693 notes): cadenza bars are partly reference encoding choices (46 notes as 23:12), low priority for the model.
4. Grace notes written as regular short notes (4 %, KV309, Mazeppa): small, checks the grace count per bar.

Limits: one cause per note by a fixed priority order (tuplet before bar length before voice); the sub-classifications are heuristics, checked on 10 bars (4 of 5 and 4 of 5 clearly right).
