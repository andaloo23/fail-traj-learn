#!/usr/bin/env bash
# Shift-level calibration for the full run: 12 cm / 90 deg on the three hardest libero_object tasks, 10 episodes each.
# Dataset: data/cal_shift12__t{6,4,0}. Accept if failures land in the 40-60 percent band with zero predicate artifacts.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export PROJ SCRIPTS
LOG="$PROJ/logs/calibrate_shift12.log"
echo "=== calibrate shift12 start $(date -Is) ===" | tee -a "$LOG"
NAME=cal_shift12 SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS='[6,4,0]' N_EP=10 INIT=shifted SXY=0.12 SYAW=90 SEED=4500 \
  NOTES="shift calibration: fine-tuned MolmoAct2-LIBERO, shifted init 12cm/90deg, container yaw locked" \
  bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$LOG"
echo "=== calibrate shift12 end $(date -Is) rc=${PIPESTATUS[0]} ===" | tee -a "$LOG"
