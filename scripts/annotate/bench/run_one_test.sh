#!/usr/bin/env bash
# Run one bench test module (or dotted test id) verbosely: run_one_test.sh test_oracle_reference [lines]
PY=/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python
B=/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/annotate/bench
export CUDA_VISIBLE_DEVICES=""
cd "$B" && $PY -m unittest "$1" 2>&1 | grep -v "FutureWarning\|warnings.warn" | tail -"${2:-60}"
