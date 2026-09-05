#!/usr/bin/env bash
# Wrapper: runs eval_smoke.sh with fixed settings and logs to a fixed file.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export SUITE=libero_object TASK_IDS='[0]' N_EP=5 RECORD=false NAME=smoke_libero_object_0_norec
bash "$SCRIPTS/eval_smoke.sh" > "$PROJ/eval_smoke.log" 2>&1
echo "EXIT=$?" >> "$PROJ/eval_smoke.log"
