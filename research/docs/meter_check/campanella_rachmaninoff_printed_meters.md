# La Campanella and Rachmaninoff Op. 3 No. 2: time signatures printed in the scans

Sources: scores/liszt la campanella.pdf (10 pages) and scores/rach-prelude-op3-no2-let.pdf (5 pages), rendered at 150 dpi, every system on every page looked at. The first system of each piece was also cropped and upscaled.
References: out/compare/la-campanella/la-campanella-reference.musicxml and out/compare/rachmaninoff-op3-2/rachmaninoff-op3-2-reference.musicxml (not edited).

## 1. Liszt, La Campanella

Bar counting: the scan prints a bar number at the start of every system. I used those numbers (1 to 147, one continuous count) and checked the barlines between them. The last system (page 10) holds bars 144, 145, 146, 147, so the scan has 147 bars, as the reference has 147 measures.

| PDF page | System | Bar | Meter printed | Words nearby |
|---|---|---|---|---|
| 1 | 1 | 1 | 6/8, on both staves, after the five-sharp key signature | none printed (only p under the first bar). The title is "La Campanella"; no Allegretto in the scan |

That is the only time signature in the scan. Every other system start (bars 7, 10, 13, ... 144) shows clef and key signature only. Clef changes (bass/treble inside bars) and key signature are unchanged throughout.

Places checked for a mid-system meter and found none: the double barlines at the end of page 1 (after bar 21), page 2 (after bar 42), page 3 (after bar 61) and page 7 (after bar 102) are followed on the next page by the same key signature and no digits; the "8" and "15" signs (for example in bars 145 to 146 on page 10) are octave-line signs; the small "3" in bars 51, 90 and 91 are triplet numbers.

### Comparison with the reference

- The reference declares 6/8 at bar 1 and nothing else (one `<time>` element in the whole file). This matches the scan: same meter, same place. Printed meter changes: none, reference meter changes: none.
- No `<time print-object="no">` in the file. The `print-object="no"` attribute appears 511 times, all on `<note>` elements (hidden rests or filler), none on a `<time>`.
- Bar numbering differs, the music does not: the reference labels bars 61b (ordinal 62), 78b (ordinal 80) and 100b (ordinal 103) and ends at label 144, while the scan numbers straight to 147. Ordinal n in the reference is printed bar n in the scan (checked at 21/22, 42/43, 61/62, 102/103, 143/144 and 147). The labels with letters are a different bar naming, not extra bars.
- Tempo and expression words: the reference has them (Allegretto bar 1, ma sempre, ben marcato il tema, sempre staccato e piano, poco rit., Piu mosso at 100b, Animato at 134 and others), but this scan prints none of them. Only dynamics, pedal marks and ottava lines are printed. That is a difference in the scan edition, not a meter question.
- Invented or missed meters: none.

Uncertain: nothing about meters. I did not count the notes of every bar against 6/8.

Free-rhythm side notes: none labelled (no cadenza, no fermata). Bars 75 to 84 (pages 5 and 6) are long single-beamed runs of fast notes in the 6/8 bar; they look like free runs but are written as ordinary bars with no meter change. The last bar (147) is a held dotted chord.

## 2. Rachmaninoff, Prelude in C-sharp minor, Op. 3 No. 2

Bar counting: the scan prints a bar number at the start of every system after the first. The first bar (two quarter notes, A and G sharp) is an unnumbered pickup, then bars 1, 2, 3 stand on the first system, and system 2 starts at bar 4. The last bar is 61 (fermata chord, page 5), so 0 to 61 gives 62 bars, as in the reference. Bars 45 to 61 are set on four staves (two staves per hand), which is the same piece with the voices split.

| PDF page | System | Bar | Meter printed | Words nearby |
|---|---|---|---|---|
| 1 | 1 | pickup bar 0 | C (common time), on both staves | Lento, ff |

That is the only time signature. The printed sign is the C symbol, so the reference's `<time symbol="common">4/4` is right. No other system start has a meter (bars 4, 7, 10, 13, 16, 19, 22, 25, 28, 31, 34, 37, 40, 45, 48, 51, 54 are all clef and key only). The section words (Agitato at bar 14, Tempo primo at bar 45) have no meter change next to them.

### Comparison with the reference

- Reference: 4/4 with `symbol="common"` in implicit pickup bar 0 (two quarters, 2 beats), and no other `<time>`. Same meter at the same place as the scan. Whole file: 62 measures, numbered 0 to 61, matching the scan.
- No `<time print-object="no">`. `print-object="no"` appears only on notes.
- Invented or missed meters: none. Printed meter changes in the scan: none.

Uncertain: nothing about meters. Free-rhythm side notes: bar 61 ends on a fermata chord (ppp). Bars 55 to 59 are dotted-half chords after a quarter rest, in 4/4. The 3s in bars 14 and 15 are triplet numbers, not meters.
