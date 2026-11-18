#!/bin/bash
# brace_pull.sh TAG...  : pull the outputs of brace_eval.py tags from vast-homr5 to the same laptop paths
R=/Users/yiduoke/Documents/homr/run
for tag in "$@"; do
ssh vast-homr5 "cd $R && ls out/testset/*/*-$tag.musicxml out/testset/*/res-scores-$tag.json out/testset/*/hand-sync-$tag.json out/testset/BRACE-$tag-settings.json 2>/dev/null; find eval_run1/testset/$tag -type f \( -name '*.log' -o -name 'wall_seconds.txt' -o -path '*page-xml/*' \)" 2>/dev/null | grep -v "^Welcome\|^Have" > /tmp/brace_files_$tag.txt
ssh vast-homr5 "cd $R && tar -c -T -" < /tmp/brace_files_$tag.txt 2>/dev/null | tar -x -C $R 2>&1 | grep -v xattr
echo "$tag: $(wc -l < /tmp/brace_files_$tag.txt) files"
done
