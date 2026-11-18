# Bar-rest label audit of the main training data (D27)

2026-11-17, 6:30-7:00 pm Pacific. Read-only on vast-homr4 (token files, MusicXML, lists; scripts and outputs in `/workspace/audit_barrest/`, `nice -n 19`, 3 processes, no training touched, vast-homr5 not used) and on the laptop (pilot, saved test-page outputs). Audit only: no list, token file or model was changed. No test composition or evaluation data was used for any training action.

## Summary

1. **The bug is not in the main training data.** The bug (a rest without `<type>` and without `measure="yes"` becomes `rest_8`) needs a typeless `<rest/>` in the MusicXML. Of **56,441** source-score XML files behind the training and validation lists (52,512 + 3,929, per source, overlaps counted) **none** holds one (0 typeless rests; 430k `measure="yes"` rests and 2.5M typed rests). Every one of them is a MuseScore Studio 4.6.5 export (the data pipeline re-exports everything; the meter-arm windows are generated). 69 training ids (42 LilyPond, 27 octave; names ending in `v2`) could not be matched to a file, and the kern sets have no XML (typed kern rests, see below). The ASAP XML as downloaded (MuseScore 2.3 / 3.x, Finale, Dorico) does have them: **138 of 211 files, 4,465 typeless rests against 70 `measure="yes"`**. So the bug exists only where labels are made straight from original ASAP XML: the scan-pair pilot.
2. **Detector result on the main lists: 820 of 149,891 training staves flagged (0.55 %), 891 of 645,993 bars (0.14 %); validation 29 of 7,012 (0.41 %).** These are not the bug: the XML of the 57 sampled flagged staves (up to 10 per source; 55 with an XML found) has, in 52, a typed eighth rest (`<type>eighth</type>`) in pickup bars (m0: 60 % of all flags are in the first bar of the staff, 19 % in the last) or in a voice that rests while a second voice plays. The detector marks suspects for review; it cannot tell a pickup rest from the bug without the XML.
3. **Staves that would change by the typeless rule: 0** in every main training and validation list (no typeless rest to convert), so no re-conversion of the main data is needed. Still wrong after the pilot's fix: **2 pilot hard crops** (`A13_p-11_s4`, 5 bars; `A10_p-12_s2`, 1 bar), found by the detector in `lists/pilot_scan_v2.txt`; their corrected tokens already exist (`scan_pairs_virtuoso/work/tuplet/regress_*.tokens`).
4. **The released model does not carry the bug.** On the 190 label bars of the 82 pilot crops where the label has the bar rest as `rest_8` (and the bar count of label and read agree), the stored free-generation read has a single rest token in 170 bars (`rest_2.` 110, `rest_1` 36, `rest_4.` 24), never `rest_8`. No model trained so far used the buggy labels (the pilot arm is prepared, not launched, D19).
5. **On the 29 saved test-scan pages** the final MusicXML has a bar rest of the wrong length in 29 of 227 rest-only staff bars (12.8 %; 0.23 % of 12,719 measures; Petrushka with its meter changes left out, see Task 3): 24 are longer than the bar (21 of them one whole rest, 4 quarters, in a 3/4 bar), 4 are shorter, 1 is a measure rest of another length. This is the writer reading a bar rest as a whole rest, not the label bug. It touches no pitch, and onset only in the bar's staff: it cannot move the pitch benchmarks.

Side finding: the converter writes `rest_1` for a bar rest in a meter it has no token for (3/2, 9/8, 5/4, 5/8, 7/8, ...): 592 bar-rest staff bars in the training lists (4.0 % of the single-rest bars with a known meter). See the plan.

Correction to the task brief: **the model vocabulary has no `measureRest` token.** `measureRest` is a symbol the decoder and the writer create (hidden staves, `homr/staff_parsing.py`, `music_xml_generator.py`); the vocabulary has `rest_N` and the multirests `rest_Nm`. The converter writes a bar rest as a typed rest of the bar's length (`_measure_rest_rhythm`: 4 quarters rest_1, 3 rest_2., 2 rest_2, 1.5 rest_4., 1 rest_4, 0.75 rest_8., 0.5 rest_8, anything else rest_1). So the pilot fix produces `rest_1` / `rest_2.` ..., not `measureRest`.

## Task 1: detector

`detect_barrest.py` (this folder; no dependencies beyond the standard library). Input: token files (`image,tokens` lists). Rules:

