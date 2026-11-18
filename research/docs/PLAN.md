# Piano OMR plan

**Goal.** Reach 97% staff-sensitive sounding-pitch F1 on every real piece. Match each visible notehead to its sounding pitch, aligned bar and printed staff.

Remove each task when it closes. Record dated status in [PROGRESS.md][progress] and measured outcomes in [EXPERIMENTS.md][experiments] or the experiment’s report.

**Minimal pairs for training.** Render two versions of the same passage, changing one printed cue. Use the same engraving and scan degradation for both. Derive each label from its own version and check which MusicXML fields should change. In the later trials, add or remove one inner chord note, tie or reattack the same repeated pitch, or show or omit a numeral over an already established tuplet while keeping its timing identical. A courtesy accidental can likewise change the printed sign while preserving pitch. For meter, render a whole-measure rest in 3/4 and 3/8. Changing the printed denominator changes the rest’s duration. Keep variants of a work in one split. On held-out pairs, count how often **both** versions are read correctly. Judge transfer on independent real scans.

## Next steps

1. **Analysis — finish the scan pilot.** Complete the seed-11 scan and rendered-twin evaluations. Compare the arms within each seed, by work, on the 28 complete scans, the original 72 crops and the independent 145 crops. Expand scan exposure if the gain repeats across independent development works. If it stays concentrated in Schubert, test implied tuplets directly. Reserve the 520 second-batch crops for the next mixture and keep *Une barque* for a separate comparison because it shares an edition with *Alborada*. [Pilot specification][spec]

2. **Data preparation — build octave-bracket minimal pairs.** Keep the printed notes and bracket start fixed. Move the end hook from one note to the next, then make an unbracketed copy. Adjust the source sounding pitches to preserve notehead positions. Inspect the augmented 256×1280 crops by eye. Include 8va and 8vb, mid-bar and chord endings, low bass without a bracket, and real continuations across systems. Keep genuinely open spans open at the crop edge. Split by work, including all its variants. [Octave examples][octave]

3. **Analysis — run the two-image, two-answer test before pitch training.** Take a held-out pair where the hook ends after D in one image and after E in the other. Use the released decoder to score both token sequences on each image. Count a pair as correct only when moving the hook flips the preference in the correct direction. If both rankings are correct but the final transcription is wrong, compare free decoding with the exported MusicXML. If ranking errors persist after ordinary minimal-pair training, compare that arm with the same arm plus a contrastive ranking loss on training pairs.

4. **Training — test bracket endings and unbracketed register errors separately.** Use one control with ordinary examples, one arm with the bracket pairs, and one with unbracketed ledger lines, clef changes and cross-staff notes. In register pairs, vary the clef or move one notehead by one staff step. Match checkpoint, training exposure, update count, seeds and layout. On unseen real works, score both notes bordering the hook, missed starts, early/late/missing stops, false 8vb and unbracketed octave errors. Compare raw tokens with final MusicXML to catch automatic closure. Combine changes if each helps independently.

5. **Layout analysis — proceed in parallel.** Verify *Petrushka*’s three-staff reference against the print. On independent mixed-staff pages, trace the first system that loses a staff or collapses voices. Check hand placement on Scriabin’s restored page. Before adopting the Schott-trained pairing model, test it end to end with the same merger on a different thin-brace edition and on vocal or chamber pages where a false join matters. [Brace transfer tests][brace]

6. **Rhythm training — compare explicit tuplet groups with the current encoding on identical images.** Label voice, group boundaries, exact ratio, written values and dots, and whether the numeral or bracket is printed. Include mixed values, rests, nested and implied groups, and ordinary groups of three in 6/8 and 9/16. Score boundaries, invented marks and full-note F1 by work. Check MusicXML appearance and playback duration. Test adjacent-system context separately when the crop is ambiguous. Check the writer on whole-bar rests, pickups and partial-voice rests. [Timing audit][timing] · [Bar-rest audit][rests]

## Other open work

- **Encoder localization probe, if the hook is still missed.** Save hook coordinates on new renders. Freeze the encoder and train a small predictor on its image tokens. Check on hand-marked real development scans whether it locates the hook precisely enough to distinguish neighboring notes. Reliable localization points to testing hook-to-note assignment next. Weak localization warrants a trial adding a location loss alongside transcription.
- **Hard-example mining on training works.** Use the released model to flag late stops, invented 8vb and skipped repeated attacks. Verify the flags against the print. Compare training on those crops with training on equally many randomly selected, verified crops from the same works. Match updates and evaluate both on independent real pieces.
- **Training-pair recovery, in parallel.** Pilot the aligner on three Scarlatti sonatas, including repeated notes. Compare the aligner alone with Terra- and Sonnet-assisted matches under blind musical review. Count false accepts and difficult verified pairs per review hour and per dollar before expanding to independent virtuoso works. [KernScores pairing notes][kern]
- **Later notation trials, in order.** Test line/space pitch with predicted and verified clefs, then shared chord rhythm with per-note ties and accidentals and distinct voices, then meter digits with distinct common- and cut-time symbols. Evaluate each change separately on held-out real editions. [Meter data][meter]
- **Choose further training from residual errors.** Replay development pages with verified staff pairs, bar placement and octave spans individually and together. Count skipped attacks, missing chord members and wrong pitches in aligned bars. Test native higher resolution if resizing erases marks, decoder capacity if visible attacks are skipped, or a longer schedule if development gains continue.
- **Release evaluation.** Select on development works. On the frozen 28 and fresh editions, report each staff, the worst piece, the count reaching 97%, pitch+onset and full-note F1. Use pooled pitch to diagnose staff assignment. Run the required Polish benchmark comparison and inspect each regressing real page.

[progress]: PROGRESS.md
[experiments]: EXPERIMENTS.md
[spec]: ../scan_pairs_virtuoso/PILOT_SPEC.md
[octave]: ../octave_checks/OCTAVE_CAUSES.md
[brace]: ../staff_rel_realbrace/SAME_EDITION.md
[timing]: ../eval/timing_audit.md
[rests]: ../barrest_audit/REPORT.md
[kern]: ../box_scripts/run4_scans/README.md
[meter]: ../box_scripts/run4_meters/README.md
