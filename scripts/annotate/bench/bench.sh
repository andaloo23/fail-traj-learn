#!/usr/bin/env bash
# Run a benchmark script in the LeRobot venv (WSL): bench.sh <script.py|/abs/path.py> [args...]
# Mirrors scripts/annotate/py.sh; logs to $PROJ/logs/bench_<script>.log (tee, so the console still shows output).
# CPU only (CUDA_VISIBLE_DEVICES=""), private HF datasets cache (other jobs loading the same datasets corrupt the
# shared cache's dataset_info.json while we read it).
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
s=$1; shift
case "$s" in
  /*) path=$s ;;
  *) path=$SCRIPTS/annotate/bench/$s ;;
esac
mkdir -p "$PROJ/logs" "$PROJ/bench/.hf_cache"
log=$PROJ/logs/bench_$(basename "$s" .py).log
cd "$PROJ/lerobot"
export PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false CUDA_VISIBLE_DEVICES="" FTL_PROJ="$PROJ"
export HF_DATASETS_CACHE="$PROJ/bench/.hf_cache"
echo "== $(date -Is) $path $*" >> "$log"
.venv/bin/python "$path" "$@" 2>&1 | grep --line-buffered -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$' | tee -a "$log"
rc=${PIPESTATUS[0]}
echo "EXIT=$rc" | tee -a "$log"
exit "$rc"
