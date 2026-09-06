#!/usr/bin/env bash
# Run check_snapshot_restore.py in the venv. Args pass through, e.g.: restore.sh v2_C_shift__t6 0 3 --replay 30
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
cd "$PROJ/lerobot"
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
.venv/bin/python "$SCRIPTS/analysis/check_snapshot_restore.py" "$@" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$|Svt|moov atom'
echo "EXIT=${PIPESTATUS[0]}"
