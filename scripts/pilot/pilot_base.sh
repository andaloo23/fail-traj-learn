#!/usr/bin/env bash
# Pilot stage D: base MolmoAct2 weights (no LIBERO fine-tune) driven with the LIBERO normalization stats
# taken from the MolmoAct2-LIBERO checkpoint. Run after pilot_molmoact2.sh (needs the GPU).
set -uo pipefail
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
mkdir -p "$PROJ/logs"
MASTER="$PROJ/logs/pilot_base.log"

NORM=$(ls /home/aliu/.cache/huggingface/hub/models--allenai--MolmoAct2-LIBERO/snapshots/*/norm_stats.json | head -1)
if [ -z "$NORM" ]; then echo "LIBERO norm_stats.json not found" | tee -a "$MASTER"; exit 1; fi
echo "=== pilot_base start $(date -Is) norm_stats=$NORM ===" | tee -a "$MASTER"

run_stage () {
  local stage=$1; shift
  local skipvar="SKIP_${stage}"
  if [ "${!skipvar:-0}" = "1" ]; then echo "[skip] $stage" | tee -a "$MASTER"; return 0; fi
  echo "--- stage $stage start $(date -Is) ---" | tee -a "$MASTER"
  env "$@" bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$MASTER"
  echo "--- stage $stage end $(date -Is) rc=${PIPESTATUS[0]} ---" | tee -a "$MASTER"
}

# Smoke first: one task, 2 episodes, to catch config errors before spending an hour.
run_stage D_smoke \
  NAME=pilot_D_base_smoke SOURCE=molmoact2_base CKPT=allenai/MolmoAct2 NORM_TAG=libero \
  SUITE=libero_object TASK_IDS='[0]' N_EP=2 INIT=standard SEED=3500 \
  EXTRA="--policy.norm_stats_path=$NORM" \
  NOTES="pilot D smoke: base MolmoAct2 + LIBERO norm stats"

run_stage D_object_std \
  NAME=pilot_D_base_object_std SOURCE=molmoact2_base CKPT=allenai/MolmoAct2 NORM_TAG=libero \
  SUITE=libero_object TASK_IDS= N_EP=10 INIT=standard SEED=3600 \
  EXTRA="--policy.norm_stats_path=$NORM" \
  NOTES="pilot D: base MolmoAct2 + LIBERO norm stats, core object tasks, standard init"

run_stage D_goal_std \
  NAME=pilot_D_base_goal_std SOURCE=molmoact2_base CKPT=allenai/MolmoAct2 NORM_TAG=libero \
  SUITE=libero_goal TASK_IDS='[3,7]' N_EP=10 INIT=standard SEED=3700 \
  EXTRA="--policy.norm_stats_path=$NORM" \
  NOTES="pilot D: base MolmoAct2 + LIBERO norm stats, libero_goal 3 and 7"

echo "=== pilot_base end $(date -Is) ===" | tee -a "$MASTER"
cd "$PROJ/lerobot" && .venv/bin/python "$SCRIPTS/analysis/summarize_datasets.py" pilot_D_base_smoke pilot_D_base_object_std pilot_D_base_goal_std 2>/dev/null | tee -a "$MASTER"
