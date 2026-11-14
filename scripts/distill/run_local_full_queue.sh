#!/bin/bash
set -euo pipefail
cd /mnt/c/Users/LocalPC/dev/fail-traj-learn
export HF_HUB_CACHE=/home/aliu/.cache/ftl-qwen-hub
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8 CUDA_VISIBLE_DEVICES=0
task_python=/home/aliu/.venvs/ftl-oopsie-recipes-v1/bin/python
"$task_python" scripts/distill/local_full_recipe_queue.py check
exec "$task_python" -u scripts/distill/local_full_recipe_queue.py run
