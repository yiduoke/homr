#!/bin/bash
# usage: restart.sh EPOCHS [extra env assignments...]
tmux kill-session -t train 2>/dev/null
for p in $(ps -eo pid,cmd | grep "[f]inetune_octave.py" | awk "{print \$1}"); do kill -9 $p; done
sleep 3
rm -rf /workspace/homr/current_training; rm -f /workspace/logs/train.log; ln -sf /workspace/logs/train.1.log /workspace/logs/train.log
E=$1; shift
tmux new-session -d -s train "env OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 OPENCV_FOR_THREADS_NUM=1 FT_EPOCHS=$E $* /workspace/train.sh"
tmux ls
