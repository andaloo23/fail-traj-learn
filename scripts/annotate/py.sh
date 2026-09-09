#!/usr/bin/env bash
# Run any script under scripts/annotate in the LeRobot venv: py.sh <script.py> [args...]
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
s=$1; shift
cd "$PROJ/lerobot"
export PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
.venv/bin/python "$SCRIPTS/annotate/$s" "$@" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$'
echo "EXIT=${PIPESTATUS[0]}"
