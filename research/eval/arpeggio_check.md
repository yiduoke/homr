# Arpeggio marks: precision and recall on real scan pages (run2s7 vs upstream 566)

Method: I looked at the page images (150 dpi PNG) and drew a circle on each `<arpeggiate/>` note of the
per-page MusicXML (`imgpos` comment gives the pixel position), then checked every circle against the printed
page, zoomed in with PIL where needed. Counts by eye: expect an error of 1 or 2 per page on the dense pages.
Nothing was modified. Page references are the page file numbers (page-XX); bar numbers are the printed ones.

Counting rules
- "Printed" = printed arpeggio signs. A long sign that spans both staves (Mazeppa p03, bars 1-4) counts once.
- A mark is a true positive (TP) if its chord has a printed sign. It is a false positive (FP) if not.
- Recall = printed signs that got at least one mark / printed signs. For Mazeppa p03 I also give the per-staff
  chord count (one long sign covers a chord in each hand, 20 chords for 10 signs).
- Marks are counted in the per-page XML (`page-xml/`), one mark per marked note. The final joined file has more
  `<arpeggiate/>` elements (Ballade 60, Mazeppa 99) because the join step copies the mark onto every note of a
  merged chord: Ballade 27 chords carry it in both files, Mazeppa 46 chord groups in the joined file vs 54 marked
  notes in the page files. So "60" is not 60 arpeggios; it is 27.

## Per page: ours (run2s7)

| Piece, page | Printed | Our marks | TP | FP | FN | Note |
|---|---|---|---|---|---|---|
| Ballade 4, p04 (bars 55-68) | 14 | 14 | 14 | 0 | 0 | all on the right chord |
| Ballade 4, p08 | 3 | 3 | 3 | 0 | 0 | |
| Ballade 4, p12 | 3 | 3 | 3 | 0 | 0 | |
| Ballade 4, p17 | 1 | 1 | 1 | 0 | 0 | |
| **Ballade subtotal** | 21 | 21 | 21 | 0 | 0 | |
| Mazeppa, p03 (bars 1-4) | 10 (20 chords) | 12 | 12 | 0 | 3 signs (8 chords) | bar 3 signs 2 and 3, and bar 4 sign, missed; bar 3 signs 1 and 4 got one hand only |
| Mazeppa, p09 (bars 62-74) | 24 | 24 | 24 | 0 | 0 | all left-hand signs found |
| Mazeppa, p11 (bars 92-98) | 9 | 8 | 6 | 2 | 3 | 2 marks sit on a clef read as a half note; the 3 real chords next to them unmarked |
| Mazeppa, p15 (bars 160-165) | 6 | 5 | 5 | 0 | 1 | bar 165 missed |
| **Mazeppa subtotal** | 49 | 49 | 47 | 2 | 7 | |
| Liszt Sonata, p08 | 2 | 2 | 2 | 0 | 0 | |
| Liszt Sonata, p09 | 8 | 7 | 7 | 0 | 1 | system 5 chord after clef missed |
| Liszt Sonata, p10 | 6 | 4 | 4 | 0 | 2 | system 4 chord and last-system chord missed |
| Liszt Sonata, p15 | 1 | 2 | 1 | 1 | 0 | FP: chord under a fermata, no sign printed |
| **Liszt subtotal** | 17 | 15 | 14 | 1 | 3 | |
| **Total (12 pages)** | 87 | 85 | 82 | 3 | 10 | |

Totals, ours: precision 82/85 = 96.5%. Recall 77/87 = 88.5% (82/97 = 84.5% counting each hand's chord on the
cross-staff signs of Mazeppa p03).
By piece: Ballade P 100%, R 100%. Mazeppa P 95.9%, R 85.7%. Liszt P 93.3%, R 82.4%.

## Per page: upstream 566

566 writes arpeggios too, and almost the same ones.

