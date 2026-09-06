#!/usr/bin/env bash
# Appended stage(s) for the full run. Waits for full_run.sh to finish (GPU hand-off), then records shift16 on the
# object suite (the volume failure source once shift4 turned out to be near in-distribution). Same conventions as
# full_run.sh: datasets data/full_shift16__t<k>, master log logs/full_run.log, resumable.
set -uo pipefail
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
export SCRIPTS PROJ
MASTER="$PROJ/logs/full_run.log"
until grep -aq "=== full run end" "$MASTER" 2>/dev/null; do sleep 30; done
while pgrep -f record_rollouts.py >/dev/null; do sleep 10; done
echo "=== full run ext start $(date -Is) ===" | tee -a "$MASTER"
echo "--- stage shift16 start $(date -Is) ---" | tee -a "$MASTER"
env NAME=full_shift16 SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP=${N_SHIFT:-30} INIT=shifted SXY=0.16 SYAW=90 SEED=5600 \
  NOTES="full run: shifted init 16cm/90deg, container yaw locked" \
  bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$MASTER"
echo "--- stage shift16 end $(date -Is) rc=${PIPESTATUS[0]} ---" | tee -a "$MASTER"
echo "=== full run ext end $(date -Is) ===" | tee -a "$MASTER"
cd "$PROJ/lerobot" && .venv/bin/python "$SCRIPTS/analysis/summarize_datasets.py" full_anchor full_shift4 full_shift8 full_shift12 full_shift16 full_goal full_l90 2>/dev/null | tee -a "$MASTER"
