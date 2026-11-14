#!/bin/bash
# CPU-only validation gates the GPU allocation; no model inference here.
#SBATCH --job-name=flora-dev50-check
#SBATCH --account=IRI26045
#SBATCH --partition=development,normal
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:20:00
#SBATCH --output=flora-dev50-check-%j.out
#SBATCH --error=flora-dev50-check-%j.err
set -euo pipefail
ulimit -v unlimited
cd "${SLURM_SUBMIT_DIR:?}"
sha256sum --quiet -c SHA256SUMS
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
export FLORA_ROOT=/scratch/11388/al62479/ftl-flora
export HF_HOME="$FLORA_ROOT/hf" HF_HUB_OFFLINE=1
export OMP_NUM_THREADS=4 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
"$FLORA_ROOT/venv-reference/bin/python" scripts/tacc/preflight_flora_dev50.py \
    --root "$FLORA_ROOT" --inputs "$PWD" --out "$PWD/preflight_verified"
