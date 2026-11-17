#!/bin/bash
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=.
FT_DATASETS=Corpus,grandstaff FT_MAX_FILES=3000 FT_EPOCHS=1 FT_WORKERS=${W:-4} python -X faulthandler training/transformer/finetune_octave.py > /workspace/logs/smoke.log 2>&1 &
P=$!
sleep ${T:-100}
tr "\r" "\n" < /workspace/logs/smoke.log | grep -a "it/s\|s/it" | tail -1 | cut -c1-200
if kill -0 $P 2>/dev/null; then kill -ABRT $P; sleep 3; fi
grep -a -B2 -A45 "Fatal Python error" /workspace/logs/smoke.log | cut -c1-200 | head -120
