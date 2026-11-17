# Run 3 candidate lists (harder data), built 2026-11-16 on vast-homr4

Goal: control list (run 2 lists without the 29 new test pieces) plus harder data with run-2 labels
(lift = printed sign): hard PDMX, ASAP, Scriabin. Everything lives in `/workspace/run3/` on the box.
Originals of `run1/`, `run2/` and `datasets_meter/` are untouched. Numbers: `manifest.json`, `audit/`.

Order of the scripts (all run with `/venv/main/bin/python`; the ones that read tokens need
`PYTHONPATH=/workspace/homr_acc`, commit afae0e3):

1. `staff_stats3.py` - per staff: notes, chords, ledger notes, brackets, repeated notes, runs, meters.
2. `export_ms.py` - ASAP and Scriabin: their MuseScore exports had been deleted, so the MusicXML is
   exported again from `r6_extra/{asap_mxl,kern_mxl}` with the same MuseScore 4.6.5 and per-piece style
   into `run3/ms_export/<set>/`. Scriabin is therefore labeled like ASAP (MuseScore export), not with
   Verovio MEI `@accid`: its images are MuseScore renders of a music21 conversion of the kern.
3. `valid_staffs.py` - the training-time filters (vocabulary, sequence length, at most 5 ledger lines)
   applied before sampling (prebuilt lists are not filtered by the trainer); Scriabin Verovio crops of
   part >= 1 are left out (image shows 2-3 staves, label one).
4. `select_candidates.py` - hard PDMX: pool = staffs in no control list, sampled by score (weight
   density^2, meter quota 400 staffs per meter outside 4/4 3/4 2/4 6/8 common cut), held-out whole
   scores that occur in no control line (also not in the octave sets); ASAP and Scriabin: whole pieces held out.
5. `relabel_run3.py` - copy of `run/box_scripts/relabel_run2.py` (unchanged original) for the new sets,
   input `NEEDED=<list>`, output `run3/tokens/` with the run-2 path layout, status in `run3/status/`.
6. `verify_run3.py`, `make_view.py`, `view_flagged.py` - label checks (identical to run 1 apart from lift;
   sounding alteration recomputed from printed signs vs run-1 lift) and montages image + labels.
7. `image_stats3.py`, `analyze_img.py`, `analyze_crops.py`, `clef_changes.py` - crop audit (`audit/`).
8. `build_cand_lists.py`, `check_lists.py`, `finish_manifest.py` - lists, integrity check, manifest.

Lists: `cand_train.txt`, `cand_val.txt` (= control val + `cand_val_hard.txt`), `cand_val_hard.txt`, and
`cand_train_nooct.txt` (same without the added staffs that contain an octave bracket, because the control's
original sets have none; the octave exposure of the control comes from the octave sets only).
Seeds: selection 20261117, list shuffle 20261118, verification sample 11.
