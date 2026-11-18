#!/bin/bash
# pipeline_arm2.sh TAG MODEL.onnx|shipped   (on vast-homr5, GPU path, no HOMR_FORCE_CPU): page XML of the three Schott test scans and of the Schott Mazeppa pages
# with the relation model MODEL (HOMR_STAFF_RELATION_MODEL; 'shipped' = no override). Merging (merger by staff role) and scoring are done on the laptop.
TAG=$1; MODEL=$2
R=/Users/yiduoke/Documents/homr/run; E=$R/eval_run1; WT=$R/rel_wt
unset HOMR_FORCE_CPU
[ "$MODEL" != shipped ] && export HOMR_STAFF_RELATION_MODEL=$MODEL
for piece in liszt-sonata liszt-te-5 liszt-te-10 liszt-te-4-schott; do
  if [ -d $E/testset/$TAG/$piece/page-xml ] && [ "${FORCE:-0}" != 1 ]; then continue; fi
  $E/run_testset.sh $TAG $WT $piece none 1 1
done
grep -c "Onnxruntime is not using GPU" $E/testset/$TAG/*/homr.log
