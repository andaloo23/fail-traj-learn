#!/bin/bash
# Native dense segment labels for the three real-world OopsieData pilot episodes.
#SBATCH --job-name=flora-oopsie-dense
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=flora-oopsie-dense-%j.out
#SBATCH --error=flora-oopsie-dense-%j.err
set -euo pipefail
module load gcc/13.2.0 cuda/12.8
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
export CC="$(command -v gcc)"
export CXX="$(command -v g++)"
export NVCC_CCBIN="$CXX"
: "${SCRATCH:?}"
: "${SLURM_JOB_ID:?}"
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
export FLORA_ROOT=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export HF_HOME="$FLORA_ROOT/hf"
export HF_HUB_OFFLINE=1
export FLORA_MODEL_CACHE="$FLORA_ROOT/models"
export FLASHINFER_WORKSPACE_BASE="$FLORA_ROOT"
export TORCH_EXTENSIONS_DIR="$FLORA_ROOT/torch-extensions"
export TRITON_CACHE_DIR="$FLORA_ROOT/triton-cache"
export CUDA_VISIBLE_DEVICES=0,1
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PATH="$FLORA_ROOT/venv-rewarder/bin:$PATH"
export TMPDIR="$FLORA_ROOT/tmp/oopsie-dense-$SLURM_JOB_ID"
mkdir -p "$TMPDIR"
cd "$repo"
ninja --version
nvidia-smi
"$FLORA_ROOT/venv-rewarder/bin/python" scripts/tacc/run_flora.py \
    --root "$FLORA_ROOT" --mode dense \
    --jobs "$repo/outputs/oopsiedata_pilot_v1/dense_jobs.jsonl" \
    --tensor-parallel-size 2 \
    --out "$repo/outputs/flora_oopsie_dense_${SLURM_JOB_ID}"
