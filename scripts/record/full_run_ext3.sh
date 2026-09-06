#!/usr/bin/env bash
# Diversity stages: the long-horizon suite (two-step tasks -> sequencing failures) and the whole goal suite under
# shift. Waits for full_run_ext2.sh. libero_10 tasks 4 ("left plate / right plate") and 6 ("to the right of the
# plate") are excluded at 12 cm because a large shift can invalidate the spatial wording. libero_spatial is skipped:
# its target bowl is identified by a spatial relation that independent shifts break. Master log logs/full_run.log.
set -uo pipefail
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
export SCRIPTS PROJ
MASTER="$PROJ/logs/full_run.log"
until grep -aq "=== full run ext2 end" "$MASTER" 2>/dev/null; do sleep 30; done
while pgrep -f record_rollouts.py >/dev/null; do sleep 10; done
echo "=== full run ext3 start $(date -Is) (diversity: libero_10 + goal under shift) ===" | tee -a "$MASTER"
run_stage () {
  local stage=$1; shift
  local skipvar="SKIP_${stage}"
  if [ "${!skipvar:-0}" = "1" ]; then echo "[skip] $stage" | tee -a "$MASTER"; return 0; fi
  echo "--- stage $stage start $(date -Is) ---" | tee -a "$MASTER"
  env "$@" bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$MASTER"
  echo "--- stage $stage end $(date -Is) rc=${PIPESTATUS[0]} ---" | tee -a "$MASTER"
}
run_stage l10s8 NAME=full_l10s8 SOURCE=molmoact2_libero SUITE=libero_10 TASK_IDS='[0,1,2,3,4,5,6,7,8,9]' N_EP=20 INIT=shifted SXY=0.08 SYAW=60 SEED=7100 \
  NOTES="full run v3.1: libero_10 all tasks, shifted init 8cm/60deg, clean-init sampling"
run_stage l10s12 NAME=full_l10s12 SOURCE=molmoact2_libero SUITE=libero_10 TASK_IDS='[0,1,2,3,5,7,8,9]' N_EP=20 INIT=shifted SXY=0.12 SYAW=90 SEED=7200 \
  NOTES="full run v3.1: libero_10 (no spatial-wording tasks), shifted init 12cm/90deg, clean-init sampling"
run_stage goals8 NAME=full_goals8 SOURCE=molmoact2_libero SUITE=libero_goal TASK_IDS='[0,1,2,3,4,5,6,7,8,9]' N_EP=20 INIT=shifted SXY=0.08 SYAW=60 SEED=7300 \
  NOTES="full run v3.1: libero_goal all tasks, shifted init 8cm/60deg, clean-init sampling"
echo "=== full run ext3 end $(date -Is) ===" | tee -a "$MASTER"
cd "$PROJ/lerobot" && .venv/bin/python "$SCRIPTS/analysis/summarize_datasets.py" full_anchor full_shift4 full_shift8 full_shift12 full_shift16 full_goal full_l90 full_l10s8 full_l10s12 full_goals8 2>/dev/null | tee -a "$MASTER"
