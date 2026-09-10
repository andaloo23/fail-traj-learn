#!/usr/bin/env bash
# Stage-5 sweep: every segment-supervision mode against the same IQL critic and the same evaluation.
# The comparison is only meaningful next to iql_terminal from baselines.sh, so run that first.
# Usage: segment_sweep.sh [steps] ; env: LABELS, FAMILIES, EP, MODES, DATASET, EXTRA
set -u
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
STEPS=${1:-100000}
DATASET=${DATASET:-object_v1}
LABELS=${LABELS:-oracle_labels_r6_object.parquet}
FAMILIES=${FAMILIES:-"full_shift4 full_shift8 full_shift12"}
EP=${EP:-5}
MODES=${MODES:-"pm1 sign expectile decisive potential events awr mask"}
EXTRA=${EXTRA:-"--seg-use-q"}

for m in $MODES; do
  tag="iql_${m//,/_}"
  echo "=================== $tag ==================="
  bash "$R/py.sh" train.py --tag "$tag" --dataset "$DATASET" --labels "$LABELS" \
    --algo iql --segments "$m" --steps "$STEPS" --log-every 25000 \
    --final-eval-families $FAMILIES --final-eval-episodes "$EP" $EXTRA
done
