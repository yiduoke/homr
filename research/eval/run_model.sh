#!/bin/bash
# usage: run_model.sh MODEL WORKTREE   (runs all eight pieces sequentially)
MODEL=$1; WT=$2; R=/Users/yiduoke/Documents/homr/run; E=$R/eval_run1; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
for f in mazeppa la-campanella rachmaninoff-op3-2 bach-prelude-848 bach-fugue-848 mozart-kv331-theme mozart-kv309-1 beethoven-pathetique-1; do
  D=$E/$MODEL/$f; mkdir -p $D/pages
  [ -f $D/done ] && continue
  for p in $E/pages/$f/page-*.png; do ln -sf $p $D/pages/$(basename $p); done
  ( cd $WT && PYTHONPATH=$WT HOMR_FIXED_MARGIN=1 $PY $E/run_homr.py $D/page-xml $D/pages/page-*.png > $D/homr.log 2>&1 ) && touch $D/done
done
echo finished > $E/$MODEL/ALLDONE
