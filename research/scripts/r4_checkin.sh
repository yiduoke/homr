#!/bin/bash
# One-shot status of round four, and the real-page tests for any newly exported epoch.
# Run from anywhere; prints what a check-in needs to report.
ROOT=/Users/yiduoke/Documents/homr
OUT=$ROOT/run/models/octave
mkdir -p $OUT/real_eval $OUT/round3
quiet() { grep -v "Welcome to vast\|Have fun\|AI agents\|Activated"; }

echo "=== preparation"
ssh -o ConnectTimeout=20 vast-homr4 'date -u +%T; tail -3 /workspace/logs/r4/status.log; for p in D; do f=/workspace/logs/r4/lily$p.err; [ -f $f ] && { echo "pass $p: $(grep -a "^[0-9]*/" $f | tail -1 | cut -c1-330)"; }; done; cat /workspace/logs/r4/augment.out 2>/dev/null; cat /workspace/logs/r4/index.err 2>/dev/null | tail -22; tmux ls 2>/dev/null | cut -d: -f1 | paste -sd" " -; df -h /workspace | tail -1' 2>&1 | quiet

echo "=== training"
ssh -o ConnectTimeout=20 vast-homr4 'tail -2 /workspace/logs/driver.log; f=$(ls -t /workspace/logs/train.*.log | head -1); echo $f; tr "\r" "\n" < $f | grep -a "Error\|Traceback" | tail -2 | cut -c1-200; tr "\r" "\n" < $f | grep -aE "^ *[0-9]+%.*[0-9]+/[0-9]+ \[" | tail -1 | cut -c1-110; tr "\r" "\n" < $f | grep -a "eval_accuracy" | grep -o "eval_[a-z]*_\?accuracy.: [0-9.]*\|.epoch.: [0-9.]*" | paste -sd" " - | sed "s/.epoch.: \([0-9.]*\) /epoch \1\n/g"; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader; ls /workspace/logs/r4/ | grep checkpoint | paste -sd" " -; ls /workspace/homr/training/architecture/transformer/pytorch_model_octave_round4_*.pth 2>/dev/null' 2>&1 | quiet

echo "=== octave tests on the box"
ssh -o ConnectTimeout=20 vast-homr4 'for f in $(ls /workspace/logs/r4/checkpoint-*.out 2>/dev/null | sort -t- -k2 -n); do echo "--- $(basename $f)"; cat $f; done' 2>&1 | quiet

echo "=== real-page tests (run by r3_realpages.sh, one at a time)"
ls $OUT/real_eval/round3.finished 2>/dev/null && echo "all real-page tests finished" || echo "real-page tests still running (or not started)"
for f in $OUT/real_eval/round2-checkpoint-5738.txt $OUT/real_eval/round2-e2-cropfix.txt $OUT/real_eval/round3-checkpoint-*.released.tmp $OUT/real_eval/round3-checkpoint-*.cropfix.tmp; do
  [ -f "$f" ] && { echo "--- $(basename $f)"; grep "|" $f | cut -d"|" -f1- | cut -c1-170; }
done
