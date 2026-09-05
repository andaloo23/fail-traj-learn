#!/usr/bin/env bash
# Failure-induction pilot with the MolmoAct2-LIBERO checkpoint (configs that need no new download).
# Runs sequentially (one GPU). Each stage is one recorder invocation -> one dataset under data/.
# Skip a stage by exporting SKIP_<stage>=1. Re-running a stage appends to its dataset (resume).
set -uo pipefail
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
mkdir -p "$PROJ/logs"
MASTER="$PROJ/logs/pilot_molmoact2.log"
echo "=== pilot start $(date -Is) ===" | tee -a "$MASTER"

run_stage () {  # name, then env assignments as KEY=VAL ...
  local stage=$1; shift
  local skipvar="SKIP_${stage}"
  if [ "${!skipvar:-0}" = "1" ]; then echo "[skip] $stage" | tee -a "$MASTER"; return 0; fi
  echo "--- stage $stage start $(date -Is) ---" | tee -a "$MASTER"
  env "$@" bash "$SCRIPTS/record_config.sh" 2>&1 | tee -a "$MASTER"
  echo "--- stage $stage end $(date -Is) rc=${PIPESTATUS[0]} ---" | tee -a "$MASTER"
}

# A-lite: anchor. Fine-tuned policy, core object tasks, standard init. Expect ~100% success.
run_stage A_object_std \
  NAME=pilot_A_object_std SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP=5 INIT=standard SEED=3000 \
  NOTES="pilot A: fine-tuned MolmoAct2-LIBERO, standard init, anchor"

# Core goal tasks (drawer+bowl, stove knob), standard init.
run_stage A_goal_std \
  NAME=pilot_A_goal_std SOURCE=molmoact2_libero SUITE=libero_goal TASK_IDS='[3,7]' N_EP=10 INIT=standard SEED=3100 \
  NOTES="pilot A: fine-tuned MolmoAct2-LIBERO, libero_goal 3 and 7, standard init"

# C: shifted initial states on the core object tasks.
run_stage C_object_shift \
  NAME=pilot_C_object_shift SOURCE=molmoact2_libero SUITE=libero_object TASK_IDS= N_EP=10 INIT=shifted SXY=0.08 SYAW=60 SEED=3200 \
  NOTES="pilot C: fine-tuned MolmoAct2-LIBERO, shifted init 8cm/60deg"

# B: unseen libero_90 tasks (kitchen sequencing/drawers/stove, living-room and study pick-and-place variants).
run_stage B_libero90_std \
  NAME=pilot_B_libero90_std SOURCE=molmoact2_libero SUITE=libero_90 TASK_IDS='[1,8,13,16,21,26,38,42,47,53,63,66,74,89]' N_EP=10 INIT=standard SEED=3300 \
  EXTRA='--max_steps_override=400' \
  NOTES="pilot B: fine-tuned MolmoAct2-LIBERO on 14 unseen libero_90 tasks, horizon 400"

# Degraded inference: one flow step instead of the default. The policy's own imprecision, no external noise.
run_stage A_object_1step \
  NAME=pilot_A_object_1step SOURCE=molmoact2_libero_1step SUITE=libero_object TASK_IDS= N_EP=10 INIT=standard SEED=3400 \
  EXTRA='--policy.num_inference_steps=1' \
  NOTES="pilot degraded: fine-tuned MolmoAct2-LIBERO with num_inference_steps=1"

echo "=== pilot end $(date -Is) ===" | tee -a "$MASTER"
cd "$PROJ/lerobot" && .venv/bin/python "$SCRIPTS/summarize_datasets.py" pilot_A_object_std pilot_A_goal_std pilot_C_object_shift pilot_B_libero90_std pilot_A_object_1step 2>/dev/null | tee -a "$MASTER"
