#!/bin/bash
# Runs unattended: wait for the five dataset conversions, then fine-tune.
L=/workspace/logs/driver.log
say() { echo "$(date -u +%FT%TZ) $*" >> $L; }
source /venv/main/bin/activate; cd /workspace/homr; export PYTHONPATH=.
say "driver started, waiting for conversions"
until [ "$(grep -c "^END" /workspace/logs/status.log)" -ge 5 ]; do sleep 30; done
say "conversions done: $(wc -l datasets/*/index.txt | tail -1)"
for i in datasets/Lieder-main/index.txt datasets/pdmx/index.txt datasets/musetrainer/index.txt datasets/grandstaff/index.txt datasets/Corpus/index.txt; do
  [ -s "$i" ] || { say "MISSING INDEX $i - not starting training"; exit 1; }
done
say "training start epochs=${FT_EPOCHS:-8}"
FT_EPOCHS=${FT_EPOCHS:-8} FT_WORKERS=11 python training/transformer/finetune_octave.py > /workspace/logs/train.log 2>&1
say "training exit=$?"
ls -la training/architecture/transformer/pytorch_model_octave_*.pth >> $L 2>&1
say "DONE"
