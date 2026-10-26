#!/bin/bash
# CPU compute job: install dependencies and download weights before GPU allocation.
#SBATCH --job-name=flora-setup
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=02:00:00
#SBATCH --output=flora-setup-%j.out
#SBATCH --error=flora-setup-%j.err
set -euo pipefail
: "${SCRATCH:?}"
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
export FLORA_ROOT=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export HF_HOME="$FLORA_ROOT/hf"
export UV_CACHE_DIR="$FLORA_ROOT/uv-cache"
export UV_PYTHON_INSTALL_DIR="$FLORA_ROOT/python"
export UV_PYTHON_BIN_DIR="$FLORA_ROOT/bin"
export PIP_CACHE_DIR="$FLORA_ROOT/pip-cache"
export TMPDIR="$FLORA_ROOT/tmp"
mkdir -p "$FLORA_ROOT" "$TMPDIR"
# Bootstrap while the login's Python 3.9 module and its shared libraries are
# still active. Switching to GCC first deactivates that Python module.
bootstrap="$FLORA_ROOT/bootstrap-uv-py39"
if [[ ! -x "$bootstrap/bin/uv" ]]; then
    python3 -m venv "$bootstrap"
    "$bootstrap/bin/python" -m pip install uv==0.13.4
fi
module load gcc/15.2.0 cuda/12.8
"$bootstrap/bin/uv" python install 3.12
export FLORA_BOOTSTRAP_PYTHON
FLORA_BOOTSTRAP_PYTHON=$("$bootstrap/bin/uv" python find --managed-python 3.12)
"$FLORA_BOOTSTRAP_PYTHON" --version
# This CUDA 12.9 wheel is published by vLLM and supports the host's glibc 2.28.
export FLORA_TORCH_INDEX_URL=https://download.pytorch.org/whl/cu129
export FLORA_VLLM_WHEEL='https://github.com/vllm-project/vllm/releases/download/v0.24.0/vllm-0.24.0%2Bcu129-cp38-abi3-manylinux_2_28_x86_64.whl#sha256=597949743f2a00c0539d9e2ff0f67b32c608a378e973f99e7529fd6fa9445f70'
export FLORA_SETUP_REQUIRE_CUDA=0
bash "$repo/scripts/tacc/setup_flora.sh" rewarder
"$FLORA_ROOT/venv-rewarder/bin/python" - "$FLORA_ROOT/setup_ready.json" <<'PY'
import json
from datetime import datetime, timezone
from pathlib import Path
import sys
Path(sys.argv[1]).write_text(json.dumps(dict(
    environment_prepared=True, weights_cached=True, gpu_validated=False,
    finished_utc=datetime.now(timezone.utc).isoformat(), python=sys.version), indent=2)+'\n')
PY
