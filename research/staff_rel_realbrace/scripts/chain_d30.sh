#!/bin/bash
# chain_d30.sh (box): runs pipeline_arm2.sh for every arm/seed whose ONNX has arrived in models2/, one evaluation at a time, waiting for the control first
R=/Users/yiduoke/Documents/homr/run
for arm in A B C; do for s in 0 1; do
  tag=relbrace2_${arm}_s${s}_gpu; m=$R/staff_rel_realbrace/models2/realbrace2-$arm-s$s.onnx
  while [ ! -f $m.ready ]; do sleep 10; done
  /root/pipeline_arm2.sh $tag $m 2>&1 | tee /root/logs/d30_$tag.log
  touch /root/logs/d30_$tag.done
done; done
