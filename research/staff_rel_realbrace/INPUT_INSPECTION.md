# What the staff-pairing classifier sees of the Schott brace (D25)

Written 2026-11-17, about 7:05 pm Pacific. Code and figures in `run/staff_rel_realbrace/input_inspection/` (`inspect_input.py`, `run_all.py`, `summary.json`, figures `*.png`).
Nothing was trained; the Schott scans were only looked at (test data). Shipped model = `staff_relations_pdmx2`; rb1, rb2, rb3 = `staff_relations_realbrace-{1,2,3}.onnx`.

## What was done

For the 13 printed systems of the three opening pages (Etude 5 p. 29, Etude 10 p. 76, Sonata p. 2), 5 pairs of two working scans (Waldstein, Paganini) and 16 grand-staff pairs of the Reichardt song volume
(held out for the shipped model, A0 s0 and B s0; rb3 is trained on it) the crop was rebuilt exactly as `homr.staff_relations.page_inputs` builds it (96 x 96, 4 pixels per unit, 10 units of margin, 5 channels).
Each figure row shows: the page margin at native resolution (straight rectangle of `predictions.original`, 12-17 px per staff unit at 150 dpi), the five channels (gray ink, staff, symbols, stems/rests, clefs/keys) and the three probabilities of each model.
Figures: `schott_te5_p029.png`, `schott_te10_p076.png`, `schott_sonata_p02.png` (the 13 systems), `working_waldstein_p02.png`, `working_paganini_p11.png`, `reichardt_p04_0/1.png`, `reichardt_p06.png`, `reichardt_p08.png`, `reichardt_p09_0/1.png`, `reichardt_p10_0/1.png`.
Numbers: `summary.json` (per pair: calls, probabilities, tallest connected structure per channel, brace peak per channel at 4, 8 and 12 pixels per unit). The brace is at columns 38-43 of the crop, i.e. right at the staff start (column 40).
"Peak" = the best column in the margin zone (3 units left to 1 unit right of the staff start), mean over the gap rows between the staves (0 = nothing, 1 = a solid line across the whole gap).

## Findings

1. **The Schott brace survives the crop.** It is a thin, nearly straight stroke (2-3 px at 150 dpi, about 0.8 px in the crop). It is visible in the gray-ink channel in all 13 systems (continuous, with the point) and in the
   symbols channel. Peak over the gap, mean of 13 (min): gray 0.74 (0.62) at 4 px/unit, 0.86 (0.81) at 8, 0.88 (0.81) at 12; symbols 0.53 (0.41), 0.76 (0.61), 0.82 (0.73). The working scans (5 pairs) give gray 0.50 and symbols 0.52 at 4
   (curved brace, wider stroke, so the area average is lower): the Schott brace is not weaker in the crop than the brace of the scans the model reads at 100 %. Going from 4 to 8 px/unit would raise the symbols peak by about 40 % and the gray peak by 15 %, which is a gain in contrast,
   not a brace which was lost. The staff, stems/rests and clefs/keys channels do not carry the brace (clefs/keys picks up nothing in the margin on Schott).
2. **The segmentation net draws it differently.** It has no brace class; the brace is rendered in the *symbols* channel. On the working scans it is one continuous wavy curve over both staves (tallest connected structure 0.73 of the crop height,
   Waldstein / Paganini); on Schott it is a thin straight line which is broken at the point of the brace (tallest 0.38, i.e. one piece per staff: it looks like the first line of each staff, not like a connection). In the gray channel the stroke is continuous on Schott (tallest 0.80). See `schott_*.png`
   against `working_waldstein_p02.png`, and the enlarged channels of Schott pair 0-1 and Waldstein pair 0-1 in `channels_schott_vs_waldstein.png`.
3. **The shipped model reads this as "same system" with certainty**: 13 of 13 pairs, mean p(same system) 0.99, p(grand staff) 0.01 (rb1 2 of 13 grand, rb2 5, rb3 7, mean p(grand) 0.22 / 0.39 / 0.47: the same 13 pairs the README counts as 0, 2, 5, 7).
   A diagnostic, not a fix, on the shipped model (crops edited, nothing trained, `input_inspection/diag_symbols.py`): copying the gray line into the symbols channel left of the staff start changes nothing (0 of 13 grand); erasing the symbols channel there
   moves 3 of 13 to grand staff (mean p(grand) 0.34) and leaves the 5 working pairs at grand staff. So the symbols channel margin pushes the Schott crops to "same system" and the gray-channel line does not outweigh it; the model learned to read the symbols channel, where the Schott brace looks like two separate staff starts.
4. **Reichardt (the held-out thin edition) is a different case.** Its grand pairs have a heavy double line through all three staves of the system (voice and piano, 'same system' for the voice / upper piano pair) and the small grand-staff brace of the piano stands inside it, partly in the clefs/keys channel
   (`reichardt_p10_0.png`). The margin line is as strong for the 'same system' pairs as for the grand pairs (gray peak 0.64 vs 0.56, symbols 0.69 vs 0.53, 16 + 16 pairs), so a heavy line is no cue for a grand staff there. Shipped, A0 s0 and B s0 call the same 13 of 16 grand pairs
   'same system' (identical calls; rb3, trained on the volume, 15 of 16 grand). Caveat: these labels come from the position in the three-staff chain (pair n mod 3 = 1 is the grand pair), 7 of 9 sampled pages were usable (two have a staff count not divisible by 3), and in 4 of the 16 crops the gray peak is below 0.2
   (a weak or absent margin line: the chain may be shifted by a mis-detected staff, or the pair is on a page edge), so this part is qualitative.
5. **Resolution test not run.** The brace is neither degraded by the resizing nor missing from the channels (finding 1), so a higher-resolution crop (8 or 12 px/unit, a bigger input and a longer head) with a retrained network would not address what is wrong: the symbols channel, which the model reads, shows two staff starts
   on Schott where it shows one curve on the training scans. It would also need new crops of all training pages (the stored mixture is at 4 px/unit) and a longer head, and every real scan in it is of the curved-brace kind. No GPU or CPU training was started.

## Recommendation

Train the same CNN on broader real examples first: scans whose brace is thin and straight with a point and no connecting line (the other Schott etudes, other thin-brace editions), and with the brace drawn by variations that also break the symbols-channel line at the point. The input does not need to change.
Cheaper checks before that: (a) take the segmentation net's symbols output for the Schott pages and see whether the break at the point is the net's choice (a larger 'brace' class in its training data would fix it for every consumer), (b) whether the gray line suffices for a model trained without the symbols channel (ablation on the existing training mixture; needs the stored crops only, channel 2 set to zero).
