#!/bin/bash
# Supply --account and --partition at submission; no system-specific queue is assumed.
#SBATCH --job-name=ftl-flora
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --time=01:00:00
#SBATCH --output=flora-%j.out
#SBATCH --error=flora-%j.err
set -euo pipefail
: "${SCRATCH:?}"
mode=${1:?Usage: sbatch ... flora.sbatch dense|terminal|caption JOBS NEW_OUTPUT_DIR}
jobs=${2:?Missing absolute jobs JSONL path}
out=${3:?Missing new absolute output path}
case "$mode" in
    dense|terminal) component=rewarder ;;
    caption) component=data-engine ;;
    *) echo "Unknown mode: $mode" >&2; exit 2 ;;
esac
runtime=${FLORA_ROOT:-$SCRATCH/ftl-flora}
repo=${FLORA_REPO:-$SLURM_SUBMIT_DIR}
# If setup required nondefault modules, provide a shell file with the same module loads.
if [[ -n "${FLORA_MODULES_FILE:-}" ]]; then source "$FLORA_MODULES_FILE"; fi
export HF_HOME=${HF_HOME:-$runtime/hf}
export FLORA_MODEL_CACHE="$runtime/models"
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=${OMP_NUM_THREADS:-8}
export PATH="$runtime/venv-$component/bin:$PATH"
ninja --version
nvidia-smi
"$runtime/venv-$component/bin/python" "$repo/scripts/tacc/run_flora.py" \
    --root "$runtime" --mode "$mode" --jobs "$jobs" --out "$out"
