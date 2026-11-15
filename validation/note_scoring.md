# Individual-note evaluation

Run on existing uncompressed, concert-pitch, score-partwise MusicXML:

```sh
python -m validation.score_notes reference.musicxml baseline=baseline.musicxml candidate=candidate.musicxml --json note-scores.json
```

The scorer uses only the Python standard library. It reads scores without changing
them. JSON output includes input SHA-256 hashes, counts for each staff and both
combined, and every aligned or skipped measure. Indices in that report are one-based;
printed measure numbers are recorded separately. The default onset/duration tolerance
is 1/96 of a quarter note; override it with `--tolerance QUARTERS`.

## What counts

Every pitched notehead counts once, including every member of a chord, each grace note,
and each written segment of a tied note. Rests affect time but are not counted as
notes. Pitches include accidentals and octaves; enharmonic spellings are equivalent.
MusicXML already contains sounding pitches for octave brackets, so octave-shift
directions are not applied a second time.

Three metrics separate pitch content from timing:

| Metric | A match requires |
|---|---|
| `pitch_inventory` | Same staff and pitch within the aligned bar; ignores order, timing and grace status |
| `pitch_onset` | Same staff, pitch, grace status and onset relative to the bar |
| `pitch_onset_duration` | All of the above, plus duration |

Matching is one-to-one. A predicted note cannot match two reference notes. Chord members
can appear in any XML order. For the timing metrics, maximum bipartite matching avoids
greedy assignment errors when several repeated notes fall within the tolerance.

For each metric, let `M` be matched notes, `R` all reference notes and `H` all predicted
notes. Precision is `M/H`, recall is `M/R`, and micro F1 is `2M/(R+H)`. All notes in
skipped bars remain in these denominators. Empty bars cannot increase the score. Two
entirely empty scores receive 1; an empty score against a nonempty score receives 0.

These are **F1 scores, not percentages of correct notes**. `unmatched_reference` and
`unmatched_prediction` include wrong pitches and timing errors as well as omissions
and additions. A substitution contributes one unmatched note on each side. A wrong
rest or duration can shift several later onsets in the same bar. Report the pitch-only
diagnostic alongside the timing metrics so that this effect is visible.

## Alignment and limits

One monotonic bar alignment is shared by all staves. Dynamic programming maximizes
the overlap of `(staff, pitch)` inventories, breaking ties by fewer skipped bars and
then a diagonal match. This is a heuristic alignment, not a verified mapping. Review
the JSON pairs around repeated passages, cadenzas and split/merged bars. The scorer
does not support many-to-many bar alignment.

Onsets restart at each aligned bar. This measures notation timing, not uninterrupted
playback timing or tempo. Meter, beam groups, voice labels, spelling, ties, pedal and
dynamics are not scored directly. Grace notes at the same onset are unordered; ties
are not collapsed into sustained events. Staff assignment must agree, including for
cross-staff notation. Parts and staves are flattened in document order, allowing one
grand-staff part to match two single-staff parts. Unequal measure counts between parts,
transposing instruments and unpitched percussion are rejected.

Pitch inventory is a lenient diagnostic: scrambled notes can still match it. The
timing metrics are stricter, but cannot by themselves distinguish recognition errors,
postprocessing errors, reference errors or a bad bar alignment. When scoring merged
MusicXML, describe the result as exported-score quality, not transformer accuracy.

## Checks and local results

`tests/test_score_notes.py` covers chords, rests, backups/forwards, changing divisions,
grace notes, octave directions, part layout, duplicate pitches, note order, durations,
tolerance matching, missing/extra bars, joint staff alignment and CLI input protection.

The local Mazeppa and La Campanella results and diagnosis are recorded in
[PROGRESS.md](../PROGRESS.md#individual-note-rescoring-2026-11-15). Their reference
transcriptions and real pages remain evaluation-only. These two pieces are not evidence
of generalization to other music.
