#!/bin/bash
# train_arms2.sh: arms A, B, C of D30, seeds 0 and 1 (same budget: 12 epochs x 150 steps x batch 64, lr 1e-4 one-cycle), laptop MPS, ONNX in models2/
cd /Users/yiduoke/Documents/homr/run/staff_rel_realbrace
export PYTHONPATH=/Users/yiduoke/Documents/homr/run/rel_wt
for arm in A B C; do for s in 0 1; do
  [ -f models2/realbrace2-$arm-s$s.onnx ] || /Users/yiduoke/Documents/homr/.venv/bin/python scripts/finetune2.py d30/mixture2_$arm.npz models2/realbrace2-$arm-s$s.onnx --seed $s --device mps > d30/train_${arm}_s$s.log 2>&1
done; done
