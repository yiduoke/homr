#!/bin/bash
# Box 4 (vast-homr4) side of the pilot automation (D29): export one trained pilot model to ONNX WITHOUT disturbing the next training run.
# usage: pilot_export.sh NAME        e.g. NAME=pilot_CTRL_RENDER_s7   (RES=1 models: 256x1280, code = git HEAD of /workspace/homr_acc, the run3 recipe of /workspace/export_run.sh)
#   env PTH_OVERRIDE=<file.pth>  dry run: export that checkpoint instead of the one of NAME (the dry run uses the run3_ctrl_s7 weights)
# CPU only (CUDA_VISIBLE_DEVICES=""), nice 10, idle I/O class, 2 threads; work dir /workspace/export_NAME (removed at the end, the weights are only symlinked);
# result /workspace/onnx/NAME/{encoder,decoder}_NAME{,_fp16}.onnx; log /workspace/logs/pilot_auto/export_NAME.log whose last line is EXPORT_EXIT=<code>.
# Never touches /workspace/homr_acc, the training checkpoints, the tmux session `pilot` or any training process. No pkill, nothing is killed.
NAME=$1; LOGD=/workspace/logs/pilot_auto; mkdir -p $LOGD; LOG=$LOGD/export_$NAME.log
exec > $LOG 2>&1
fail() { echo "EXPORT FAILED: $*"; echo "EXPORT_EXIT=${2:-1}"; exit ${2:-1}; }
echo "$(date -u +%FT%TZ) export $NAME start"
PTH=${PTH_OVERRIDE:-$(ls /workspace/homr_acc/training/architecture/transformer/pytorch_model_${NAME}_*.pth 2>/dev/null | tail -1)}
[ -n "$PTH" ] && [ -s "$PTH" ] || fail "no weights pytorch_model_${NAME}_*.pth" 3
avail=$(df --output=avail -BM /workspace | tail -1 | tr -dc 0-9)
[ "$avail" -gt 1500 ] || fail "only ${avail} MB free on /workspace (need 1500; the training run needs its checkpoints)" 4
echo "weights $PTH ($(stat -c %s $PTH) bytes), free ${avail} MB"
source /venv/main/bin/activate
D=/workspace/export_$NAME; rm -rf $D; mkdir -p $D
(cd /workspace/homr_acc && git archive HEAD) | tar -x -C $D || fail "git archive" 5
cd $D
export PYTHONPATH=/workspace/xt216:. CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2
nice -n 10 python -c "
import os
from homr.transformer.configs import Config
c = Config().filepaths.checkpoint
os.makedirs(os.path.dirname(c), exist_ok=True)
os.symlink('$PTH', c); print('checkpoint link', c)" || fail "checkpoint link" 6
ionice -c3 nice -n 10 python -m training.onnx.main --tromr --overwrite || fail "onnx export" 7
mkdir -p /workspace/onnx/$NAME
for f in homr/transformer/encoder_*.onnx homr/transformer/decoder_*.onnx; do
  b=$(basename $f); n=$(echo $b | sed -E "s/pytorch_model_[^_.]+-[0-9a-f]+/$NAME/"); cp $f /workspace/onnx/$NAME/$n
done
ls -l /workspace/onnx/$NAME
# the same architecture as run3_ctrl_s7: the four files must have exactly its sizes
for f in encoder_run3_ctrl_s7.onnx encoder_run3_ctrl_s7_fp16.onnx decoder_run3_ctrl_s7.onnx decoder_run3_ctrl_s7_fp16.onnx; do
  g=$(echo $f | sed "s/run3_ctrl_s7/$NAME/"); a=$(stat -c %s /workspace/onnx/run3_ctrl_s7/$f); b=$(stat -c %s /workspace/onnx/$NAME/$g 2>/dev/null || echo 0)
  [ "$a" = "$b" ] || fail "size of $g is $b, run3_ctrl_s7 has $a" 8
done
cd /workspace; rm -rf $D
echo "$(date -u +%FT%TZ) export $NAME ok"
echo EXPORT_EXIT=0
