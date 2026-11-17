#!/bin/bash
# One-shot status of round two, and the real-page test for any newly exported epoch.
# Run from anywhere; prints what a check-in needs to report.
ROOT=/Users/yiduoke/Documents/homr
OUT=$ROOT/run/models/octave
mkdir -p $OUT/real_eval $OUT/round2
quiet() { grep -v "Welcome to vast\|Have fun\|AI agents\|Activated"; }

echo "=== training"
ssh -o ConnectTimeout=20 vast-homr 'date -u +%T; tail -2 /workspace/logs/driver.log; f=$(ls -t /workspace/logs/train.*.log | head -1); tr "\r" "\n" < $f | grep -a "Error\|Traceback" | tail -2 | cut -c1-200; tr "\r" "\n" < $f | grep -aE "/86[0-9][0-9] " | tail -1 | cut -c1-100; tr "\r" "\n" < $f | grep -a "eval_accuracy" | grep -o "eval_[a-z]*_\?accuracy.: [0-9.]*\|.epoch.: [0-9.]*" | paste -sd" " - | sed "s/.epoch.: \([0-9.]*\) /epoch \1\n/g"; nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader; tmux ls 2>/dev/null | cut -d: -f1 | paste -sd" " -; ls /workspace/logs/r2/ 2>/dev/null | paste -sd" " -; ls /workspace/homr/training/architecture/transformer/pytorch_model_octave_round2_*.pth 2>/dev/null' 2>&1 | quiet

echo "=== octave tests on the box"
ssh -o ConnectTimeout=20 vast-homr 'for f in $(ls /workspace/logs/r2/*.out 2>/dev/null | sort -t- -k2 -n); do echo "--- $(basename $f)"; cat $f; done' 2>&1 | quiet

echo "=== real-page tests"
for n in $(ssh -o ConnectTimeout=20 vast-homr 'ls /workspace/logs/r2/*.exported 2>/dev/null | xargs -n1 basename 2>/dev/null | sed "s/.exported//"' 2>/dev/null | grep checkpoint); do
  result=$OUT/real_eval/round2-$n.txt
  if [ ! -f $result ] && [ ! -f $result.running ] && [ -f $OUT/NO_DOWNLOAD ]; then
    echo "real-page test for $n NOT started: downloads are paused (user on a hotspot); remove $OUT/NO_DOWNLOAD to resume"
  elif [ ! -f $result ] && [ ! -f $result.running ]; then
    mkdir -p $OUT/round2/$n
    for kind in encoder decoder; do
      scp -q "vast-homr:/workspace/onnx/$n/${kind}_pytorch_model_509-2293bba14bfea47d9d28411339362af15fce4c31.onnx" $OUT/round2/$n/ 2>/dev/null
    done
    touch $result.running
    (cd $ROOT && .venv/bin/python run/real_eval.py $OUT/round2/$n round2-$n > $result.tmp 2>&1; mv $result.tmp $result; rm -f $result.running) > /dev/null 2>&1 &
    echo "started real-page test for $n (about 10 minutes)"
  elif [ -f $result.running ]; then
    echo "real-page test for $n still running"
  fi
done
for f in $OUT/real_eval/round1-epoch2.txt $(ls $OUT/real_eval/round2-checkpoint-*.txt 2>/dev/null | sort -t- -k3 -n); do
  [ -f "$f" ] && { echo "--- $(basename $f)"; grep "|" $f | cut -d"|" -f2- | cut -c1-150; }
done
