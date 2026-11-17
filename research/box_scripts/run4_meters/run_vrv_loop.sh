#!/bin/bash
# usage: run_vrv_loop.sh <plan> <outdir> <k> <n>  restarts the Verovio renderer after a crash until it exits normally
for i in $(seq 1 60); do
  nice -n 19 /venv/main/bin/python /workspace/run4/meters/scripts/render_windows.py vrv "$1" "$2" "$3" "$4" && break
done
