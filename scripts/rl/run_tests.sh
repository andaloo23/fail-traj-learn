#!/usr/bin/env bash
set -o pipefail
# Run every CPU unit test under scripts/rl in the LeRobot venv. Arg "fails" prints only failure lines.
PY=${PY:-/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python}
R=${R:-$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)}
export CUDA_VISIBLE_DEVICES="" FTL_PROJ=${FTL_PROJ:-/home/aliu/projects/fail-traj-learn}
cd "$R" || exit 1
if [ "${1:-}" = "fails" ]; then
  "$PY" -m unittest discover -s "$R" -p 'test_*.py' 2>&1 | grep -E "^(FAIL|ERROR|AssertionError|Ran |OK|FAILED|  File .*/rl/test_)" | cut -c1-200
else
  "$PY" -m unittest discover -s "$R" -p 'test_*.py' 2>&1 | tail -8
fi
