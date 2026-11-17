# Petrushka (Stravinsky, Three Movements, piano): time signatures printed in the scan

Source: scores/Stravinsky - Petrushka (3 movements arr. piano).pdf (37 pages, all music; rendered at 150 dpi, every system looked at, doubtful spots cropped and upscaled, barlines also located by a column-darkness script).
Compared with: out/testset/stravinsky-petrushka/stravinsky-petrushka-reference.musicxml (627 bars, 61 `<time>` entries, listed in meters.md).

## How the bars were counted

- This edition prints no rehearsal numbers and no bar numbers. I counted barlines from bar 1 (page 1, first bar) to the final barline (page 37). Ossia staves (pages 34, 36) are not counted. No repeats. Total: 624 bars.
- Two bars run across a system break with no barline at the end of the first system: bar 152 (page 8, from the end of system 3 into the start of system 4, the 6/8 bar) and bar 451 (page 29, from the end of system 2 into the start of system 3). Each is counted once.
- Bar 221 is one unmetered cadenza bar. It has no barline from the start of page 13 system 3 to the double barline in page 14 system 2 (about one and a half pages), and no meter is printed in it.
- Per-page bar counts (first-last, bars per system): p1 1-17 (4,4,4,5); p2 18-34 (4,5,4,4); p3 35-52 (5,5,4,4); p4 53-70 (4,4,5,5); p5 71-82 (3,3,3,3); p6 83-108 (6,7,5,4,4); p7 109-133 (5,4,5,5,6); p8 134-159 (6,6,7+,4,4; bar 152 split); p9 160-173 (2,2,2,2,6); p10 174-190 (5,4,2,3,3); p11 191-201 (3,3,3,2); p12 202-213 (3,3,3,3); p13 214-220 (3,4) then bar 221 starts; p14 221 ends, 222-232 (2,3,3,3 after the end of 221); p15 233-248 (3,2,4,3,4); p16 249-264 (5,5,3,3); p17 265-282 (3,3,4,5,3); p18 283-292 (2 per system); p19 293-302 (2 per system); p20 303-314 (2,2,3,3,2); p21 315-325 (2,3,3,3); p22 326-334 (2,2,3,2); p23 335-346 (3,3,3,3); p24 347-360 (5,3,3,3); p25 361-383 (2,4,5,6,6); p26 384-400 (4,4,3,4,2); p27 401-426 (5,5,6,5,5); p28 427-442 (4 per system); p29 443-465 (5,4,6,5,4; bar 451 split); p30 466-489 (4,4,5,5,6); p31 490-512 (6,5,6,6); p32 513-528 (5,5,6); p33 529-540 (5,3,2,2); p34 541-549 (2,2,3,2); p35 550-570 (2,5,4,5,5); p36 571-591 (6,3,3,5,4); p37 592-624 (6,6,7,7,7).
- Cross-check with the model's page-xml: the bar count agrees on 25 of 37 pages (1-7, 11, 12, 15, 18-25, 27, 28, 30, 31, 34-36). It differs by one on pages 8, 9 and 29, and by a lot on dense pages (10, 13, 14, 16, 17, 26, 32, 33, 37), where the model splits or merges bars. On pages 8 and 29 the model counts the split bar twice.

## 1. Printed time signatures

"new" = a meter change with no caution sign before it. "caution" = a sign printed at the end of a system, after the barline, for the next system. "repeat" = the sign printed again at the start of the next system after a caution sign; the meter change takes effect there (the repeat at bar 134 changes nothing). System numbers count top to bottom. Tempo and expression words are only those near a sign or at a section start.

