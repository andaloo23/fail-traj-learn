#!/bin/bash
# One-episode generic-rubric experiment; retain the native model reasoning.
#SBATCH --job-name=flora-rubric-R001
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=flora-rubric-%j.out
#SBATCH --error=flora-rubric-%j.err
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
export HF_HUB_OFFLINE=1
export FLORA_MODEL_CACHE="$FLORA_ROOT/models"
export FLASHINFER_WORKSPACE_BASE="$FLORA_ROOT"
export TORCH_EXTENSIONS_DIR="$FLORA_ROOT/torch-extensions"
export TRITON_CACHE_DIR="$FLORA_ROOT/triton-cache"
export FORCE_QWENVL_VIDEO_READER=torchcodec
export TORCHCODEC_NUM_THREADS=1
export LD_LIBRARY_PATH="$FLORA_ROOT/ffmpeg-pyav19:$FLORA_ROOT/venv-rewarder/lib/python3.12/site-packages/av.libs:${LD_LIBRARY_PATH:-}"
export CUDA_VISIBLE_DEVICES=0,1
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export TMPDIR="$FLORA_ROOT/tmp/rubric-$SLURM_JOB_ID"
export PATH="$FLORA_ROOT/venv-rewarder/bin:$PATH"
mkdir -p "$TMPDIR"
py="$FLORA_ROOT/venv-rewarder/bin/python"
cd "$repo"
test -f "$FLORA_ROOT/rubric_decoder.json"
date -Iseconds
ninja --version
"$CXX" --version | head -n 1
nvidia-smi
"$py" - <<'PY'
import torch
assert torch.cuda.is_available() and torch.cuda.device_count() == 2
for i in range(2):
    p = torch.cuda.get_device_properties(i)
    print(i, p.name, p.total_memory, flush=True)
    assert p.total_memory >= 39*1024**3
from flashinfer.sampling import top_k_top_p_sampling_from_logits
sample = top_k_top_p_sampling_from_logits(torch.zeros((1, 32), device='cuda'), 5, 0.9)
torch.cuda.synchronize()
assert sample.shape == (1,)
print('FlashInfer CUDA sampling check passed', flush=True)
PY
"$py" scripts/tacc/run_flora.py --root "$FLORA_ROOT" --mode rubric \
    --jobs "$repo/outputs/flora_pilot_v1/rubric_generic_R001_v1.jsonl" \
    --tensor-parallel-size 2 --rubric-samples 1 \
    --rubric-max-new-tokens 8192 --rubric-max-model-len 32768 \
    --rubric-max-batched-tokens 8192 \
    --out "$repo/outputs/flora_rubric_generic_${SLURM_JOB_ID}"
echo "Generic rubric pilot completed: outputs/flora_rubric_generic_${SLURM_JOB_ID}"
