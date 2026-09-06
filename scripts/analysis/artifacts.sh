#!/usr/bin/env bash
# Run predicate_artifacts.py in the venv. Args: dataset prefixes/names, e.g.: artifacts.sh pilot_C_object_shift v2_C_shift
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
cd "$PROJ/lerobot"
.venv/bin/python "$SCRIPTS/analysis/predicate_artifacts.py" "$@" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$'
echo "EXIT=${PIPESTATUS[0]}"
