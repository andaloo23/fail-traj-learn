#!/usr/bin/env bash
# Run the VLM annotator in the LeRobot venv. All args pass through to annotate.py; log to $PROJ/logs/annotate_<tag>.log
# Examples:
#   annotate.sh --datasets full_shift8 --episodes 0 --dry-run
#   annotate.sh --datasets full_shift8 --failures-only --limit 5
#   annotate.sh --datasets full_shift8 full_shift12 full_goal full_l90 --refine
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
mkdir -p "$PROJ/logs" "$PROJ/annot"
tag=annotate
for ((i=1; i<=$#; i++)); do
  if [ "${!i}" = "--tag" ]; then j=$((i+1)); tag="annotate_${!j}"; fi
done
LOG="$PROJ/logs/$tag.log"
cd "$PROJ/lerobot"
export MUJOCO_GL=egl PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
echo "$(date -Is) START annotate.py $*" >> "$LOG"
.venv/bin/python "$SCRIPTS/annotate/annotate.py" "$@" 2>&1 | grep --line-buffered -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$' | tee -a "$LOG"
rc=${PIPESTATUS[0]}
echo "$(date -Is) EXIT=$rc" >> "$LOG"
echo "EXIT=$rc"
