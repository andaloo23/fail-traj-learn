#!/bin/bash
#SBATCH --job-name=oopsie-full-sft
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --array=0-7%3
#SBATCH --time=24:00:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-full-sft-%A_%a.out
#SBATCH --error=oopsie-full-sft-%A_%a.err
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
module load gcc/15.2.0 cuda/12.8
task_root=/scratch/11388/al62479/ftl-oopsie-full-v1
export HF_HUB_CACHE="$task_root/hf/hub" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
recipes=(binary joint categories_aux evidence_aux both_aux binary_compute_control joint_then_binary failure_balanced)
recipe=${recipes[${SLURM_ARRAY_TASK_ID:?}]}
nvidia-smi
"$task_root/venv/bin/python" -u scripts/distill/oopsie_full_jobs.py run --recipe "$recipe"
