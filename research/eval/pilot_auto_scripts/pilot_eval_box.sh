#!/bin/bash
# Box 5 side of the pilot automation (D29): the 28-scan GPU evaluation of one model with the harness of the resolution experiment (res_eval.py, scale 1).
# usage: pilot_eval_box.sh NAME TAG [res_eval args...]        e.g. pilot_eval_box.sh pilot_SCAN_s7 pilot_SCAN_s7_gpu
# Status lines in /root/logs/gpu_chain.status ("start TAG" / "end TAG exit=N", UTC) like the earlier chains. A piece that FAILED (e.g. a pool worker killed
# for memory) is simply repeated by repeating the command (finished pieces are kept): up to 3 passes. Exit 0 only if all 28 pieces have scores.
R=/Users/yiduoke/Documents/homr/run; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
NAME=$1; TAG=$2; shift 2; LOG=/root/logs/$TAG.log; mkdir -p /root/logs
echo "$(date -u +%FT%TZ) start $TAG" >> /root/logs/gpu_chain.status
cd $R; rc=1
want=28; [ -n "$*" ] && want=0
for pass in 1 2 3; do
  echo "$(date -u +%FT%TZ) pass $pass" >> $LOG
  nice $PY eval_run1/res_eval.py --tag $TAG --model $NAME --scale 1 "$@" >> $LOG 2>&1
  n=$(ls $R/out/testset/*/res-scores-$TAG.json 2>/dev/null | wc -l)
  echo "$(date -u +%FT%TZ) pass $pass scored $n pieces" >> $LOG
  if [ "$want" = 0 ] || [ "$n" -ge "$want" ]; then rc=0; break; fi
done
echo "$(date -u +%FT%TZ) end $TAG exit=$rc" >> /root/logs/gpu_chain.status
exit $rc
