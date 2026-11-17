# Time signature numerators are inferred, and that couples them to duration errors

I ran homr over nine public domain piano scores from Mutopia (clean LilyPond
engravings, so about as easy as real input gets) and noticed that every meter
which isn't 4/4 or 2/2 came out wrong:

| Score | Printed | homr | Audiveris | rokot-omr-2b |
|---|---|---|---|---|
| Bach BWV 848 prelude | 3/8 | **1/4** | 3/8 | 3/8 |
| Mozart KV 331 mvt 1 | 6/8 | **3/4** | 6/8 | 6/8 |
| Chopin Ballade 4 | 6/8 | **3/4** | 6/8 | 6/8 |
| Liszt La Campanella | 6/8 | **4/4** | 6/8 | 6/8 |
| Bach BWV 848 fugue | 4/4 | 4/4 | 4/4 | — |
| Mozart KV 309 mvt 1 | 4/4 | 4/4 | 4/4 | — |
| Beethoven Op. 13 mvt 1 | C and ¢ | both ✓ | both ✓ | ✓ |
| Rachmaninoff Op. 3/2 | C | ✓ | ✓ | ✓ |

Four out of eight, and the four failures are exactly the non-simple meters.

## Why I think it happens

`Vocabulary.md` rule 6 documents the design:

> Time signatures contain only the beat type. The number of beats is
> reconstructed from the median measure length.

That is mathematically exact — `numerator = median_bar_duration × denominator`
recovers 6/8 from three quarter-notes and a denominator of 8, and homr does emit
compound meters when the arithmetic calls for them (Petrushka came out with 9/16
and 5/8). So this isn't a representational limit.

The cost is that meter correctness now depends on duration correctness, and the
dependency runs both ways. La Campanella is the clearest case: homr called it
4/4. Every genuine 6/8 bar then measures a quarter short, so a downstream tool
that trusts the meter sees ~270 short measures in a 147 bar piece. A single wrong
token at the top of the score turns into an error in every bar after it.

The 6/8 cases are also interesting because 6/8 and 3/4 hold the same amount of
music. Where homr read the durations correctly it still had to choose a label,
and it chose 3/4 both times. No amount of measuring bar contents can separate
those two — the distinction only exists in the printed symbol.

## The question

Would encoding the numerator as its own branch (or as a combined
`timeSignature/6/8` token) be worth the vocabulary cost?

What makes me think it might: rokot-omr-2b is also an autoregressive sequence
model with no dedicated header stage, and it reads the numerator directly as part
of `M:6/8`. It got all six meters right in this set. So the usual argument that
the token is too rare to learn doesn't obviously apply — the difference seems to
be whether the numerator is *read* or *computed*.

Happy to share the exact scores and outputs if useful, all of them are public
Mutopia PDFs.
