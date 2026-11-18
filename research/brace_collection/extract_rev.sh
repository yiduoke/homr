#!/bin/bash
# like extract.sh but walks the pages of an edition from the last to the first (a second worker; existing outputs are skipped)
R=/Users/yiduoke/Documents/homr/run
cd $R/rel_wt
ed=$1
for f in $(ls -r $R/brace_collection/pages/$ed/page-*.png); do
  PYTHONPATH=$R/rel_wt /Users/yiduoke/Documents/homr/.venv/bin/python $R/staff_rel_realbrace/scripts/extract_pairs.py $R/brace_collection/extract $f >> $R/brace_collection/logs/extract_rev_$ed.log 2>&1
done
