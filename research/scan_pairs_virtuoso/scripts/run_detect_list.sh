#!/bin/bash
# usage: run_detect_list.sh "pdf:pages" ...   (pages as detect_pages args, space-free comma list e.g. 1,2,3)
export HOMR_FIXED_MARGIN=1 PYTHONPATH=/Users/yiduoke/Documents/homr/run/integration_wt
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso
for item in "$@"; do
  p=${item%%:*}; pages=${item#*:}
  while [ ! -f work/pages/$p/.done ]; do sleep 20; done
  nice -n 10 /Users/yiduoke/Documents/homr/.venv/bin/python scripts/detect_pages.py $p $(echo $pages | tr ',' ' ')
done
echo list-done
