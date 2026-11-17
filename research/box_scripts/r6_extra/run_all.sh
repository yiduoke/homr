#!/bin/bash
L=/workspace/logs/r6
say() { echo "$(date -u +%FT%TZ) $*" >> $L/extra_status.log; }
( while true; do find /root/.local/share/MuseScore/MuseScore4/logs -type f -mmin +3 -delete 2>/dev/null; sleep 120; done ) &
CLEANER=$!
source /venv/main/bin/activate; cd /workspace/homr566
export PYTHONPATH=. APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen MUSESCORE_WORKERS=10 HOMR_CONVERT_WORKERS=10
say "prep kern"; python /workspace/r6_extra/prep_kern.py /workspace/r6_extra/kern_mxl 0 > $L/extra_prep_kern.out 2>&1
say "prep asap"; python /workspace/r6_extra/prep_asap.py /workspace/r6_extra/asap_mxl 0 > $L/extra_prep_asap.out 2>&1
for n in kern_scriabin:kern_mxl asap:asap_mxl; do
  d=${n%%:*}; s=${n##*:}
  say "render $d"; xvfb-run -a python /workspace/r6_extra/render.py $d /workspace/r6_extra/$s > $L/extra_$d.out 2> $L/extra_$d.err
  say "done $d: $(wc -l < datasets/$d/index.txt) staffs"
done
kill $CLEANER; say "ALL DONE EXTRA"
