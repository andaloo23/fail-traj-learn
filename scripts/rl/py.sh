#!/usr/bin/env bash
# Run any script under scripts/rl in the LeRobot venv: py.sh <script.py|/abs/path.py> [args...]
# Logs to $PROJ/logs/rl_<script>.log (tee). CUDA stays visible: training and closed-loop eval need it.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
s=$1; shift
case "$s" in
  /*) path=$s ;;
  *) path=$SCRIPTS/rl/$s ;;
esac
mkdir -p "$PROJ/logs" "$PROJ/rl"
log=$PROJ/logs/rl_$(basename "$s" .py).log
cd "$PROJ/lerobot"
export PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false FTL_PROJ="$PROJ"
export MUJOCO_GL=${MUJOCO_GL:-egl} PYOPENGL_PLATFORM=${PYOPENGL_PLATFORM:-egl}
echo "== $(date -Is) $path $*" >> "$log"
# robosuite/LIBERO print the same banner from every worker process; drop it so the log stays readable.
NOISE='FutureWarning|warnings\.warn|robosuite|Creating LIBERO envs|Restricting to task_ids|using task orders|Built vec env|Local assets not found|Assets already downloaded|^[[:space:]]*$'
.venv/bin/python "$path" "$@" 2>&1 | grep --line-buffered -vE "$NOISE" | tee -a "$log"
rc=${PIPESTATUS[0]}
echo "EXIT=$rc" | tee -a "$log"
exit "$rc"
