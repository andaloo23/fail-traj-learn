#!/bin/bash
# Prepared for review only; submission requires the matching user approval.
#SBATCH --job-name=oopsie-qwen-setup
#SBATCH --account=IRI26045
#SBATCH --partition=vm-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-qwen-setup-%j.out
#SBATCH --error=oopsie-qwen-setup-%j.err
set -euo pipefail
task_repo=${SLURM_SUBMIT_DIR:?}
task_root=/scratch/11388/al62479/ftl-oopsie-recipes-v1
task_python=/scratch/11388/al62479/ftl-flora/python/cpython-3.12.15-linux-x86_64-gnu/bin/python3.12
task_uv=/scratch/11388/al62479/ftl-flora/bootstrap-uv-py39/bin/uv
cd "$task_repo"
"$task_python" - <<'PY'
import hashlib,json
from pathlib import Path
root=Path('outputs/oopsie_distillation_recipes_v1')
approval=json.loads((root/'submission_approval.json').read_text())
digest=hashlib.sha256((root/'submission_plan.json').read_bytes()).hexdigest()
if approval.get('approved') is not True or approval.get('plan_sha256')!=digest:
    raise SystemExit('User approval of this exact plan is required before setup')
PY
module load gcc/15.2.0 cuda/12.8
export UV_CACHE_DIR="$task_root/uv-cache"
export HF_HUB_CACHE="$task_root/hf/hub"
export TMPDIR="$task_root/tmp"
mkdir -p "$TMPDIR" "$HF_HUB_CACHE"
"$task_uv" venv --python "$task_python" "$task_root/venv"
task_py="$task_root/venv/bin/python"
"$task_uv" pip install --python "$task_py" --index-url https://download.pytorch.org/whl/cu128 torch==2.7.0 torchvision==0.22.0
"$task_uv" pip install --python "$task_py" -r scripts/distill/requirements-recipes.txt
"$task_py" scripts/distill/fetch_qwen_pinned.py
"$task_py" scripts/distill/probe_recipe_runtime.py > outputs/oopsie_distillation_recipes_v1/runtime_tacc_setup.jsonl
"$task_py" - <<'PY'
import json
from pathlib import Path
Path('outputs/oopsie_distillation_recipes_v1/tacc_setup_ready.json').write_text(json.dumps(dict(environment_ready=True,weights_ready=True,model='Qwen/Qwen2.5-VL-7B-Instruct',revision='cc594898137f460bfe9f0759e9844b3ce807cfb5'))+'\n')
PY
