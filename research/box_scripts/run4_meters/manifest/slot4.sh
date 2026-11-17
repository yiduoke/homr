#!/bin/bash
M=/workspace/run4/meters
until grep -q "^done" $M/logs/build_e.log 2>/dev/null; do sleep 15; done
mkdir -p $M/data/e; touch $M/data/e/staffs_vrv_0.jsonl
$M/scripts/run_vrv_loop.sh $M/plan/windows_e_train.jsonl $M/data/e 0 1
nice -n 19 /venv/main/bin/python $M/scripts/render_windows.py ms $M/plan/windows_e_train.jsonl $M/data/e 0 2
nice -n 19 /venv/main/bin/python $M/scripts/render_windows.py ms $M/plan/windows_e_train.jsonl $M/data/e 1 2
