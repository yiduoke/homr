#!/bin/bash
# Rerun of r6_hard.sh after the disk filled with MuseScore logs; deletes those logs every 5 minutes.
L=/workspace/logs/r6
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
( while true; do find /root/.local/share/MuseScore/MuseScore4/logs -type f -mmin +5 -delete 2>/dev/null; sleep 300; done ) &
CLEANER=$!
source /venv/main/bin/activate; cd /workspace/homr566
export PYTHONPATH=. APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen MUSESCORE_WORKERS=12 HOMR_CONVERT_WORKERS=14
export PDMX_MIN_COMPLEXITY=2 PDMX_MAX_COMPLEXITY=3 PDMX_TARGET_FILES=100000 PDMX_SUBSET=hard PDMX_EXCLUDE=training/omr_datasets/pdmx_exclude_test_pieces.txt
say "convert pdmx hard, retry (disk was full of MuseScore logs)"
xvfb-run -a python -c "from training.omr_datasets.convert_pdmx import convert_pdmx; convert_pdmx()" > $L/pdmx_hard2.out 2> $L/pdmx_hard2.err
n=$(wc -l < datasets/pdmx/hard/index.txt 2>/dev/null)
if [ "${n:-0}" -gt 1000 ]; then say "done pdmx hard ($n staffs)"; else say "FAILED pdmx hard retry (index has ${n:-0} lines)"; fi
kill $CLEANER
say "ALL DONE HARD2"