- A measure is the run of lines between two barline lines; a track is one position tag (`upper`, `upper2`, `lower`, `lower2`), a chord counts once. Durations are exact fractions of a whole note (kern number, dots, tuplet kerns; grace notes count 0).
- Bar length: the last `timeSignature_*` token (`common` and `cut` = 1) at or before the measure; if none, **inferred** as the most frequent longest-track total of the staff's measures that hold a note (2 agreeing measures, or all agree); if neither, **unknown**.
- Suspicious primary track (`upper`, `lower`) that holds only rests and is shorter than the bar: `rest_8` alone (**rest_8 alone**, the typeless signature); a measure in which every track is rest-only and none fills the bar (**all-rest short**, e.g. rest_16 + rest_4 in 4/4); a lone `rest_8` where the bar length is unknown (**unknown**). Never flagged: a track as long as the longest track of a short measure (pickup, split bar); the single typed bar-rest token the converter writes for this bar length; a voice-1 rest that starts after the bar's first time step while a second voice plays. Rest-only tracks that are longer than the bar (`over`) and other short rest tracks (`other_short`, mostly a voice that rests) are counted, not flagged.
- Counts per staff: bars, bars by meter basis (known / inferred / unknown), flagged bars, per kind; details per flagged bar with `--details`.

**Validation (token files of the pilot, `data/control_*.tsv`, `data/pilot_*_details.tsv`):**

| set | staves | flagged | note |
|---|---|---|---|
| positive control: the 86 known crops (79 train + 7 val), frozen tokens | 86 | **86** (84 with a known or inferred bar, 2 with bar length unknown, all bars `rest_8`) | 181 rest_8 tracks in 168 bars |
| same crops, fixed tokens (`tokens_typeless_rest_fixed/`) | 86 | **0** | the fix removes every flag |
| negative control: 100 random strong crops without the bug (seed 20261120) | 100 | **0** | |
| all 785 other strong crops | 785 | **0** | 20 `other_short` voice rests, not flagged |
| whole frozen pilot (`pilot_scan.txt`) | 867 | 80 | includes hard crops not in the 86 |
| pilot v2 (`pilot_scan_v2.txt`) | 881 | **2** | `A13_p-11_s4`, `A10_p-12_s2`: both really have the bug (regress tokens differ only in the rest) |
| batch 2 v2 (train + val) | 665 | 0 rest_8; 2 all-rest short | partial final bars, not the bug |

Sensitivity and specificity on the pilot: 86/86 and 785/785 (100 random: 100/100), with one false positive class excluded by design (the lone voice-1 rest of a second-voice bar). On the main data the specificity cannot be measured with token files alone (see Task 2).

## Task 2: full training and validation lists

Lists: `/workspace/run3/B_train.txt` (149,891 lines = control `run2_train_excl_v3.txt` 107,444 + candidate additions 24,044 + meter arm 14,998 + KernScores scan pairs 3,405; the control and candidate lists are subsets) and `B_val.txt` (7,012; contains `cand_val_v3.txt`). The released model's training data is the control. Per source (the set by path of the image/token file); `typeless rests in XML` is the regex scan of the source XML (`xml_scan.py`).

#### train

| source | staves | staves flagged | % | suspicious bars | bars | % of bars | rest_8 alone | all-rest short | rest_8, bar unknown | XML scores scanned | typeless rests in XML |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PDMX | 34,767 | 314 | 0.90 | 360 | 148,458 | 0.24 | 234 | 129 | 8 | 18,206 | 0 |
| hard PDMX | 31,075 | 11 | 0.04 | 11 | 117,090 | 0.01 | 6 | 5 | 3 | 10,490 | 0 |
| ASAP (4.6.5 re-export) | 3,561 | 5 | 0.14 | 5 | 11,021 | 0.05 | 3 | 2 | 1 | 336 | 0 |
| Scriabin (4.6.5 re-export) | 2,432 | 2 | 0.08 | 2 | 10,526 | 0.02 | 2 | 0 | 0 | 388 | 0 |
| Lieder | 10,914 | 150 | 1.37 | 156 | 39,185 | 0.40 | 72 | 96 | 1 | 3,269 | 0 |
| GrandStaff (kern) | 10,036 | 2 | 0.02 | 2 | 47,142 | 0.00 | 0 | 2 | 0 | n/a (kern) | n/a |
| LilyPond | 29,695 | 274 | 0.92 | 289 | 166,105 | 0.17 | 126 | 176 | 0 | 5,634 | 0 |
| MuseScore octave sets | 9,008 | 33 | 0.37 | 33 | 33,048 | 0.10 | 12 | 21 | 1 | 1,555 | 0 |
| KernScores scan pairs (kern) | 3,405 | 14 | 0.41 | 15 | 17,510 | 0.09 | 3 | 13 | 0 | n/a (kern) | n/a |
| meter arm | 14,998 | 15 | 0.10 | 18 | 55,908 | 0.03 | 6 | 13 | 0 | 12,634 | 0 |
| **total** | 149,891 | 820 | 0.55 | 891 | 645,993 | 0.14 | 464 | 457 | 14 | | |

