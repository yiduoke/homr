#!/bin/bash
export HOMR_FIXED_MARGIN=1 PYTHONPATH=/Users/yiduoke/Documents/homr/run/integration_wt
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso
PY=/Users/yiduoke/Documents/homr/.venv/bin/python
for p in "$@"; do $PY scripts/build_piece.py $p 2>&1 | tail -1; $PY scripts/export.py $p 2>&1 | tail -1; done
