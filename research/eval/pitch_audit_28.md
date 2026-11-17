# Where the pitch error of the 28 real-scan pieces comes from (layout1 outputs; 2026-11-17 03:51 PST)

Script `pitch_audit_28.py` (this folder; `--report` prints all tables, `pitch_audit_28.json` holds every error record, per-page counts and the page map). Read-only on outputs and references.
Model: released weights + layout code, tag `layout1` (out/testset/<piece>/<piece>-layout1.musicxml against `-reference.musicxml`). Question: the staff-level read is 98.8-99.8 %, the 28 pages score 85.3 mean pitch F1; where does the rest go?

## Method (same classifier as `pitch_audit.md`)

* Unit and categories exactly as in `pitch_audit.py` (imported, not copied): per aligned bar, multiset of (staff, pitch); error events: 1 unaligned/lost bar (incl. aligned bar with overlap < 10 % and staff-bar empty on one side), 2 octave (+ bracket state), 3 accidental, 4 step, 5 clef, 6 wrong staff, 7a chord member missing, 7b whole event missing, 8 extra, 9 other.
* Alignment: the one stored in `note-scores-layout1.json`. For pieces whose reference and output have different staff counts (Petrushka, Scriabin Sonata 5, the three Liszt Schott pieces) every note is put on one staff and the bars are re-aligned with `align_measures(ignore_staff=True)` of the integration worktree (Petrushka's stored staff-ignored match count, 11,058, is reproduced). Consequence: category 6 is empty for them, and "chord member missing" (7a) is inflated for them because notes of different hands at one onset now count as a chord.
* Checks: my matched-note count equals the stored one for all 23 pieces scored per staff; the F1 recomputed equals SUMMARY-layout1 for them; the category note counts add up exactly to 100 - F1.
* **Reading-only F1** = F1 after removing from both sides every note that falls in a category-1 event (bars without partner, aligned bars that share < 10 % of their notes, staff-bars empty on one side). **F1 points lost per category** = (missed reference notes + extra output notes of the category) / (reference + output notes), so the categories sum to 100 - F1.
* Differences to the earlier audit: new pieces and no mean-pitch staff remap (staff-ignored instead), added diagnostics outside the categories (passage-level octave blocks, bracket context, trill-like runs, per-page F1, pitch-class F1).

## Results: 25 pieces (without the Liszt Schott three)

Mean pitch F1 over the 25: SUMMARY 89.4 (Scriabin 69.1 and Petrushka 58.3 are per-staff numbers), audited 91.0 (those two staff-ignored: 88.9, 79.2), **reading-only 91.9**. Mean over all 28: SUMMARY 85.3, audited 87.1, reading-only 89.5. Octave-blind F1 (pitch class, same alignment): 93.7, so octave costs at most 2.7 points.
Columns 8-14 are F1 points lost (their sum for a piece = 100 - audited F1). `*` = staff-ignored.

| piece | edition | F1 full (SUMMARY) | F1 audited | reading-only F1 | lost-bar share of loss | error events | lost bars | octave | accid. | missing notes (7a+7b) | extra | staff | step+clef+other | two largest (F1 points) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | Bach-Gesellschaft (engraved) | 99.0 | 99.0 | 99.0 | 0% | 25 | 0.0 | 0.0 | 0.1 | 0.7 | 0.1 | 0.0 | 0.1 | missing notes 0.7, accidental 0.1 |
| bach-italian-concerto-2 | Universal Edition | 98.9 | 98.9 | 98.9 | 0% | 19 | 0.0 | 0.0 | 0.3 | 0.0 | 0.6 | 0.0 | 0.3 | extra notes 0.6, accidental 0.3 |
| bach-prelude-873 | Bach-Gesellschaft (engraved) | 83.2 | 83.2 | 83.2 | 0% | 491 | 0.0 | 0.1 | 0.2 | 16.4 | 0.0 | 0.0 | 0.1 | missing notes 16.4, accidental 0.2 |
| beethoven-appassionata-1 | Universal Edition (Schenker) | 97.0 | 97.0 | 97.0 | 0% | 327 | 0.0 | 0.0 | 0.5 | 2.0 | 0.0 | 0.2 | 0.3 | missing notes 2.0, accidental 0.5 |
| beethoven-hammerklavier-4 | Peters | 78.3 | 78.3 | 80.5 | 12% | 3014 | 2.7 | 0.8 | 0.3 | 13.5 | 0.4 | 3.4 | 0.4 | missing notes 13.5, staff 3.4 |
| beethoven-waldstein-1 | Peters | 93.7 | 93.7 | 95.9 | 37% | 768 | 2.3 | 0.0 | 0.2 | 2.4 | 0.1 | 1.2 | 0.1 | missing notes 2.4, lost bars 2.3 |
| chopin-etude-op10-4 | Breitkopf | 94.8 | 94.8 | 94.8 | 0% | 136 | 0.0 | 0.5 | 2.2 | 0.7 | 0.2 | 1.0 | 0.6 | accidental 2.2, staff 1.0 |
| chopin-etude-op25-10 | Peters | 95.9 | 95.9 | 95.9 | 0% | 153 | 0.0 | 1.6 | 1.8 | 0.2 | 0.1 | 0.0 | 0.3 | accidental 1.8, octave 1.6 |
| chopin-etude-op25-11 | Peters | 88.5 | 88.5 | 88.5 | 0% | 395 | 0.0 | 8.4 | 1.0 | 0.9 | 0.2 | 0.0 | 0.9 | octave 8.4, accidental 1.0 |
| chopin-polonaise-op53 | Breitkopf | 87.4 | 87.4 | 87.6 | 2% | 1073 | 0.2 | 3.0 | 1.6 | 4.0 | 0.6 | 1.9 | 1.2 | missing notes 4.0, octave 3.0 |
| chopin-scherzo3 | Breitkopf | 91.8 | 91.8 | 92.2 | 4% | 499 | 0.4 | 5.0 | 0.5 | 0.5 | 0.3 | 0.9 | 0.7 | octave 5.0, staff 0.9 |
| debussy-pour-le-piano-1 | Fromont | 91.6 | 91.6 | 92.0 | 5% | 407 | 0.4 | 1.8 | 1.4 | 2.3 | 0.8 | 0.4 | 1.2 | missing notes 2.3, octave 1.8 |
| debussy-reflets | Durand | 85.5 | 85.5 | 86.9 | 11% | 437 | 1.7 | 5.2 | 1.5 | 2.2 | 1.4 | 0.4 | 2.2 | octave 5.2, missing notes 2.2 |
| haydn-hob16-49-1 | Breitkopf 1799 | 95.1 | 95.1 | 95.5 | 8% | 176 | 0.4 | 0.2 | 0.9 | 0.7 | 0.5 | 0.2 | 2.0 | accidental 0.9, missing notes 0.7 |
| liszt-hr-6 | Paderewski | 91.6 | 91.6 | 93.7 | 27% | 666 | 2.2 | 1.6 | 0.9 | 2.9 | 0.2 | 0.1 | 0.5 | missing notes 2.9, lost bars 2.2 |
| liszt-paganini-6 | Breitkopf 1851 | 90.8 | 90.8 | 90.8 | 0% | 490 | 0.0 | 5.7 | 0.9 | 1.6 | 0.3 | 0.4 | 0.3 | octave 5.7, missing notes 1.6 |
| mozart-k475 | Schirmer | 92.0 | 92.0 | 93.0 | 13% | 452 | 1.1 | 0.1 | 1.2 | 1.3 | 1.6 | 2.5 | 0.3 | staff 2.5, extra notes 1.6 |
| prokofiev-toccata | Dover (Sarcasms/Visions) | 92.7 | 92.7 | 93.1 | 5% | 436 | 0.4 | 2.5 | 2.0 | 1.2 | 0.5 | 0.0 | 0.7 | octave 2.5, accidental 2.0 |
| ravel-alborada | Demets | 80.5 | 80.5 | 81.7 | 8% | 1137 | 1.6 | 11.1 | 1.8 | 2.5 | 0.6 | 0.4 | 1.4 | octave 11.1, missing notes 2.5 |
| schubert-impromptu-d899-4 | Breitkopf | 96.7 | 96.7 | 96.7 | 0% | 158 | 0.0 | 2.5 | 0.7 | 0.0 | 0.1 | 0.0 | 0.0 | octave 2.5, accidental 0.7 |
| schubert-wanderer-3-4 | Peters | 94.9 | 94.9 | 95.0 | 2% | 501 | 0.1 | 1.4 | 0.4 | 0.2 | 1.5 | 1.4 | 0.2 | extra notes 1.5, staff 1.4 |
| schumann-kreisleriana-1 | Schirmer | 95.8 | 95.8 | 96.1 | 7% | 63 | 0.3 | 0.6 | 1.3 | 0.3 | 0.5 | 0.6 | 0.6 | accidental 1.3, octave 0.6 |
| schumann-toccata | Peters | 91.2 | 91.2 | 94.1 | 35% | 1026 | 3.1 | 1.0 | 0.9 | 0.4 | 2.9 | 0.2 | 0.3 | lost bars 3.1, extra notes 2.9 |
| scriabin-sonata-5* | Muzgiz | 69.1 | 88.9 | 93.4 | 43% | 1359 | 4.8 | 3.3 | 1.3 | 0.6 | 0.1 | 0.0 | 1.0 | lost bars 4.8, octave 3.3 |
| stravinsky-petrushka* | (piano score, file x.pdf) | 58.3 | 79.2 | 82.6 | 20% | 4751 | 4.1 | 4.7 | 1.5 | 8.5 | 0.5 | 0.0 | 1.6 | missing notes 8.5, octave 4.7 |
| **mean of the 25** | | 89.4 | 91.0 | 91.9 | 11% | 18959 | 1.0 | 2.4 | 1.0 | 2.6 | 0.6 | 0.6 | 0.7 | |


Shares of the mean loss (9.0 points) over the 25: octave 27 %, missing notes (7a 10 % + 7b 19 %) 29 %, lost bars 11 %, accidental 11 %, wrong staff 7 %, extra notes 6 %, step 4 %, other 4 %, clef 0.3 %.
Shares of error events pooled over the 25 (18,959 events; Petrushka alone has 4,751, so pooled numbers lean on it): lost bars 20 %, whole event missing 23 %, octave 17 %, chord member missing 17 %, extra 8 %, accidental 6 %, wrong staff 4 %, step 2 %, other 2 %. Without Petrushka: whole event missing 26 %, lost bars 19 %, octave 18 %, chord member 11 %.

Only 1.0 of the 9.0 mean points (11 %) come from bars that never aligned. Reading-only F1 is still below 90 for Hammerklavier (80.5), Ravel (81.7), Petrushka (82.6), Bach prelude (83.2), Reflets (86.9), Polonaise (87.6) and Op. 25/11 (88.5).
By pieces: lost bars dominate in Scriabin (43 % of the loss), Waldstein (37 %), Schumann Toccata (35 %), Hungarian Rhapsody 6 (27 %); everything else is not a layout loss.

Density is not the driver: pooled F1 of aligned, non-lost bars by reference notes per bar is 92.3 (0-11), 93.3 (12-23), 90.4 (24-35), 87.9 (36-59), 82.3 (60+).

## Liszt Schott three (staff-pairing failure; excluded above)

| piece | edition | F1 full (SUMMARY) | F1 audited | reading-only F1 | lost-bar share of loss | error events | lost bars | octave | accid. | missing notes (7a+7b) | extra | staff | step+clef+other | two largest (F1 points) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| liszt-sonata* | Schott | 47.4 | 52.2 | 67.2 | 47% | 6185 | 22.4 | 2.6 | 0.7 | 21.6 | 0.1 | 0.0 | 0.3 | lost bars 22.4, missing notes 21.6 |
| liszt-te-5* | Schott | 53.3 | 56.9 | 70.0 | 44% | 3602 | 18.8 | 4.4 | 0.9 | 17.6 | 0.7 | 0.0 | 0.7 | lost bars 18.8, missing notes 17.6 |
| liszt-te-10* | Schott | 52.3 | 55.2 | 69.9 | 47% | 3581 | 21.0 | 2.5 | 0.4 | 19.9 | 0.1 | 0.0 | 0.8 | lost bars 21.0, missing notes 19.9 |
| **mean of the 3** | | 51.0 | 54.8 | 69.0 | 46% | 13368 | 20.7 | 3.2 | 0.7 | 19.7 | 0.3 | 0.0 | 0.6 | |

Bars come out doubled (305 / 182 / 134 reference bars against 604 / 358 / 261), so 44-49 % of the loss is bars without a partner and most "missing" notes sit in the other half of the doubled bars. Reading-only F1 is 67-70, i.e. even without the doubling the Schott pieces are the weakest reading cases besides Petrushka.

## The four findings behind the numbers

**1. Octave events are whole passages, and many are a bracket (ottava) problem, on both sides of the comparison.** 3,219 octave events in the 25 pieces; 2,715 (84 %) sit in blocks of >= 4 same-direction shifts in one staff-bar, only 142 (4 %) are single notes. So these are not stray ledger-line misreads. By bracket state at bar level: the reference carries a bracket 1,210, only the output carries one 1,011, neither 998. Direction: output higher 2,332, lower 887.
Checked on page images:
* Schubert Impromptu p. 29 (bars 57-64, 231-238): the print has an 8va line, the reference has no octave-shift and the printed pitch, the output applies the bracket (F6 against F5). The output also writes the direction into the left-hand part. So 116 events are a reference convention, not a misread.
* Chopin Scherzo pp. 4 and 12: same pattern (dotted 8va lines printed over the right-hand figures; 53 of the 107 events on p. 4 are bars where only the output has a bracket).
* Ravel p. 41 (glissandi under "8"): brackets in print, output and (for 41 of 92 events) reference, and still the output is one octave above the reference; extent or double application, not decided.
* Wanderer p. 31: long 8va brackets over four systems; the output keeps the printed pitch (lower by one octave), the reference has the sounding pitch without an octave-shift element: a missed bracket (34 events on that page).
* Scriabin p. 14 (bars 329-332, 349-351): no bracket for these chords, output one octave above the reference in 8 consecutive bars: a real octave misread or a reference error, not decided.
* Ravel pp. 42-44: right-hand chords one or two octaves above the reference in 13-17 bars per page, with almost no printed bracket; cause not decided (not checked against the notes of the image).
If all 1,011 only-output-bracket events were reference-side (confirmed for Schubert and the Scherzo; open for Ravel, which has 409 of them, where the print shows few brackets and the output's bracket state may be spurious) and the trill runs of finding 2 were removed, the mean over the 25 would rise from 91.0 to 92.4. Octave is the largest single class (27 % of the loss; 2.4 points, 11.1 in Ravel, 8.4 in Op. 25/11, 5.7 Paganini, 5.2 Reflets, 5.0 Scherzo).

**2. "Missing notes" are partly the reference's expanded ornaments.** 7a + 7b is 29 % of the loss, but the reference writes long trills out as alternating notes (Hammerklavier p. 46, bars 379-402: 40 reference notes in a bar the output reads as 16; the printed line is one trill sign). Reference notes in trill-like runs (>= 5 single notes, alternating two pitches a tone or less apart, onsets < 0.2 quarter apart): Hammerklavier 1,665 of 8,875 (18.8 %), Bach prelude 203, Appassionata 96, Polonaise 59. 1,920 of the 7,578 missing-note events of the 25 are such notes (1,562 of Hammerklavier's 2,123; 203 of the prelude's 486; in the prelude another 67 are grace notes and 90 notes <= 1/8 quarter, i.e. ornament realisations). Removing those reference notes lifts the mean over the 25 by 0.65. Hammerklavier (78.3) and Bach prelude 873 (83.2, precision 100) are therefore mostly a reference problem, and the earlier open question about their low recall is answered.

**3. Layout failures are few but large.** Scriabin p. 18 is lost completely: page-xml has two parts (P1 24 bars, 135 notes; P2 24 bars, 620 notes), `merge_pages` matches parts by id, the music lands in a second part and `drop_minor_parts` removes it ("dropped minor part P2-Staff1/2 (24 measures)"): 706 reference notes, Scriabin reading-only 93.4 against 88.9. Petrushka: the joiner also drops two minor parts of 69 measures ("dropped minor part P2-Staff1/2") and the output has 598 bars against 647 in the per-page files (not traced further). Schumann Toccata (bars split differently on the dense pp. 11-12: 329 reference notes without partner, 388 extra notes), Hammerklavier (key/meter/tempo changes on p. 31), Hungarian Rhapsody 6 p. 5 (unbarred cadenza runs become extra bars) are bar-splitting failures.

**4. The rest is small.** Accidental 1.0 point (Chopin Etudes 10/4 and 25/10, Prokofiev, Debussy), wrong staff 0.6 (middle-register inner voices swapped between hands: Hammerklavier 3.4, Mozart K. 475 2.5, Waldstein 1.2, Wanderer 1.4; the pitches are right, the same convention issue as the Bach fugue before), extra notes 0.6 (Schumann Toccata 2.9, Wanderer and Mozart 1.5), step, clef, other 0.7 together.

## Edition and visible difficulty (scores/testset/*.pdf; reference features from the reference MusicXML)

Columns: notes per bar of the reference, share of notes with >= 3 ledger lines, octave-shift marks in the reference, grace notes, tremolo marks, notes in tuplets.

| piece | edition | notes/bar | ledger >= 3 | 8va marks | grace | tremolo | tuplets | what makes it hard (page images and reference) |
|---|---|---|---|---|---|---|---|---|
| bach-fugue-873 | Bach-Gesellschaft | 20.6 | 0 % | 0 | 1 | 0 | 0 % | clean 3-voice fugue |
| bach-italian-concerto-2 | Universal Edition | 23.5 | 4 % | 0 | 2 | 0 | 0 % | clean |
| bach-prelude-873 | Bach-Gesellschaft | 27.8 | 0 % | 0 | 64 | 0 | 1 % | ornaments (trills, mordents) that the reference writes out |
| beethoven-appassionata-1 | Universal Edition (Schenker) | 25.5 | 8 % | 0 | 13 | 0 | 4 % | dense sixteenths, ledger lines, trills |
| beethoven-hammerklavier-4 | Peters | 21.9 | 7 % | 0 | 0 | 0 | 4 % | long trills, fugue with voices crossing hands, key and clef changes mid-system |
| beethoven-waldstein-1 | Peters | 22.9 | 7 % | 0 | 26 | 0 | 16 % | triplets and octave runs, hand-crossing figures, grace notes |
| chopin-etude-op10-4 | Breitkopf | 27.2 | 3 % | 1 | 0 | 0 | 0 % | dense sixteenths, many accidentals |
| chopin-etude-op25-10 | Peters | 28.7 | 4 % | 4 | 9 | 0 | 64 % | octave double notes in triplets, 8va |
| chopin-etude-op25-11 | Peters | 33.2 | 16 % | 21 | 1 | 0 | 76 % | sextuplet runs with 8va brackets in both hands, many ledger lines |
| chopin-polonaise-op53 | Breitkopf | 35.2 | 7 % | 9 | 78 | 0 | 1 % | octaves, dense chords, grace notes, 8va |
| chopin-scherzo3 | Breitkopf | 8.2 | 12 % | 43 | 2 | 0 | 1 % | old plates, 8va in about every second system (dotted line, short extents) |
| debussy-pour-le-piano-1 | Fromont | 21.2 | 8 % | 9 | 0 | 0 | 4 % | many accidentals, 8va, bar-count drift (29 extra output bars) |
| debussy-reflets | Durand | 23.4 | 17 % | 27 | 0 | 0 | 42 % | small 4/8, tuplets, 8va, ledger lines |
| haydn-hob16-49-1 | Breitkopf 1799 | 12.1 | 1 % | 0 | 95 | 0 | 0 % | old plates, grace notes; light density |
| liszt-hr-6 | Paderewski | 21.7 | 13 % | 4 | 1 | 10 | 13 % | unbarred cadenza runs, 8va, ossia handled elsewhere |
| liszt-paganini-6 | Breitkopf 1851 | 20.3 | 15 % | 27 | 63 | 0 | 25 % | octave passages with 8va, ledger lines, grace notes, old plates |
| mozart-k475 | Schirmer | 21.0 | 2 % | 0 | 16 | 0 | 3 % | hands crossing, inner voices on the other staff, grace notes |
| prokofiev-toccata | Dover | 20.6 | 9 % | 10 | 8 | 0 | 0 % | repeated notes in long beamed runs, 8va and 8vb |
| ravel-alborada | Demets | 20.8 | 14 % | 13 | 15 | 0 | 20 % | clef changes inside bars in both staves, meter changes (6/8, 9/8, 3/8), glissandi under 8va |
| schubert-impromptu-d899-4 | Breitkopf | 16.8 | 5 % | 0 | 0 | 0 | 3 % | modern engraving, 8va lines over right-hand runs |
| schubert-wanderer-3-4 | Peters | 15.2 | 10 % | 0 | 0 | 38 | 5 % | 8va brackets running over several systems, tremolo |
| schumann-kreisleriana-1 | Schirmer | 15.3 | 5 % | 0 | 12 | 0 | 87 % | triplet figuration, grace notes |
| schumann-toccata | Peters | 23.7 | 5 % | 4 | 5 | 0 | 0 % | double-note sixteenths in both hands, fingering digits, cross-staff, clef changes, 8va |
| scriabin-sonata-5 | Muzgiz | 18.7 | 10 % | 17 | 227 | 0 | 14 % | 3-staff systems (two treble staves and bass), grace notes, 8va, dense chords |
| stravinsky-petrushka | not stated (x.pdf) | 24.7 | 11 % | 126 | 294 | 266 | 15 % | 2, 3 and 4 staves per system, ossia, tremolo, many 8va/8vb |
| liszt-sonata, liszt-te-5, liszt-te-10 | Schott | 22.7 / 34.0 / 22.8 | 12-14 % | 34 / 26 / 42 | 30 / 50 / 0 | 59 / 0 / 0 | 20 / 0 / 73 % | hands paired as separate parts (bars doubled), 8va, tremolo |

Editions are mostly Peters and Breitkopf; with this sample the edition does not separate good from bad (Breitkopf: Etude 10/4 94.8, Impromptu 96.7, Scherzo 91.8, Polonaise 87.4; Peters: Wanderer 94.9, Op. 25/10 95.9, Hammerklavier 78.3). What separates them is what is printed: 8va brackets (the 8 pieces with an octave loss of 3 points or more, all below 92 F1: Ravel 11.1, Op. 25/11 8.4, Paganini 5.7, Reflets 5.2, Scherzo 5.0, Petrushka 4.7, Scriabin 3.3, Polonaise 3.0) and ornaments that the reference expands.

## Ten pages with the lowest per-page F1 (25 pieces)

Per-page F1 = matched / (reference notes of the page's bars + output notes of the page's bars), pages mapped from the page-xml bar counts (exact: first-bar check on 5 pieces); unaligned reference bars go to the previous page (the last ones to the first lost page). Petrushka and the Liszt Schott pieces cannot be mapped (two parts per page); pages with fewer than 100 reference notes are not in the list.

| rank | piece, page (file number) | F1 | ref / out notes | what goes wrong |
|---|---|---|---|---|
| 1 | scriabin-sonata-5 p. 18 | 0.0 | 706 / 0 | whole page missing: two parts on the page, merged by id, the music part dropped as "minor part"; 3-staff systems at the top |
| 2 | liszt-hr-6 p. 5 | 45.6 | 292 / 265 | cadenza page, runs with 8va without barlines: 20 output bars on the page, 138 notes in bars with no reference partner or an unrelated one, 132 whole events missing |
| 3 | ravel-alborada p. 43 | 49.0 | 385 / 346 | right-hand chords one or two octaves above the reference in 15 bars (123 events, no bracket printed except a short one), clef changes inside bars, 9/8 and 6/8; cause of the octave offset not decided |
| 4 | ravel-alborada p. 42 | 49.0 | 391 / 388 | same octave offset (154 events) plus bars lost (64 notes); clef changes inside bars in both staves |
| 5 | beethoven-hammerklavier-4 p. 46 | 55.2 | 776 / 391 | reference has the long trills written out (776 notes against 391); output reads each trill as one note; 275 of the 374 missing notes are in trill runs; final 8va chord |
| 6 | ravel-alborada p. 44 | 55.4 | 350 / 372 | right-hand chords one octave above the reference without printed bracket (125 events); last bar with 8/8vb brackets |
| 7 | beethoven-hammerklavier-4 p. 31 | 58.8 | 550 / 422 | tempo, key and meter changes (Largo, Prestissimo, Allegro risoluto) and trills: 211 notes in lost bars, 115 missing notes (97 in trill runs), 50 extras |
| 8 | beethoven-hammerklavier-4 p. 35 | 59.0 | 587 / 372 | trills in both hands written out in the reference (142 of 216 missing notes are in trill runs), middle-register notes in the other staff (81 wrong-staff events), clef changes inside bars |
| 9 | schumann-toccata p. 12 | 65.1 | 547 / 562 | dense double-note sixteenths with fingering and clef changes: bars split differently from the reference (157 notes in lost bars, 176 extras) |
| 10 | schumann-toccata p. 11 | 67.8 | 607 / 578 | same figuration under a long 8va; 172 notes in lost bars, 147 extras, 23 octave events |

Five of the ten (1, 2, 5, 7, 8) are not reading errors of the staff reader (page lost in assembly, cadenza bars, the reference's written-out trills); the three Ravel pages are an octave question still open, the two Toccata pages bar splitting on dense figuration.

## Conclusion

1. Largest single cause: **octave (8va/8vb) brackets**, 27 % of the loss over the 25 pieces (2.4 points; at most 2.7 points by the octave-blind F1), in whole passages. About a third of those events (1,011 of 3,219) are bars where only the output carries a bracket (printed brackets confirmed on 3 pages; for Ravel the print shows few), so they are partly a reference/scoring problem; the model-side part is missed brackets (Wanderer p. 31, Rhapsody 6: 63 of 80 events lower), wrong extents, and unexplained +1/+2 octave blocks (Ravel pp. 42-44, Scriabin p. 14).
2. Second: **missing notes**, 29 % of the loss, of which a large part is the reference's written-out trills and ornaments (Hammerklavier, Bach prelude; 0.7 points of the mean at a minimum). Together these two are about 56 % of the loss; layout (lost bars) 11 %, accidentals 11 %.
3. Mostly a reading problem (reading-only F1 close to F1, lost-bar share < 10 %): Chopin Etudes, Polonaise, Scherzo, Paganini, Ravel, Reflets, Prokofiev, Impromptu, Wanderer, Pour le piano, Kreisleriana, Haydn, K. 475, Bach pieces. Mostly layout (lost-bar share >= 27 %): Scriabin, Waldstein, Schumann Toccata, Hungarian Rhapsody 6 (and the Schott three, Hammerklavier partly). Mostly reference artefact: Hammerklavier, Bach prelude 873, and the octave part of Schubert Impromptu and Scherzo.
4. The scanned-staff read at 98.8-99.8 % and the 91.9 reading-only page F1 differ because the pages add ottava brackets, ornaments and layout that the cut staffs and rendered staffs rarely carry in the same form, not because of scanning or note density.

## Recommended fixes (not done here)

1. **Scoring first, no training:** score in a bracket-normalised way (compare written pitch: undo the octave-shift of both files where it exists, and report the pitch-class F1 next to it) and collapse written-out trills in the references; then the real octave and missing-note errors can be counted. This changes the picture of Hammerklavier, Bach prelude, Impromptu, Scherzo, Ravel by up to 13 points.
2. **Data:** octave brackets with their printed form: real scan pairs with 8va/8vb and brackets that start at the beginning of a system or run over several systems (Wanderer, Scherzo, Paganini, Op. 25/11 have many), with labels that include the bracket extent; the KernScores pairs of D6 exclude octave shifts (98 in quarantine), so they do not cover this.
3. **Code:** (a) `merge_pages` part matching: a page whose first part is a small staff or has another staff count loses its music (Scriabin p. 18, Petrushka 69 bars); match by staff count/note mass for the page, with a regression check on K. 309 (the earlier try matching by most notes broke it); (b) write the octave-shift direction into the part and staff that carries the shifted notes (Schubert: direction in the left-hand part); (c) cadenza bars without barlines should not be cut into pseudo-bars (Rhapsody 6 p. 5).

## Limits

Sixteen pages were viewed (Schubert 29, Ravel 41-44, Scherzo 4 and 12, Wanderer 31, Scriabin 14 and 18, Rhapsody 6 p. 5, Hammerklavier 31, 35, 46, Toccata 11 and 12); the octave statements outside these are inferred from the bracket flags in the files and from the passage-level pattern. "Only the output has a bracket" counts a bracket tracked per bar and staff, so a bracket that runs over several bars with its "stop" in the same bar (Schubert) is counted as "neither". The trill detector is a proxy (five notes, two pitches); other ornaments (grace notes, turns, tied duplicates) are not counted as reference artefacts, so the artefact share is a lower bound. Petrushka's and Scriabin's staff-ignored classes (7a) are inflated. Per-page F1 depends on the join of unaligned reference bars to pages.
