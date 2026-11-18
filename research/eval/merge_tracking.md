# Part tracking across pages in the merger: one fixed list of staff slots (D31)

Run 2026-11-17, 9:35 pm to 11:15 pm Pacific, laptop only: saved page XML re-merged, no transcription, no GPU, `vast-homr4` untouched, `vast-homr5` not used, nothing pushed, no default changed, nothing adopted.
Code: `run/merge2_wt` (new branch `merge-staff-slots` from `merge-by-staff-role`), files `merge_pages.py` (sha256 16 `f1e4a7260a1e846b`), `slot_tracking.py` (`65ff6dcde8ffb813`), tests `tests/test_slot_tracking.py`. Scripts in `eval_run1/`: `merge_tracking_diagnose.py`, `merge_tracking_eval.py`, `merge_tracking_table.py`, `merge_tracking_regress.py`. Tables and logs in `eval_run1/merge_tracking/`.

**Test-data rule.** Petrushka, the three Schott scans and Scriabin are test scans. They were used for diagnosis and for one scoring pass of the finished rule. Nothing was tuned on their scores: the rule and its three constants (octave for another clef, one semitone per place a staff moves in the stack, eight notes before a staff's own median counts) were fixed from what a musician does when following a part, and corrected only where the identity regression on the other saved page sets showed a structural fault (section 3, "How the rule got its final form"). The scores of the finished rule were then read once.

## 1. Result in short

* **Cause confirmed, and it is in the merger plus one transcription-side effect.** The D24 merger names the parts of a page by staff role only if the page is one uniform stack (`P1-Staff1..k` or k parts `Voice`). A Petrushka page is `[grand, single]` (control) or `[single, grand]` (retrained models), so it is "matched by id", and the ids of the two layouts share nothing with the two-staff pages: control 5 keys (`P1-Staff1/2` 598 bars, `Voice` 463, `P2-Staff1/2` 69, dropped), rb2 5 parts (475/390/390/286/286), rb3 5 keys (516/499/499 kept, `P1-Staff1/2` 142 bars dropped). The page XML itself is complete in all three runs.
* **Rule.** One list of staff slots per piece, ordered from the top. A page with as many staves as established slots continues them by position; otherwise its staves are matched to the slots in vertical order, never crossing, by register and clef; a page with surplus staves opens new slots in place; a slot a page lacks gets rests for the page's bars; a slot which fewer than half of the pages gave a staff is an extra staff and is not a match target for ordinary pages. How homr paired the staves into parts no longer matters (music21 already flattens a grand part into `P1-Staff1/2`).
* **Petrushka, same page XML, no transcription** (reference 627 bars, 3 staves; pooled / staff-sensitive pitch F1; D24 merger -> slot tracker): control 79.2 / 58.6, 598x2 -> **84.1 / 71.8, 647x3**; realbrace-2 44.8* / 44.8*, five parts 475/390/390/286/286 -> **80.7 / 63.1, 676x3**; realbrace-3 58.8* / 58.8*, 516/499/499 -> **82.2 / 61.9, 661x3** (`*` = per-staff numbers, no joint bar list).
* **28 scans, mean pooled pitch** (D24 -> slot tracker): control 91.94 -> 92.20, rb2 91.46 -> 92.83, rb3 91.92 -> 92.85. Staff-sensitive 90.21 -> 90.66, 90.53 -> 91.15, 90.99 -> 91.07; pooled +onset 76.77 -> 76.96, 76.95 -> 78.02, 77.32 -> 78.01; pooled full 74.72 -> 74.92, 75.08 -> 76.10, 75.43 -> 76.10. Bars equal to the reference: 14 -> 15 (control), 15 -> 16 (rb2), 14 -> 15 (rb3).
* **Only two of the 28 scans change** (identical page sets elsewhere): Petrushka (above) and Scriabin Sonata 5 (+2.47 pooled for all three runs, 432 -> 456 bars = reference; **staff-sensitive -0.7, hands in the same bar 97 -> 95 %**, see section 5). The three Schott scans are byte-for-byte the D28 results.
* **Regression on all saved page sets** (every tag, 425 sets): 392 of 425 give the same final MusicXML as the D24 merger (parts, bars, notes, ids normalised; both before and after `drop_minor_parts.py`); the 33 that differ are Petrushka (13 sets), Scriabin (13) and `liszt-te-4-schott` (7 sets of the D30 pairing arms, not one of the 28).
* **Adoption of the retrained pairing models: not yet** (section 6). On the same slot merger, Petrushka is the one piece where realbrace-2 / -3 are below the shipped control (pooled -3.5 / -2.0, bars 676 / 661 against 647, reference 627); every other piece equals or beats the control, but one Schott scan (Etude 5) is one bar short with rb3 as in D28. What is left on Petrushka is not part tracking: pages where the staff detection hides a staff in some systems, and pages which the transcriber reads as one long voice.

## 2. Diagnosis (task 1)

Source: the saved page XML of the three D28 runs (`testset/{shipped_merge_role_gpu,relbrace2_gpu,relbrace3_gpu}/stravinsky-petrushka/page-xml`, 37 pages each), the pairing replay of D28 (`brace_models/replay_all.json`: staves per system, the replay is an approximation of the runs, for example control page 2 has four staves in the XML but three per system in the replay) and `homr.log`. Full per-page table, all 37 pages and 3 runs: `merge_tracking/diagnose_stravinsky-petrushka.md` (`merge_tracking_diagnose.py`).

**Staves per system.** The staff detection gives systems of 2, 3 and 4 staves on the same pages for all three models (the pairing models only change what is joined): largest system 3 staves on 30 pages, 2 on 5, 4 on 2, and **21 of 37 pages mix system sizes** (for example `[2,2,2,2,3]` on page 9, `[3,4,4]` on page 32, `[4,2,1,2,2]` on page 33). The writer makes one part per "voice" (the n-th multi-staff of every system); a staff which a smaller system lacks is filled with measure rests (`Staffs are hidden in some systems`, 18 / 17 / 19 pages for control / rb2 / rb3) and **which staff of the page is hidden depends on the pairing**: the control (`G+s`) puts the staves of a two-staff system in staves 1-2 of the page and hides the bottom one, the retrained models (`s+G`) put them in staves 2-3 and hide the top one. If the layouts cannot be assigned uniquely the transcriber reads every staff on its own, one long voice (`The layout changes on the page`, 3 / 4 / 2 pages; rb2 page 32: 11 staves become two staves of 41 bars, page 23: 21 bars instead of 12).

**Which staves form a part, the ids music21 gives, and where the D24 merger puts them** (8 pages; `m` = median pitch, `bars/notes` of the page XML staff; slot = the slot tracker's slot of each staff, `K` = slots so far):

| page | run | staves per system | page XML staves (part id, clef, bars/notes, m) | D24 part of each staff | slot of each staff (K) |
|---|---|---|---|---|---|
| 1 | ctl | 3,3,3,3 | P1-S1 G 17/339 m81; P1-S2 G 17/194 m64; Voice F 17/122 m57 (grand + single) | P1-S1, P1-S2, Voice | 0,1,2 (3) |
| 1 | rb2, rb3 | 3,3,3,3 | Voice G 17/341 m78; P2-S1 G 17/150 m65; P2-S2 F 17/118 m55 (single + grand) | Voice, P2-S1, P2-S2: **no part shared with the control's page** | 0,1,2 (3) |
| 2 | ctl | 3,3,3,3 | P1-S1 G; P1-S2 G; P2-S1 F; P2-S2 F (two grand parts, four staves) | P1-S1, P1-S2, P2-S1, P2-S2 | 0,1,2,3 (4) |
| 2 | rb2, rb3 | 3,3,3,3 | Voice G 17/257; P2-S1 G 17/93; P2-S2 F 17/149 | Voice, P2-S1, P2-S2 | 0,1,2 (3) |
| 7 | all | 3,3,3,3,3 | Voice G m88; P2-S1 G m65; P2-S2 F m53 | Voice, P2-S1, P2-S2 | 0,1,2 |
| 8 | all | 2,2,2,2,2 | P1-S1 G 27/152 m73; P1-S2 F 27/133 m66 (one grand part, a two-staff page) | **uniform stack: P1-S1, P1-S2** (the roles of the first k=2 page) | ctl 1,2 / rb 0,1 |
| 9 | ctl | 2,2,2,2,3 | P1-S1 G 13/89 m79; P1-S2 G 13/61 m78; Voice G 13/30 m60 | P1-S1, P1-S2, Voice | 0,1,2 (4) |
| 9 | rb2, rb3 | 2,2,2,2,3 | Voice G 13/24 m72; P2-S1 G 13/69 m83; P2-S2 G 13/85 m73 | Voice, P2-S1, P2-S2 | 0,1,2 (3) |
| 11 | ctl | 3,3,3,3 | P1-S1 G; P1-S2 G; P2-S1 G; P2-S2 F (four staves) | P1-S1, P1-S2, P2-S1, P2-S2 | 0,1,2,3 (4) |
| 11 | rb2, rb3 | 3,3,3,3 | Voice G; P2-S1 G; P2-S2 F (three staves) | Voice, P2-S1, P2-S2 | 0,1,2 (3) |
| 23 | rb2 | 3,3,3,2 | P1-S1 G 21/373; P1-S2 F 21/92 (collapsed page: 21 bars instead of 12) | P1-S1, P1-S2 (as page 8) | 0,2 (3) |
| 32 | rb2, rb3 | 3,4,4 | P1-S1 G 41/253; P1-S2 F 41/31 (collapsed: 41 bars instead of 16) | P1-S1, P1-S2 | rb2 1,2 / rb3 1,2 |
| 33 | all | 4,2,1,2,2 | P1-S1 G; P1-S2 G (grand pair on every system) | P1-S1, P1-S2 | 0,1 |

What the merged score looks like under D24 (`key: staves, bars`): control `P1-Staff1` 35 staves 598 bars, `P1-Staff2` 598, `Voice` 27 staves 463, `P2-Staff1/2` 4 staves 69 (dropped, below 50 %), the pages of layout `[single, grand]` (pages 7, 32 and others) are not in the two main parts at all, which is why the control has 598 bars; rb2 `Voice` 27 staves 475 bars, `P2-Staff1/2` 24 staves 390, `P1-Staff1/2` 14 staves 286: five parts that append the same pages at the same offset; rb3 `Voice` 516, `P2-Staff1/2` 499, `P1-Staff1/2` 142 (dropped).

## 3. The rule (task 2)

`slot_tracking.py` (no music21, testable alone) and `merge_pages.py`:

1. A page is its list of staves, top to bottom (`score.parts` of music21; a grand part is already `P1-Staff1`, `P1-Staff2`).
2. The piece has an ordered list of **slots**. A staff's profile is its first clef and the median pitch of its notes on the page (clef default 72 / 48 / 60 if it has fewer than 8 notes); a slot's profile is the pooled median of the staves it has had and the majority clef.
3. **Established slots** are those which at least half of the pages so far gave a staff. A page with no more staves than there are established slots is matched to those only; a page with more staves can use every slot.
4. **Equal count:** n-th staff to n-th slot. **Fewer staves than slots:** order-preserving match to the slots, minimum summed distance (|register difference| + 12 semitones for another clef + 1 semitone per place the staff moves in the stack); the other slots stay empty on the page. **More staves than slots:** every slot is matched, the surplus staves open new slots at their place in the stack (among the slots the page leaves out, by register). Ties go to the upper staves.
5. Every slot keeps one bar per bar of the piece: a slot a page does not fill gets rests for the page's bars (the page's longest staff gives the bar lengths and meter changes), a slot opened late gets rests for the bars before it, the shorter staves of a page are padded to its longest staff (as D24 did for same-named parts).
6. The merger's own minor-part rule (a part with real staves on fewer than half of the bars is an ossia or small extra staff) counts real bars, not the rest fill; `drop_minor_parts.py` is unchanged.
7. Part order in the output is the slot order, from the top; part ids are those of the first staff which opened the slot (as before).

No piece is named anywhere; no rule depends on the number of staves of a piece.

**How the rule got its final form** (all on saved page sets, no score read for the choice; the identity regression is the check of section 5):
* v1: free new slots at a fixed cost, free skips. The regression on the old-model sets (tag 566) changed Balakirev Islamey (a page with two grand pairs): the lower pair took the main slots on a near tie. Fixed: forced matching (a page opens a slot only if it has more staves than slots), a position term for near ties, and the majority clef for a slot (Islamey page 2 had a misread first clef).
* v2: on `liszt-te-4-schott` (D30 arms with spurious three- and four-staff pages) the extra slots split the left hand over two slots on the ordinary pages. Fixed: the **established-slot** rule (3 above).
* v3: position term from 3 to 1 semitone and ties to the upper staves (a three-staff page of a two-staff piece put its middle staff in the bass slot).
* A write failure (`Cannot convert "2048th" duration`) on one set: a real page bar which D24 had left in a dropped part now reaches a main part and music21 cannot write it; after five failed repair attempts the bar is replaced by rests (logged `blanked measure N`) instead of losing the whole file. The rests I add are built with exact fractions.
* **Candidate against the evidence, plain top alignment** (the D24 rule extended to every page: staff n to slot n, surplus staves open slots at the bottom; same fill, same padding; ablation copy in the scratchpad, tags `*_top`): Petrushka pooled / staff-sensitive control 79.8 / 59.4 with `drop_minor_parts.py`, 84.5 / 74.4 without (the sparse third slot is dropped), rb2 80.7 / 64.7, rb3 82.2 / 62.6; Scriabin control 92.2 / 90.7 (slot tracker 91.6 / 88.4, D24 89.1 / 89.1). **On these two test pieces plain top alignment is equal in pooled pitch and 1.5 to 2.3 staff-sensitive points better than the register rule.** The register rule was not changed in response (test data must not choose the rule); it is what the task asked to evaluate, and it handles a small extra staff above the piano staves (a unit test, the Mazeppa / Rachmaninoff page 5 case of the merger comments), but the owner may prefer the simpler rule. Pooled pitch does not depend on which slot a staff gets; the large gains below come from the fixed slots and the rest fill, not from the register matching.

## 4. Implementation and tests (task 3)

`run/merge2_wt`, branch `merge-staff-slots`. `tests/test_slot_tracking.py`, 18 tests, 2 s (`.venv/bin/python -m pytest run/merge2_wt/tests`): tracker alone (same stack keeps roles; a three-staff page after two-staff pages adds a middle slot; four-staff pages add a slot and lower pages keep theirs; a first page with more staves than later ones; a page never opens a slot unless it has more staves; a staff without notes follows its clef; the ambiguous surplus pair keeps the top pair; a small staff above a piano page opens its own slot; a few pages with extra staves do not split the piece; an established slot is used again) and `merge_pages.py` on synthetic page sets written like homr writes them (regular two-staff piece unchanged; 2-, 3- and 4-staff pages give four fixed parts with every note in the slot of its register; **the same three staves written as grand + single on one page and single + grand on the next land in the same three slots, not five** (the half-paired pages); Voice pages and grand pages continue each other; a page with a lost bar is padded; a late slot gets rests; the minor-part rule counts staves, not fill). `MERGER=run/merge_wt/merge_pages.py` runs the same page sets through the D24 merger: it fails the 2/3/4-staff, half-paired, late-slot and padding tests (four tests), as expected.

## 5. Results

All numbers: the saved page XML of the D28 runs, re-merged with the slot tracker, `drop_minor_parts.py`, the D28 scorer (`rel_wt` `validation/score_notes.py --ignore-staff`, edition-corrected references) and `hand_sync.py`. `d24` = D28 numbers, `slots` = new. Full tables for 28 pieces and all metrics: `merge_tracking/table.md`.

### Petrushka (reference 627 bars, one part with three staves, unchecked)

| run | merger | pooled pitch | staff-sensitive | pooled +onset | pooled full | parts x bars |
|---|---|---|---|---|---|---|
| control | D24 | 79.21 | 58.56 | 59.1 | 54.2 | 2 x 598 |
| control | slots | **84.13** | **71.77** | 61.8 | 57.1 | 3 x 647 |
| realbrace-2 | D24 | 44.83* | 44.83* | 32.2* | 29.5* | 475/390/390/286/286 |
| realbrace-2 | slots | **80.68** | **63.11** | 59.4 | 55.3 | 3 x 676 |
| realbrace-3 | D24 | 58.85* | 58.85* | 43.7* | 40.2* | 516/499/499 |
| realbrace-3 | slots | **82.16** | **61.92** | 60.3 | 56.1 | 3 x 661 |

`*` per-staff numbers (parts of different lengths, no joint bar list). With and without `drop_minor_parts.py` the slot results are equal (the merger's own rule drops the fourth slot, 46 / 16 real bars; rb3 has only three). Pooled notes in the page XMLs 15,342 / 15,238 / 15,158 against 15,483 in the reference; the merged output holds 17,735 / 18,051 / 17,900 note elements, rests included (D24: 13,936 / 18,551 / 14,577), so the three-staff content is no longer dropped.

**How the scorer aligns the three reference staves.** The reference is one part with three staves in all 627 bars. A prediction with the same number of staves (three slots) is compared staff to staff in one joint bar alignment (staff 1 of the output to staff 1 of the reference, and so on). A prediction with another number of staves (D24 control: two parts) is remapped bar by bar, each predicted staff to the reference staff with the closest mean pitch (`remap_staves`); parts of different lengths (D24 rb2, rb3) are aligned staff by staff and each staff is mapped as a whole to the reference staff of closest mean pitch, which is why their pooled column is not defined. **The staff-sensitive and pooled numbers of Petrushka are provisional:** the reference is not verified against the print (the number of staves per system in the print is 2, 3 or 4), and the pooled score does not depend on the slot but does depend on the bar alignment (676 and 661 output bars against 627 are partly the collapsed pages of section 2). Per reference staff (slots, pitch F1): control 81.7 / 71.3 / 48.4, rb2 66.4 / 58.5 / 62.6, rb3 64.6 / 53.8 / 66.3: the retrained models' top reference staff is weak because the two-staff systems of a mixed page lie in staves 2-3 of the page, not 1-2.

### The 28 scans (mean over 28; Petrushka included)

| metric | control D24 | control slots | rb2 D24 | rb2 slots | rb3 D24 | rb3 slots |
|---|---|---|---|---|---|---|
| pooled pitch | 91.94 | 92.20 | 91.46 | 92.83 | 91.92 | 92.85 |
| staff-sensitive pitch | 90.21 | 90.66 | 90.53 | 91.15 | 90.99 | 91.07 |
| pooled +onset | 76.77 | 76.96 | 76.95 | 78.02 | 77.32 | 78.01 |
| pooled full | 74.72 | 74.92 | 75.08 | 76.10 | 75.43 | 76.10 |
| bars equal to the reference (of 28) | 14 | 15 | 15 | 16 | 14 | 15 |
| hands in the same bar, mean of the 27 two-staff pieces | 95.86 | 95.80 | 98.05 | 97.98 | 98.14 | 98.08 |

Without Petrushka (27 pieces): pooled 92.41 -> 92.50 (control), 93.19 -> 93.28 (rb2), 93.15 -> 93.24 (rb3), all from Scriabin.

* **Three Schott scans:** identical to D28 in every column (the pages there are uniform stacks; the page sets are identical in the regression). Pooled pitch control / rb2 / rb3: Sonata 80.5 / 86.9 / 88.2, Etude 5 78.0 / 79.5 / 79.5, Etude 10 77.9 / 91.2 / 88.6; bars 307 / 306 / 304, 134 / 134 / 133, 181 / 182 / 182 (reference 305, 134, 182); hands in the same bar 79 / 93 / 96 %, 71 / 88 / 92 %, 67 / 95 / 91 %.
* **Scriabin Sonata 5, all three runs:** page 18 has a small extra staff above the piano staves (`Voice`, then `P2-Staff1/2`); D24 matched it by id and left the page's 24 bars out of the main parts (432 bars, reference 456). The slot tracker puts the two piano staves in the two slots and the extra staff in a slot of its own (dropped as minor): 456 bars, pooled 89.1 -> 91.6 (+2.47), pooled +onset 73.2 -> 75.9, full 70.6 -> 73.3. **Regression: staff-sensitive 89.1 -> 88.4 (-0.7) and hands in the same bar 97 -> 95 %**: the newly included page is read badly (200 of the 487 reference notes in its 20 aligned bars match), which lowers per-staff precision while pooled recall rises. D24 did not show this because it left the page out.
* No other scan changes in any metric (26 scans: same parts, bars, notes and scores in every column).

### Regression on all saved page sets (task 3)

`merge_tracking_regress.py`: every `eval_run1/testset/<tag>/<piece>/page-xml` (27 tags, 59 pieces, **425 sets**: the 28 scans and their rendered twins in the old-model tags, the D28 and D30 arms, the pilot and resolution tags), merged with `merge_wt` (D24) and `merge2_wt`, both through `drop_minor_parts.py`, part ids normalised: **392 identical (parts, bars, notes, text) before and after the drop, 33 different:**

* Petrushka, 13 sets (every tag with Petrushka and its rendered twin): D24 parts 598x2 (or 5 and 3 parts for rb2 and rb3) -> 3 x 646-686 bars; notes in the final file 13.9 k -> 17.7 k.
* Scriabin Sonata 5, 13 sets (every tag): 432 -> 456 bars, notes +630; the rendered twin had three parts (304, 304, 418 bars) and now has two (468, 468).
* `liszt-te-4-schott` (not one of the 28; relbrace2 A/B/C arms and control of D30, 7 sets): parts 224 / 209 bars -> 225 / 225, 190 -> 206 bars (the spurious three-staff pages of the weak arms no longer drop pages); notes 7.9 k -> 7.8 k (arm A), 7.5 k -> 7.8 k (B, C), control 8.3 k -> 8.0 k. Not scored here (no reference run in this session).

## 6. Can the retrained pairing models be adopted with the improved merger? (task 4)

Criteria (D28): no piece regresses by 0.5 pooled points or more against the shipped control **on the same merger**, bars and hands in the same bars not worse. On the slot merger:

| piece | rb2 vs control | rb3 vs control |
|---|---|---|
| 26 other scans | pooled equal, bars equal, hands equal (Schott: pooled +1.5 to +13.3, hands in the same bar +14 to +28 points) | same; **Etude 5 one bar short (133 of 134)**, pooled +1.5 |
| Petrushka | pooled **-3.5** (80.7 against 84.1), bars 676 against 647 (reference 627), staff-sensitive 63.1 against 71.8; hands not defined (three reference staves) | pooled **-2.0** (82.2), bars 661, staff-sensitive 61.9 |

**Answer: the criteria are not met on Petrushka, so no, not by the letter.** Everything the merger can do is done (D24: -34.4 / -20.4 pooled against the control; now -3.5 / -2.0); what is left on this piece is not part tracking:

1. **Hidden-staff placement on mixed pages** (21 of 37 pages): the transcriber puts the staves of a two-staff system in staves 2-3 of the page with the retrained pairing (`s+G`) and in staves 1-2 with the shipped one (`G+s`); neither is known to be the staff which the print leaves out. A slot tracker working per page cannot repair it; it needs the system structure (the page XML marks system starts with `<print new-system>`) or the transcriber's `_assign_parts` to place a hidden staff by register.
2. **Collapsed pages**: where `_assign_parts` finds the layouts ambiguous (3 / 4 / 2 pages control / rb2 / rb3) the page is one long voice (rb2 pages 23 and 32: 21 and 41 bars); the extra bars (676 and 661 against 627, control 647) shift the bar alignment.
3. The reference of Petrushka is unchecked and has three staves; the staff-sensitive column is provisional. Whether the collapsed pages explain the remaining pooled gap of rb2 / rb3 against the control (-3.5 / -2.0) was not tested.

Judgement for the owner: on the 27 other scans the slot merger makes the retrained models adoptable (no regression, three Schott scans +1.5 to +13), and the control itself is not worse anywhere except Scriabin's staff-sensitive column (-0.7, section 5). If Petrushka's remaining gap is accepted as a transcription-side problem of three-staff systems that the shipped model does not solve either (in the D24 output the control had dropped its third staff), adoption is a decision about that piece; the held-out edition test of D28 is still open and the Schott gains are not an unbiased estimate (the models were chosen after seeing those scans).

## 7. Open

* Hidden staves per system (item 1 above): a per-system treatment or a transcriber change. Nothing was tried.
* Collapsed pages (item 2): the transcriber side.
* The minor-part rule `drop_minor_parts.py` counts bars with notes, which drops a legitimately sparse slot (a third staff silent in half of the bars); the merger's own rule counts staves of pages. With the slot tracker the two give the same result on Petrushka; nothing changed there.
* Register matching against plain top alignment (section 3): a decision on principle, not settled by these test pieces.
* `liszt-te-4-schott` and the other D30 outputs were only re-merged, not scored.
* The Petrushka reference has to be checked against the print before its staff-sensitive column means anything.

## 8. Files and commands

* Code: `run/merge2_wt` (branch `merge-staff-slots`, commit `c304aa6`): `merge_pages.py`, `slot_tracking.py`, `tests/test_slot_tracking.py`. Copy in the research repository: `research/scripts/merge_slots/`.
* Diagnosis: `python eval_run1/merge_tracking_diagnose.py [piece]` -> `merge_tracking/diagnose_<piece>.md`.
* Re-merge and score a saved run: `python eval_run1/merge_tracking_eval.py --src shipped_merge_role_gpu --tag ctl_slots` (likewise `relbrace2_gpu` / `rb2_slots`, `relbrace3_gpu` / `rb3_slots`): writes `out/testset/<piece>/<piece>-<tag>.musicxml` (merger + `drop_minor_parts.py`) and `-<tag>_nodrop.musicxml` (merger only), `res-scores-<tag>.json`, `hand-sync-<tag>.json`; 84 merges, about 12 minutes on 4 workers.
* Tables: `python eval_run1/merge_tracking_table.py` -> `merge_tracking/table.md`, `results.json` (28 pieces, four metrics, bars, hands, regression criteria).
* Regression: `python eval_run1/merge_tracking_regress.py eval_run1/merge_tracking/regress 6` -> `regress/regress.tsv` (425 sets, about 55 minutes on 6 workers; the outputs of the 33 differing sets stay in `regress/<tag>/<piece>/`).
* Ablation (plain top alignment): `merge_tracking/ablation_top/` (copies of the merger and tracker from before the last two small fixes, with `align` replaced by staff n -> slot n and no established-slot rule), tags `ctl_top`, `rb2_top`, `rb3_top` (Petrushka) and `ctl_top` (Scriabin) in `out/testset/`.
* Scorer: `rel_wt/validation/score_notes.py --ignore-staff` (unchanged), references as in D28 (Schubert D. 899/4 against `-reference-edition.musicxml`). Hands: `eval_run1/hand_sync.py`, not meaningful for Petrushka (it looks at the first two of three reference staves).
