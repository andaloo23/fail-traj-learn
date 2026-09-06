#!/usr/bin/env bash
# Render side-by-side videos + contact sheets for a spread of failures across the full-run stages, then build
# outputs/review/index.html (a local gallery). Args: optional MAX per dataset (default 6) and dataset names
# (default: one hard task per stage). Output: C:\Users\LocalPC\dev\fail-traj-learn\outputs\review\<dataset>\
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
MAX=${1:-6}
shift 2>/dev/null
DATASETS=${*:-"full_shift4__t3 full_shift8__t8 full_shift12__t3 full_shift16__t7 full_goal__t2 full_l90__t74 full_l90__t26 full_l10s8__t2 full_l10s8__t4"}
LOG=$PROJ/logs/review_batch.log
cd "$PROJ/lerobot"
echo "=== review batch start $(date -Is) max=$MAX ===" | tee -a "$LOG"
for d in $DATASETS; do
  if [ ! -d "$PROJ/data/$d" ]; then echo "[skip] $d missing" | tee -a "$LOG"; continue; fi
  echo "--- $d ---" | tee -a "$LOG"
  .venv/bin/python "$SCRIPTS/analysis/review_failures.py" "$d" --max "$MAX" --video 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$' | tee -a "$LOG"
done
.venv/bin/python "$SCRIPTS/analysis/build_review_index.py" 2>&1 | tee -a "$LOG"
echo "=== review batch end $(date -Is) ===" | tee -a "$LOG"
