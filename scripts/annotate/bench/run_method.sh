#!/usr/bin/env bash
# GPU launcher for the benchmark harness (bench.sh hides the GPU with CUDA_VISIBLE_DEVICES="" for the CPU scripts).
#   run_method.sh --method whole_p8 --set dev [--limit 3] [--dry-run]
# Logs the console to $PROJ/logs/bench_run_method.log; run_method.py itself appends per-episode lines to
# $PROJ/logs/bench_<method>.log.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
mkdir -p "$PROJ/logs" "$PROJ/bench/.hf_cache_gpu"
log=$PROJ/logs/bench_run_method.log
cd "$PROJ/lerobot"
export MUJOCO_GL=egl PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True FTL_PROJ="$PROJ"
# private datasets cache (bench.sh uses .hf_cache; concurrent loads of the same dataset corrupt a shared cache)
export HF_DATASETS_CACHE="$PROJ/bench/.hf_cache_gpu"
echo "== $(date -Is) run_method.py $*" >> "$log"
.venv/bin/python "$SCRIPTS/annotate/bench/run_method.py" "$@" 2>&1 | grep --line-buffered -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$' | tee -a "$log"
rc=${PIPESTATUS[0]}
echo "EXIT=$rc" | tee -a "$log"
exit "$rc"
