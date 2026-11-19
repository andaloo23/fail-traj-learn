#!/bin/bash
#SBATCH --job-name=qwen-backbone-setup
#SBATCH --account=IRI26045
#SBATCH --partition=vm-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --output=setup-%j.out
#SBATCH --error=setup-%j.err
set -euo pipefail
task_root=${QWEN_TIMING_ROOT:-/scratch/11388/al62479/ftl-qwen-backbone-timing-v1}
task_env=${QWEN_TIMING_ENV:-$task_root/venv}
cd "$task_root"
module load gcc/13.2.0 cuda/12.8
export PYTHONNOUSERSITE=1 TOKENIZERS_PARALLELISM=false
export UV_CACHE_DIR="$task_root/uv-cache" HF_HOME="$task_root/hf"
export TORCH_CUDA_ARCH_LIST=8.0 MAX_JOBS=8
export TMPDIR="$task_root/tmp"
mkdir -p "$TMPDIR"
task_uv=/scratch/11388/al62479/ftl-flora/bootstrap-uv-py39/bin/uv
task_python=/scratch/11388/al62479/ftl-flora/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12
test ! -e setup_ready.json
"$task_python" qwen_backbone_timing.py verify --root "$task_root"
if [[ ! -x "$task_env/bin/python" ]]; then
"$task_uv" venv --python "$task_python" "$task_env"
"$task_uv" pip install --python "$task_env/bin/python" \
  --index-url https://download.pytorch.org/whl/cu128 \
  torch==2.11.0+cu128 torchvision==0.26.0+cu128
"$task_uv" pip install --python "$task_env/bin/python" -r requirements-backbone-timing-v1.txt
"$task_uv" pip install --python "$task_env/bin/python" --no-build-isolation --no-deps causal-conv1d==1.7.0
fi
"$task_env/bin/python" -u qwen_backbone_timing.py setup --root "$task_root"
