#!/usr/bin/env bash
# Short CPU run of every segment mode: catches shape, index and NaN bugs before a GPU sweep.
# Usage: segment_smoke.sh [steps] ; env: DATASET, LABELS
set -u
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
STEPS=${1:-400}
DATASET=${DATASET:-object_v1}
LABELS=${LABELS:-oracle_labels_r6_object.parquet}
MODES=${MODES:-"pm1 sign expectile decisive potential events awr mask sign,mask sign,expectile"}
fail=0
for m in $MODES; do
  echo "--- segments=$m"
  out=$(CUDA_VISIBLE_DEVICES="" bash "$R/py.sh" train.py --tag "segsmoke_${m//,/_}" --dataset "$DATASET" \
        --labels "$LABELS" --segments "$m" --algo iql --steps "$STEPS" --batch-size 256 \
        --device cpu --log-every "$STEPS" --no-final-eval 2>&1)
  echo "$out" | grep -E "segments:|segments dropped|step=$STEPS|EXIT=" || true
  echo "$out" | grep -qE "EXIT=0" || { echo "  !! FAILED"; echo "$out" | tail -20; fail=1; }
  echo "$out" | grep -qE "nan|inf" && { echo "  !! non-finite metric"; fail=1; }
done
echo "SEGMENT_SMOKE_$([ $fail -eq 0 ] && echo OK || echo FAIL)"
