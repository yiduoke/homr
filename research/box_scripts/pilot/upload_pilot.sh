#!/bin/bash
# Upload the pilot images, tokens, lists and scripts to the training box (vast-homr4). Run on the LAPTOP. Touches only /workspace/pilot (new directory, about 115 MB,
# the box has about 8.7 GB free); nothing else on the box is read or changed. NOT RUN YET. rsync is refused on the boxes: tar over ssh.
# usage: upload_pilot.sh [--dry-run]          (--dry-run prints the file count and size only)
set -e
cd /Users/yiduoke/Documents/homr/run
P=scan_pairs_virtuoso
FILES=$(mktemp)
# every image (scan and twin) and token file named in the four lists (relative to run/), de-duplicated
cat $P/lists/pilot_scan.txt $P/lists/pilot_twin_render.txt $P/lists/val_scan.txt $P/lists/val_twin_render.txt | tr ',' '\n' | sort -u | sed "s#^$P/##" > $FILES
wc -l < $FILES | xargs echo "files:"
(cd $P && cat $FILES | xargs du -ck | tail -1 | awk '{print "size: " $1/1024 " MB"}')
[ "$1" = "--dry-run" ] && exit 0
ssh vast-homr4 'mkdir -p /workspace/pilot/lists /workspace/pilot/mix /workspace/pilot/scripts /workspace/logs/pilot && df -h /workspace | tail -1'
# images (images/<pid>/..., twins/<pid>/...) and tokens (tokens/...) keep their relative paths under /workspace/pilot
(cd $P && COPYFILE_DISABLE=1 tar -cf - -T $FILES) | ssh vast-homr4 'tar -xf - -C /workspace/pilot'
# box-path lists (the lists/box/ versions carry /workspace/pilot/... paths), keyed by the names the scripts expect
(cd $P/lists/box && COPYFILE_DISABLE=1 tar -cf - pilot_scan.txt pilot_twin_render.txt val_scan.txt val_twin_render.txt) | ssh vast-homr4 'tar -xf - -C /workspace/pilot/lists'
(cd research_wt/research/box_scripts/pilot && COPYFILE_DISABLE=1 tar -cf - train_pilot.sh chain_pilot.sh build_pilot_mix.py pilot_val_eval.py) | ssh vast-homr4 'tar -xf - -C /workspace/pilot/scripts && chmod +x /workspace/pilot/scripts/*.sh'
# check: counts and that every path of the box lists exists
ssh vast-homr4 'cd /workspace/pilot && for f in lists/*.txt; do echo $f $(wc -l < $f); done; cut -d, -f1,2 lists/pilot_scan.txt lists/pilot_twin_render.txt lists/val_scan.txt lists/val_twin_render.txt | tr "," "\n" | sort -u | while read p; do [ -e "$p" ] || echo MISSING $p; done; du -sh /workspace/pilot; df -h /workspace | tail -1'
