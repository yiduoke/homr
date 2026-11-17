#!/bin/bash
L=/workspace/logs/driver.log
say() { echo "$(date -u +%FT%TZ) $*" >> $L; }
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=.
for attempt in 1 2 3 4; do
  say "training start attempt=$attempt epochs=${FT_EPOCHS} batch=${FT_BATCH:-16}x${FT_ACCUM:-2} resume=${FT_RESUME:-none}"
  FT_SKIP_CHECK=1 FT_WORKERS=11 python training/transformer/finetune_octave.py > /workspace/logs/train.$attempt.log 2>&1
  code=$?
  ln -sf /workspace/logs/train.$attempt.log /workspace/logs/train.log
  say "training exit=$code"
  [ $code -eq 0 ] && break
  latest=$(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n | tail -1)
  if [ -n "$latest" ]; then export FT_RESUME=$(basename $latest); else unset FT_RESUME; fi
  sleep 20
done
ls -la training/architecture/transformer/pytorch_model_octave_*.pth >> $L 2>&1
say "DONE"