| PDF page | System | Bar | Meter printed | Kind | Tempo / mark |
|---|---|---|---|---|---|
| 1 | 1 | 1 | 2/4 (all 3 staves) | new | Allegro giusto, quarter = 116 |
| 6 | 2 | 89 | none | - | Poco meno mosso |
| 6 | 3 | 96 | none | - | Tempo I (Allegro giusto), after a double barline at 95|96 |
| 7 | 3 | 122 | 1/4 | new | |
| 7 | 3 end | 122|123 | 2/4 | caution | |
| 7 | 4 | 123 | 2/4 | repeat | |
| 8 | 1 | 134 | 2/4 | repeat (new movement, meter unchanged) | II. Chez Petrouchka, Stringendo, quarter = 100 |
| 8 | 2 | 142 | none | - | Molto meno, quarter = 50 (after double barline, no sign) |
| 8 | 3 end | 152 | 6/8, with "(2/4)" printed in parentheses under it | new | bar 152 continues into page 8 system 4 |
| 8 | 4 | 154 | 2/4 | new | |
| 8 | 5 | 156 | none | - | Allegro, quarter = 76 |
| 9 | 5 | 168 | none | - | Furioso, quarter = 108 |
| 9 | 5 | 173 | 3/4 | new | |
| 9 | 5 end | 173|174 | 2/4 | caution | |
| 10 | 1 | 174 | 2/4 | repeat | |
| 10 | 1 end | 178|179 | 4/8 | caution (after double barline and key change to D major) | |
| 10 | 2 | 179 | 4/8 | repeat | Adagietto, eighth = 54 (accel. over bar 183) |
| 10 | 3 | 184 | 3/8 | new (after double barline) | one bar, no barlines inside |
| 10 | 3 end | 184|185 | 4/8 | caution | |
| 10 | 4 | 185 | 4/8 | repeat | Andantino, eighth = 80 |
| 10 | 5 end | 190|191 | none | - | double barline, key change to G major, no sign |
| 11 | 1 | 193 | 3/4 | new | |
| 11 | 1 end | 193|194 | 2/4 | caution | |
| 11 | 2 | 194 | 2/4 | repeat | |
| 11 | 2 | 196 | 3/4 | new | |
| 11 | 2 end | 196|197 | 2/4 | caution | |
| 11 | 3 | 197 | 2/4 | repeat | |
| 12 | 1 | 204 | 3/4 | new | Meno mosso at 203 (double barline, no sign), rit. at 204 |
| 12 | 1 end | 204|205 | 2/4 | caution (after double barline, key change to C) | |
| 12 | 2 | 205 | 2/4 | repeat | Allegro, quarter = 100 |
| 12 | 2 | 206 | 3/4 | new | |
| 12 | 2 | 207 | 2/4 | new | |
| 12 | 3 end | 210|211 | 3/4 | caution | bars 208-210 carry no sign |
| 12 | 4 | 211 | 3/4 | repeat | |
| 12 | 4 | 212 | 2/4 | new | |
| 12 | 4 | 213 | 3/4 | new | |
| 12 | 4 end | 213|214 | 2/4 | caution | |
| 13 | 1 | 214 | 2/4 | repeat | |
| 13 | 3 | 221 | none (no meter anywhere in the cadenza) | - | Cadenza, Tempo, ritardando, accelerando, rapido; runs to page 14 system 2 |
| 14 | 2 | 222 | 3/4 (after double barline) | new | Vivo-stringendo, quarter = 100 |
| 14 | 2 | 223 | none | - | Lento (a one-beat bar) |
| 14 | 3 | 224 | none | - | a tempo (3 groups of 5) |
| 14 | 3 | 225 | none | - | Lento (one-beat bar) |
| 14 | 3 | 226 | none | - | a tempo (2 groups of 5) |
| 14 | 3 end | 226|227 | 2/4 | caution | |
| 14 | 4 | 227 | 2/4 | repeat | |
| 15 | 2 | 237 | 3/4 | new | |
| 15 | 3 | 240 | 2/4 | new | |
| 15 | 3 | 241 | 3/4 | new | |
| 15 | 5 | 245 | none | - | Lento (doppio movimento) |
| 15 | 5 | 246 | 2/4 | new | fermata bar |
| 15 | 5 | 248 | 4/4 (after double barline) | new | Piu mosso, risoluto; final barline of movement II |
| 16 | 1 | 249 | 6/8 (3 staves) | new | III. La semaine grasse, Con moto, dotted quarter = 84. The small 5/4 and 3/2 stacks above the first two chords are fingerings. |
| 17 | 5 | 282 | 9/8 | new | |
| 17 | 5 end | 282|283 | clipped by the page margin (probably 3/2) | caution (after double barline, key change to F) | "eighth = eighth" tempo link |
| 18 | 1 | 283 | 3/2 | new | Allegretto, half note = 63 |
| 20 | 2 end | 306|307 | 4/4 | caution (after double barline, key change to C) | |
| 20 | 3 | 307 | 4/4 | repeat | |
| 23 | 4 end | 346|347 | 6/8 | caution | metric-modulation mark (dotted half note = ...) |
| 24 | 1 | 347 | 6/8 | repeat | metric-modulation mark (dotted quarter = ...) |
| 25 | 2 | 364 | 2/4 (after double barline) | new | Piu mosso (eighth = eighth, footnote: speed unchanged) |
| 26 | 1 end | 387|388 | 6/8 | caution (after double barline) | |
| 26 | 2 | 388 | 6/8 | repeat | Tempo I |
| 26 | 5 end | 400|401 | 2/4 | caution (after double barline) | |
| 27 | 1 | 401 | 2/4 | repeat | Piu mosso (come sopra) |
| 27 | 3 end | 416|417 | none | - | double barline, key change to A major, no sign |
| 27 | 4 | 417 | none | - | Tempo giusto, quarter = 112 |
| 30 | 2 | 471 | 3/4 | new | |
| 30 | 2 | 472 | 2/4 (after double barline) | new | key change to C |
| 31 | 1 end | 495|496 | none | - | double barline, key change to A major, no sign |
| 33 | 1 end | 533|534 | 4/4 | caution (after double barline, key change to C) | |
| 33 | 2 | 534 | 4/4 | repeat | Agitato |
| 35 | 1 end | 551|552 | 2/4 | caution | |
| 35 | 2 | 552 | 2/4 | repeat | |
| 35 | 2 | 555 | 3/4 | new | |
| 35 | 2 | 556 | 2/4 | new | |
| 35 | 3 | 559 | 3/4 | new | |
| 35 | 3 | 560 | 5/8 (after double barline, key change to E flat) | new | Piu mosso, (quarter = 72) |
| 35 | 5 | 570 | 6/8 | new | one bar |
| 35 | 5 end | 570|571 | 5/8 | caution (after double barline) | |
| 36 | 1 | 571 | 5/8 | repeat | |
| 36 | 5 | 589 | 2/4 (after double barline, key change to A flat) | new | |
| 37 | 2 end | 603|604 | none | - | double barline, key change to C, no sign |

