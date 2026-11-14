#!/bin/bash
# Run inside a compute allocation after loading a Python 3.12 / CUDA environment.
set -euo pipefail
component=${1:?Usage: bash scripts/tacc/setup_flora.sh rewarder|data-engine}
case "$component" in rewarder|data-engine) ;; *) exit 2 ;; esac
: "${SCRATCH:?Run on TACC, where SCRATCH is defined}"
runtime=${FLORA_ROOT:-$SCRATCH/ftl-flora}
bootstrap_python=${FLORA_BOOTSTRAP_PYTHON:-python3}
repo=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)
"$bootstrap_python" -c 'import sys; assert sys.version_info[:2] == (3,12), "Select Python 3.12 with FLORA_BOOTSTRAP_PYTHON"'
export HF_HOME=${HF_HOME:-$runtime/hf}
export PIP_CACHE_DIR=${PIP_CACHE_DIR:-$runtime/pip-cache}
mkdir -p "$runtime"
"$bootstrap_python" "$repo/scripts/tacc/fetch_flora.py" --root "$runtime" --component "$component"
venv="$runtime/venv-$component"
if [[ ! -d "$venv" ]]; then
    "$bootstrap_python" -m venv "$venv"
fi
py="$venv/bin/python"
"$py" -m pip install --upgrade pip
pip_indexes=()
if [[ -n "${FLORA_TORCH_INDEX_URL:-}" ]]; then
    pip_indexes+=(--extra-index-url "$FLORA_TORCH_INDEX_URL")
fi
if [[ "$component" == rewarder && -n "${FLORA_VLLM_WHEEL:-}" ]]; then
    "$py" -m pip install "$FLORA_VLLM_WHEEL" "${pip_indexes[@]}"
fi
if [[ "$component" == data-engine ]]; then
    "$py" -m pip install torch==2.11.0 torchvision==0.26.0 --index-url https://download.pytorch.org/whl/cu128
fi
requirements="$runtime/$component/batch_utils/requirements.txt"
if [[ "$component" == rewarder ]]; then
    # Dense/terminal use PyAV. Only the unused rubric path imports decord.
    # Its old wheel also fails pip's platform check on Lonestar6/Python 3.12.
    # Preserve upstream requirements and generate a list for the supported paths.
    requirements="$runtime/$component/requirements-terminal-dense.txt"
    "$py" - "$runtime/$component/batch_utils/requirements.txt" "$requirements" <<'PY'
from pathlib import Path
import sys
source, target = map(Path, sys.argv[1:])
target.write_text(''.join(line for line in source.read_text().splitlines(keepends=True)
                          if not line.startswith('decord==')))
PY
    "$py" -m pip uninstall -y decord
fi
"$py" -m pip install -r "$requirements" "${pip_indexes[@]}"
"$py" -m pip check
"$py" - <<'PY'
import os
import torch
print(torch.__version__, torch.version.cuda)
available = torch.cuda.is_available()
if os.environ.get('FLORA_SETUP_REQUIRE_CUDA', '1') == '1':
    assert available, 'CUDA unavailable'
if available:
    print(torch.cuda.get_device_name(0), torch.cuda.get_device_properties(0).total_memory)
else:
    print('Environment preparation on CPU; GPU validation remains pending.')
PY
"$py" -m pip freeze > "$runtime/$component/environment.freeze.txt"
"$py" "$repo/scripts/tacc/fetch_flora.py" --root "$runtime" --component "$component" --weights
echo "Environment and weights prepared: $venv"
