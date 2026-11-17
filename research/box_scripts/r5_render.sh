#!/bin/bash
# Round five, step 1: a further 15% of the scores with round three's bracket settings,
# rendered with octave brackets set tight on the notes in 35% of the files.
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. LILY_WORKERS=15
L=/workspace/logs/r5
SRC="datasets/Lieder-main/rendered_scores datasets/pdmx/rendered_scores datasets/musetrainer/rendered_scores"
echo "$(date -u +%FT%TZ) augment" >> $L/status.log
rm -rf /workspace/aug_xml5
AUG_SUFFIX=oct5 AUG_SHARE=0.15 python training/omr_datasets/augment_octave_shifts.py /workspace/aug_xml5 $SRC > $L/augment.out 2> $L/augment.err
echo "$(date -u +%FT%TZ) pass E" >> $L/status.log
LILY_TIGHT_OTTAVA=0.35 python training/omr_datasets/convert_lilypond.py --all /workspace/aug_xml5 > $L/lilyE.out 2> $L/lilyE.err
echo "$(date -u +%FT%TZ) RENDER_DONE" >> $L/status.log