Pages with no sign at all (the meter in force continues): 2-6, 19, 21, 22, 28, 29, 31, 32, 34, 37. Page 4 has a key change (double barline at bars 58|59, to A major, no sign) and one back at bar 70|71, also no sign.

Printed meter changes in total: 48 (31 "new" rows, including the opening 2/4 on page 1, plus 17 "repeat" rows; the repeat at bar 134 is not a change and is not counted). A change that has a caution sign and a repeat is counted once.

## 2. Comparison with the reference's 61 entries

Bar alignment. The reference and my count agree exactly up to bar 154. After that the reference is one bar early (ref 172 is scan bar 173) up to the cadenza. The reference then spends four bars on the one cadenza bar (ref 220-223 = scan 221), so from ref 224 on, ref = scan + 2. Between ref 403 and ref 474 it gains one more bar, so from ref 474 on, ref = scan + 3. The totals fit: 624 + 3 = 627. The "scan bar" column below is my running number.

Where the reference loses the one bar between bar 154 and 173 I did not find. Page 9 (bars 160-173) has 8 bars in systems 1-4 (two per system, each with a visible interior barline and a right-edge barline) and 6 in the Furioso system; the model's page 9 output also has 13 instead of my 14 bars. The extra bar that appears between ref 403 and ref 474 is probably the split bar 451 on page 29 (the model counts it twice too); not confirmed.

