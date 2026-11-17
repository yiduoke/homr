#!/bin/bash
# Run 2 (printed accidentals): from the run-1 model, lift head reset, same mix as run 1, 2 epochs.
L=/workspace/logs/run2s7/status.log
say() { echo "$(date -u +%FT%TZ) $*" >> $L; }
source /venv/main/bin/activate; cd /workspace/homr_acc; export PYTHONPATH=.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OPENCV_FOR_THREADS_NUM=1 NUMBA_NUM_THREADS=1
export FT_EPOCHS=2 FT_LR=2e-5 FT_TRAIN_INDEX=/workspace/run2/run2_train.txt FT_VAL_INDEX=/workspace/run2/run2_val.txt
export FT_CKPT=/workspace/homr_meter/training/architecture/transformer/pytorch_model_meter_run1_653-10bc7e642bc29de1e0c7cefec4149fd3d7f6fcd6.pth FT_OLD_VOCAB=/workspace/ckpt/vocab_meter_run1.json
export FT_RESET_LIFT=1 FT_NAME=pytorch_model_acc_run2s7 FT_SEED=7 FT_SKIP_CHECK=1 FT_WORKERS=11
for attempt in 1 2 3 4; do
  say "training start attempt=$attempt resume=${FT_RESUME:-none}"
  python training/transformer/finetune_octave.py > /workspace/logs/run2s7/train.$attempt.log 2>&1
  code=$?; say "training exit=$code"
  [ $code -eq 0 ] && break
  latest=$(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n | tail -1)
  if [ -n "$latest" ]; then export FT_RESUME=$(basename $latest); else unset FT_RESUME; fi
  sleep 20
done
P=$(ls /workspace/homr_acc/training/architecture/transformer/pytorch_model_acc_run2s7*.pth | tail -1); echo "$P" >> $L
/workspace/export_run.sh /workspace/homr_acc $P acc_run2s7 > /workspace/logs/run2s7/export.log 2>&1 && say "EXPORTED"
say "DONE"
