#!/usr/bin/env bash
# Run episode_progress.py in the venv. Args pass through, e.g.: progress.sh pilot_B_libero90_std --episodes
PROJ=/home/aliu/projects/fail-traj-learn
SCRIPTS=/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts
cd "$PROJ/lerobot"
.venv/bin/python "$SCRIPTS/episode_progress.py" "$@" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$'
echo "EXIT=${PIPESTATUS[0]}"
