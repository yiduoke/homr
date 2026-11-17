#!/bin/bash
# interleaved so a partial result is still balanced: control and candidate, seed 7 then seed 11
for spec in "ctrl 7" "cand 7" "ctrl 11" "cand 11"; do /workspace/run3/train_run3.sh $spec; done
echo "$(date -u +%FT%TZ) CHAIN DONE" >> /workspace/logs/run3/status.log
