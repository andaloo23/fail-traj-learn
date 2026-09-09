#!/usr/bin/env bash
# Run the bench unit tests and print only the failing test ids with their traceback tails: run_tests_failures.sh [lines]
PY=/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python
B=/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/annotate/bench
export CUDA_VISIBLE_DEVICES=""
cd "$B" && $PY -m unittest discover -s "$B" -p 'test_*.py' 2>&1 | grep -v "FutureWarning\|warnings.warn" | grep -A "${1:-25}" "^FAIL:\|^ERROR:"
