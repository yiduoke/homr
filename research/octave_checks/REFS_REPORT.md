# Reference hygiene for octave brackets: seven suspect pieces (D33)

Laptop only, released weights (tag `layout1`) and the saved outputs of all tags, written about 10:10 pm Pacific, 2026-11-17. No model run, no training, nothing pushed, vast-homr4 not touched, no job started on vast-homr5. The scans and the references are evaluation data: used to decide, never to tune or train.
Procedure as for Schubert D. 899/4 (`REPORT.md`): find the disputed bracket spans in the reference XML, the released output and the page XML, locate them on the scan, decide (a) reference lacks or ends the printed bracket wrongly, (b) editions differ, (c) the model invented or misplaced a bracket.
Scripts (this folder): `refs_lib.py`, `bar_octave_diff.py` (per bar: pitch matches, and the matches if the upper staff of the output is moved by an octave), `notes_dump.py`, `locate.py` (bar -> page, system), `view.py`, `crop_render2.py` (Verovio, grand staff kept), `make_refs_evidence.py` (the figures), `rescore_edition.py`. Figures: `refs/*.png` (scan, reference engraving, model engraving; 12 decisions).

## Result in one paragraph

**None of the suspects is a Schubert-type reference gap.** In Hammerklavier, Wanderer, Liszt HR 6, Debussy Pour le piano and Scriabin the reference holds the *sounding* pitch under every printed bracket that was checked (Verovio draws them high above the staff exactly where the print has an 8va); what the references lack is only the bracket directions (no direction at all in Hammerklavier, orphan stops in Wanderer, HR 6, Debussy). Pitch scoring is therefore right, and the disputed octave differences are **model errors** (stop too late, stop too early, never closed, invented 8vb/8va, bracket not read). No edition-specific reference was written, the list of edition-corrected pieces stays `{schubert-impromptu-d899-4}` (now one list, `eval_run1/edition_refs.py`). Two statements of `OCTAVE_CAUSES.md` are corrected: Hammerklavier bar 247 and Wanderer bars 473-474 are model errors, not (e) reference gaps (those counts compared bracket directions, not the printed extent).

Why Schubert D. 899/4 was different: there ASAP kept the *written* pitch with no direction, so the sounding pitch was an octave low. In the other pieces ASAP kept the sounding pitch (the MuseScore export lost the directions, or most starts of them).

## How the disputed bars were found

`bar_octave_diff.py piece layout1 3` (pooled bar alignment): a bar is flagged if moving the upper-staff notes of the output by +-12/+-24 semitones gains 3 or more pitch matches against the reference. Positive shift = the output is lower than the reference (missed or too early stop), negative = higher (late stop, invented 8va). Lower staff checked the same way (flag at 4). Hammerklavier 7 bars, Wanderer 7, HR 6 8, Debussy 3, Kreisleriana 0 (upper) + 1 (lower), Scriabin 23 (+5 lower), Petrushka 49 (not usable, see below).

## Decisions (what the print shows; flagged bars are positions in the output file, "ref" is the reference bar index)

