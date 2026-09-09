#!/usr/bin/env bash
# Resume after the 2026-09-06 crash: the ext3 queue died during full_goals8 task 9 (3 of 20 episodes written,
# dataset never finalized). Move the partial dataset aside, re-record task 9 with the same stage seed (the
# recorder seeds per task, so the offsets match what the original run would have produced), finish the ext3
# bookkeeping, then run the acceptance checks. Master log logs/full_run.log; acceptance log logs/accept_run.log.
set -uo pipefail
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
export SCRIPTS PROJ
MASTER="$PROJ/logs/full_run.log"
PARTIAL="$PROJ/data/full_goals8__t9"
ARCHIVE="$PROJ/data/archive_pre_v3/crash_partial_full_goals8__t9"
echo "=== full run ext3 RESUME $(date -Is) after machine crash during full_goals8__t9 ===" | tee -a "$MASTER"
if [ -d "$PARTIAL" ]; then
  if [ -e "$ARCHIVE" ]; then echo "archive target already exists: $ARCHIVE" | tee -a "$MASTER"; exit 1; fi
  mkdir -p "$PROJ/data/archive_pre_v3"
  mv "$PARTIAL" "$ARCHIVE" && echo "moved partial dataset to $ARCHIVE" | tee -a "$MASTER"
fi
echo "--- stage goals8 (task 9 only) start $(date -Is) ---" | tee -a "$MASTER"
env NAME=full_goals8 SOURCE=molmoact2_libero SUITE=libero_goal TASK_IDS='[9]' N_EP=20 INIT=shifted SXY=0.08 SYAW=60 SEED=7300 \
  NOTES="full run v3.1: libero_goal all tasks, shifted init 8cm/60deg, clean-init sampling" \
  bash "$SCRIPTS/record/record_config.sh" 2>&1 | tee -a "$MASTER"
echo "--- stage goals8 (task 9 only) end $(date -Is) rc=${PIPESTATUS[0]} ---" | tee -a "$MASTER"
echo "=== full run ext3 end $(date -Is) ===" | tee -a "$MASTER"
cd "$PROJ/lerobot" && .venv/bin/python "$SCRIPTS/analysis/summarize_datasets.py" full_anchor full_shift4 full_shift8 full_shift12 full_shift16 full_goal full_l90 full_l10s8 full_l10s12 full_goals8 2>/dev/null | tee -a "$MASTER"
echo "=== acceptance start $(date -Is) ===" | tee -a "$MASTER"
bash "$SCRIPTS/analysis/accept_run.sh" 2>&1 | tee "$PROJ/logs/accept_run.log" | grep -E "^== |!!|RESTORE_|BAD INIT|ACCEPT_" | tee -a "$MASTER"
echo "=== acceptance end $(date -Is) ===" | tee -a "$MASTER"
