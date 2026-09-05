#!/usr/bin/env bash
# Run review_failures.py in the venv. Args are passed through, e.g.: review.sh pilot_C_object_shift --max 12 --video
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
cd "$PROJ/lerobot"
.venv/bin/python "$SCRIPTS/review_failures.py" "$@" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$'
echo "EXIT=${PIPESTATUS[0]}"
