#!/bin/bash
# usage: score_more.sh PIECE...   score run2s7 and 566 against the reference (three F1 levels)
R=/Users/yiduoke/Documents/homr/run; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
cd $R/octave_wt
for F in "$@"; do D=$R/out/testset/$F
  $PY -m validation.score_notes $D/$F-reference.musicxml run2s7=$D/$F-run2s7.musicxml 566=$D/$F-566.musicxml --json $D/note-scores.json > $D/score.log 2>&1 || echo "$F scoring failed"
done
