#!/bin/bash
# Round four, step 2: build the lists, train from round three epoch 1, test every epoch.
L=/workspace/logs/r4
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=.
until grep -q "RENDER_DONE" $L/status.log; do sleep 30; done
say "building lists"
R3_NAME=round4 R3_8VB_REPEAT=3 python training/transformer/build_round3_index.py > $L/index.out 2> $L/index.err || { say "INDEX FAILED"; exit 1; }
mkdir -p /workspace/round3_checkpoints; mv current_training/checkpoint-* /workspace/round3_checkpoints/ 2>/dev/null
say "training"
/workspace/restart.sh 2 NUMBA_NUM_THREADS=1 FT_INIT=/workspace/ckpt/round3_checkpoint-3463.safetensors FT_LR=2e-5 FT_TRAIN_INDEX=datasets/lilypond/round4_train.txt FT_VAL_INDEX=datasets/lilypond/round4_val.txt FT_NAME=pytorch_model_octave_round4
sed -e "s#/logs/r3#/logs/r4#; s#round3_\$n#round4_\$n#g; s#onnx/r3-#onnx/r4-#g; s#round three#round four#" /workspace/auto3.sh > /workspace/auto4.sh; chmod +x /workspace/auto4.sh
tmux new-session -d -s auto4 /workspace/auto4.sh
say "training started"
# Round three epoch 1 on the same held-out staffs, as the baseline
n=r3e1-baseline
EVAL_INDEX=datasets/lilypond/holdout_inserted.txt EVAL_POS=150 EVAL_NEG=60 python training/transformer/octave_eval.py /workspace/ckpt/round3_checkpoint-3463.safetensors > $L/$n.inserted.out 2> $L/$n.inserted.err
EVAL_INDEX=datasets/lilypond/holdout_real.txt EVAL_POS=130 EVAL_NEG=60 python training/transformer/octave_eval.py /workspace/ckpt/round3_checkpoint-3463.safetensors > $L/$n.real.out 2> $L/$n.real.err
say "baseline tested"
