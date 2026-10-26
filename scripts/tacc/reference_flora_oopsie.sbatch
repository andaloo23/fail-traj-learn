#!/bin/bash
# Reference batch defaults: dense on one H100; rubric on two H100s.
# Submit only after audit_flora_reference.py has passed on these exact inputs.
# Whole-node rate: 6 SU/hour; four-hour upper bound: 24 SU.
#SBATCH --job-name=flora-oopsie-reference
#SBATCH --account=IRI26045
#SBATCH --partition=gpu-h100
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=16
#SBATCH --time=04:00:00
#SBATCH --output=flora-oopsie-reference-%j.out
#SBATCH --error=flora-oopsie-reference-%j.err
set -euo pipefail
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
: "${SCRATCH:?}" "${SLURM_JOB_ID:?}"
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
source "$repo/scripts/tacc/flora_cuda_env.sh"
export FLORA_ROOT=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export FLORA_INPUTS_RELATIVE=${FLORA_INPUTS_RELATIVE:-outputs/oopsiedata_reference_v2}
export FLORA_AUDIT_RELATIVE=${FLORA_AUDIT_RELATIVE:-outputs/flora_oopsie_reference_audit_v1}
export FLORA_RESULT_TAG=${FLORA_RESULT_TAG:-flora_oopsie_reference}
export HF_HOME="$FLORA_ROOT/hf"
export HF_HUB_OFFLINE=1
export FORCE_QWENVL_VIDEO_READER=decord
export FLASHINFER_WORKSPACE_BASE="$FLORA_ROOT"
export TORCH_EXTENSIONS_DIR="$FLORA_ROOT/torch-extensions"
export TRITON_CACHE_DIR="$FLORA_ROOT/triton-cache"
export VLLM_CACHE_ROOT="$FLORA_ROOT/vllm-reference-cache"
export OMP_NUM_THREADS=8
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
export PATH="$FLORA_ROOT/venv-reference/bin:$FLORA_ROOT/venv-rewarder/bin:$PATH"
export TMPDIR="$FLORA_ROOT/tmp/oopsie-reference-$SLURM_JOB_ID"
mkdir -p "$TMPDIR"
py="$FLORA_ROOT/venv-reference/bin/python"
cd "$repo"
date -Iseconds
nvidia-smi
CUDA_VISIBLE_DEVICES=0 "$py" scripts/tacc/check_flora_cuda.py \
    --out "outputs/${FLORA_RESULT_TAG}_cuda_preflight_${SLURM_JOB_ID}.json"
"$py" -u - <<'PY'
import hashlib,json,os
from pathlib import Path
import torch
root=Path(os.environ['FLORA_ROOT'])
inputs=Path(os.environ['FLORA_INPUTS_RELATIVE'])
audit_dir=Path(os.environ['FLORA_AUDIT_RELATIVE'])
audit=json.loads((audit_dir/'native_preflight/preflight.json').read_text())
assert audit['media_and_prompt_preflight_passed'] and audit['native_code_verified']
for name,expected in audit['inputs_sha256'].items():
    assert hashlib.file_digest((inputs/name).open('rb'),'sha256').hexdigest()==expected,name
assert torch.cuda.is_available() and torch.cuda.device_count() >= 2
devices=[]
for i in range(2):
    p=torch.cuda.get_device_properties(i)
    assert 'H100' in p.name and p.total_memory >= 79*1024**3
    devices.append(dict(index=i,name=p.name,bytes=p.total_memory))
published=json.loads((audit_dir/'hub_metadata.json').read_text())
snapshot=root/'hf/hub/models--nvidia--Flora-Rewarder/snapshots'/published['sha']
checks=[]
for item in published['siblings']:
    if not item['rfilename'].endswith('.safetensors'):continue
    path=snapshot/item['rfilename']
    actual=hashlib.file_digest(path.open('rb'),'sha256').hexdigest()
    assert actual==item['lfs']['sha256'],item['rfilename']
    checks.append(dict(name=item['rfilename'],sha256=actual))
    print('Verified weight:',item['rfilename'],flush=True)
assert len(checks)==11
out=Path('outputs')/(os.environ['FLORA_RESULT_TAG']+'_hardware_'+os.environ['SLURM_JOB_ID']+'.json')
out.write_text(json.dumps(dict(gpus=devices,torch=torch.__version__,cuda=torch.version.cuda,
    weights=checks,inputs_sha256=audit['inputs_sha256'],
    validated_against_pinned_batch_defaults=True),indent=2)+'\n')
PY
CUDA_VISIBLE_DEVICES=0 "$py" scripts/tacc/run_flora.py \
    --root "$FLORA_ROOT" --mode dense --reference-defaults \
    --jobs "$repo/$FLORA_INPUTS_RELATIVE/dense_jobs.jsonl" \
    --out "$repo/outputs/${FLORA_RESULT_TAG}_dense_${SLURM_JOB_ID}"
CUDA_VISIBLE_DEVICES=0,1 "$py" scripts/tacc/run_flora.py \
    --root "$FLORA_ROOT" --mode rubric --reference-defaults \
    --jobs "$repo/$FLORA_INPUTS_RELATIVE/rubric_jobs.jsonl" \
    --out "$repo/outputs/${FLORA_RESULT_TAG}_rubric_${SLURM_JOB_ID}"
date -Iseconds
