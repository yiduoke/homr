#!/bin/bash
M=/workspace/run4/meters
until grep -q "^done" $M/logs/build_g.log 2>/dev/null && grep -q "^done" $M/logs/build_w.log 2>/dev/null; do sleep 10; done
export HOLDOUT=1
F=1/4,5/4,6/4,7/4,8/4,9/4,10/4,1/8,2/8,4/8,5/8,7/8,9/8,11/8,12/8,13/8,15/8,5/16,7/16,9/16,11/16,12/16,13/16,15/16,17/16,19/16,3/2,4/2
RARE_FOCUS=$F nice -n 19 /venv/main/bin/python $M/scripts/build_windows.py x 1500 val 62 > $M/logs/build_x.log 2>&1 &
nice -n 19 /venv/main/bin/python $M/scripts/render_windows.py ms $M/plan/windows_g_train.jsonl $M/data/g 0 2 &
$M/scripts/run_vrv_loop.sh $M/plan/windows_g_train.jsonl $M/data/g 0 1 &
wait
nice -n 19 /venv/main/bin/python $M/scripts/render_windows.py ms $M/plan/windows_g_train.jsonl $M/data/g 1 2 &
for r in w x; do mkdir -p $M/data/$r; touch $M/data/$r/staffs_vrv_0.jsonl; done
$M/scripts/run_vrv_loop.sh $M/plan/windows_w_val.jsonl $M/data/w 0 1 &
wait
nice -n 19 /venv/main/bin/python $M/scripts/render_windows.py ms $M/plan/windows_w_val.jsonl $M/data/w 0 1 &
$M/scripts/run_vrv_loop.sh $M/plan/windows_x_val.jsonl $M/data/x 0 1 &
nice -n 19 /venv/main/bin/python $M/scripts/render_windows.py ms $M/plan/windows_x_val.jsonl $M/data/x 0 1 &
wait
