#!/bin/bash
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. LILY_WORKERS=11
rm -rf datasets/lilypond
python training/omr_datasets/convert_lilypond.py --share 0.05 datasets/Lieder-main/rendered_scores datasets/pdmx/rendered_scores datasets/musetrainer/rendered_scores > /workspace/logs/lily.out 2> /workspace/logs/lily.err
echo "EXIT $?" >> /workspace/logs/lily.out
