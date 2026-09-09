#!/usr/bin/env bash
# Run every CPU unit test under scripts/annotate/bench in the LeRobot venv. Arg "fails" prints only failure lines.
PY=/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python
B=/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/annotate/bench
export CUDA_VISIBLE_DEVICES=""
cd "$B"
if [ "$1" = "fails" ]; then
  $PY -m unittest discover -s "$B" -p 'test_*.py' 2>&1 | grep -E "^(FAIL|ERROR|AssertionError|Ran |OK|FAILED|  File .*/bench/test_)" | cut -c1-200
else
  $PY -m unittest discover -s "$B" -p 'test_*.py' 2>&1 | tail -6
fi
