#!/bin/bash
# wait for the epoch-2 test that is already running, file its result, then go automatic
while tmux has-session -t oeval 2>/dev/null; do sleep 30; done
grep -v "^EXIT" /workspace/logs/octave_eval.out > /workspace/logs/octave_eval.checkpoint-19618.out
exec /workspace/auto_oeval.sh
