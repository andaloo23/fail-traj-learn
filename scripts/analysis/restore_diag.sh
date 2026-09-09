#!/usr/bin/env bash
# Run restore_diag.py on several (dataset, episode, chunk) triples. Args: dataset:episode:chunk[:priorEP.priorCHUNK] (episode -1 = first failure, -2 = first success; prior is EP.CHUNK with a dot, e.g. -1.20).
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
cd "$PROJ/lerobot"
export MUJOCO_GL=egl PYOPENGL_PLATFORM=egl
for t in "$@"; do
  IFS=: read -r d e c p <<< "$t"
  extra=""
  [ -n "${p:-}" ] && extra="--prior=${p/./:}"
  echo "=================== $d ep $e chunk $c prior=${p:-none}"
  .venv/bin/python "$SCRIPTS/analysis/restore_diag.py" "$d" "$e" "$c" --steps ${STEPS:-10} $extra 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$|Svt|moov atom|robosuite WARNING|robosuite_logs'
done
echo DIAG_DONE