#### val

| source | staves | staves flagged | % | suspicious bars | bars | % of bars | rest_8 alone | all-rest short | rest_8, bar unknown | XML scores scanned | typeless rests in XML |
|---|---|---|---|---|---|---|---|---|---|---|---|
| PDMX | 2,005 | 15 | 0.75 | 19 | 8,402 | 0.23 | 12 | 7 | 0 | 1,634 | 0 |
| hard PDMX | 1,666 | 4 | 0.24 | 4 | 6,601 | 0.06 | 1 | 3 | 0 | 720 | 0 |
| ASAP (4.6.5 re-export) | 352 | 0 | 0.00 | 0 | 1,274 | 0.00 | 0 | 0 | 0 | 7 | 0 |
| Scriabin (4.6.5 re-export) | 101 | 0 | 0.00 | 0 | 390 | 0.00 | 0 | 0 | 0 | 9 | 0 |
| Lieder | 618 | 9 | 1.46 | 9 | 2,281 | 0.39 | 4 | 5 | 0 | 463 | 0 |
| GrandStaff (kern) | 543 | 0 | 0.00 | 0 | 2,551 | 0.00 | 0 | 0 | 0 | n/a (kern) | n/a |
| KernScores scan pairs (kern) | 227 | 1 | 0.44 | 1 | 1,275 | 0.08 | 0 | 1 | 0 | n/a (kern) | n/a |
| meter arm | 1,500 | 0 | 0.00 | 0 | 5,268 | 0.00 | 0 | 0 | 0 | 1,096 | 0 |
| **total** | 7,012 | 29 | 0.41 | 33 | 28,042 | 0.12 | 17 | 16 | 0 | | |

Where the flagged staves sit: control list 776 of 107,444 staves, candidate additions 15 of 24,044, meter arm + scan pairs 29 of 18,403. Flagged bars (921 rows incl. tracks): first bar of the staff 549, last 174, middle 198: a pickup or a partial last bar. In the validation lists 15 first, 7 last, 11 middle.

**Converter path of each source (bar rest forms):**

| source | converter | how a whole-bar rest is written |
|---|---|---|
| PDMX, hard PDMX, Lieder, LilyPond (labels from the MuseScore XML), MuseScore octave sets, ASAP and Scriabin (4.6.5 re-export, D3), meter arm | `music_xml_parser.py` `_process_note` (homr566 and `homr_acc` have the same code) | `<rest measure="yes"/>` + `<duration>` goes to `_measure_rest_rhythm` and is a typed rest of the bar (rest_1, rest_2., rest_2, ..., fallback rest_1). A `<rest/>` without `<type>` and without `measure` would take the default type `eighth` (`music_xml_parser.py` line 840) and become `rest_8`; **none exists in these XML files** |
| GrandStaff (kern), KernScores scan pairs | `humdrum_kern_parser.py` `parse_note_or_rest` (`music21_kern_parser.py` for some) | the kern rest as written: `2.r` is `rest_2.`; never measureRest. In 3/4 bars 647 of the bar-rest tracks are `rest_2.`, in 2/4 254 `rest_2`, in 3/8 214 `rest_4.`, in 4/4 175 `rest_1`; `over` = 0 in GrandStaff |
| scan pairs (pilot, batch 2) | `tuplet_tokens.fixed_tuplets(typeless_rests=True)`; the frozen pilot used the plain parser on the original ASAP XML | frozen pilot: typeless bar rest = `rest_8` (bug); v2 and batch 2: `measure` is set for a typeless rest with a duration, so rest_1 / rest_2. as above |

**Sample of 10 per affected source** (random, seed 20261120; token excerpt of the flagged bar and the XML finding): `data/examples_out.txt` (57 samples: ASAP 3, kern scans 2 without XML, Lieder 10, LilyPond 10, MuseScore octave 10, meter arm 5, PDMX 10, hard PDMX 10, Scriabin 1; GrandStaff has no `rest_8 alone` bar, its 2 flagged bars are `rest_4+rest_8` in a 2/4 bar of a final measure: `data/det_train.tsv`). In 52 of the 55 samples with an XML the matching measure shows a typed eighth rest (pickup bar m0 or a voice rest), in 3 the search found no single typed eighth rest (another rest form); all 55 files have 0 typeless rests. Three typical ones:

