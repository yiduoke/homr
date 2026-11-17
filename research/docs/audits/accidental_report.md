# Printed accidental labels: source audit (2026-11-15)

Scripts: `run/audits/accidental_scripts/` (same files in `/workspace/audit_acc/` on vast-homr4). No code or dataset changed.
Rule used for "needed": key signature, state per (staff, step, octave) in time order (all voices of a staff share it), reset at the barline, tie-stop notes need none.

## Findings in one table

| Dataset | Renderer | Recommended label source | Agreement with images |
|---|---|---|---|
| Lieder, PDMX, ASAP, kern_scriabin, musescore_octave (MuseScore crops) | MuseScore | `<accidental>` element of MuseScore's own export (all types: sharp, flat, natural, double-sharp, flat-flat) | SVG glyph count and type per measure identical in 99.6% (Lieder, 30,046 measures), 99.4% / 98.1% (PDMX, 2,047 + 8,159), 99.2% (ASAP, 5,814), 99.5% (Scriabin, 2,134). All disagreements inspected were errors of my SVG-to-staff matching, not of the XML. |
| PDMX / Lieder / ASAP / Scriabin `-vrv-` crops (about 25% of PDMX, 22% of Lieder, 9% of ASAP, 18% of Scriabin crops) | Verovio 6.4.1 from the same MusicXML | the same `<accidental>` elements | 6,462 of 6,462 measures: accidentals drawn == `<accidental>` count (4,757). The rule would match only 97.3%. |
| GrandStaff | older Verovio, kern | Verovio 6.4.1 MEI `@accid` UNION kern `n` tokens | 20 of 21 inspected crops: every accidental matches. Differences: redundant `n` and `X` (below). |
| LilyPond sets (lilypond, lilypond_round2) | musicxml2ly + LilyPond 2.24 | the rule, plus musicxml2ly's `?` / `!` marks (from `<accidental cautionary>` / forced) | rule == drawn in 98.0% of 5,575 measures (84 pieces); XML `<accidental>` == drawn only 94.6%. |

## Q1 MuseScore export vs drawn

`<accidental>` elements per measure compared with `class="Accidental"` glyphs in MuseScore's SVG (Lieder SVGs kept; for PDMX/ASAP/Scriabin I re-exported MuseScore with the dataset's font rule: byte-identical MusicXML, so the crops are reproducible). Crops were mapped to measures by matching the token files to homr's parser output (`crop_map.py`, `svg_check2.py`, `svg_eval2.py`).

| Set | measures | identical per-type histogram | crops with equal total |
|---|---|---|---|
| Lieder (400 pieces) | 30,046 | 99.60% | 99.26% |
| PDMX (60 pieces) | 2,047 | 99.41% | 99.46% |
| PDMX, 70 pieces chosen for courtesy signs | 8,159 | 98.11% | 96.75% |
| ASAP (45 pieces) | 5,814 | 99.24% | 98.42% |
| kern_scriabin (45 pieces) | 2,134 | 99.53% | 98.23% |

Per case (measures containing the case, identical): needed and printed 99.3% (Lieder), 97.0% (PDMX-2); courtesy after an alteration in the previous bar 98.2% / 96.6%; courtesy in another octave 98.2% / 96.0%; repeat of the same pitch 96.3% / 98.8%; accidental on a tie-stop note across a barline 93.7% (n=126, Lieder) and 100% (ASAP, n=18); tie-stop of an altered note with no sign 98.9% / 99.3%; rule says needed but XML has none (n=24, 32, 11): 100% drawn none. Courtesy and tie-stop signs are exported. Parenthesised cautionary signs are drawn as three glyphs but one `<accidental>`.
Residual errors seen: system-start tie-continuation (sign drawn, XML also has it), `natural-sharp` glyph (one element). The 1-4% "disagreements" I opened were my staff assignment (cross-staff ledger-line chords assigned to the neighbour staff, measure boundary at an invisible barline) or ambiguity of repeated music; the images agreed with the XML.

Checked crops (viewed; every accidental per measure compared with the list from the XML), 17 with a full count plus 6 more during debugging:
- lc5060918-12-1 m1 G4 natural drawn in parentheses on a tie-stop; m1 F4 sharp, m2 F4 natural, m3 F4 natural drawn: 4/4.
- lc4946077-5-6 m1 B5 flat, B3 flat, B4 flat, B5 flat: 4/4.
- lc5052801-3-10 m1 eight signs incl. B4 sharp on a tie-stop at system start: 8/8.
- lc5084888-5-6: D5 natural tie-stop, B4 sharp, D4 sharp, D4 natural: 4/4.
- lc6421659-4-4 m1 E5 natural, m2 five sharps (two voices) and B1, B2 flat: 8/8.
- lc6567603-5-4 (locating error: crop starts one bar later than first match), counts then agree.
- Qmb6KZ..-6-3 (C4 sharp, natural, G3 flat x2), QmTXuxt..-6-5, QmT4sxk..-1-4: all drawn.
- ASAP Beethoven 21-1-18-5 (C5/C6 natural on tie, then tie-stop C6 natural drawn at start of next bar), 3-1-8-3 (B natural on both tie ends), 17-1-9-6: all drawn.
- Scriabin op19_no02-2-6 (F4 double-sharp drawn as x), op8_no02-1-2: all drawn. Scriabin op56_no02-2-9 m1: 4 flats drawn on ledger-line chord, XML 4.
- Verovio crops QmTTSgd..-vrv-4-0, QmWyx7E..-vrv-5-0 (naturals, double-sharps): all drawn.

## Q2 GrandStaff

