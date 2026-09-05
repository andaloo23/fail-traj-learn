#!/usr/bin/env bash
# Test / launch the interactive LIBERO viewer via WSLg. Args: suite task_id seconds
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
SUITE=${1:-libero_object}
TID=${2:-0}
SECS=${3:-12}
cd "$PROJ/lerobot"
echo "DISPLAY=$DISPLAY WAYLAND_DISPLAY=$WAYLAND_DISPLAY XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR"
timeout 180 .venv/bin/python "$SCRIPTS/tools/view_libero.py" "$SUITE" "$TID" "$SECS" 2>&1 \
  | grep -vE 'robosuite WARNING|macro|OpenGL_accelerate|Fetching|^[[:space:]]*$' | tail -20
echo "EXIT=${PIPESTATUS[0]}"