```
pdmx  QmV4mCHq3x...-1-2   bar 0 of the staff, 9/8, track upper = rest_8 alone
      XML  m1: <note><rest /><duration>2</duration><voice>1</voice><type>eighth</type></note>    (typed, a real eighth rest)
lieder lc6205693-3-6      bar 29, 3/4, voice 5 of staff 2: one rest_8 while voice 1 carries the bar
      XML  <rest /><duration>6</duration><voice>5</voice><type>eighth</type><staff>2</staff>
lieder lc6218732-1-4      bar 0 of 5, 6/8 (timeSignature_6/8 in the staff):  clef_F4 / keySignature_-3 / timeSignature_6/8 / rest_8 upper
      XML  m0 (pickup): <rest /><duration>1</duration><voice>1</voice><type>eighth</type>
```

Counterpart in the original ASAP XML (what the bug looks like): `<note><rest measure="yes"/>` is rare there; the typical element is `<note><rest/><duration>..</duration><voice>1</voice></note>` without `<type>`; the pilot tokens read `... & rest_8 _ _ _ _ lower`.

## Task 3: impact

- **Training staves that would change: 0** in `B_train.txt` and `B_val.txt`. The 820 + 29 flagged staves are real rests (pickups, voices). A converter fix would only act on a typeless `<rest/>`; there is none.
- **Pilot:** 86 strong crops (79 + 7) plus 2 hard crops; 190 rest_8 label bars in the 82 crops with matching bar counts. What the released model reads there (`data/model_read_at_rest8_bars.txt`, stored free-generation reads `work/reads/`, script `model_read_barrest.py`): `rest_2.` 110, `rest_1` 36, `rest_4.` 24, track absent 12, notes 6, several rests 2; `rest_8` 0. The model reads the bar rest the main data teaches (the length of the bar); the buggy label would have taught `rest_8` for a bar rest on real scans (9.1 % of the strong crops).
- **Saved test-page outputs** (`run/eval_run1/testset/layout1/*/joined.musicxml`, final writer output; script `musicxml_barrests.py`, table `data/test_pages_barrests.tsv`). Per staff and measure that holds only rests, the staff's total against the time signature in force:

| outputs | measures | rest-only staff bars | equal to the bar | shorter (rest_8-like) | longer (rest_1 in a short bar) | measure rest with another duration |
|---|---|---|---|---|---|---|
| 29 scan pages | 14,377 | 443 | 312 | 4 | 25 | 102 (101 Petrushka) |
| same without Petrushka | 12,719 | 227 | 198 | 4 | 24 | 1 |
| 29 rendered pages | 14,487 | 570 | 420 | 34 | 37 | 79 |

  Petrushka changes its meter every few bars and the writer's measure rests there have the previous meter; it is a writer / meter question, not the label. The 24 longer ones (Hammerklavier 6, Alborada 6, Haydn 4, Pour le piano 3, others 5) are 21 times one whole rest (4 quarters) in a 3/4 bar: the model read a bar rest as `rest_1` where the main data labels `rest_2.`; the 4 shorter ones are partial rests (Prokofiev Toccata 2, Liszt HR 6, Appassionata). The writer writes the rest token's length, so a whole rest in a 3/4 bar is an overfull measure. Effect on the benchmark: none on pitch (staff-sensitive and pooled); in the onset columns at most a shift of that staff's later bars in the part clock, 0.23 % of the measures; I did not re-score.
- The D1 token files of ASAP and Scriabin (`datasets/asap/flat`, `kern_scriabin/flat`, superseded by the D3 re-exports) have 11 of 6,105 and 8 of 1,893 staves flagged, the same order as the re-exports (5 of 3,561, 2 of 2,432); not inspected, not the typeless pattern by the rate.

## Task 4: re-conversion plan (not run)

**Verdict: no regeneration of the main sets.** Expected token changes: 0 files. Do the following, in this order:

