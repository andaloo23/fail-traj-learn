#!/usr/bin/env bash
# Launch review_oracle.py detached through bench.sh (CPU + ffmpeg); output goes to $PROJ/logs/bench_review_oracle.log.
#   review_oracle_bg.sh --set all --successes 15
# Prints the PID; follow with: tail -f /home/aliu/projects/fail-traj-learn/logs/bench_review_oracle.log
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export PROJ SCRIPTS
mkdir -p "$PROJ/logs"
nohup bash "$SCRIPTS/annotate/bench/bench.sh" review_oracle.py "$@" > /dev/null 2>&1 &
echo "PID=$! log=$PROJ/logs/bench_review_oracle.log"
