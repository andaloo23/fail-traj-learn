#!/usr/bin/env bash
# Run any analysis script in the LeRobot venv: py.sh <script.py under scripts/analysis> [args...]
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
s=$1; shift
cd "$PROJ/lerobot"
.venv/bin/python "$SCRIPTS/analysis/$s" "$@" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$'
echo "EXIT=${PIPESTATUS[0]}"
