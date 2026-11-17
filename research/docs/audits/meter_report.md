# Time-signature labels vs images (audit, 2026-11-15)

Sonnet helper; 263 staff crops checked by eye. Raw tables and the checked examples are on the
GPU box in `/workspace/audit_meter/` (`agg_all.txt`, `analyse_full_all.txt`,
`staff_stats_all.txt`, `vocab_counts.txt`, `kern_meta.out`, `examples.md`); scripts in
`audits/meter_scripts/`; crop montages were in the session scratch folder.

## Conclusion

Every dataset: the full time signature can be derived from the source, and the existing
images agree. No re-render; regenerate tokens only.

## What each renderer draws

- MuseScore, and Verovio from MuseScore XML (PDMX, hard PDMX, Lieder, ASAP, Scriabin,
  MuseScore octave): `<time symbol="common">` draws C, `symbol="cut"` draws cut C (also on
  4/4), otherwise numbers. A system without `<time>` in its first bar draws no signature.
  Restated meters are drawn.
- LilyPond (octave data): musicxml2ly writes `\numericTimeSignature` when the source has no
  symbol, so 4/4 and 2/2 are drawn as numbers (the plan's assumption that LilyPond turns
  them into C was wrong). With a symbol: C for 4/4, cut C for 2/2.
- GrandStaff (Verovio from kern): `*met(c)`/`*met(C)` draw C, `*met(c|)`/`*met(C|)` cut C,
  otherwise `*M` numbers.

## Label fixes

- `<time print-object="no">` draws nothing but has a token: 246 staffs (PDMX, hard, Lieder,
  octave). Drop the token.
- 124 GrandStaff samples without `*M` draw nothing but carry `timeSignature/4`. Drop it.
- 435 GrandStaff samples draw C on a 3/4 or 3/8 meter. Drop these samples.
- PDMX windows do not always draw a signature (only 14.6% of PDMX staffs start with one);
  the comment in `convert_lieder.py` (`always_include_time`) needs checking.

## Meter changes and pickups

60-73% of meter changes keep the denominator (PDMX 63%, hard 60%, Lieder 73%); staffs with
one: PDMX 6,553, hard 5,767, Lieder 969, LilyPond 538, MuseScore octave 469. The loader
removes the repeated denominator-only token, so these changes are lost today. Pickup staffs
(PDMX 895, Lieder 737, LilyPond 590) all draw the meter.

## Caveat

ASAP and Scriabin could only be read from the pre-export `.mxl`; 91% and 64% of their staffs
could be matched to a source.

## Proposed vocabulary (before deduplication)

34 numeric meters with at least 50 occurrences plus `common` (8,438) and `cut` (1,329),
covering 99.7% of printed signatures: 3/4 31,024; 4/4 29,063; 2/4 19,311; 6/8 10,748;
3/8 7,171; 2/2 5,128; 1/4 4,380; 9/8 3,050; then 5/8, 1/8, 7/8, 6/4, 12/8, 5/4, 3/2, 17/16,
7/4, 13/16, 4/2, 11/16, 8/4, 15/16, 4/8, 13/8, 9/16, 19/16, 12/16, 5/16, 9/4, 11/8, 15/8,
10/4, 7/16, 2/8. Denominators in use: 1, 2, 4, 8, 16, 32. Odd meters (17/16, 13/16, 19/16)
are probably cadenzas or encoding artefacts; check before keeping them.
