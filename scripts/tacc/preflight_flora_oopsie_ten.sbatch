#!/bin/bash
# CPU-only native preprocessing audit; the GPU job depends on success.
#SBATCH --job-name=flora-oopsie-ten-audit
#SBATCH --account=IRI26045
#SBATCH --partition=development
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=01:00:00
#SBATCH --output=flora-oopsie-ten-audit-%j.out
#SBATCH --error=flora-oopsie-ten-audit-%j.err
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
cd "${FLORA_REPO:-$SLURM_SUBMIT_DIR}"
"$FLORA_ROOT/venv-reference/bin/python" scripts/tacc/audit_flora_reference.py \
    --root "$FLORA_ROOT" --inputs outputs/oopsiedata_ten_reference_v1 \
    --published outputs/flora_oopsie_ten_audit_v1/published_code.json \
    --out outputs/flora_oopsie_ten_audit_v1/native_preflight
