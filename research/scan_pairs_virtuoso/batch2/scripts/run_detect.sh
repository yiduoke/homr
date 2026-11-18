#!/bin/bash
# usage: run_detect.sh pdf:page,page,... ...   homr detection per page (released weights, no homr change), nice'd
export HOMR_FIXED_MARGIN=1 PYTHONPATH=/Users/yiduoke/Documents/homr/run/integration_wt
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2
for item in "$@"; do
  p=${item%%:*}; pages=${item#*:}
  nice -n 10 /Users/yiduoke/Documents/homr/.venv/bin/python scripts/detect_pages.py $p $(echo $pages | tr ',' ' ')
done
echo list-done
