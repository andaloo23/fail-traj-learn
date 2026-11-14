#!/bin/bash
#SBATCH --job-name=oopsie-rep-v2-packed
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=24
#SBATCH --array=0-2%3
#SBATCH --time=32:00:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-rep-v2-sft-%A_%a.out
#SBATCH --error=oopsie-rep-v2-sft-%A_%a.err
set -euo pipefail
cd /scratch/11388/al62479/ftl-oopsie-full-v1/repo
module load gcc/15.2.0 cuda/12.8
task_root=/scratch/11388/al62479/ftl-oopsie-full-v1
export HF_HUB_CACHE="$task_root/hf/hub" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8 PYTHONNOUSERSITE=1
nvidia-smi
task_py="$task_root/venv-replicates-v2/bin/python"
"$task_py" scripts/distill/tacc_recipe_replicates_v2.py check
# A full gpu-a100 node belongs to this job and contains three physical GPUs.
# Each process sees only its assigned device as cuda:0; no model shares a GPU.
mapfile -t task_gpu_devices < <(nvidia-smi --query-gpu=index --format=csv,noheader)
test "${#task_gpu_devices[@]}" -eq 3
case "${SLURM_ARRAY_TASK_ID:?}" in
  0) recipes=(base binary joint) ;;
  1) recipes=(categories_aux evidence_aux both_aux) ;;
  2) recipes=(binary_compute_control joint_then_binary failure_balanced) ;;
  *) exit 2 ;;
esac
task_log=outputs/oopsie_distillation_tacc_replicates_v2/logs
mkdir -p "$task_log"
task_pids=()
for task_slot in 0 1 2; do
  recipe=${recipes[$task_slot]}
  CUDA_VISIBLE_DEVICES="${task_gpu_devices[$task_slot]}" \
    "$task_py" -u scripts/distill/tacc_recipe_replicates_v2.py run --recipe "$recipe" \
      > "$task_log/${recipe}_${SLURM_JOB_ID}.out" \
      2> "$task_log/${recipe}_${SLURM_JOB_ID}.err" &
  task_pids+=("$!")
  printf 'Started %s on GPU %s, PID %s\n' "$recipe" "${task_gpu_devices[$task_slot]}" "${task_pids[$task_slot]}"
done
task_exit=0
for task_pid in "${task_pids[@]}"; do
  if wait "$task_pid"; then true; else task_exit=1; fi
done
exit "$task_exit"
