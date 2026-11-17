#!/bin/bash
# usage: run_extra.sh MODEL WORKTREE FOLDER PDF  -- a listening-room piece without reference:
# render pages at 150 dpi, run homr on all pages in one call, join, drop minor parts, render audio.
MODEL=$1; WT=$2; F=$3; PDF=$4; R=/Users/yiduoke/Documents/homr/run; E=$R/eval_run1; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
mkdir -p $E/pages/$F; [ -f $E/pages/$F/page-1.png ] || [ -f $E/pages/$F/page-01.png ] || pdftoppm -r 150 -png "$PDF" $E/pages/$F/page
D=$E/$MODEL/$F; mkdir -p $D/pages
for p in $E/pages/$F/page-*.png; do ln -sf $p $D/pages/$(basename $p); done
( cd $WT && PYTHONPATH=$WT HOMR_FIXED_MARGIN=1 $PY $E/run_homr.py $D/page-xml $D/pages/page-*.png > $D/homr.log 2>&1 )
cd /Users/yiduoke/Documents/homr
TRUST=0; case "$MODEL" in run*) TRUST=1;; esac
HOMR_TRUST_PAGE_TIME=$TRUST HOMR_PAGES=$D/page-xml HOMR_OUT=$D/joined $PY $R/merge_pages.py > $D/merge.log 2>&1
$PY $R/drop_minor_parts.py $D/joined.musicxml $R/out/compare/$F/$F-$MODEL.musicxml > $D/drop.log 2>&1
$PY $R/render_score.py $R/out/compare/$F/$F-$MODEL.musicxml $D/$F.wav > /dev/null 2>&1
afconvert -f m4af -d aac -b 48000 $D/$F.wav $R/out/compare/$F/$F-$MODEL.m4a && rm $D/$F.wav && echo "$F done"
