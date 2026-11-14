#!/bin/bash
#SBATCH --job-name=oopsie-rep-v2-setup
#SBATCH --account=IRI26045
#SBATCH --partition=vm-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-rep-v2-setup-%j.out
#SBATCH --error=oopsie-rep-v2-setup-%j.err
set -euo pipefail
cd /scratch/11388/al62479/ftl-oopsie-full-v1/repo
task_root=/scratch/11388/al62479/ftl-oopsie-full-v1
task_python=/scratch/11388/al62479/ftl-flora/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12
task_uv=/scratch/11388/al62479/ftl-flora/bootstrap-uv-py39/bin/uv
"$task_python" scripts/distill/tacc_recipe_replicates_v2.py check
module load gcc/15.2.0 cuda/12.8
export UV_CACHE_DIR="$task_root/uv-cache" HF_HUB_CACHE="$task_root/hf/hub" TMPDIR="$task_root/tmp"
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8 PYTHONNOUSERSITE=1
mkdir -p "$TMPDIR" "$HF_HUB_CACHE"
test ! -e "$task_root/venv-replicates-v2"
"$task_uv" venv --python "$task_python" "$task_root/venv-replicates-v2"
task_py="$task_root/venv-replicates-v2/bin/python"
# Exact CUDA wheels, original recipe requirements, and an explicit NumPy pin
# are resolved together so a later dependency cannot upgrade NumPy again.
"$task_uv" pip install --python "$task_py" \
  --index-url https://download.pytorch.org/whl/cu128 \
  --extra-index-url https://pypi.org/simple --index-strategy unsafe-best-match \
  -r scripts/distill/requirements-tacc-replicates-v2.txt
"$task_py" scripts/distill/fetch_qwen_pinned.py
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
"$task_py" -u scripts/distill/tacc_recipe_replicates_v2.py setup
