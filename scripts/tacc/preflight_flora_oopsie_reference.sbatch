#!/bin/bash
# CPU-only media/prompt audit before the reference GPU job is eligible to run.
#SBATCH --job-name=flora-reference-audit
#SBATCH --account=IRI26045
#SBATCH --partition=development
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:30:00
#SBATCH --output=flora-reference-audit-%j.out
#SBATCH --error=flora-reference-audit-%j.err
set -euo pipefail
unset PYTHONPATH PYTHONHOME
export PYTHONNOUSERSITE=1
export FLORA_ROOT=${FLORA_ROOT:-$SCRATCH/ftl-flora}
export HF_HOME="$FLORA_ROOT/hf"
export HF_HUB_OFFLINE=1
export FORCE_QWENVL_VIDEO_READER=decord
export OMP_NUM_THREADS=1
export TOKENIZERS_PARALLELISM=false
export PYTHONUNBUFFERED=1
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
cd "$repo"
hostname
ulimit -v
"$FLORA_ROOT/venv-reference/bin/python" scripts/tacc/audit_flora_reference.py \
    --root "$FLORA_ROOT" --inputs outputs/oopsiedata_reference_v2 \
    --published outputs/flora_oopsie_reference_audit_v1/published_code.json \
    --old-dense outputs/flora_oopsie_dense_3529899/dense.jsonl \
    --old-jobs outputs/oopsiedata_pilot_v1/dense_jobs.jsonl \
    --out outputs/flora_oopsie_reference_audit_v1/native_preflight
