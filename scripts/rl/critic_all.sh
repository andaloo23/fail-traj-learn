#!/usr/bin/env bash
# Critic metrics for every IQL run under $FTL_RL/runs (skips BC runs, which have no critic).
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
LABELS=${LABELS:-oracle_labels_r6_object.parquet}
for d in "$PROJ"/rl/runs/*/; do
  [ -f "$d/final.pt" ] || continue
  case "$(basename "$d")" in bc_*) continue ;; esac
  echo "=== $(basename "$d")"
  bash "$R/py.sh" eval_critic.py --ckpt "$d/final.pt" --labels "$LABELS" --out "$d/critic.json" 2>&1 \
    | grep -E "outcome_auc |adv_sign_agree|adv_decisive_margin|v_gap |adv_failure_inducing|adv_progress|EXIT=[1-9]"
done
