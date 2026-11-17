#!/bin/bash
M=/workspace/run4/meters
until grep -q "^done" $M/logs/build_f.log 2>/dev/null; do sleep 10; done
mkdir -p $M/data/f; touch $M/data/f/staffs_vrv_0.jsonl
# at most 3 processes: wait for the two MuseScore e renders first
while [ $(ps -eo args | grep "render_windows.py ms" | grep "windows_e_train" | grep -v grep | grep -v "bash -c" | wc -l) -gt 0 ]; do sleep 15; done
$M/scripts/run_vrv_loop.sh $M/plan/windows_f_train.jsonl $M/data/f 0 1 &
nice -n 19 /venv/main/bin/python $M/scripts/render_windows.py ms $M/plan/windows_f_train.jsonl $M/data/f 0 1
wait
