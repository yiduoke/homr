#!/bin/bash
# collect_d30.sh: for every arm/seed, waits for the box run to finish (marker /root/logs/d30_<tag>.done), pulls the page XML and merges / scores it on the laptop
cd /Users/yiduoke/Documents/homr/run/staff_rel_realbrace
for arm in A B C; do for s in 0 1; do
  tag=relbrace2_${arm}_s${s}_gpu
  until ssh vast-homr5 "test -f /root/logs/d30_$tag.done" 2>/dev/null; do sleep 15; done
  scripts/pull_d30.sh $tag
  /Users/yiduoke/Documents/homr/.venv/bin/python scripts/merge_score_d30.py $tag
done; done