| Piece, page | Printed | 566 marks | TP | FP | Signs hit | Differences from ours |
|---|---|---|---|---|---|---|
| Ballade p04 | 14 | 14 | 14 | 0 | 14 | same; bar 68 mark is on another note of the same chord |
| Ballade p08 / p12 / p17 | 3 / 3 / 1 | 3 / 3 / 1 | all | 0 | 3 / 3 / 1 | identical |
| Mazeppa p03 | 10 | 10 | 10 | 0 | 6 | lacks 2 of our marks (bar 1 right hand, bar 3 sign 4) |
| Mazeppa p09 | 24 | 23 | 23 | 0 | 23 | lacks our bar 64 mark |
| Mazeppa p11 | 9 | 9 | 7 | 2 | 7 | FPs: clef note (same as ours) and a ghost note in the middle of bar 95; gets the bar-94 chord (note placed 15 px off the chord) |
| Mazeppa p15 | 6 | 6 | 5 | 1 | 5 | FP: bar 159 chord has no sign |
| Liszt p08 | 2 | 2 | 2 | 0 | 2 | identical |
| Liszt p09 | 8 | 8 | 8 | 0 | 8 | finds the system 5 chord we miss |
| Liszt p10 | 6 | 5 | 5 | 0 | 5 | finds the system 4 chord we miss |
| Liszt p15 | 1 | 1 | 1 | 0 | 1 | does not have our fermata FP |
| **Total** | 87 | 85 | 82 | 3 | 78 | |

566 totals: precision 82/85 = 96.5%, recall 78/87 = 89.7%. Ours and 566 are the same within noise on these pages.
The model change does not show up in arpeggio marks here (ours 3 FPs and 10 missed signs vs 566 3 FPs and 9).

## Checks beyond the 12 pages (looked at, not counted in the table)

- Ballade 4, all 17 pages: printed arpeggios on pages 01, 04, 05, 06, 08, 09, 12, 17 only (1, 14, 1, 1, 3, 3, 3, 1 =
  27), and our 27 marks sit on exactly those 27 chords. Pages 02, 03, 07, 10, 11, 13, 14, 15, 16 have none and we
  write none. Whole piece: precision 27/27, recall 27/27. The Claude reference (13) is wrong, so is "60"; the
  printed count is 27.
- Mazeppa p05: 1 mark on the marcato wedge below a chord in bar 17, no arpeggio printed on the page (FP).
  Mazeppa p13: 1 mark on a marcato wedge above a chord in bar 130, no arpeggio on the page (FP).
  Mazeppa p10: 3 printed, 3 marks, all TP. Pages 04, 12, 14, 16 have none printed and none written.
  Pages 06, 07, 08 (runs) not examined. Mazeppa, pages examined: 52 printed signs (62 per-staff chords),
  54 marks of ours, 50 TP and 4 FP (2 clef notes, 2 marcato wedges). The Claude reference count of 205 is far too high.
- Liszt pages 03 and 13 (1 mark each) and Beethoven Waldstein 1 and Rachmaninoff Op. 3 No. 2 (0 marks from both
  models) not looked at. I did not find a third piece with more arpeggios than the Liszt Sonata among those that
  have marks; the other two have no marks to check precision on and I did not inspect them for missed signs.

## Kinds of errors

False positives (ours, 3 in the 12 pages, 4 more on 2 extra Mazeppa pages):
- Clef read as a note (Mazeppa p11, bars 94 and 96, 2 marks): the model puts a spurious half note on the bass
  clef sign and gives it the mark; the real arpeggiated chord is just to its left and stays unmarked.
  566 makes the same mistake on bar 96 and 566 also adds one inside bar 95.
- Marcato/accent wedge near a chord read as arpeggio (Mazeppa p05 and p13, 1 each).
- Chord under a fermata (Liszt p15, 1 mark). No wavy line, no slur.
- No wavy slurs or ornaments were involved.

Missed signs (ours, 10 in the 12 pages): mostly when several signs follow each other in one bar (Mazeppa p03 bar 3-4,
p11 bars 94-96), after a clef or key change in the middle of a system (Liszt p09 system 5, Liszt p10 system 6),
and a sign on the first chord of a system (Mazeppa p15 bar 165).

Placement when the arpeggio is real: always on the right chord, 82 of 82 TP. The mark usually sits on the
top note of the chord (sometimes on a different note of the chord). It does not sit on a neighbouring chord.
Cross-staff signs (Mazeppa p03) get a mark on each hand's chord; where the model marks only one hand the sign still counts as found.

## How sure

Printed counts by eye: about +-1 on the dense pages (Ballade p04 = 14, Mazeppa p09 = 24, p03 = 10), +-0 on the
others. The four clef/wedge/fermata FPs and the Liszt FNs I looked at at 2.5x to 3.5x zoom. The conclusions do not
depend on any of these: precision about 96% and recall about 86-89% on the sampled pages; Ballade 4 is perfect.
Caveat: the pages were selected where our model writes the most marks, so recall is slightly flattered (I counted
the pages with zero marks only for Ballade and some of Mazeppa).
