#!/bin/bash
# render_pages.sh EDITION PDF PAGES...   renders pdf pages at 150 dpi (pages wider than 1000 pt, i.e. scans stored at 600 dpi
# with a huge page box, are scaled to 1415 px width) into pages/EDITION/page-NNN.png (like run_testset.sh)
cd "$(dirname "$0")"
ed=$1; pdf=$2; shift 2
mkdir -p pages/$ed
w=$(pdfinfo "$pdf" 2>/dev/null | awk '/Page size/{print $3}')
dpi=$(python3 -c "w=float('$w'); print(150 if w<=1000 else round(1415/w*72,3))")
for p in "$@"; do
  f=$(printf "pages/%s/page-%03d.png" $ed $p)
  [ -f $f ] || pdftoppm -r $dpi -png -f $p -l $p -singlefile "$pdf" ${f%.png}
done