1. **Fix the converter default (code, no data effect).** In `training/omr_datasets/music_xml_parser.py` `_process_note`, move the pilot rule from `tuplet_tokens.patched_process_note` into the parser: a `<rest>` without `measure` and without `<type>` that has a `<duration>` is read as `measure="yes"`; it takes the bar rest of its duration (`_measure_rest_rhythm`) and never the default `eighth`. Where the lookup has no token for the duration, raise (quarantine the crop) instead of writing `rest_1`. Tests: typeless rest in 4/4, 3/4, 6/8, 2/4 (rest_1, rest_2., rest_2., rest_2); typed eighth rest stays rest_8; `measure="yes"` unchanged; a typeless pitched note keeps its error behaviour; regression: the 1,153 pilot crops convert to byte-identical files as in D18. Also check typeless pitched notes in the original ASAP XML (not counted here).
2. **Pilot hard crops:** replace the tokens of `A13_p-11_s4` and `A10_p-12_s2` by `work/tuplet/regress_*.tokens` in `lists/pilot_scan_v2.txt`, `lists/box/pilot_scan_v2.txt` and the twin lists (the two differ from the frozen tokens only in the rest tokens). Laptop, seconds. Re-run `detect_barrest.py` on all pilot and batch 2 lists: expected 0 `rest_8 alone`, 0 unknown.
3. **Gate for every new data set** (ASAP originals, MuseScore 2/3, Finale, Dorico, new scan pairs): `detect_barrest.py` on the tokens and `xml_scan.py` on the XML before any list is built. A flag is a suspect to look at, not a label to rewrite: 60 % of the flags in the main data are real pickup rests.
4. **Not recommended now: change the bar-rest convention** (one token for every bar rest, or a new `measureRest` class). It would rewrite the labels of about 13,800 single-rest bar tracks with a known meter, needs a vocabulary change (the vocabulary has no such token; new tokens are appended at the end), and the released model already reads bar rests as the bar length. The cheaper fix for the one residual problem (24 of 227 rest-only staff bars with `rest_1` in a short bar, plus the 592 of 14,878 single-rest bar tracks that say `rest_1` for a bar of another length) is in the writer: a track that holds a single rest token in a bar of known meter becomes a measure rest of the bar's length. No retraining; test on the saved pages with `musicxml_barrests.py` (target: longer-than-bar 24 to 0, equal-to-bar unchanged).

**Where and how long.** Nothing on the boxes is needed for steps 1-3 (laptop, minutes). A belt-and-braces re-conversion of the main token files would be parse-only (no rendering): measured on vast-homr4 with `nice`, 3 processes: detector over 157,000 token files 20 s, XML regex scan of 56,000 files about 3 min, so a full parse of the XML into tokens would take roughly 30 to 60 min (estimate, not measured), under 1 GB of output in `/workspace/audit_barrest/` (disk 6.8 GB free), expected diff 0 lines; a 2,000-file sample (minutes) is enough to confirm it. vast-homr5 is not needed.

**Risks.** (a) Changing labels of a trained distribution: the main-data labels do not change, the scan arm only moves to what the main data already teaches (bar rest = bar length), so no distribution shift is introduced; any later change of the bar-rest convention (item 4) does shift it and needs a matched control: same lists, seeds, steps and learning rate, one arm with the old and one with the new convention, scored on the saved test pages (bar-rest lengths, pooled pitch) and on the validation lists. (b) The parser rule must not turn a real short typeless rest into a bar rest: it keys on the duration, and the lookup raises where it has no token. (c) The detector uses inferred bar lengths (72 % of bars have no meter in their staff): a wrong inference gives a false flag, never a missed bug in the pilot controls, but an unknown bar length hides a lone `rest_8` (14 tracks, counted as unknown). (d) The 69 unmatched ids and the kern sets were checked by tokens only. (e) If the pilot arm is trained with the 2 hard crops uncorrected, 2 crops (6 bars) carry the bug: negligible, but fix it anyway.

## Files

`detect_barrest.py` (detector), `xml_scan.py`, `xml_check.py`, `xml_find_bar.py`, `examples.py` (XML evidence, run on the box), `model_read_barrest.py`, `musicxml_barrests.py` (laptop), `make_tables.py`; `data/`: `summary.json`, `tables.md`, `det_train.tsv`, `det_val.tsv` (every flagged bar), `examples_out.txt`, `xml_find_out.txt`, `xml_check_out.tsv`, control and pilot TSVs, `model_read_at_rest8_bars.txt`, `test_pages_barrests.tsv`. Box copies: `/workspace/audit_barrest/`. Commands: `python3 detect_barrest.py LIST --out out.tsv --details det.tsv`; on the box `nice -n 19 /venv/main/bin/python detect_barrest.py Btrain_part_0N --out out_train_0N.tsv`.
