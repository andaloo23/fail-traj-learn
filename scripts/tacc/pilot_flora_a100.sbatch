#!/bin/bash
# Full A100 development node; two GPUs shard the unchanged BF16 Rewarder.
#SBATCH --job-name=flora-libero-a100
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=flora-a100-%j.out
#SBATCH --error=flora-a100-%j.err
set -euo pipefail
module load gcc/13.2.0 cuda/12.8
export CC="$(command -v gcc)"
export CXX="$(command -v g++)"
export NVCC_CCBIN="$CXX"
: "${SCRATCH:?}"
: "${SLURM_JOB_ID:?}"
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
export FLORA_ROOT=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export HF_HOME="$FLORA_ROOT/hf"
export FLORA_MODEL_CACHE="$FLORA_ROOT/models"
export FLASHINFER_WORKSPACE_BASE="$FLORA_ROOT"
export TORCH_EXTENSIONS_DIR="$FLORA_ROOT/torch-extensions"
export TRITON_CACHE_DIR="$FLORA_ROOT/triton-cache"
export CUDA_VISIBLE_DEVICES=0,1
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export TMPDIR="$FLORA_ROOT/tmp/a100-$SLURM_JOB_ID"
mkdir -p "$TMPDIR"
py="$FLORA_ROOT/venv-rewarder/bin/python"
export PATH="$FLORA_ROOT/venv-rewarder/bin:$PATH"
ninja --version
"$CXX" --version | head -n 1
cd "$repo"
date -Iseconds
nvidia-smi
"$py" - <<'PY'
import torch
assert torch.cuda.is_available(), 'CUDA unavailable on the allocated node'
assert torch.cuda.device_count() == 2, 'Expose two GPUs for tensor parallelism'
print(torch.__version__, torch.version.cuda, flush=True)
for index in range(2):
    properties = torch.cuda.get_device_properties(index)
    print(index, properties.name, properties.total_memory, flush=True)
    assert properties.total_memory >= 39*1024**3, 'Use two 40 GB GPUs for this pilot'
    assert torch.cuda.is_bf16_supported(), 'This pilot preserves upstream BF16 inference'
# Exercise the kernel that failed on previous attempts before loading 52 GB of weights.
from flashinfer.sampling import top_k_top_p_sampling_from_logits
sample = top_k_top_p_sampling_from_logits(torch.zeros((1, 32), device='cuda'), 5, 0.9)
torch.cuda.synchronize()
assert sample.shape == (1,) and 0 <= sample.item() < 32
print('FlashInfer CUDA sampling compilation and execution passed', flush=True)
PY
jobs="$repo/outputs/flora_pilot_v1/reward_jobs.jsonl"
smoke_jobs="$repo/outputs/flora_pilot_v1/reward_smoke_jobs_a100_${SLURM_JOB_ID}.jsonl"
"$py" - "$jobs" "$smoke_jobs" <<'PY'
from pathlib import Path
import sys
source, target = map(Path, sys.argv[1:])
with target.open('x') as stream:
    stream.write(next(line for line in source.read_text().splitlines() if line.strip())+'\n')
PY
"$py" scripts/tacc/run_flora.py --root "$FLORA_ROOT" --mode dense --jobs "$smoke_jobs" \
    --tensor-parallel-size 2 --out "$repo/outputs/flora_dense_smoke_a100_${SLURM_JOB_ID}"
"$py" scripts/tacc/run_flora.py --root "$FLORA_ROOT" --mode dense --jobs "$jobs" \
    --tensor-parallel-size 2 --out "$repo/outputs/flora_dense_pilot_a100_${SLURM_JOB_ID}"
echo "Validated dense labeling completed: outputs/flora_dense_pilot_a100_${SLURM_JOB_ID}"
