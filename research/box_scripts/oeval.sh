#!/bin/bash
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. OMP_NUM_THREADS=1 NUMBA_NUM_THREADS=1
python training/transformer/octave_eval.py "$1" > /workspace/logs/octave_eval.out 2> /workspace/logs/octave_eval.err
echo "EXIT $?" >> /workspace/logs/octave_eval.out
