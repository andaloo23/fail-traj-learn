#!/usr/bin/env bash
# WSL: reuse one observable dataset and identical training/evaluation settings for every arm.
set -euo pipefail
R=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
PY=${PY:-$PROJ/lerobot/.venv/bin/python}
export FTL_PROJ=${FTL_PROJ:-$PROJ}
export FTL_RL=${FTL_RL:-$FTL_PROJ/rl}
export MUJOCO_GL=${MUJOCO_GL:-egl} PYOPENGL_PLATFORM=${PYOPENGL_PLATFORM:-egl}
export PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false
DATASET=${DATASET:-object_v2}
LABELS=${LABELS:-oracle_labels_r6_object.parquet}
PREFIX=${PREFIX:-reward_matched}
read -r -a seeds <<< "${SEEDS:-0 1 2}"
# Check every destination before starting; never overwrite previous runs.
for seed in "${seeds[@]}"; do
  for mode in terminal failure productive; do
    dest="$FTL_RL/runs/${PREFIX}_${mode}_s${seed}"
    if [[ -e "$dest" ]]; then
      echo "Run already exists: $dest. Set PREFIX to a new experiment name." >&2
      exit 1
    fi
  done
done
for seed in "${seeds[@]}"; do
  for mode in terminal failure productive; do
    "$PY" "$R/train.py" --dataset "$DATASET" --labels "$LABELS" \
      --tag "${PREFIX}_${mode}_s${seed}" --algo iql --data all --reward-mode "$mode" \
      --reward-success-scale "${SUCCESS_SCALE:-1}" \
      --reward-failure-scale "${FAILURE_SCALE:-0.01}" \
      --reward-productive-scale "${PRODUCTIVE_SCALE:-0.01}" \
      --seed "$seed" --steps "${STEPS:-100000}" --batch-size "${BATCH_SIZE:-1024}" \
      --device "${DEVICE:-cuda}" --val-frac 0.05 --eval-every 0 \
      --eval-seed "${EVAL_SEED:-90000}" --eval-init-state-offset "${EVAL_OFFSET:-30}" \
      --final-eval-families full_shift8 full_shift12 full_shift16 \
      --final-eval-episodes "${EVAL_EPISODES:-5}" --eval-workers "${EVAL_WORKERS:-10}"
  done
done
