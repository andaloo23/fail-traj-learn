#!/usr/bin/env bash
# Re-render contact sheets + per-episode json (no video) for datasets already in outputs/review, then rebuild index.
# Args: MAX per dataset (default 6), then dataset names (default: the review_batch.sh set).
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
MAX=${1:-6}
shift 2>/dev/null
DATASETS=${*:-"full_shift4__t3 full_shift8__t8 full_shift12__t3 full_shift16__t7 full_goal__t2 full_l90__t74 full_l90__t26 full_l10s8__t2 full_l10s8__t4"}
cd "$PROJ/lerobot"
for d in $DATASETS; do
  [ -d "$PROJ/data/$d" ] || continue
  .venv/bin/python "$SCRIPTS/analysis/review_failures.py" "$d" --max "$MAX" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$'
done
.venv/bin/python "$SCRIPTS/analysis/build_review_index.py" 2>&1
echo "SHEETS_DONE"
