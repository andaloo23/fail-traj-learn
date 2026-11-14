#!/bin/bash
# Single evaluation; Slurm chooses the first eligible A100/H100 partition.
#SBATCH --job-name=flora-dev50
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-a100-dev,gpu-a100-small,gpu-h100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=02:00:00
#SBATCH --output=flora-dev50-%j.out
#SBATCH --error=flora-dev50-%j.err
set -euo pipefail
ulimit -v unlimited
cd "${SLURM_SUBMIT_DIR:?}"
sha256sum --quiet -c SHA256SUMS
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
source scripts/tacc/flora_cuda_env.sh
export FLORA_ROOT=/scratch/11388/al62479/ftl-flora
py="$FLORA_ROOT/venv-reference/bin/python"
export PATH="$FLORA_ROOT/venv-reference/bin:$FLORA_ROOT/venv-rewarder/bin:$PATH"
command -v ninja
ninja --version
export HF_HOME="$FLORA_ROOT/hf"
export HF_HUB_OFFLINE=1
export FLORA_MODEL_CACHE="$FLORA_ROOT/models"
export FLASHINFER_WORKSPACE_BASE="$FLORA_ROOT"
export TORCH_EXTENSIONS_DIR="$FLORA_ROOT/torch-extensions"
export TRITON_CACHE_DIR="$FLORA_ROOT/triton-cache"
export VLLM_CACHE_ROOT="$FLORA_ROOT/vllm-reference-cache"
export OMP_NUM_THREADS=8 TOKENIZERS_PARALLELISM=false PYTHONUNBUFFERED=1
export TMPDIR="$FLORA_ROOT/tmp/dev50-${SLURM_JOB_ID:?}"
mkdir -p "$TMPDIR" results
export CUDA_VISIBLE_DEVICES=0,1
gpu_name=$(nvidia-smi --query-gpu=name --format=csv,noheader -i 0)
if [[ "$gpu_name" == *H100* ]]; then
    export CUDA_VISIBLE_DEVICES=0
    batch_args=(--reference-defaults)
elif [[ "$gpu_name" == *A100* ]]; then
    batch_args=(--tensor-parallel-size 2 --max-num-seqs 1)
else
    printf 'Unsupported GPU: %s\n' "$gpu_name" >&2
    exit 1
fi
durable=/corral/utexas/IRI26024/oopsiedata/annotation/review_bundles/al62479/flora_development50_20261110_v2
mkdir -p "$durable"
archive_results() {
    rc=$?
    trap - EXIT
    cp -a results "$durable/" || true
    cp -a flora-dev50-"$SLURM_JOB_ID".* "$durable/" || true
    exit "$rc"
}
trap archive_results EXIT
"$py" - <<'PY'
import json
from pathlib import Path
r=json.loads(Path('preflight_verified/preflight.json').read_text())
assert r['passed'] is True and len(r['episodes']) == 50
import hashlib
for key, name in [('jobs_sha256', 'dense_jobs.jsonl'), ('inputs_sha256', 'inputs.json')]:
    assert hashlib.sha256(Path(name).read_bytes()).hexdigest() == r[key]
PY
nvidia-smi
"$py" scripts/tacc/check_flora_dev50_gpu.py --out "results/gpu_preflight_${SLURM_JOB_ID}.json"
"$py" scripts/tacc/run_flora.py --root "$FLORA_ROOT" --mode dense \
    --jobs "$PWD/dense_jobs.jsonl" "${batch_args[@]}" \
    --out "$PWD/results/dense_${SLURM_JOB_ID}"
"$py" scripts/tacc/report_flora_dev50.py --root "$FLORA_ROOT" \
    --inputs "$PWD" --run "$PWD/results/dense_${SLURM_JOB_ID}"
