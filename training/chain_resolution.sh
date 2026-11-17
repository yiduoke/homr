#!/bin/bash
# Arm B for both seeds (arm A exists as run3_ctrl_s7 and run3_ctrl_s11)
for spec in "B 7" "B 11"; do /workspace/homr_res/training/train_resolution.sh $spec; done
echo "$(date -u +%FT%TZ) CHAIN DONE" >> /workspace/logs/res/status.log
