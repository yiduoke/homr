#!/bin/bash
# usage: queue_reads.sh pdf1 pdf2 ... ; builds read inputs from pieces.py page lists, reads with the released model
export HOMR_FIXED_MARGIN=1 PYTHONPATH=/Users/yiduoke/Documents/homr/run/integration_wt HOMR_ORT_THREADS=2
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso
PY=/Users/yiduoke/Documents/homr/.venv/bin/python
mkdir -p work/reads work/reads_in
for pdf in "$@"; do
  pages=$($PY -c "
import sys; sys.path.insert(0,'scripts')
from pieces import P
s=sorted({p for c in P if c['pdf']=='$pdf' and c['pages'] for p in c['pages']}); print(','.join(map(str,s)))")
  $PY scripts/make_read_inputs.py $pdf $pages work/reads_in/$pdf.jsonl
  nice -n 12 $PY scripts/model_read.py work/reads_in/$pdf.jsonl work/reads/$pdf.jsonl > work/reads/$pdf.log 2>&1
  echo done $pdf
done
