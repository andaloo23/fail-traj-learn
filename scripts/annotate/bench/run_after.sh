#!/usr/bin/env bash
# Wait until no other benchmark/annotator GPU process is running, then launch run_method.sh with the given args.
# Usage: run_after.sh --method NAME [run_method args...]
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
while pgrep -f "run_method.py|annotate.py --datasets|segmentation_lab.py|local_segmenter.py" > /dev/null; do
  sleep 30
done
exec bash "$SCRIPTS/annotate/bench/run_method.sh" "$@"