Verdict key: match = the scan prints that meter at that place (within the stated offset); different = the scan prints another meter there; nothing = no sign printed at that place.

| Ref bar | Ref meter | Scan bar | Scan prints | Verdict |
|---|---|---|---|---|
| 1 | 2/4 | 1 | 2/4 | match |
| 122 | 1/4 | 122 | 1/4 | match |
| 123 | 2/4 | 123 | 2/4 | match |
| 152 | 6/8 | 152 | 6/8 (and "(2/4)") | match |
| 154 | 2/4 | 154 | 2/4 | match |
| 172 | 3/4 | 173 | 3/4 | match (ref one bar early) |
| 173 | 2/4 | 174 | 2/4 | match (ref one bar early) |
| 178 | 4/8 | 179 | 4/8 | match (ref one bar early) |
| 183 | 3/8 | 184 | 3/8 | match (ref one bar early) |
| 184 | 4/8 | 185 | 4/8 | match (ref one bar early) |
| 190 | 2/4 | 191 | nothing (double barline and key change to G major, no sign; the 4/8 in force is the same length as 2/4) | nothing |
| 192 | 3/4 | 193 | 3/4 | match |
| 193 | 2/4 | 194 | 2/4 | match |
| 195 | 3/4 | 196 | 3/4 | match |
| 196 | 2/4 | 197 | 2/4 | match |
| 203 | 3/4 | 204 | 3/4 | match |
| 204 | 2/4 | 205 | 2/4 | match |
| 205 | 3/4 | 206 | 3/4 | match |
| 206 | 2/4 | 207 | 2/4 | match |
| 210 | 3/4 | 211 | 3/4 | match |
| 211 | 2/4 | 212 | 2/4 | match |
| 212 | 3/4 | 213 | 3/4 | match |
| 213 | 2/4 | 214 | 2/4 | match |
| 220 | 43/16 | 221 | nothing (cadenza, no meter) | nothing |
| 221 | 49/32 | 221 | nothing (same bar) | nothing |
| 222 | 15/8 | 221 | nothing (same bar) | nothing |
| 223 | 65/32 | 221 | nothing (same bar) | nothing |
| 224 | 3/4 | 222 | 3/4 | match |
| 225 | 1/4 | 223 | nothing (Lento bar, one beat long) | nothing |
| 226 | 3/4 | 224 | nothing (the 3/4 printed at 222 is still in force) | nothing |
| 227 | 1/4 | 225 | nothing (Lento bar, one beat long) | nothing |
| 228 | 2/4 | 226 | nothing at 226 (2 groups, so 2/4 long); 2/4 is printed at 227 | match (ref one bar early again) |
| 239 | 3/4 | 237 | 3/4 | match |
| 242 | 2/4 | 240 | 2/4 | match |
| 243 | 3/4 | 241 | 3/4 | match |
| 248 | 2/4 | 246 | 2/4 | match |
| 250 | 4/4 | 248 | 4/4 | match |
| 251 | 6/8 | 249 | 6/8 | match |
| 284 | 12/8 | 282 | 9/8 | different (9 eighth-note chords in the bar, sign reads 9/8) |
| 285 | 3/2 | 283 | 3/2 | match |
| 295 | 6/4 | 293 | nothing (3/2 in force; same length as 6/4) | nothing |
| 309 | 4/4 | 307 | 4/4 | match |
| 331 | 5/4 | 329 | nothing (4/4 in force; I did not check the bar's length) | nothing |
| 332 | 4/4 | 330 | nothing (4/4 in force since 307) | nothing |
| 349 | 6/8 | 347 | 6/8 | match |
| 366 | 2/4 | 364 | 2/4 | match |
| 390 | 6/8 | 388 | 6/8 | match |
| 399 | 3/8 | 397 | nothing (6/8 in force; I did not check the bar's length) | nothing |
| 401 | 6/8 | 399 | nothing (the 6/8 printed at 388 is still in force) | nothing |
| 403 | 2/4 | 401 | 2/4 | match |
| 474 | 3/4 | 471 | 3/4 | match |
| 475 | 2/4 | 472 | 2/4 | match |
| 537 | 4/4 | 534 | 4/4 | match |
| 555 | 2/4 | 552 | 2/4 | match |
| 558 | 3/4 | 555 | 3/4 | match |
| 559 | 2/4 | 556 | 2/4 | match |
| 562 | 3/4 | 559 | 3/4 | match |
| 563 | 5/8 | 560 | 5/8 | match |
| 573 | 6/8 | 570 | 6/8 | match |
| 574 | 5/8 | 571 | 5/8 | match |
| 592 | 2/4 | 589 | 2/4 | match |

Meters the scan prints that the reference lacks: none as a change, except that 9/8 (bar 282) is absent as a value; the reference has 12/8 there. The 2/4 printed again at the start of page 8 (bar 134) is a repeat of the meter in force and needs no entry.

Reference meters the scan does not print: 43/16, 49/32, 15/8 and 65/32 (bars 220-223). All four fall inside the single unmetered cadenza bar (bar 221 here); none of the four is printed anywhere in the score, and no printed meter has a denominator above 8. The other nine entries with nothing printed are 190 (2/4), 225 (1/4), 226 (3/4), 227 (1/4), 295 (6/4), 331 (5/4), 332 (4/4), 399 (3/8) and 401 (6/8). Of these, 226, 332 and 401 restate a printed meter that is already in force, and 190 and 295 relabel the meter in force with another of the same length (4/8 as 2/4, 3/2 as 6/4). 225 and 227 are the two one-beat Lento bars; 331 and 399 are lengths the reference inferred, which I did not verify.

No `<time>` element in the reference has `print-object="no"`. The 1100 `print-object="no"` attributes in the file are all on `<note>` elements.

## 3. Totals

| | Count |
|---|---|
| Reference entries | 61 |
| Right (the scan prints that meter at that place, allowing the offsets above) | 47 |
| Wrong (the scan prints a different meter there: 12/8 against 9/8) | 1 |
| Invented (nothing printed there) | 13 |
| Printed meter changes in the scan | 48 |
| Printed meters missing from the reference (9/8 at bar 282; the reference has 12/8 in its place) | 1 |

The 13 invented: bars 220, 221, 222, 223 (cadenza), 225, 227 (Lento bars), 331, 399, and the five restatements or relabels 190, 226, 295, 332, 401.

17 of the 47 right entries (ref 172-213) sit one bar earlier in the reference than in my count, and ref 228 sits one bar before the sign. Taken at the reference's own bar numbers and not allowing for the offsets, only the first 5 entries (1, 122, 123, 152, 154) match exactly.

## Uncertain points

- The sign at the end of page 17 (after the 9/8 bar) is clipped by the page margin. It is the caution for the 3/2 that opens page 18; the digits themselves cannot be read for certain (they look like 6 over 4 or 3 over 2).
- The count of 33 bars on page 37 comes from reading barlines; the model's output has 28. No sign is printed on page 37, so the comparison does not depend on it, but the total of 624 does.
- The offset arguments depend on the unexplained missing bar between 154 and 173 and the guess about bar 451. If either is wrong the bar alignment of the later entries shifts by one, but every verdict above holds at the level of "the same sign in the same sequence of signs".
- Lengths of the nothing-printed bars were not measured, except where stated.
