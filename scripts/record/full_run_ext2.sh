#!/usr/bin/env bash
# Re-record the shifted stages with the rejection-sampled initial states (recorder v3.1). Waits for full_run_ext.sh
# (shift16) to finish, moves the contaminated full_shift{4,8,12} datasets to data/archive_pre_v3/contaminated_shift/,
# then records them again under the same names with fresh seeds. Master log logs/full_run.log.
set -uo pipefail
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
export SCRIPTS PROJ
MASTER="$PROJ/logs/full_run.log"
until grep -aq "=== full run ext end" "$MASTER" 2>/dev/null; do sleep 30; done
while pgrep -f record_rollouts.py >/dev/null; do sleep 10; done
echo "=== full run ext2 start $(date -Is) (re-record shifted stages with clean init sampling) ===" | tee -a "$MASTER"
mkdir -p "$PROJ/data/archive_pre_v3/contaminated_shift"
for s in 4 8 12; do
  for d in "$PROJ/data/full_shift${s}__t"*; do
    [ -d "$d" ] && mv "$d" "$PROJ/data/archive_pre_v3/contaminated_shift/"
  done
done
echo "archived contaminated shift datasets: $(ls "$PROJ/data/archive_pre_v3/contaminated_shift" | wc -l)" | tee -a "$MASTER"
run_stage () {
  local stage=$1; shift
  echo "--- stage $stage start $(date -Is) ---" | tee -a "$MASTER"
  env "$@" bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$MASTER"
  echo "--- stage $stage end $(date -Is) rc=${PIPESTATUS[0]} ---" | tee -a "$MASTER"
}
run_stage shift8 NAME=full_shift8 SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP=${N_SHIFT:-30} INIT=shifted SXY=0.08 SYAW=60 SEED=6200 \
  NOTES="full run v3.1: shifted init 8cm/60deg, container yaw locked, clean-init rejection sampling"
run_stage shift12 NAME=full_shift12 SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP=${N_SHIFT:-30} INIT=shifted SXY=0.12 SYAW=90 SEED=6300 \
  NOTES="full run v3.1: shifted init 12cm/90deg, container yaw locked, clean-init rejection sampling"
run_stage shift4 NAME=full_shift4 SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP=${N_SHIFT:-30} INIT=shifted SXY=0.04 SYAW=30 SEED=6100 \
  NOTES="full run v3.1: shifted init 4cm/30deg, container yaw locked, clean-init rejection sampling"
echo "=== full run ext2 end $(date -Is) ===" | tee -a "$MASTER"
cd "$PROJ/lerobot" && .venv/bin/python "$SCRIPTS/analysis/summarize_datasets.py" full_anchor full_shift4 full_shift8 full_shift12 full_shift16 full_goal full_l90 2>/dev/null | tee -a "$MASTER"
