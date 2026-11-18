#!/bin/bash
# render every page of the 17 batch-2 PDFs at 150 dpi, grayscale PNG, to work/pages/<pdf stem>/p-NN.png (the PDFs are not modified)
cd /Users/yiduoke/Documents/homr/run/scan_pairs_virtuoso/batch2
for f in ~/Downloads/imslp_virtuoso_batch2/*.pdf; do
  s=$(basename "$f" .pdf); mkdir -p work/pages/$s
  [ -f work/pages/$s/.done ] && continue
  nice -n 10 pdftoppm -r 150 -gray -png "$f" work/pages/$s/p
  touch work/pages/$s/.done
done
echo render-done
