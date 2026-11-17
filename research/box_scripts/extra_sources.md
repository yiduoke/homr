# Extra sources: kern_scriabin and asap

Output: datasets/kern_scriabin/{index.txt,flat/} and datasets/asap/{index.txt,flat/}. Same format as pdmx/hard (png + tokens in flat/, index lines relative to repo root).

## Counts
- kern_scriabin: 1847 staffs. 207 krn, 3 excluded, 203 converted to MusicXML (1 failed: op62, music21 export error), 149 pieces yielded staffs, 54 skipped (token vocab errors). 1505 token files contain beamStart.
- asap: 5832 staffs. 235 score files, 10 excluded, 14 repeat variants skipped, 211 converted, 62 yielded nothing. 5503 token files contain beamStart.
- Skip causes (converter errors, whole piece dropped): "long" duration (invisible filler rest in MuseScore export of music21 output; kern only), 256th/128th notes, odd durations (note_20., note_28., note_14.), tuplets the vocabulary cannot encode.
- Lists of dropped pieces: /workspace/logs/r6/extra_kern_failed.txt, extra_asap_failed.txt.

## Exclusions
Kern: scriabin-op8_no12 (Etude Op.8 No.12), op30_no01 and op30_no02 (Sonata 4 Op.30).
ASAP: Liszt Gran_Etudes_de_Paganini/2_La_campanella; Liszt Transcendental_Etudes/4 (Mazeppa); Liszt Mephisto_Waltz; Chopin Ballades/4; Chopin Scherzos/20; Bach Prelude/bwv_848 and Fugue/bwv_848; Mozart Piano_Sonatas/11-3 (K.331; only movement in ASAP); Beethoven Piano_Sonatas/8-1 (Op.13 mvt 1); Ravel Gaspard_de_la_Nuit/1_Ondine.
Not in ASAP: Liszt Hungarian Rhapsody 2 (ASAP has no.6, kept), Liebestraum, Totentanz, Mozart K.309, Rachmaninoff Op.3/2, Scriabin Op.8/12 and Op.30 (ASAP has Op.8/11 and Sonata 5, kept), Jeux d eau, L isle joyeuse, Mussorgsky, Stravinsky.
Dedup: ASAP score per folder (unique xml_score, 235) with *_repeat / *_no_repeat variants dropped when a base score exists.

## Method
Kern: music21 parse, two parts merged into one PartStaff pair with a brace StaffGroup (otherwise each hand is a separate part and images show a half-cropped second staff), written as .mxl. Then MuseScore render and the pdmx path (convert_lieder.create_musicxml_and_svg_files_from_mxl, convert_xml_and_svg_file, write_index). ASAP: xml_score.musicxml wrapped as .mxl, same path. Dry run checked clef, key, meter and first-bar notes against the originals for both.

## Commands
ssh vast-homr4; tmux session r6extra runs /workspace/r6_extra/run_all.sh, which does:
cd /workspace/homr566; source /venv/main/bin/activate; export PYTHONPATH=. APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen MUSESCORE_WORKERS=10 HOMR_CONVERT_WORKERS=10
python /workspace/r6_extra/prep_kern.py /workspace/r6_extra/kern_mxl 0
python /workspace/r6_extra/prep_asap.py /workspace/r6_extra/asap_mxl 0
xvfb-run -a python /workspace/r6_extra/render.py kern_scriabin /workspace/r6_extra/kern_mxl
xvfb-run -a python /workspace/r6_extra/render.py asap /workspace/r6_extra/asap_mxl
(plus a loop deleting MuseScore logs). Temporary rendered_scores were deleted afterwards.
