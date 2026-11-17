#!/bin/bash
# After r6_data3.sh: the hardest PDMX piano scores (complexity 2-3), test pieces left out,
# in their own folder datasets/pdmx/hard.
L=/workspace/logs/r6
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
until grep -q "ALL DONE 3" $L/status.log; do sleep 120; done
source /venv/main/bin/activate; cd /workspace/homr566
export PYTHONPATH=. APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen MUSESCORE_WORKERS=12 HOMR_CONVERT_WORKERS=14
export PDMX_MIN_COMPLEXITY=2 PDMX_MAX_COMPLEXITY=3 PDMX_TARGET_FILES=100000 PDMX_SUBSET=hard PDMX_EXCLUDE=training/omr_datasets/pdmx_exclude_test_pieces.txt
say "convert pdmx hard (complexity 2-3)"
xvfb-run -a python -c "from training.omr_datasets.convert_pdmx import convert_pdmx; convert_pdmx()" > $L/pdmx_hard.out 2> $L/pdmx_hard.err
n=$(wc -l < datasets/pdmx/hard/index.txt 2>/dev/null)
if [ "${n:-0}" -gt 1000 ]; then say "done pdmx hard ($n staffs)"; else say "FAILED pdmx hard (index has ${n:-0} lines)"; fi
say "ALL DONE HARD"
