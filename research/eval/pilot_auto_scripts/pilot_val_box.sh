#!/bin/bash
# Box 5 (vast-homr5) side of the pilot automation (D29): held-out read of the pilot validation passages with one model, on the GPU.
# usage: pilot_val_box.sh NAME     NAME = a model in run/models/NAME (pilot_*, run3_ctrl_s7, ...) or `released` (integration_wt, released ONNX)
# Five lists (pilot_val_eval.py, free generation per staff crop; pitch F1, pitch+rhythm F1, bars, exact):
#   val_scan_v2 / val_twin_render_v2 : the 72 v2 validation passages (Liszt TE3, Schubert D.899/2), scan and rendered twin
#   b2_scan / b2_scan_matched / b2_twin : the independent 145-crop extension (batch2_val_v2: Liszt S.145/2, Chopin Op.10/5, Beethoven Op.81a mvt 1 and 3);
#       the twin exists for the 134 crops that render (batch2_val_v2_twin.txt), b2_scan_matched = the scan crops of those 134
# Output: run/eval_run1/pilot_val/NAME/<key>.json. GPU path (fp16), HOMR_FORCE_CPU unset: compare only with other GPU reads.
R=/Users/yiduoke/Documents/homr/run; PY=/Users/yiduoke/Documents/homr/.venv/bin/python
NAME=$1; OUT=$R/eval_run1/pilot_val/$NAME; mkdir -p $OUT /root/logs; LOG=/root/logs/pilot_val_$NAME.log; : > $LOG
unset HOMR_FORCE_CPU HOMR_INPUT_SCALE HOMR_MODEL_NAME
if [ "$NAME" = released ]; then WT=$R/integration_wt; else
  WT=$R/res_wt; export HOMR_MODEL_NAME=$NAME
  for f in $R/models/$NAME/*$NAME*; do [ -e $WT/homr/transformer/$(basename $f) ] || ln -s $f $WT/homr/transformer/$(basename $f); done
  [ -e $WT/homr/transformer/encoder_$NAME.onnx ] || { echo "VAL FAILED: no ONNX for $NAME" | tee -a $LOG; echo VAL_EXIT=2 >> $LOG; exit 2; }
fi
cd $R; rc=0
S=scan_pairs_virtuoso
for spec in val_scan_v2:$S/lists/val_scan_v2.txt val_twin_v2:$S/lists/val_twin_render_v2.txt b2_scan:$S/batch2/lists/batch2_val_v2.txt \
            b2_scan_matched:$S/batch2/lists/batch2_val_v2_scan_matched.txt b2_twin:$S/batch2/lists/batch2_val_v2_twin.txt; do
  key=${spec%%:*}; lst=${spec#*:}
  echo "$(date -u +%FT%TZ) $NAME $key start" >> $LOG
  PYTHONPATH=$WT nice $PY eval_run1/pilot_val_eval.py $lst $OUT/$key.json --root $R >> $LOG 2>&1 || { echo "VAL FAILED $key" >> $LOG; rc=1; }
done
echo "$(date -u +%FT%TZ) $NAME val done rc=$rc" >> $LOG; echo VAL_EXIT=$rc >> $LOG
exit $rc
