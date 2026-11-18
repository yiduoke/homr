# Octave-bracket review of batch 2 (by eye), 2026-11-17

47 crops where the label and the released model's read disagree on an 8va/8vb sign or on octaves (pitch classes agree) plus 3 kept-tier crops whose label bracket extent differs from the print. Per crop: `octave_review.csv` (crop, piece, direction, label/read bracket events as bar.note, octave delta label-read under the label bracket, decision, aligned share after correction, note, corrected tokens).
Method as the pilot (`../octave_review.md`): scan region (margin above) over a Verovio engraving of the label measures (open brackets re-opened) and per-note octave deltas against the read (`scripts/octave_delta.py`); token convention: pitch tokens are the written pitches, the shift tokens carry the shift.

| decision | crops | meaning |
|---|---|---|
| admit as is | 7 | label right: print and label agree (no bracket in either, the model invented one: N1 x2, N2 x2; both have the bracket and the model missed it: N11_p-15_s5, N12_p-05_s0, N16_p-04_s2) |
| corrected, admitted | 27 | 20 edition difference (print writes the notes at pitch, ASAP has 8va with lowered notes): all shift tokens removed, notes under them raised; after it 92-100 % of aligned notes equal the scan read. 7 add a bracket the ASAP label lacks (printed bracket spans whole bars: N1_p-03_s1, N4_p-17_s0, N12_p-06_s4, Ravel p-25_s3/s4, p-26_s0/s1) |
| quarantined | 16 | N20 Schubert D.935/3 x7 (print has partial 8va, ASAP none), N7_p-03_s0 (12/8 vs 4/4 triplets), N7_p-04_s3 and N8_p-04_s2 (more than 5 ledger lines once raised), N6_p-29_s3, N8_p-05_s4, N9_p-07_s5 (unclear or partial extent), 3 kept-tier crops with partly wrong bracket extent (N8_p-05_s0, N11_p-16_s4, NR1_p-36_s5) |

Findings: Bote & Bock/Klindworth (Op.10/8), Breitkopf Serie 16 (Op.81a), Peters/Scholtz (Berceuse), Augener/Klindworth (Sonata 2) print high notes at pitch where ASAP uses 8va; the Gutheil, Cotta and Demets scans and Schubert Breitkopf print the brackets, and ASAP lacks some of them (Schubert variations, Une barque bars 98-102, Waldesrauschen, Op.10/5).
Pilot (`../octave_review.md`) finding repeated: training on the unreviewed ASAP label would teach 8va where the print has ledger lines.
