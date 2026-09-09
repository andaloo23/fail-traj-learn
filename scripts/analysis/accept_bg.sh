#!/usr/bin/env bash
# Run accept_run.sh with its full output in logs/accept_run.log and the verdict lines appended to the master log.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export PROJ SCRIPTS
MASTER="$PROJ/logs/full_run.log"
echo "=== acceptance start $(date -Is) ===" | tee -a "$MASTER"
bash "$SCRIPTS/analysis/accept_run.sh" "$@" 2>&1 | tee "$PROJ/logs/accept_run.log" | grep -E "^== |!!|RESTORE_|BAD INIT|ACCEPT_" | tee -a "$MASTER"
echo "=== acceptance end $(date -Is) ===" | tee -a "$MASTER"
