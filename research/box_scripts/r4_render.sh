#!/bin/bash
# Round four, step 1: more scores with inserted brackets, with more octave-lower and
# short ones (AUG_* settings), rendered with LilyPond and added to the staff index.
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. LILY_WORKERS=15
L=/workspace/logs/r4
until grep -q SETUP_DONE /workspace/logs/setup4.log; do sleep 20; done
SRC="datasets/Lieder-main/rendered_scores datasets/pdmx/rendered_scores datasets/musetrainer/rendered_scores"
echo "$(date -u +%FT%TZ) augment" >> $L/status.log
rm -rf /workspace/aug_xml4
AUG_SUFFIX=oct4 AUG_SHARE=0.3 AUG_P_8VB=0.45 AUG_P_SINGLE=0.35 AUG_RUNS=0,2,3,5,6 \
  python training/omr_datasets/augment_octave_shifts.py /workspace/aug_xml4 $SRC > $L/augment.out 2> $L/augment.err
echo "$(date -u +%FT%TZ) pass D" >> $L/status.log
python training/omr_datasets/convert_lilypond.py --all /workspace/aug_xml4 > $L/lilyD.out 2> $L/lilyD.err
echo "$(date -u +%FT%TZ) RENDER_DONE" >> $L/status.log
