#!/bin/bash
# Prepared only. This exits before GPU work unless the exact plan is approved.
set -euo pipefail
task_repo=/mnt/c/Users/LocalPC/dev/fail-traj-learn
task_py=/home/aliu/.venvs/ftl-oopsie-recipes-v1/bin/python
cd "$task_repo"
export HF_HUB_CACHE=/home/aliu/.cache/ftl-qwen-hub
export TOKENIZERS_PARALLELISM=false
export OMP_NUM_THREADS=8
"$task_py" scripts/distill/recipe_job_plan.py check-approval
for recipe in binary base failure_balanced; do
  if timeout --signal=TERM --kill-after=10s 119m "$task_py" -u scripts/distill/recipe_job_plan.py run-arm --recipe "$recipe"; then
    printf 'Completed local recipe: %s\n' "$recipe"
  else
    task_rc=$?
    printf 'Local recipe %s stopped with exit code %s; preserving outputs.\n' "$recipe" "$task_rc"
    "$task_py" - "$recipe" "$task_rc" <<'PY'
import json,sys
from pathlib import Path
p=Path('outputs/oopsie_distillation_recipes_v1/arm_states')/(sys.argv[1]+'.json')
state=json.loads(p.read_text()) if p.exists() else dict(recipe=sys.argv[1])
if state.get('status')=='running' or 'status' not in state:
    state.update(status='stopped',exit_code=int(sys.argv[2]),automatic_retry=False)
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(state,indent=2)+'\n')
PY
  fi
done
