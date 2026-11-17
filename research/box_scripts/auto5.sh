#!/bin/bash
# After every epoch checkpoint of round five: export it and run the octave tests.
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
L=/workspace/logs/r5
while true; do
  for c in $(ls -d current_training/checkpoint-* 2>/dev/null | sort -t- -k2 -n); do
    n=$(basename $c)
    [ -f $L/$n.done ] && continue
    [ -f $c/model.safetensors ] || continue
    sleep 60
    cp $c/model.safetensors /workspace/ckpt/round5_$n.safetensors
    /workspace/export.sh /workspace/ckpt/round5_$n.safetensors > $L/$n.export.log 2>&1 && mkdir -p /workspace/onnx/r5-$n && cp /workspace/export/homr/transformer/*.onnx /workspace/onnx/r5-$n/ && touch $L/$n.exported
    EVAL_INDEX=datasets/lilypond/holdout_inserted.txt EVAL_POS=150 EVAL_NEG=60 python training/transformer/octave_eval.py /workspace/ckpt/round5_$n.safetensors > $L/$n.inserted.out 2> $L/$n.inserted.err
    EVAL_INDEX=datasets/lilypond/holdout_real.txt EVAL_POS=130 EVAL_NEG=60 python training/transformer/octave_eval.py /workspace/ckpt/round5_$n.safetensors > $L/$n.real.out 2> $L/$n.real.err
    EVAL_POS=150 EVAL_NEG=50 python training/transformer/octave_eval.py /workspace/ckpt/round5_$n.safetensors > $L/$n.musescore.out 2> $L/$n.musescore.err
    touch $L/$n.done
  done
  sleep 60
done
