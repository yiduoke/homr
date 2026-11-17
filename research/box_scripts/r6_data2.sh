#!/bin/bash
# Rerun PDMX and Lieder with the MuseScore settings this box needs.
L=/workspace/logs/r6
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
source /venv/main/bin/activate; cd /workspace/homr566
export PYTHONPATH=. APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen
for ds in pdmx lieder; do
  say "convert $ds (with MuseScore settings)"
  xvfb-run -a python -c "from training.omr_datasets.convert_$ds import convert_$ds; convert_$ds()" > $L/${ds}2.out 2> $L/${ds}2.err
  n=$(wc -l < datasets/$( [ $ds = lieder ] && echo Lieder-main || echo pdmx )/index.txt 2>/dev/null)
  if [ "${n:-0}" -gt 1000 ]; then say "done $ds ($n staffs)"; else say "FAILED $ds (index has ${n:-0} lines)"; fi
done
say "ALL DONE 2"
