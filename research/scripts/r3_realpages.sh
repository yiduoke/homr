#!/bin/bash
# Round three real-page tests, one after another (they share the worktree's model files).
ROOT=/Users/yiduoke/Documents/homr
OUT=$ROOT/run/models/octave
cd $ROOT
for n in checkpoint-3463 checkpoint-6926; do
  HOMR_FIXED_MARGIN=1 .venv/bin/python run/real_eval.py $OUT/round3/$n round3-$n > $OUT/real_eval/round3-$n.released.tmp 2>&1
  .venv/bin/python run/real_eval.py $OUT/round3/$n round3-$n-cropfix > $OUT/real_eval/round3-$n.cropfix.tmp 2>&1
done
echo done > $OUT/real_eval/round3.finished
