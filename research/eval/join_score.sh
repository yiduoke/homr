#!/bin/bash
# usage: join_score.sh MODEL FOLDER  -- join per-page MusicXML, drop minor parts, score vs reference
MODEL=$1; F=$2; R=/Users/yiduoke/Documents/homr/run; E=$R/eval_run1; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
D=$E/$MODEL/$F; REF=$R/out/compare/$F/$F-reference.musicxml
# single-page piece: homr.main does not join, the page file stays next to the image
[ -d $D/page-xml ] || { mkdir -p $D/page-xml; cp $D/pages/page-*.musicxml $D/page-xml/; }
cd /Users/yiduoke/Documents/homr
TRUST=0; case "$MODEL" in run*) TRUST=1;; esac
HOMR_TRUST_PAGE_TIME=$TRUST HOMR_PAGES=$D/page-xml HOMR_OUT=$D/joined $PY $R/merge_pages.py > $D/merge.log 2>&1
$PY $R/drop_minor_parts.py $D/joined.musicxml $D/$F-$MODEL.musicxml > $D/drop.log 2>&1
cd $R/octave_wt && $PY -m validation.score_notes $REF "$MODEL=$D/$F-$MODEL.musicxml" --json $D/note-scores.json > $D/score.log 2>&1
