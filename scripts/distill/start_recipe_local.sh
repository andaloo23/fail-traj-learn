#!/bin/bash
set -euo pipefail
task_repo=/mnt/c/Users/LocalPC/dev/fail-traj-learn
task_runtime=/home/aliu/.venvs/ftl-oopsie-recipes-v1
task_base=/home/aliu/miniconda3/envs/ml/bin/python
cd "$task_repo"
if [[ ! -x "$task_runtime/bin/python" ]]; then
  "$task_base" -m venv --system-site-packages "$task_runtime"
fi
"$task_runtime/bin/python" -m pip install --disable-pip-version-check -r scripts/distill/requirements-recipes.txt
export HF_HUB_CACHE=/home/aliu/.cache/ftl-qwen-hub
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
"$task_runtime/bin/python" scripts/distill/probe_recipe_runtime.py > outputs/oopsie_distillation_recipes_v1/runtime_linux.jsonl
"$task_runtime/bin/python" -u scripts/distill/qwen_recipe_runner.py benchmark \
  > outputs/oopsie_distillation_recipes_v1/benchmark_linux.stdout.log \
  2> outputs/oopsie_distillation_recipes_v1/benchmark_linux.stderr.log
