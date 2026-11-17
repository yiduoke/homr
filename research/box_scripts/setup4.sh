#!/bin/bash
# New box: system tools and Python packages (only /workspace was copied).
exec > /workspace/logs/setup4.log 2>&1
set -x
apt-get update -qq && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq lilypond librsvg2-bin tmux
source /venv/main/bin/activate; cd /workspace/homr
uv pip install -e ".[cuda]" --group dev
uv pip install --no-deps x-transformers==2.16.1
python -c "import x_transformers, homr, torch; print(\"PY_OK\", torch.cuda.is_available())"
lilypond --version | head -1; which rsvg-convert musicxml2ly
echo SETUP_DONE
