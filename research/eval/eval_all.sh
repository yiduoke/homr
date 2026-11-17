#!/bin/bash
# One command for the whole real-scan test set: recognise every piece with TAG's code, score it against the
# references (with run2s7 and 566 for comparison) and write out/testset/SUMMARY-TAG.md.
# usage: eval_all.sh TAG WORKTREE [PIECE...]    e.g.  eval_all.sh layout1 /Users/yiduoke/Documents/homr/run/integration_wt
# Existing outputs are kept unless FORCE=1. Pieces are listed in testset_manifest.tsv. Run time: about 8 s a page on the
# laptop (about 330 pages). Needs the scan PDFs in run/scores/testset/ and, for Wanderer, the pre-rendered pages.
set -u
TAG=$1; WT=$2; shift 2
E=/Users/yiduoke/Documents/homr/run/eval_run1; R=/Users/yiduoke/Documents/homr/run; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
S=$R/scores/testset
while IFS=$'\t' read -r piece pdf first last; do
  case "$piece" in \#*|"") continue;; esac
  if [ $# -gt 0 ]; then case " $* " in *" $piece "*) ;; *) continue;; esac; fi
  D=$R/out/testset/$piece
  if [ "${FORCE:-0}" = 1 ] || [ ! -f $D/$piece-$TAG.musicxml ]; then
    $E/run_testset.sh $TAG $WT $piece $S/$pdf $first $last
  fi
  models="$TAG=$D/$piece-$TAG.musicxml"
  for m in run2s7 566; do [ "$m" != "$TAG" ] && [ -f $D/$piece-$m.musicxml ] && models="$models $m=$D/$piece-$m.musicxml"; done
  extra=""; case "$piece" in stravinsky-petrushka|stravinsky-petrushka-rendered) extra="--ignore-staff";; esac
  ( cd $WT && PYTHONPATH=$WT $PY -m validation.score_notes $D/$piece-reference.musicxml $models --json $D/note-scores-$TAG.json $extra > $D/score-$TAG.log 2>&1 ) || echo "$piece: scoring failed"
done < ${MANIFEST:-$E/testset_manifest.tsv}
$PY $E/make_summary.py $TAG $R/out/testset/SUMMARY-$TAG.md > /dev/null && echo "wrote out/testset/SUMMARY-$TAG.md"
