#!/bin/bash
# usage: RES=1|1.5 [R=8] [GROUPS_TAG=] train_pilot.sh ARM SEED       ARM = CTRL_RENDER | SCAN
# NOT LAUNCHED (prepared 2026-11-17 for the pilot comparison, see run/scan_pairs_virtuoso/PILOT_SPEC.md).
# Continues the released run2s7 for a fixed 6716 steps exactly as run3 'ctrl' did (box_scripts/run3/train_run3.sh, res_wt/training/train_resolution.sh);
# the ONLY differences: the training list = run2_train_excl_v3 + R copies of the 867 pilot passages (rendered twins for CTRL_RENDER, scanned crops for SCAN,
# same order, same tokens; built by build_pilot_mix.py), and the model name. Validation list = the run-3 control validation list (rendered staffs, unchanged),
# so the epoch evaluations stay comparable with run3_ctrl_* and res_*; the held-out pilot crops are evaluated afterwards (pilot_val_eval.py).
# RES=1   : 256x1280, code /workspace/homr_acc (as run3), model name pilot_<ARM>_s<SEED>
# RES=1.5 : 384x1920, code /workspace/homr_res with HOMR_INPUT_SCALE=1.5 (as res_B), model name pilot_<ARM>_r15_s<SEED>
ARM=$1; SEED=$2; RES=${RES:?set RES=1 or RES=1.5 (decided by the resolution experiment)}; R=${R:-8}; GT=${GROUPS_TAG:-}
case $ARM in CTRL_RENDER|SCAN) ;; *) echo "ARM must be CTRL_RENDER or SCAN"; exit 2 ;; esac
case $RES in
  1)   CODE=/workspace/homr_acc; NAME=pilot_${ARM}_s${SEED}; unset HOMR_INPUT_SCALE ;;
  1.5) CODE=/workspace/homr_res; NAME=pilot_${ARM}_r15_s${SEED}; export HOMR_INPUT_SCALE=1.5 ;;
  *)   echo "RES must be 1 or 1.5"; exit 2 ;;
esac
LOGD=/workspace/logs/pilot; mkdir -p $LOGD; L=$LOGD/status.log; say() { echo "$(date -u +%FT%TZ) $NAME $*" >> $L; }
MIX=/workspace/pilot/mix/mix_${ARM}_R${R}${GT}.txt
[ -s "$MIX" ] || { say "MISSING $MIX (run build_pilot_mix.py first)"; exit 3; }
source /venv/main/bin/activate; cd $CODE; export PYTHONPATH=.
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OPENCV_FOR_THREADS_NUM=1 NUMBA_NUM_THREADS=1
export FT_TRAIN_INDEX=$MIX FT_VAL_INDEX=/workspace/run3/run2_val_excl_v3.txt
export FT_EPOCHS=2 FT_MAX_STEPS=${FT_MAX_STEPS:-6716} FT_LR=2e-5 FT_LAST=1 FT_SEED=$SEED FT_NAME=pytorch_model_$NAME FT_SKIP_CHECK=1 FT_WORKERS=${FT_WORKERS:-13}
export FT_BATCH=${FT_BATCH:-16} FT_ACCUM=${FT_ACCUM:-2}
export FT_OLD_VOCAB=/workspace/ckpt/vocab_meter_run1.json
export FT_CKPT=/workspace/homr_acc/training/architecture/transformer/pytorch_model_acc_run2s7_658-afae0e3dbdf84b2f9a53bc0e57fa7db788f64f10.pth
# FT_MAX_STEPS stops the run after 6716 updates (1.88 passes over the longer list); FT_EPOCHS=2 is only the upper bound for the trainer.
[ -e current_training ] && mv current_training current_training.before_$NAME.$(date +%s)
for attempt in 1 2 3; do
  say "training start attempt=$attempt resume=${FT_RESUME:-none} scale=${HOMR_INPUT_SCALE:-1} list=$MIX"
  python training/transformer/finetune_octave.py > $LOGD/$NAME.$attempt.log 2>&1
  code=$?; say "training exit=$code"; [ $code -eq 0 ] && break
  latest=$(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n | tail -1)
  if [ -n "$latest" ]; then export FT_RESUME=$(basename $latest); else unset FT_RESUME; fi
  sleep 20
done
ls training/architecture/transformer/pytorch_model_$NAME*.pth 2>/dev/null | tail -1 >> $L
# the optimiser checkpoints are about 1 GB each and the box has little disk: keep only the weights (KEEP_CKPT=1 keeps them)
if [ -n "$(ls training/architecture/transformer/pytorch_model_$NAME*.pth 2>/dev/null)" ] && [ "$KEEP_CKPT" != 1 ]; then
  rm -rf current_training; say "removed current_training"
fi
unset FT_RESUME
say "DONE"
