#!/usr/bin/env bash
# Re-run the whole stage-4 + stage-5 sweep against the fixed pipeline (docs/rl_verification.md).
#
# Why a full sweep and not just `events` and `potential`: only those two modes read a reward array that
# the fixes changed, but every one of the 18 saved runs was trained with observation whitening fit on the
# whole corpus, validation episodes included. Retraining only the two would leave a table whose rows were
# preprocessed differently from each other, which is worse than a table that is uniformly stale.
#
# Output goes to a SEPARATE artifact root ($FTL_PROJ/rl_v2) so the pre-fix runs, checkpoints and
# evaluations that docs/rl_results.md and docs/rl_verification.md cite stay exactly where they are.
# `datasets` is symlinked, not copied: the built transitions are unchanged by any of this.
#
# The evaluation protocol is deliberately IDENTICAL to the old one (seed block 90000, base initial-state
# ids 0..29, i.e. --eval-init-state-offset 0), so the new table is comparable row-for-row with the old.
# Evaluating on held-out base layouts is a separate experiment: rerun with EVAL_OFFSET=30.
#
# Usage: rebaseline.sh [steps]      env: SEEDS, EVAL_OFFSET, FTL_RL_TAG, DATASET, FAMILIES
set -u
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
STEPS=${1:-100000}
SEEDS=${SEEDS:-"1 2"}
EVAL_OFFSET=${EVAL_OFFSET:-0}
FTL_RL_TAG=${FTL_RL_TAG:-rl_v2}
export DATASET=${DATASET:-object_v1}
# Evaluate where the behaviour policy has room to be beaten. MolmoAct2-LIBERO scores 95.0 / 75.7 / 50.0
# / 39.7 % at shift 4 / 8 / 12 / 16 on the recorded corpus, so the old shift4/8/12 block (73.6% for the
# behaviour policy, and shift4 nearly saturated) left almost no headroom to demonstrate improvement.
export FAMILIES=${FAMILIES:-"full_shift8 full_shift12 full_shift16"}

export FTL_PROJ="$PROJ"
export FTL_RL="$PROJ/$FTL_RL_TAG"
export EP=5
OFFSET_ARG=""
[ "$EVAL_OFFSET" != "0" ] && OFFSET_ARG="--eval-init-state-offset $EVAL_OFFSET"

mkdir -p "$FTL_RL/runs"
[ -e "$FTL_RL/datasets" ] || ln -s "$PROJ/rl/datasets" "$FTL_RL/datasets"
echo "== re-baseline into $FTL_RL  ($STEPS steps, seeds 0 $SEEDS, eval offset $EVAL_OFFSET)"
echo "   dataset $DATASET   eval families: $FAMILIES"
"$PROJ/lerobot/.venv/bin/python" -c "
import json,sys
m=json.load(open('$FTL_RL/datasets/$DATASET/meta.json'))
print('   obs spec %s (%dd)%s' % (m.get('obs_spec','v1'), m['obs_dim'],
      ', encoder ' + str(m['encoder']) if m.get('encoder') else ''))
" || exit 1
date -Is

# 4 stage-4 baselines + 8 segment modes + 2 extra seeds x 3 configs = 18 runs, same as the saved set.
EXTRA="$OFFSET_ARG" bash "$R/baselines.sh" "$STEPS"
EXTRA="--seg-use-q $OFFSET_ARG" bash "$R/segment_sweep.sh" "$STEPS"
EXTRA="$OFFSET_ARG" SEEDS="$SEEDS" STEPS="$STEPS" bash "$R/seed_replication.sh"

echo "== done"
date -Is
ls "$FTL_RL/runs"
