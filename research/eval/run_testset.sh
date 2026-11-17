#!/bin/bash
# usage: run_testset.sh MODELTAG WORKTREE PIECE PDF FIRST LAST  (test-set piece: render, recognise, join, drop minor parts)
TAG=$1; WT=$2; F=$3; PDF=$4; FP=$5; LP=$6; R=/Users/yiduoke/Documents/homr/run; E=$R/eval_run1; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
mkdir -p $E/pages/$F; ls $E/pages/$F/page-*.png >/dev/null 2>&1 || pdftoppm -r 150 -png -f $FP -l $LP "$PDF" $E/pages/$F/page
D=$E/testset/$TAG/$F; mkdir -p $D/pages
for p in $E/pages/$F/page-*.png; do ln -sf $p $D/pages/$(basename $p); done
( cd $WT && PYTHONPATH=$WT HOMR_FIXED_MARGIN=1 $PY $E/run_homr.py $D/page-xml $D/pages/page-*.png > $D/homr.log 2>&1 )
cd /Users/yiduoke/Documents/homr
TRUST=${TRUST:-1}; [ "$TAG" = 566 ] && TRUST=0
HOMR_TRUST_PAGE_TIME=$TRUST HOMR_PAGES=$D/page-xml HOMR_OUT=$D/joined $PY $R/merge_pages.py > $D/merge.log 2>&1
$PY $R/drop_minor_parts.py $D/joined.musicxml $R/out/testset/$F/$F-$TAG.musicxml > $D/drop.log 2>&1
echo "$TAG $F done"
