#!/bin/bash
# usage: train_resolution.sh ARM SEED   ARM = A (256x1280, control) | B (384x1920)
# Continues the released run2s7 for a fixed 6716 steps on the run-2 data, exactly as
# run3 'ctrl' did (train_run3.sh); only the input resolution differs. Arm A is already trained
# as run3_ctrl_s7 / run3_ctrl_s11 and only needs this script to be repeated in a new environment.
ARM=$1; SEED=$2; NAME=res_${ARM}_s${SEED}
L=/workspace/logs/res/status.log; mkdir -p /workspace/logs/res
say() { echo "$(date -u +%FT%TZ) $NAME $*" >> $L; }
source /venv/main/bin/activate; cd /workspace/homr_res; export PYTHONPATH=.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OPENCV_FOR_THREADS_NUM=1 NUMBA_NUM_THREADS=1
case $ARM in
  A) unset HOMR_INPUT_SCALE ;;
  B) export HOMR_INPUT_SCALE=1.5 ;;
  *) echo "ARM must be A or B"; exit 2 ;;
esac
export FT_TRAIN_INDEX=/workspace/run3/run2_train_excl_v3.txt FT_VAL_INDEX=/workspace/run3/run2_val_excl_v3.txt
export FT_EPOCHS=2 FT_MAX_STEPS=${FT_MAX_STEPS:-6716} FT_LR=2e-5 FT_LAST=1 FT_SEED=$SEED FT_NAME=pytorch_model_$NAME FT_SKIP_CHECK=1 FT_WORKERS=${FT_WORKERS:-13}
export FT_BATCH=${FT_BATCH:-16} FT_ACCUM=${FT_ACCUM:-2}
export FT_OLD_VOCAB=/workspace/ckpt/vocab_meter_run1.json
export FT_CKPT=/workspace/homr_acc/training/architecture/transformer/pytorch_model_acc_run2s7_658-afae0e3dbdf84b2f9a53bc0e57fa7db788f64f10.pth
[ -e current_training ] && mv current_training current_training.before_$NAME.$(date +%s)
for attempt in 1 2 3; do
  say "training start attempt=$attempt resume=${FT_RESUME:-none} scale=${HOMR_INPUT_SCALE:-1}"
  python training/transformer/finetune_octave.py > /workspace/logs/res/$NAME.$attempt.log 2>&1
  code=$?; say "training exit=$code"; [ $code -eq 0 ] && break
  latest=$(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n | tail -1)
  if [ -n "$latest" ]; then export FT_RESUME=$(basename $latest); else unset FT_RESUME; fi
  sleep 20
done
ls training/architecture/transformer/pytorch_model_$NAME*.pth 2>/dev/null | tail -1 >> $L
# The optimiser checkpoints are about 1 GB each and the box has little disk: keep only the weights
if [ -n "$(ls training/architecture/transformer/pytorch_model_$NAME*.pth 2>/dev/null)" ] && [ "$KEEP_CKPT" != 1 ]; then
  rm -rf current_training; say "removed current_training"
fi
unset FT_RESUME
say "DONE"