Kern has no printed/not printed information except `n` (explicit natural), `X`, `y`. Verovio 6.4.1 prints `@accid` only when needed by key and bar state; in-key sharps/flats get `@accid.ges` only. Compared with the images (21 crops, e.g. sonata18-1 min3_up_m-94-97, scarlatti L347K227, joplin maple leaf, mozart sonata10-1, scarlatti L334K122 with ## drawn as x, sonata05-3, sonata17-3, sonata31-3, sonata16-3, sonata04-1, sonata06-3k): 6.4.1 matches every drawn sign except:
1. Redundant `n`: the images print every kern `n` (e.g. L347K227 `16Dn` in D major, sonata05-3 m4 `fn`); 6.4.1 stays silent for 22% of them (686 of 3,132 `n` in 8,000 files = 0.14% of notes). Use `@accid` OR kern `n`.
2. `X`: 0.15% of notes (746 of 499,774). The images print the accidental (sonata16-3 m1 `b--X`: double flat drawn; sonata04-1 m1 `ee-X` in E-flat key: flat drawn); 6.4.1 prints it in 6% and hides it otherwise. Treat `X` as forced display. `y` (14 notes): hidden sign, not drawn.
Not verified against the original Verovio version (unknown); the table is from images only.
Sample of 8,000 of 45,635 files: printed accidental on 11.96% of notes (s 4.27, f 2.92, n 3.70, x 0.67, ff 0.40).

## Q3 LilyPond

.ly files are not kept; I regenerated them (musicxml2ly + the dataset's style block, `ly_audit.py`; examples in `/workspace/audit_acc/ly/`) with a class on Accidental grobs and counted per measure (84 pieces, 5,575 measures, 6 failed measure count). Sources: Lieder, PDMX, musetrainer, aug_xml* (octave-augmented).
- drawn == rule: 5,462 (98.0%); drawn == XML `<accidental>`: 5,272 (94.6%); drawn total 3,823, rule 3,708, XML 4,000.
- musicxml2ly writes `?` (cautionary, in parentheses) 151 times and `!` 15 times in 90 files, from `<accidental>` elements flagged cautionary: this explains drawn > rule. Drawn < rule (e.g. QmbYk..oct-1-3 m14,15: rule 4, drawn 2, a natural chord then a sharp chord in the same bar and staff) not explained; the LilyPond rule apparently carries less than my per-staff per-octave state in these chords (one crop viewed, naturals drawn and the following sharps not). Only 1 crop was viewed for LilyPond; the automated SVG count is the evidence. Recommended: take the label from the LilyPond SVG (re-engrave, class on Accidental, assign to the note by position) rather than from a rule, or accept about 2% of measures wrong.

## Q4 kern_scriabin and ASAP

Both use MuseScore: `prep_kern.py` (music21 kern to MXL) / `prep_asap.py`, then `render.py` = `create_musicxml_and_svg_files_from_mxl` + `convert_xml_and_svg_file`, so MuseScore plus the same Verovio share (`choose_parts`: 50% of single-staff parts, 10% of grand-staff parts rendered by Verovio from MuseScore's export). Their `rendered_scores` were deleted; re-exports in `/workspace/audit_acc/{asap,kern_scriabin}_svg/`. Kern X markers are irrelevant there (MuseScore decides). Scriabin shows many printed doubles (1.19% of notes).

## Q5 Estimates (share printed, and current label differing from the printed target)

Current label: `<accidental>` sharp/flat/natural if present (natural stripped to none; double-sharp, flat-flat map to none, a bug), else sounding `<alter>`. Target: printed sign or none.

| Dataset | notes with printed sign | label differs | of which sounding alteration, no sign | printed natural, label none | printed double, label none |
|---|---|---|---|---|---|
| PDMX (3000 files) | 6.4% | 28.2% | 25.9% | 2.3% | 0.06% |
| PDMX hard (3000) | 7.8% | 34.6% | 31.4% | 3.0% | n/a |
| Lieder (1346) | 10.6% | 34.3% | 30.1% | 4.1% | n/a |
| ASAP (45 pieces) | 14.4% | 29.1% | 24.3% | 4.6% | n/a |
| kern_scriabin (45) | 18.5% | 48.0% | 40.4% | 6.4% | 1.2% |
| GrandStaff (8000 files, MEI) | 12.0% | 42.2% | 38.5% | 3.7% | (x/ff printed 1.1%, labelled ## / bb, no differ) |
| LilyPond sets (rule, 90 pieces) | 7.5% | 23.8% | 21.0% | 2.8% | n/a |

Token files (all notes): lift `_` 53-72%, `#` 13-20%, `b` 14-25%, `##` <=0.9%; token files hold no `N` (strip_naturals in the converters).
Other notes: PDMX rendered (`.musicxml` mixed) = MuseScore + Verovio crops; tokens mix both; grace notes 0.3-0.8% of notes carry accidentals as usual. `_alter_to_lifts` truncates quarter tones (`<alter>0.5</alter>` to natural); 12-22 quarter-tone accidentals per 1.35M PDMX notes.

## Failure cases and risks
1. Verovio crops: label must be `<accidental>` (rule 97.3%).
2. LilyPond: neither rule nor XML exact (98.0% / 94.6% of measures).
3. GrandStaff: add kern `n`, `X` forced display; `y` hidden; transposed variants (min3_up etc.) share the same rule.
4. Double sharps/flats: current parser maps `double-sharp`, `flat-flat`, `sharp-sharp` printed to none; fix when relabelling.
5. Crops with crop-to-measure ambiguity in repeated music (about 1%): mapping by token order with lift in the key.
