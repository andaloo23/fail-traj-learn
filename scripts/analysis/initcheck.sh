#!/usr/bin/env bash
# Run init_state_check.py in the venv. Args: anchor prefix, then shifted prefixes. e.g. initcheck.sh full_anchor full_shift8 full_shift12
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
cd "$PROJ/lerobot"
.venv/bin/python "$SCRIPTS/analysis/init_state_check.py" "$@" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$'
echo "EXIT=${PIPESTATUS[0]}"
