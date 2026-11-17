#!/bin/bash
# Round three, step 2: wait for the staffs, build the lists, train, test every epoch.
L=/workspace/logs/r3
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=.
until grep -q "RENDER_DONE" $L/status.log && grep -q "^EXIT" $L/recrop.out; do sleep 30; done
say "building lists"
python training/transformer/build_round3_index.py > $L/index.out 2> $L/index.err || { say "INDEX FAILED"; exit 1; }
mkdir -p /workspace/round2_checkpoints; mv current_training/checkpoint-* /workspace/round2_checkpoints/ 2>/dev/null
say "training"
/workspace/restart.sh 2 NUMBA_NUM_THREADS=1 FT_INIT=/workspace/ckpt/round2_checkpoint-5738.safetensors FT_LR=2e-5 FT_TRAIN_INDEX=datasets/lilypond/round3_train.txt FT_VAL_INDEX=datasets/lilypond/round3_val.txt FT_NAME=pytorch_model_octave_round3
tmux new-session -d -s auto3 /workspace/auto3.sh
say "training started"
