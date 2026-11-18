#!/bin/bash
# Minimal pull of tag(s) from vast-homr5: outputs, scores, per-piece wall times; no per-page files (much faster than cloud2_pull.sh).
# usage: cloud2_pull_min.sh TAG [TAG...]
R=/Users/yiduoke/Documents/homr/run
for T in "$@"; do
  ssh vast-homr5 "cd $R && { find out/testset -maxdepth 2 \( -name '*-$T.musicxml' -o -name 'res-*-$T.json' -o -name 'note-scores-$T.json' \) ; ls out/testset/RES-$T* 2>/dev/null; find eval_run1/testset/$T -maxdepth 2 -name wall_seconds.txt; } 2>/dev/null | tar -c -T - 2>/dev/null" | tar -x -C $R
  echo "pulled $T: $(ls $R/out/testset/*/*-$T.musicxml 2>/dev/null | wc -l) musicxml"
done
