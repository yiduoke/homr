#!/bin/bash
# Rerun the Lieder conversion with MuseScore settings for this box if r6_data.sh failed it.
L=/workspace/logs/r6
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
until grep -q "done lieder\|FAILED lieder" $L/status.log 2>/dev/null; do sleep 60; done
grep -q "done lieder" $L/status.log && exit 0
source /venv/main/bin/activate; cd /workspace/homr566
export PYTHONPATH=. APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen
rm -f datasets/Lieder-main/index.txt
say "convert lieder (retry with xvfb)"
xvfb-run -a python -c "from training.omr_datasets.convert_lieder import convert_lieder; convert_lieder()" > $L/lieder2.out 2> $L/lieder2.err && say "done lieder retry ($(wc -l < datasets/Lieder-main/index.txt))" || say "FAILED lieder retry"
