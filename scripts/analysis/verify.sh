#!/usr/bin/env bash
# Run verify_dataset.py on a recorded dataset. Args: dataset_name [episode_index]
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
cd "$PROJ/lerobot"
.venv/bin/python "$SCRIPTS/analysis/verify_dataset.py" "${1:-smoke_rec}" "${2:-0}" 2>&1 \
  | grep -vE '^[[:space:]]*$|Svt|FutureWarning|warnings\.warn|moov atom' | tail -60
echo "EXIT=${PIPESTATUS[0]}"
