# Run B scan pairs: real scanned systems from the KernScores source editions (2026-11-17, vast-homr4)

Lists on the box in `/workspace/run4/scans/` (283 MB incl. crops): `scan_train.txt` 3,480 lines, `scan_val.txt` 230 (whole pieces,
seed 20261118), `scan_quarantine.txt` 341 (line = image,tokens,reasons), `scan_{train,val}_strong.txt` (the same without
the 88 pairs verified only "medium"), `pairs.jsonl` (every pair with all check results), `pieces.json`, `manifest.json`.
Sources: Mozart sonatas, Beethoven sonatas, Chopin mazurkas (the scan PDFs of the repos, `reference-edition/`). Haydn and Scarlatti
are left out (their `.krn` line breaks are `g=z`, not the scanned edition), Joplin (scans not cut: 52 PDFs / 47 files, not matched),
Scriabin (no line breaks) and 40 of 52 mazurkas (no `!!LO:LB` markers) are left out too.

Order: `kern_systems.py` (.krn -> systems -> tokens, per repo) ; `cut_pages.py` (homr detection + inference crop, 3 shards) ;
`model_check.py` (released model on the CPU, 3 shards) ; `build_pairs.py` (checks, lists) ; `stats.py` (manifest) ;
`image_stats.py` (scan vs rendered crops) ; `eye_montage.py` (by-eye montages).
Environment: tokens with `PYTHONPATH=/workspace/homr_acc`; crops with `PYTHONPATH=/workspace/homr566` (only tree with the segnet
weights; detection and cropping code identical to homr_acc, checked by diff); model check with `/workspace/export_acc_run2s7`
(released model run2s7). CPU only, 2 threads per process, `nice -n 19`, at most 3 processes.

Label rules (kern_systems.py): the `!!LO:LB:g=original` marker comes before the barline that closes the previous system, so
system i = lines after marker i without its leading barline + the leading barline of marker i+1; only `**kern` spines (dynamics
dropped); invisible notes/rests (`yy`) dropped; rest pitch letters (`4rGG`) dropped; barline numbers stripped; clef and key are
put in front of every system, the meter only on the first system of a movement (or where the .krn changes it: that is what is
printed); printed accidental = Verovio MEI @accid (as in relabel_run2); `repeat_start` at a system start, `*8va` and similar,
cross-staff `*staff` changes, vocabulary/length/ledger filters of the trainer -> quarantine.
Verification: see `build_pairs.py` docstring (bar count of the crop, released-model reading, piece-level alignment check).
