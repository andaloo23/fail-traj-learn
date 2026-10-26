#!/bin/bash
# Real-world OopsieData only: three episodes, generic rubric with explanations.
# Submit from a fresh workspace containing scripts/tacc and the staged pilot.
#SBATCH --job-name=flora-oopsie-rubric
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-dev
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=flora-oopsie-%j.out
#SBATCH --error=flora-oopsie-%j.err
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
export FORCE_QWENVL_VIDEO_READER=torchcodec
export TORCHCODEC_NUM_THREADS=1
export LD_LIBRARY_PATH="$FLORA_ROOT/ffmpeg-pyav19:$FLORA_ROOT/venv-rewarder/lib/python3.12/site-packages/av.libs:${LD_LIBRARY_PATH:-}"
export CUDA_VISIBLE_DEVICES=0,1
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export TMPDIR="$FLORA_ROOT/tmp/oopsie-$SLURM_JOB_ID"
export PATH="$FLORA_ROOT/venv-rewarder/bin:$PATH"
mkdir -p "$TMPDIR"
py="$FLORA_ROOT/venv-rewarder/bin/python"
cd "$repo"
test -f "$FLORA_ROOT/rubric_decoder.json"
test -f outputs/oopsiedata_pilot_v1/rubric_jobs.jsonl
date -Iseconds
ninja --version
nvidia-smi
"$py" - <<'PY'
import json
from pathlib import Path
import torch
provenance = json.loads(Path('outputs/oopsiedata_pilot_v1/provenance.json').read_text())
assert provenance['repo'] == 'OopsieData-Submissions/oopsiedata-v0.1'
assert provenance['revision'] == 'da4b16512b77f7324296a66da7c0067a40539895'
assert len(provenance['episodes']) == 3
assert provenance['source_annotations_used_as_model_input'] is False
assert torch.cuda.is_available() and torch.cuda.device_count() == 2
for i in range(2):
    p = torch.cuda.get_device_properties(i)
    print(i, p.name, p.total_memory, flush=True)
    assert p.total_memory >= 39*1024**3
from flashinfer.sampling import top_k_top_p_sampling_from_logits
sample = top_k_top_p_sampling_from_logits(torch.zeros((1, 32), device='cuda'), 5, 0.9)
torch.cuda.synchronize()
assert sample.shape == (1,)
PY
"$py" scripts/tacc/run_flora.py --root "$FLORA_ROOT" --mode rubric \
    --jobs "$repo/outputs/oopsiedata_pilot_v1/rubric_jobs.jsonl" \
    --tensor-parallel-size 2 --rubric-samples 1 \
    --rubric-max-new-tokens 8192 --rubric-max-model-len 32768 \
    --rubric-max-batched-tokens 8192 \
    --out "$repo/outputs/flora_oopsie_rubric_${SLURM_JOB_ID}"
