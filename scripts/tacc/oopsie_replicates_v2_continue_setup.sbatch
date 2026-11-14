#!/bin/bash
#SBATCH --job-name=oopsie-rep-v2-resume
#SBATCH --account=IRI26045
#SBATCH --partition=vm-small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=02:00:00
#SBATCH --no-requeue
#SBATCH --output=oopsie-rep-v2-resume-%j.out
#SBATCH --error=oopsie-rep-v2-resume-%j.err
set -euo pipefail
cd /scratch/11388/al62479/ftl-oopsie-full-v1/repo
module load gcc/15.2.0 cuda/12.8
task_root=/scratch/11388/al62479/ftl-oopsie-full-v1
export HF_HUB_CACHE="$task_root/hf/hub" HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8 PYTHONNOUSERSITE=1
"$task_root/venv-replicates-v2/bin/python" -u scripts/tacc/continue_tacc_setup_v2.py complete
