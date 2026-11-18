#!/bin/bash
# usage: queue_reads.sh pdf1 pdf2 ... ; waits for the detection json of every page, builds read inputs from pieces2.py page lists, reads with the released model (CPU)
export HOMR_FIXED_MARGIN=1 PYTHONPATH=/Users/yiduoke/Documents/homr/run/integration_wt HOMR_ORT_THREADS=2
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2
PY=/Users/yiduoke/Documents/homr/.venv/bin/python
for pdf in "$@"; do
  pages=$($PY -c "
import sys; sys.path.insert(0,'scripts')
from pieces2 import P
s=sorted({p for c in P if c['pdf']=='$pdf' for p in c['pages']}); print(','.join(map(str,s)))")
  for p in $(echo $pages | tr ',' ' '); do while [ ! -f work/crops/$pdf/p-$(printf %02d $p).json ]; do sleep 5; done; done
  # pages without staffs (title pages) have an error json; make_read_inputs skips them
  $PY scripts/make_read_inputs.py $pdf $pages work/reads_in/$pdf.jsonl
  nice -n 12 $PY scripts/model_read.py work/reads_in/$pdf.jsonl work/reads/$pdf.jsonl > work/reads/$pdf.log 2>&1
  echo done $pdf
done
