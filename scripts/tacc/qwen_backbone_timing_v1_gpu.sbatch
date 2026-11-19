#!/bin/bash
#SBATCH --job-name=qwen-backbone-timing
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:30:00
#SBATCH --no-requeue
#SBATCH --signal=B:USR1@120
#SBATCH --output=timing-%j.out
#SBATCH --error=timing-%j.err
set -euo pipefail
task_root=${QWEN_TIMING_ROOT:-/scratch/11388/al62479/ftl-qwen-backbone-timing-v1}
task_env=${QWEN_TIMING_ENV:-$task_root/venv}
cd "$task_root"
module load gcc/13.2.0 cuda/12.8
export PYTHONNOUSERSITE=1 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
export HF_HOME="$task_root/hf" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TRITON_CACHE_DIR="$task_root/triton" TMPDIR="$task_root/tmp"
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
nvidia-smi
test -f setup_ready.json
"$task_env/bin/python" qwen_backbone_timing.py verify --root "$task_root"
# Each model gets a fresh process. All temporary adapters belong to this probe.
trap 'test -z "${task_pid:-}" || kill -USR1 "$task_pid" 2>/dev/null || true' USR1
for task_model in reference candidate; do
  "$task_env/bin/python" -u qwen_backbone_timing.py gpu --root "$task_root" --model "$task_model" &
  task_pid=$!
  wait "$task_pid"
  task_pid=
done
"$task_env/bin/python" qwen_backbone_timing.py report --root "$task_root"
