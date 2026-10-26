#!/bin/bash
# Compile the H100 sampler on a CPU compute node before resubmitting inference.
#SBATCH --job-name=flora-cuda-audit
#SBATCH --account=IRI26045
#SBATCH --partition=development
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --output=flora-cuda-audit-%j.out
#SBATCH --error=flora-cuda-audit-%j.err
set -euo pipefail
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
source "$repo/scripts/tacc/flora_cuda_env.sh"
export FLORA_ROOT=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export PATH="$FLORA_ROOT/venv-reference/bin:$FLORA_ROOT/venv-rewarder/bin:$PATH"
export FLASHINFER_WORKSPACE_BASE="$FLORA_ROOT"
export MAX_JOBS=8
export OMP_NUM_THREADS=1
export PYTHONUNBUFFERED=1
cd "$repo"
"$FLORA_ROOT/venv-reference/bin/python" scripts/tacc/check_flora_cuda.py --compile-only \
    --out "outputs/flora_cuda_compile_${SLURM_JOB_ID}.json"
