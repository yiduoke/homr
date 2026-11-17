#!/bin/bash
# Round two: after every epoch checkpoint, export it for the real-page test on the laptop
# and run the octave test twice: on held-out LilyPond staffs (new styles) and on
# round one's MuseScore validation staffs (did anything get worse?).
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
while true; do
  for c in $(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n); do
    n=$(basename $c)
    [ -f /workspace/logs/r2/$n.done ] && continue
    [ -f $c/model.safetensors ] || continue
    sleep 60
    cp $c/model.safetensors /workspace/ckpt/round2_$n.safetensors
    /workspace/export.sh /workspace/ckpt/round2_$n.safetensors > /workspace/logs/r2/$n.export.log 2>&1 && mkdir -p /workspace/onnx/$n && cp /workspace/export/homr/transformer/*.onnx /workspace/onnx/$n/ && touch /workspace/logs/r2/$n.exported
    EVAL_INDEX=datasets/lilypond/holdout.txt EVAL_POS=137 EVAL_NEG=80 python training/transformer/octave_eval.py /workspace/ckpt/round2_$n.safetensors > /workspace/logs/r2/$n.lily.out 2> /workspace/logs/r2/$n.lily.err
    EVAL_POS=150 EVAL_NEG=50 python training/transformer/octave_eval.py /workspace/ckpt/round2_$n.safetensors > /workspace/logs/r2/$n.musescore.out 2> /workspace/logs/r2/$n.musescore.err
    touch /workspace/logs/r2/$n.done
  done
  sleep 60
done
