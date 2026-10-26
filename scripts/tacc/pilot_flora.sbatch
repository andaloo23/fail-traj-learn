#!/bin/bash
# Submit with --dependency=afterok:SETUP_JOB and the allocated GPU partition.
#SBATCH --job-name=flora-libero
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --output=flora-pilot-%j.out
#SBATCH --error=flora-pilot-%j.err
set -euo pipefail
module load gcc/13.2.0 cuda/12.8
export CC="$(command -v gcc)"
export CXX="$(command -v g++)"
export NVCC_CCBIN="$CXX"
: "${SCRATCH:?}"
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
export FLORA_ROOT=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export HF_HOME="$FLORA_ROOT/hf"
export FLORA_MODEL_CACHE="$FLORA_ROOT/models"
export FLASHINFER_WORKSPACE_BASE="$FLORA_ROOT"
export TORCH_EXTENSIONS_DIR="$FLORA_ROOT/torch-extensions"
export TRITON_CACHE_DIR="$FLORA_ROOT/triton-cache"
export CUDA_VISIBLE_DEVICES=0
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export TMPDIR="$FLORA_ROOT/tmp"
mkdir -p "$TMPDIR"
py="$FLORA_ROOT/venv-rewarder/bin/python"
export PATH="$FLORA_ROOT/venv-rewarder/bin:$PATH"
ninja --version
"$CXX" --version | head -n 1
cd "$repo"
nvidia-smi
"$py" - <<'PY'
import torch
assert torch.cuda.is_available(), 'CUDA unavailable on the allocated node'
print(torch.__version__, torch.version.cuda, torch.cuda.get_device_name(0), flush=True)
assert torch.cuda.get_device_properties(0).total_memory >= 75*1024**3, 'Use an 80 GB GPU for this pilot'
from flashinfer.sampling import top_k_top_p_sampling_from_logits
sample = top_k_top_p_sampling_from_logits(torch.zeros((1, 32), device='cuda'), 5, 0.9)
torch.cuda.synchronize()
assert sample.shape == (1,) and 0 <= sample.item() < 32
print('FlashInfer CUDA sampling compilation and execution passed', flush=True)
PY
jobs="$repo/outputs/flora_pilot_v1/reward_jobs.jsonl"
smoke_jobs="$repo/outputs/flora_pilot_v1/reward_smoke_jobs_${SLURM_JOB_ID}.jsonl"
"$py" - "$jobs" "$smoke_jobs" <<'PY'
from pathlib import Path
import sys
source, target = map(Path, sys.argv[1:])
with target.open('x') as stream:
    stream.write(next(line for line in source.read_text().splitlines() if line.strip())+'\n')
PY
"$py" scripts/tacc/run_flora.py --root "$FLORA_ROOT" --mode dense --jobs "$smoke_jobs" \
    --out "$repo/outputs/flora_dense_smoke_${SLURM_JOB_ID}"
"$py" scripts/tacc/run_flora.py --root "$FLORA_ROOT" --mode dense --jobs "$jobs" \
    --out "$repo/outputs/flora_dense_pilot_${SLURM_JOB_ID}"
echo "Validated dense labeling completed: outputs/flora_dense_pilot_${SLURM_JOB_ID}"
