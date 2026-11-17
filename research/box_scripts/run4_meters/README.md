# Meter arm data (run 4 / "meter arm"), built 2026-11-17 on vast-homr4

Goal: teach the model to read time-signature digits, not to prefer rare meters. New rendered staffs with all 34 numeric meters plus
common and cut C, mid-staff meter changes, system-start signatures after a change, small-print / large signatures in several
engraving styles, and staffs without a signature. Everything lives in `/workspace/run4/meters/` on the box (no existing list, token
file or run-3 directory was modified; the box trainer was not touched).

## Pipeline (scripts in this folder, run with `nice -n 19`, at most 3 processes)

1. `mine_meters.py` -> `mine_train.json`, `mining_table.py` -> `mining_table.md`: what the run-3 lists already contain.
2. `index_sources.py`: bar-level index of the source MusicXML (16,890 scores: hard PDMX, PDMX, Lieder, ASAP, Scriabin exports; only scores that
   have staffs in the run-3 lists, i.e. after the test-set exclusions by composition; the leak-hash, PDMX-hash and MuseScore-id lists are applied again).
   Per bar: meter, key, "does the bar add up to the meter", octave shifts, multi-rests, hidden signatures.
   Train pool = stems in the run-3 train lists; validation pool = stems only in the run-3 validation lists (held out by score, never by staff).
3. `xmltools.py` + `build_windows.py`: windows of 2-26 bars (one part) built from real bars. Operations: real bars; same-duration relabel
   (3/4 <-> 6/8, 2/4 <-> 4/8, 4/4 <-> 2/2, 6/4 <-> 3/2 <-> 12/8, 6/8 -> 12/16, C / cut C symbols); every note value halved or doubled
   with the beat type (4/4 -> 4/8, 5/8 -> 5/16, 5/16 -> 5/8 ...); k consecutive bars joined (5/4 x2 -> 10/4, 3/4 x3 -> 9/4);
   17/16 and 19/16 as one bar of 5/16 or 7/16 joined with a 12/16 bar; real meter changes; splices of 2-6 segments from different scores with the
   same staves and clefs. Every window is checked: each bar fills its meter (pickup allowed), each note's type matches its duration, unmatched
   ties/slurs/wedges at cut points removed, layout hints, lyrics and endings stripped.
4. `render_windows.py`: Verovio 6.4.1 (5 fonts, staff scale 30-45, time-signature size by SVG edit, cautionary end-of-system signatures removed)
   and MuseScore 4.6.5 (5 fonts via `-S style`, time-signature `<scale>` in the mscx, courtesy time/key/clef signatures switched off).
   Labels come from the homr_acc parser (`music_xml_file_to_tokens` + `MeasureCutter`, commit afae0e3, copy in `code/`): current format (full meters,
   printed accidental, beams). For MuseScore the MusicXML is the one MuseScore exports from the very mscx that is drawn.
5. `tokencheck.py`, `verify_montage.py`, `partial_stats.py`: automatic bar check on the token files and montages for the by-eye check.
6. `compose_lists.py`: the lists (trainer filters, bar check clean, quotas), manifest.
7. `measure_ts.py`: time-signature height in staff spaces (heuristic).

Run order and parameters: `run_vrv_loop.sh` (restarts the Verovio renderer after a crash; Verovio segfaults on a few windows, they are skipped).

(`mining_table.py <mine json> <clean_scores.json> <out.md>`; `manifest/mining_meters.json` is the mining result, `mining_table.md` the table; the MuseScore
AppImage was unpacked with `--appimage-extract` into `ms_extract/` and is called through its `AppRun` - removed again to save disk; `-S <style>` works on the
command line, the per-job `"style"` key of `-j` job files is ignored, see findings.)

## Result (lists in `/workspace/run4/meters/final/`, same "image.png,tokens.tokens" lines as `run3/cand_train.txt`, absolute paths)

| | train `meter_train.txt` | val `meter_val.txt` |
|---|---|---|
| staffs | 15,000 | 1,500 |
| without any signature | 3,000 (20%) | 300 |
| mid-staff change / system-start signature after a change | 5,731 / 1,965 (change staffs 7,183 = 47.9%) | 624 / 178 (755) |
| small print (all staffs) | 4,869 (32.5%) | 476 |
| large / bold | 1,553 (10.4%) | 140 |
| normal size | 5,578 | 584 |
| source scores | 5,865 | 737 (held out) |

Per renderer and size class (train): vrv/small 3,136, vrv/normal 3,641, vrv/large 1,011, ms/small 2,972, ms/normal 3,329, ms/large 911. Fonts: Verovio Leipzig 1,613,
Bravura 1,546, Gootville 1,538, Leland 1,509, Petaluma 1,582; MuseScore Leland 1,495, Bravura 1,371, Petaluma 1,450, MuseJazz 1,457, Gonville 1,439.
Kinds: splice 7,464, alt (T X T Y ...) 1,535, real 1,445, halve 1,327, realchange 894, equiv 854, sym 488, double 480, merge 428, merge2 85.
Staffs by what they print: common meters only 6,554, rare meters only 3,689, both 1,757; 59.8% of the start signatures are one of
3/4 4/4 2/4 6/8 3/8 2/2 C cut (the real data: about 85% of the printed signatures). Per-meter counts (staffs that print the meter, train): see `manifest/manifest_train.json`
(`per_meter`: staffs, at start, mid-staff, scores, small); every one of the 36 labels has >= 151 staffs and >= 8 source scores (smallest: 5/16 151, 11/8 and 11/16 8 scores).
Held-out: `manifest/heldout_scores.txt` (737 scores), the rule: 8% of the train-pool scores by sha1(score name) % 100 < 8 plus the scores that exist only in the run-3
validation lists; the 76 scores that are the only real source of a scarce meter (< 12 scores with two clean bars) stay in training and are removed from validation.
No score is in both lists (checked). The control of run 3 still contains the held-out scores as ordinary staffs: validation of the meter arm alone is clean,
a mixed run's validation is not (these scores sit in the control's training list); keep the arm's own validation list for the meter metrics.

