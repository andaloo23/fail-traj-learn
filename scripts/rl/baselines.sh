#!/usr/bin/env bash
# The stage-4 reward-only baselines (docs/proposal_overview.md section 14): no segment labels anywhere.
# Each run trains and then evaluates closed-loop on the shift levels given by FAMILIES.
# Usage: baselines.sh [steps] ; env: FAMILIES, EP (episodes per task), DATASET, EXTRA
set -u
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
STEPS=${1:-100000}
DATASET=${DATASET:-object_v1}
FAMILIES=${FAMILIES:-"full_shift4 full_shift8 full_shift12"}
EP=${EP:-5}
EXTRA=${EXTRA:-}

run () {
  tag=$1; shift
  echo "=================== $tag ==================="
  bash "$R/py.sh" train.py --tag "$tag" --dataset "$DATASET" --steps "$STEPS" \
    --log-every 25000 --final-eval-families $FAMILIES --final-eval-episodes "$EP" \
    $EXTRA "$@"
}

run bc_success      --algo bc  --data success
run bc_all          --algo bc  --data all
run bc_outcome      --algo bc  --data all --bc-weight outcome
run iql_terminal    --algo iql --data all
