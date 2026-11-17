#!/bin/bash
# Run 1 (complete time signatures): upstream 566 + new time-signature rows, round 3 mix, 2 epochs.
L=/workspace/logs/run1/status.log
say() { echo "$(date -u +%FT%TZ) $*" >> $L; }
source /venv/main/bin/activate; cd /workspace/homr_meter; export PYTHONPATH=.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OPENCV_FOR_THREADS_NUM=1 NUMBA_NUM_THREADS=1
export FT_EPOCHS=2 FT_LR=2e-5 FT_TRAIN_INDEX=/workspace/run1/run1_train.txt FT_VAL_INDEX=/workspace/run1/run1_val.txt
export FT_CKPT=/workspace/ckpt/pytorch_model_566-ccd1cb311c368b5711dd238d2464c615397a3f2b.pth FT_OLD_VOCAB=/workspace/ckpt/vocab_566.json
export FT_NAME=pytorch_model_meter_run1 FT_SKIP_CHECK=1 FT_WORKERS=11
for attempt in 1 2 3 4; do
  say "training start attempt=$attempt resume=${FT_RESUME:-none}"
  python training/transformer/finetune_octave.py > /workspace/logs/run1/train.$attempt.log 2>&1
  code=$?; say "training exit=$code"
  [ $code -eq 0 ] && break
  latest=$(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n | tail -1)
  if [ -n "$latest" ]; then export FT_RESUME=$(basename $latest); else unset FT_RESUME; fi
  sleep 20
done
ls -la training/architecture/transformer/pytorch_model_meter_run1*.pth >> $L 2>&1
say "DONE"