By-eye check (80 random staffs per style from the candidates that passed the filters, montage next to the label summary; 6 reviews were done by
sub-agents reading the montages; two reported errors of the vrv/large review were wrong, I rechecked them on the images and counted them OK): vrv/small 3/80 errors (1 swapped bass/treble staves with notes drawn without
ledger lines, 2 bars drawn differ from the bar count in the label), vrv/normal 0/80, vrv/large 0/80, ms/small 0/80, ms/normal 2/80 (staves with swapped clefs
and notes far outside the staff), ms/large 2/80 (bar count differs: a barline inside a bar). Total 7/480 = 1.5% (95% upper bound 2.9%; per style 0/80 -> 3.7%, 2/80 -> 8.7%, 3/80 -> 10.5%).
Flat/sharp counts of 5-6 accidentals could not be read reliably from the montages (8 staffs listed as doubtful, none confirmed wrong). No style was dropped.
Automatic checks on every candidate: each bar of the window adds up to its meter (MusicXML), each note type matches its duration, the token file's bar sums match
the window's meters (staffs with a failing bar, 1,872 of 29,000, and with more than 5 ledger lines, 1,849, are left out).

## Findings and limits

- MuseScore 4.6.5 ignores the `"style"` key of `-j` job files (only `-S <style>` on the command line works). The font rotation of `convert_lieder.py`
  (`_music_font_style_file` in the job) therefore had no effect: all earlier MuseScore renders (PDMX, Lieder, ASAP, octave sets) are probably Leland. Not
  re-checked on old images. MuseScore 4 has no `timesigScale` style key (the old `timesigScale w h` in MuseJazz.mss is ignored); the size goes into the mscx as
  `<scale w=".." h=".."/>` inside each `<TimeSig>` (`x`/`y` attributes make the signature disappear). Verovio has no option for it, the digits are scaled about their centre by an SVG edit.
- Printed rare meters in the existing data are mostly bars that do not fit: 1/8 is printed in 374 scores of the lists, but only 9 have two consecutive 1/8 bars that add up; 5/8: 449 vs 33; 7/8: 407 vs 42;
  4/8: 32 vs 28. The rare-meter labels of the real data are therefore largely cadenza/irregular-bar encodings (`mining_table.md`, last column). New windows use only bars that fit.
- Real (clean) rare meters are scarce: 11/8 3, 13/8 4, 15/16 3, 19/16 3, 17/16 4, 5/16 1 scores. Those meters come from halved/doubled/relabelled bars of other scores and,
  for 17/16 and 19/16 only, from one bar of 5/16 or 7/16 joined with a 12/16 bar (synthetic, key and clefs equal). Counting "scores" per meter in the manifest counts the segment sources only (staffs from real-change windows have no per-meter source).
- Unfitted validation: 13/8 and 15/8 have no validation staff, 13/16, 15/16, 11/16 only 1-6 (their scores are kept in training, see above).
- Verovio draws a courtesy key/time signature at the end of a system before a change: removed from the SVG (not labelled otherwise); MuseScore: courtesy signatures switched off. The old MuseScore/Verovio training staffs do show them with no label.
- Known defects (about 1.5% by eye): a barline inside a bar (source `<barline>` kept), swapped bass/treble staves of some sources. Both survive the bar check; the ledger-line filter removes most of the latter.
- Time-signature height (heuristic, `measure_ts.py`, C major single staffs, stacked digits, staff spaces): MuseScore PDMX default 3.75, Verovio normal 3.75, MuseScore normal 3.7, Verovio large 4.7, MuseScore large 5.2;
  small 3.3 (Verovio) and 2.8 (MuseScore) - the heuristic includes neighbouring ink for small digits; nominal factors 0.5-0.74 of 3.75. No existing set has small digits: nothing in the pipeline can make them.
- Disk: about 3.6 GB under `/workspace/run4/meters/` (data 2.3 GB incl. 14,000 unused candidate staffs, xml 0.7 GB); the volume is at 95% (9.5 GB free), caused by other jobs.

## Before training
Check on the box: the lists load (`image.png` has a `.json` crop file, tokens pass `check_token_lines`: done for both lists), the ledger-line and length filters of the trainer drop nothing more;
decide the mix with the control (the arm is rare-heavy by design: 45% of the signature staffs carry a rare meter vs about 15% in real data); decide whether the 47.9% change staffs are too many next to the control's 4%;
evaluate on the meter test set (Reflets 4/8, Alborada) and keep the plain control validation to see whether common meters get worse; the by-eye check should be repeated on a sample of the final mixture's first batch.
