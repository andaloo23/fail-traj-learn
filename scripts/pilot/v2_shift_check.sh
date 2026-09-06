#!/usr/bin/env bash
# Schema v2 validation recording: shifted init on the three libero_object tasks with the most pilot failures
# (6 butter, 4 ketchup wide object, 0 alphabet soup). 10 episodes each. Datasets: data/v2_C_shift__t{6,4,0}.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export PROJ SCRIPTS
LOG="$PROJ/logs/v2_shift_check.log"
echo "=== v2 shift check start $(date -Is) ===" | tee -a "$LOG"
NAME=v2_C_shift SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS='[6,4,0]' N_EP=10 INIT=shifted SXY=0.08 SYAW=60 SEED=4100 \
  NOTES="schema v2 validation: fine-tuned MolmoAct2-LIBERO, shifted init 8cm/60deg" \
  bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$LOG"
echo "=== v2 shift check end $(date -Is) rc=${PIPESTATUS[0]} ===" | tee -a "$LOG"
