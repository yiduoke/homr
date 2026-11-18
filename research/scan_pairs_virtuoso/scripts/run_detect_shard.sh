#!/bin/bash
# usage: run_detect_shard.sh piece1 piece2 ...
export HOMR_FIXED_MARGIN=1 PYTHONPATH=/Users/yiduoke/Documents/homr/run/integration_wt
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso
for p in "$@"; do
  while [ ! -f work/pages/$p/.done ]; do sleep 20; done
  nice -n 10 /Users/yiduoke/Documents/homr/.venv/bin/python scripts/detect_pages.py $p all
done
echo shard-done
