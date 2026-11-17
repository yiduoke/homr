#!/bin/bash
# Regenerate the regular training data with upstream 566 converters (beam tokens),
# in a fresh checkout of octave-on-566 with its own datasets folder.
L=/workspace/logs/r6
say() { echo "$(date -u +%FT%TZ) $*" >> $L/status.log; }
source /venv/main/bin/activate
say "clone"
cd /workspace && [ -d homr566 ] || git clone -q --depth 1 --branch octave-on-566 https://github.com/yiduoke/homr.git homr566 || { say "CLONE FAILED"; exit 1; }
cd /workspace/homr566 && mkdir -p datasets && cd datasets
[ -e MuseScore ] || ln -s /workspace/homr/datasets/MuseScore MuseScore
[ -e MuseScoreStyles ] || ln -s /workspace/homr/datasets/MuseScoreStyles MuseScoreStyles
[ -d Lieder-main ] || unzip -q /workspace/homr/datasets/Lieder.zip -d . || { say "UNZIP FAILED"; exit 1; }
[ -d grandstaff ] || { mkdir grandstaff && tar xzf /workspace/homr/datasets/grandstaff.tgz -C grandstaff; } || { say "UNTAR FAILED"; exit 1; }
mkdir -p pdmx && { [ -e pdmx/PDMX.csv ] || ln -s /workspace/homr/datasets/pdmx/PDMX.csv pdmx/PDMX.csv; } && { [ -e pdmx/mxl ] || ln -s /workspace/homr/datasets/pdmx/mxl pdmx/mxl; }
cd /workspace/homr566; export PYTHONPATH=.
for ds in grandstaff pdmx lieder; do
  say "convert $ds"
  python -c "from training.omr_datasets.convert_$ds import convert_$ds; convert_$ds()" > $L/$ds.out 2> $L/$ds.err && say "done $ds ($(wc -l < datasets/*/index.txt 2>/dev/null | tail -1))" || say "FAILED $ds"
done
say "ALL DONE"
