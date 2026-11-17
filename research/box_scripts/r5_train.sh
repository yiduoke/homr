#!/bin/bash
# Round five, step 2: build the lists (no extra repeats of octave-lower staffs), train
# from round three epoch 1, test every epoch.
L=/workspace/logs/r5
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=.
until grep -q "RENDER_DONE" $L/status.log; do sleep 30; done
say "building lists"
R3_NAME=round5 R3_8VB_REPEAT=1 python training/transformer/build_round3_index.py > $L/index.out 2> $L/index.err || { say "INDEX FAILED"; exit 1; }
mkdir -p /workspace/round4_checkpoints; mv current_training/checkpoint-* /workspace/round4_checkpoints/ 2>/dev/null
say "training"
/workspace/restart.sh 2 NUMBA_NUM_THREADS=1 FT_INIT=/workspace/ckpt/round3_checkpoint-3463.safetensors FT_LR=2e-5 FT_TRAIN_INDEX=datasets/lilypond/round5_train.txt FT_VAL_INDEX=datasets/lilypond/round5_val.txt FT_NAME=pytorch_model_octave_round5
sed -e "s#/logs/r3#/logs/r5#; s#round3_\$n#round5_\$n#g; s#onnx/r3-#onnx/r5-#g; s#round three#round five#" /workspace/auto3.sh > /workspace/auto5.sh; chmod +x /workspace/auto5.sh
tmux new-session -d -s auto5 /workspace/auto5.sh
say "training started"
n=r3e1-baseline
EVAL_INDEX=datasets/lilypond/holdout_inserted.txt EVAL_POS=150 EVAL_NEG=60 python training/transformer/octave_eval.py /workspace/ckpt/round3_checkpoint-3463.safetensors > $L/$n.inserted.out 2> $L/$n.inserted.err
say "baseline tested"
