#!/bin/bash
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=.
xvfb-run -a python training/omr_datasets/recrop_musescore_octave.py > /workspace/logs/r3/recrop.out 2> /workspace/logs/r3/recrop.err
echo "EXIT $?" >> /workspace/logs/r3/recrop.out
