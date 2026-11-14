#!/bin/bash
#SBATCH --job-name=oopsie-full-setup
#SBATCH --account=IRI26045
#SBATCH --partition=vm-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-full-setup-%j.out
#SBATCH --error=oopsie-full-setup-%j.err
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
task_root=/scratch/11388/al62479/ftl-oopsie-full-v1
task_python=/scratch/11388/al62479/ftl-flora/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12
task_uv=/scratch/11388/al62479/ftl-flora/bootstrap-uv-py39/bin/uv
"$task_python" scripts/distill/oopsie_full_jobs.py check-approval
module load gcc/15.2.0 cuda/12.8
export UV_CACHE_DIR="$task_root/uv-cache" HF_HUB_CACHE="$task_root/hf/hub" TMPDIR="$task_root/tmp"
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
mkdir -p "$TMPDIR" "$HF_HUB_CACHE"
"$task_uv" venv --python "$task_python" "$task_root/venv"
task_py="$task_root/venv/bin/python"
"$task_uv" pip install --python "$task_py" --index-url https://download.pytorch.org/whl/cu128 torch==2.7.0 torchvision==0.22.0
"$task_uv" pip install --python "$task_py" -r scripts/distill/requirements-recipes.txt
"$task_py" scripts/distill/fetch_qwen_pinned.py
"$task_py" scripts/distill/probe_recipe_runtime.py > outputs/oopsie_distillation_full_v1/runtime_tacc_setup.jsonl
"$task_py" scripts/distill/qwen_recipe_runner.py audit --data outputs/oopsie_distillation_full_v1/evidence_c32_x8_v3
"$task_py" - <<'PY'
import json
from pathlib import Path
Path('outputs/oopsie_distillation_full_v1/tacc_setup_ready.json').write_text(json.dumps(dict(environment_ready=True,weights_ready=True,token_audit_ready=True))+'\n')
PY
