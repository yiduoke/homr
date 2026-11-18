#!/bin/bash
# usage: run_all.sh <pid ...>: align (build_piece) + export2 for each piece
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2
PY=/Users/yiduoke/Documents/homr/.venv/bin/python
for p in "$@"; do $PY scripts/build_piece.py $p 2>&1 | tail -1; $PY scripts/export2.py $p 2>&1 | tail -1; done
