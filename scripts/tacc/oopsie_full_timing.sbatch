#!/bin/bash
#SBATCH --job-name=oopsie-full-timing
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-full-timing-%j.out
#SBATCH --error=oopsie-full-timing-%j.err
set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?}"
module load gcc/15.2.0 cuda/12.8
task_root=/scratch/11388/al62479/ftl-oopsie-full-v1
export HF_HUB_CACHE="$task_root/hf/hub" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8
"$task_root/venv/bin/python" -u scripts/distill/oopsie_full_jobs.py verify-data
nvidia-smi
"$task_root/venv/bin/python" -u scripts/distill/oopsie_full_jobs.py timing