| piece | bars | print | reference | released output | verdict | evidence |
|---|---|---|---|---|---|---|
| Hammerklavier | 246-249 | 8va over 246, only the first note of 247 (hook), run at staff pitch, 248-249 at staff pitch | sounding pitch (A#6, run at staff), no direction | 8va start 246, whole of 247 under it, stop late | (c) model, stop too late | `refs/H1_*` |
| Hammerklavier | 365-368 | 8va from 365 over the system break to the end of 368 | sounding pitch in 367-368, no direction | stop in 367 (one bar early) | (c) model | `refs/H2_*` |
| Hammerklavier | 402-406 | 8va over 403 and the first chord of 404 | no direction, pitches follow the print | start, never closed: 405-406 an octave high | (c) model | `refs/H3_*` |
| Hammerklavier | 182-183 | no bracket anywhere on p. 38 (whole page viewed) | LH at staff pitch | `up` (8vb) at 182, LH A#2 F#1 F#2 against A#3 F#2 F#3 | (c) model, invented 8vb | text only (crop failed, no figure) |
| Hammerklavier | 208, 210 | clef changes inside the bar, no bracket | | register error | (d) register, not a bracket case | text only |
| Wanderer | 114-118 | 8va over the chords of 115-116 and the first beat of 117 (hook) | sounding pitch 115-117, no start | open through 118 | (c) model | `refs/W1_*` |
| Wanderer | 438-444 (ref) | 8va from 440 over three systems to the hook in 444 | sounding pitch, stops 439/446 without start | stop in 441 | (c) model | `refs/W2_*` |
| Wanderer | 471-475 (ref) | two short 8va: bars 1-2 of the last system, and the chord of bar 4 | sounding pitch, orphan stops 472 and 474 | first bracket open through the figure bar | (c) model | `refs/W3_*` |
| Wanderer | 418-419 | bracket ends inside bar 418 (hook), bar 419 at staff pitch | sounding in the bracket, staff pitch after | +12 from 418 (second half) | (c) model (page viewed, no figure) | text |
| Wanderer | 423-424 (ref) | tremolo written as measured 16ths | tremolo as repeated notes, bar alignment slips by one here | | **undecided**, reference left | |
| Liszt HR 6 | 36-41 | 8va from bar 3 of a system over two systems to the hook in the fermata bar, and the last chord of the page | has both brackets (start and stop), sounding pitch | no bracket read | (c) model, missed | `refs/HR1_*` |
| Liszt HR 6 | ref 66-73, output 70-81 | page 3 has two ossia systems (an 8va over the second ossia) and an 8va on the last chord; the output counts 19 bars more than the reference | brackets 66-69 and 73 | 8va 70-81 | **undecided**, reference left (ossia, bar alignment) | |
| Debussy Pour le piano | 44-52 | glissando 8va ends in a hook over the first note of 51 (printed E6) | E7 sounding at 51, stops 50/51 without start | bar 51 misread | (c) model | `refs/D1_*` |
| Debussy | 141-142 | not viewed | complete start 141, stop 144, sounding pitch | start at 143 | model late start, presumed (not viewed) | |
| Kreisleriana | 1-3 | no 8vb | no direction | `up` over the LH (A0 A1 against A1 A2) | (c) model, invented 8vb | `refs/K1_*` |
| Scriabin | 299-304 | no bracket | none | `up` (8vb) over the RH chords | (c) model, invented | `refs/S1_*` |
| Scriabin | 305-314 | 8va ends at the barline before 308, again before 312 | pitch follows the print | stops one or more bars late | (c) model | `refs/S2_*` |
| Scriabin | 322-333 | 322-324 no bracket; 8va 325-328 (hook after the first bar of the next page) | start 325, stop 328 | 322-325 invented, 328 stop lost, bracket to 333 | (c) model | `refs/S3_*` |
| Scriabin | 1-4 (LH), 279-280, 350-351, 430-432 | not viewed | reference has the brackets (8vb 1-7; 278; 349; 421-432) | brackets late or missing | model presumed, **not viewed** | |
| Stravinsky Petrushka | all | not examined | 3 reference staves against 2 in the output, 627 against 598 bars, one orphan stop (372) and one unclosed 8vb (522); the staff-1 comparison is meaningless | | **not decided** (provisional piece) | |

Counting the eye-verified rows: 12 decisions with figures, 3 more by page view. No case (a) and no case (b).

## Orphan stops

Reference stops without start: Wanderer 14, HR 6 15, Debussy 4 (the inventory's 3 for Petrushka is 1 with the stricter pairing used here, plus one unclosed start). Checked on the print: Wanderer 94 (8va from 86), 472 and 474 (both seen), the stops at 439 and 446 (bracket seen, start 440), Debussy 50/51 (hook seen); HR 6 stops are inside the ossia pages and were not checked individually. In every checked case the reference pitch under the lost start is the sounding one, so the loss is pitch-neutral. Restoring the starts would only change the Verovio render; not done (no edition copy is written for a pitch-neutral direction loss). A future model that reads these brackets correctly is **not** penalised by the pitch scores.

Limits: only bars where the output and the reference disagree by an octave are flagged. A bracket that neither the output nor the reference carries in pitch would not show up. That is the Schubert pattern; none was found in the flagged and viewed bars, but a bracket missed by both cannot be excluded without a full print pass (not done). Brackets of the three Schott scans and the other 14 pieces with references that have shifts were not examined.

## Rescoring (task 2)

Edition-corrected pieces: only Schubert D. 899/4 (unchanged). The scripts now share the list (`eval_run1/edition_refs.py`, imported by `res_final_table.py`, `after_merger_tables_octave.py`, `brace_eval.py`, `merge_tracking_eval.py`, `pitch_audit_brace.py`, `brace_audit_summary.py`, `pilot_final_table.py` via `F.EDITION`). `octave_checks/rescore_edition.py` rescored every saved tag of every listed piece: Schubert, **23 tags**: 566, ctl_slots, ctl_slots_nodrop, layout1, pilot_CTRL_RENDER_s7_gpu, r3B7, r3cand_s11, r3cand_s7, r3ctrl_s11, r3ctrl_s7, rb2_slots, rb2_slots_nodrop, rb3_slots, rb3_slots_nodrop, relbrace2_gpu, relbrace3_gpu, res_A_s11_gpu, res_A_s7, res_A_s7_gpu, res_B_s11_gpu, res_B_s7_gpu, run2s7, shipped_merge_role_gpu (13 were done before; new: pilot_CTRL_RENDER_s7_gpu, the slot and brace tags). Staff-sensitive and pooled, same scorer. Later tags (pilot_SCAN_s7_gpu etc.): run `python octave_checks/rescore_edition.py` again. The table `edition_scores/EDITION_RESCORE.md` has before and after for all 23 tags; the Schubert rows for the five arms below.

New tables (old ones kept): `out/testset/RES-FINAL-table-2026-11-17-edition2.md`, `POOLED-table-2026-11-17-after-merger-octave-edition2.md`, `CORRECTED-table-2026-11-17-after-merger-octave-edition2.md`. Their numbers are identical to the `-edition` tables (diff checked), so the 28-piece means are the same as before this report; the "before" below is the original Schubert reference (the D32 correction).

| run | Schubert pooled | 28-piece pooled pitch mean | at 97+ pooled | at 97+ staff-sens | worst piece (pooled) |
|---|---|---|---|---|---|
| released | 96.7 -> 99.2 | 91.90 -> 91.99 | 5 -> 6 | 4 -> 5 | liszt-te-5 77.8 |
| res_A_s7 | 96.7 -> 99.2 | 91.70 -> 91.79 | 5 -> 6 | 4 -> 5 | liszt-te-5 78.7 |
| res_A_s11 | 96.5 -> 99.0 | 91.83 -> 91.92 | 7 -> 8 | 5 -> 6 | liszt-te-10 77.8 |
| res_B_s7 | 96.1 -> 98.6 | 91.83 -> 91.92 | 6 -> 7 | 4 -> 5 | Petrushka 78.0 (liszt-te-5 78.2 without it) |
| res_B_s11 | 96.1 -> 98.6 | 91.87 -> 91.96 | 7 -> 8 | 5 -> 6 | Petrushka 77.8 (liszt-te-5 79.4) |

The per-piece before/after of the six suspect pieces is "no change" by construction (same reference).

## What this means for training and evaluation

* The octave loss on these pieces is model loss and counts as such (D32's (e) share for Hammerklavier and Wanderer was overestimated; the model errors there are stop errors, as on the dev crops). Nothing to fix in the evaluation references.
* The failures seen on the print are the ones D32 measured: stops too late or never (H1, H3, W1, W3, S2, S3), a stop one bar too early (H2, W2), brackets not read (HR1), invented 8vb/8va (K1, S1, S3, Hammerklavier 182).
* Open: the ossia pages of Liszt HR 6 (extra bars and brackets), Wanderer 423-424 (tremolo), Petrushka (staves), and the not-viewed Scriabin and Debussy bars.
