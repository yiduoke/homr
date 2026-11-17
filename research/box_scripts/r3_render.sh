#!/bin/bash
# Round three, step 1: all LilyPond staffs again (one render per page this time), plus
# scores with inserted brackets.
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. LILY_WORKERS=11
L=/workspace/logs/r3
[ -d datasets/lilypond ] && [ ! -d datasets/lilypond_round2 ] && mv datasets/lilypond datasets/lilypond_round2
SRC="datasets/Lieder-main/rendered_scores datasets/pdmx/rendered_scores datasets/musetrainer/rendered_scores"
echo "$(date -u +%T) pass A" >> $L/status.log
python training/omr_datasets/convert_lilypond.py --share 0.05 $SRC > $L/lilyA.out 2> $L/lilyA.err
echo "$(date -u +%T) pass B" >> $L/status.log
LILY_VARIANT=v2 python training/omr_datasets/convert_lilypond.py --share 0.05 $SRC > $L/lilyB.out 2> $L/lilyB.err
echo "$(date -u +%T) augment" >> $L/status.log
rm -rf /workspace/aug_xml
AUG_SHARE=0.3 python training/omr_datasets/augment_octave_shifts.py /workspace/aug_xml $SRC > $L/augment.out 2> $L/augment.err
echo "$(date -u +%T) pass C" >> $L/status.log
python training/omr_datasets/convert_lilypond.py --all /workspace/aug_xml > $L/lilyC.out 2> $L/lilyC.err
echo "$(date -u +%T) RENDER_DONE" >> $L/status.log
