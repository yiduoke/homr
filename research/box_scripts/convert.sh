#!/bin/bash
source /venv/main/bin/activate
cd /workspace/homr
export PYTHONPATH=/workspace/homr APPIMAGE_EXTRACT_AND_RUN=1 QT_QPA_PLATFORM=offscreen
for name in "$@"; do
  echo "START $name $(date -u +%FT%TZ)" >> /workspace/logs/status.log
  xvfb-run -a python training/omr_datasets/convert_$name.py > /workspace/logs/$name.log 2>&1
  echo "END $name exit=$? $(date -u +%FT%TZ)" >> /workspace/logs/status.log
done
