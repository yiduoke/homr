#!/bin/bash
# usage: train_run3.sh ARM SEED   ARM = ctrl | cand ; continues the released model (run2s7) for a fixed 6716 steps
ARM=$1; SEED=$2; NAME=run3_${ARM}_s${SEED}
L=/workspace/logs/run3/status.log; say() { echo "$(date -u +%FT%TZ) $NAME $*" >> $L; }
source /venv/main/bin/activate; cd /workspace/homr_acc; export PYTHONPATH=.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OPENCV_FOR_THREADS_NUM=1 NUMBA_NUM_THREADS=1
if [ "$ARM" = ctrl ]; then export FT_TRAIN_INDEX=/workspace/run3/run2_train_excl_v3.txt FT_VAL_INDEX=/workspace/run3/run2_val_excl_v3.txt
else export FT_TRAIN_INDEX=/workspace/run3/cand_train_nooct_v3.txt FT_VAL_INDEX=/workspace/run3/cand_val_v3.txt; fi
export FT_EPOCHS=2 FT_MAX_STEPS=${FT_MAX_STEPS:-6716} FT_LR=2e-5 FT_LAST=1 FT_SEED=$SEED FT_NAME=pytorch_model_$NAME FT_SKIP_CHECK=1 FT_WORKERS=${FT_WORKERS:-13}
export FT_OLD_VOCAB=/workspace/ckpt/vocab_meter_run1.json
export FT_CKPT=/workspace/homr_acc/training/architecture/transformer/pytorch_model_acc_run2s7_658-afae0e3dbdf84b2f9a53bc0e57fa7db788f64f10.pth
[ -e current_training ] && mv current_training current_training.before_$NAME.$(date +%s)
for attempt in 1 2 3; do
  say "training start attempt=$attempt resume=${FT_RESUME:-none}"
  python training/transformer/finetune_octave.py > /workspace/logs/run3/$NAME.$attempt.log 2>&1
  code=$?; say "training exit=$code"; [ $code -eq 0 ] && break
  latest=$(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n | tail -1)
  if [ -n "$latest" ]; then export FT_RESUME=$(basename $latest); else unset FT_RESUME; fi
  sleep 20
done
ls training/architecture/transformer/pytorch_model_$NAME*.pth 2>/dev/null | tail -1 >> $L
[ -e current_training ] && mv current_training current_training.$NAME; unset FT_RESUME
say "DONE"
