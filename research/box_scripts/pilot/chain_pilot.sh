#!/bin/bash
# usage: RES=1|1.5 [R=8] chain_pilot.sh        NOT LAUNCHED. Four runs, interleaved so that a partial result is still balanced:
# CTRL_RENDER seed 7, SCAN seed 7, CTRL_RENDER seed 11, SCAN seed 11. Start only when no other training runs on the box (the resolution runs
# in tmux `res` first): the script waits until no finetune_octave.py process exists.
# Launch (when approved):  tmux new -s pilot 'RES=1 /workspace/pilot/scripts/chain_pilot.sh'
RES=${RES:?set RES=1 or RES=1.5}; export RES; R=${R:-8}; export R
LOGD=/workspace/logs/pilot; mkdir -p $LOGD
echo "$(date -u +%FT%TZ) CHAIN start RES=$RES R=$R" >> $LOGD/status.log
source /venv/main/bin/activate
[ -s /workspace/pilot/mix/mix_SCAN_R${R}.txt ] || python /workspace/pilot/scripts/build_pilot_mix.py --repeat $R >> $LOGD/mix.log 2>&1
for spec in "CTRL_RENDER 7" "SCAN 7" "CTRL_RENDER 11" "SCAN 11"; do
  while pgrep -f finetune_octave.py > /dev/null; do sleep 60; done          # one heavy job at a time
  /workspace/pilot/scripts/train_pilot.sh $spec
done
echo "$(date -u +%FT%TZ) CHAIN DONE" >> $LOGD/status.log
