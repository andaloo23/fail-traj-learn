#!/bin/bash
# Six independent supervised comparisons; two concurrent virtual GPU nodes.
# 6 jobs x 2 hours x 1.5 SU/hour = 18 SU maximum.
# Prepared only: do not submit without matching user approval and setup dependency.
#SBATCH --job-name=oopsie-qwen-recipes
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --array=0-5%2
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-qwen-%A_%a.out
#SBATCH --error=oopsie-qwen-%A_%a.err
set -euo pipefail
task_repo=${SLURM_SUBMIT_DIR:?}
task_root=/scratch/11388/al62479/ftl-oopsie-recipes-v1
task_py="$task_root/venv/bin/python"
cd "$task_repo"
test -f outputs/oopsie_distillation_recipes_v1/tacc_setup_ready.json
module load gcc/15.2.0 cuda/12.8
export HF_HUB_CACHE="$task_root/hf/hub"
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
export CUDA_VISIBLE_DEVICES=0
recipes=(joint categories_aux evidence_aux both_aux binary_compute_control joint_then_binary)
recipe=${recipes[$SLURM_ARRAY_TASK_ID]}
"$task_py" scripts/distill/recipe_job_plan.py check-approval
nvidia-smi
"$task_py" -u scripts/distill/recipe_job_plan.py run-arm --recipe "$recipe"
