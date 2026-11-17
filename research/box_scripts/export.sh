#!/bin/bash
# Export one training checkpoint to the ONNX files homr loads at inference time.
set -e
C=$1
source /venv/main/bin/activate
rm -rf /workspace/export; mkdir -p /workspace/export
cd /workspace/homr
git archive HEAD | tar -x -C /workspace/export
cd /workspace/export
export PYTHONPATH=/workspace/xt216:. CUDA_VISIBLE_DEVICES="" OMP_NUM_THREADS=2
python - <<PY
import torch
from safetensors.torch import load_file
from homr.transformer.configs import Config
import os; sd = load_file("$C" if "$C".endswith(".safetensors") else "/workspace/homr/$C/model.safetensors")
torch.save(sd, Config().filepaths.checkpoint)
print("wrote", Config().filepaths.checkpoint, len(sd))
PY
python -m training.onnx.main --tromr --overwrite
ls -la homr/transformer/*.onnx
