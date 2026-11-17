#!/bin/bash
# Re-merge saved page outputs of the three Schott Liszt scans with the current merge_pages.py (simultaneous
# same-name parts kept apart and lined up per page). usage: remerge_after_merger.sh TAG   (e.g. layout1)
# Writes testset/TAG_am/<piece>/joined.* and out/testset/<piece>/<piece>-TAG_am.musicxml. No inference.
TAG=$1; R=/Users/yiduoke/Documents/homr/run; E=$R/eval_run1; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
cd /Users/yiduoke/Documents/homr
for F in liszt-sonata liszt-te-5 liszt-te-10; do
  D=$E/testset/${TAG}_am/$F; mkdir -p $D
  [ -d $E/testset/$TAG/$F/page-xml ] || continue
  HOMR_TRUST_PAGE_TIME=1 HOMR_PAGES=$E/testset/$TAG/$F/page-xml HOMR_OUT=$D/joined $PY $R/merge_pages.py > $D/merge.log 2>&1
  $PY $R/drop_minor_parts.py $D/joined.musicxml $R/out/testset/$F/$F-${TAG}_am.musicxml > $D/drop.log 2>&1
  echo "$TAG $F: $(grep -o 'padded [0-9]* lost bars[^,]*' $D/merge.log) $(tail -1 $D/merge.log)"
done
