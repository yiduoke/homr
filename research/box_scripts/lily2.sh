#!/bin/bash
# Second rendering pass: same scores, the wider bracket styles, other sizes.
until grep -q "^EXIT" /workspace/logs/lily.out 2>/dev/null; do sleep 20; done
cp /workspace/convert_lilypond_v2.py /workspace/homr/training/omr_datasets/convert_lilypond.py
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=. LILY_WORKERS=11 LILY_VARIANT=v2
python training/omr_datasets/convert_lilypond.py --share 0.05 datasets/Lieder-main/rendered_scores datasets/pdmx/rendered_scores datasets/musetrainer/rendered_scores > /workspace/logs/lily2.out 2> /workspace/logs/lily2.err
echo "EXIT $?" >> /workspace/logs/lily2.out
