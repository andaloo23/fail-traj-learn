#!/usr/bin/env bash
# Replicate one configuration across seeds. A single 150-episode evaluation carries about +-8 points on
# the overall figure, so any ordering claim between neighbouring modes needs this.
# Usage: seeds.sh <tag-prefix> <seeds> -- <train.py args...>
#   seeds.sh events "0 1 2" -- --algo iql --segments events --seg-use-q
set -u
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
STEPS=${STEPS:-100000}
DATASET=${DATASET:-object_v1}
LABELS=${LABELS:-oracle_labels_r6_object.parquet}
FAMILIES=${FAMILIES:-"full_shift4 full_shift8 full_shift12"}
EP=${EP:-5}
EXTRA=${EXTRA:-}
prefix=$1; shift
seeds=$1; shift
[ "${1:-}" = "--" ] && shift

# --dataset is passed explicitly: without it these runs silently fell back to train.py's default
# (object_v1, the privileged-state build) while the rest of the sweep used whatever DATASET said.
for s in $seeds; do
  echo "=================== ${prefix}_s${s} ==================="
  bash "$R/py.sh" train.py --tag "${prefix}_s${s}" --dataset "$DATASET" --seed "$s" --steps "$STEPS" \
    --labels "$LABELS" \
    --log-every 50000 --final-eval-families $FAMILIES --final-eval-episodes "$EP" $EXTRA "$@"
done
