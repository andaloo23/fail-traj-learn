#!/usr/bin/env bash
# Full schema v3 data run with the frozen MolmoAct2-LIBERO policy (sources decided by the Sept 4 pilot, shift levels by
# the Sept 5 calibration). Sequential, one GPU, one recorder process per task -> datasets data/<stage>__t<k>.
# Skip a stage with SKIP_<stage>=1. Re-running a stage appends to its datasets (resume after a VM restart).
# Shift levels (cm/deg) and episodes per task can be overridden: LEVELS="4:30 8:60 12:90" N_SHIFT=30.
set -uo pipefail
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
export SCRIPTS PROJ
mkdir -p "$PROJ/logs"
MASTER="$PROJ/logs/full_run.log"
LEVELS=${LEVELS:-"4:30 8:60 12:90"}
N_SHIFT=${N_SHIFT:-30}
echo "=== full run start $(date -Is) levels='$LEVELS' n_shift=$N_SHIFT ===" | tee -a "$MASTER"

run_stage () {  # name, then env assignments as KEY=VAL ...
  local stage=$1; shift
  local skipvar="SKIP_${stage}"
  if [ "${!skipvar:-0}" = "1" ]; then echo "[skip] $stage" | tee -a "$MASTER"; return 0; fi
  echo "--- stage $stage start $(date -Is) ---" | tee -a "$MASTER"
  env "$@" bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$MASTER"
  echo "--- stage $stage end $(date -Is) rc=${PIPESTATUS[0]} ---" | tee -a "$MASTER"
}

# 1. Anchor successes: object suite, standard init (positive examples for the scarce-successes axis).
run_stage anchor \
  NAME=full_anchor SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP=10 INIT=standard SEED=5000 \
  NOTES="full run: anchor, standard init"

# 2. Shifted init on the object suite, one stage per level (the volume source; level = ablation axis).
seed=5100
for lv in $LEVELS; do
  cm=${lv%%:*}; deg=${lv##*:}
  sxy=$(awk "BEGIN{printf \"%.2f\", $cm/100}")
  run_stage "shift${cm}" \
    NAME="full_shift${cm}" SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP="$N_SHIFT" INIT=shifted SXY="$sxy" SYAW="$deg" SEED="$seed" \
    NOTES="full run: shifted init ${cm}cm/${deg}deg, container yaw locked"
  seed=$((seed + 100))
done

# 3. Goal suite at standard init (deep-progress failures: drawer+bowl, stove knob, wine bottle on cabinet, cream cheese in bowl).
run_stage goal \
  NAME=full_goal SOURCE=molmoact2_libero SUITE=libero_goal TASK_IDS='[2,3,6,7]' N_EP=30 INIT=standard SEED=5400 \
  NOTES="full run: libero_goal 2,3,6,7 standard init"

# 4. libero_90 keep-list (semantic/placement failures), capped, longer horizon.
run_stage l90 \
  NAME=full_l90 SOURCE=molmoact2_libero SUITE=libero_90 TASK_IDS='[74,26,38,47,89]' N_EP=20 INIT=standard SEED=5500 \
  EXTRA='--max_steps_override=400' \
  NOTES="full run: libero_90 keep-list 74,26,38,47,89 standard init, horizon 400"

echo "=== full run end $(date -Is) ===" | tee -a "$MASTER"
cd "$PROJ/lerobot" && .venv/bin/python "$SCRIPTS/analysis/summarize_datasets.py" full_anchor $(for lv in $LEVELS; do echo "full_shift${lv%%:*}"; done) full_goal full_l90 2>/dev/null | tee -a "$MASTER"
