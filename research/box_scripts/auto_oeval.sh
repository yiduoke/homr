#!/bin/bash
# After every epoch checkpoint appears, run the octave-specific test on it and
# keep the result as /workspace/logs/octave_eval.<checkpoint>.out
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1 EVAL_NEG=100
while true; do
  for c in $(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n); do
    n=$(basename $c); out=/workspace/logs/octave_eval.$n.out
    [ -f $out ] && continue
    [ -f $c/model.safetensors ] || continue
    sleep 60   # let the trainer finish writing the checkpoint
    python training/transformer/octave_eval.py $c > $out.tmp 2> /workspace/logs/octave_eval.$n.err && mv $out.tmp $out || { echo "FAILED" > $out; }
  done
  tail -1 /workspace/logs/driver.log | grep -q DONE && [ -z "$(ls -d current_training/checkpoint-* 2>/dev/null | while read c; do [ -f /workspace/logs/octave_eval.$(basename $c).out ] || echo x; done)" ] && break
  sleep 120
done
