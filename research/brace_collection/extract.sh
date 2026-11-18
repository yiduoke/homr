#!/bin/bash
# extract.sh EDITION...  detection + relation-model crops of every rendered page (scripts of run/staff_rel_realbrace, worktree run/rel_wt)
R=/Users/yiduoke/Documents/homr/run
cd $R/rel_wt
for ed in "$@"; do
  PYTHONPATH=$R/rel_wt /Users/yiduoke/Documents/homr/.venv/bin/python $R/staff_rel_realbrace/scripts/extract_pairs.py $R/brace_collection/extract $R/brace_collection/pages/$ed/page-*.png > $R/brace_collection/logs/extract_$ed.log 2>&1
done
