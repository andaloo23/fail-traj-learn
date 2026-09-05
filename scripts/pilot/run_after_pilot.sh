#!/usr/bin/env bash
# Wait until pilot_molmoact2.sh has written its "pilot end" line (and no recorder is running), then start
# pilot_base.sh. Lets stage D run unattended right after the main pilot without competing for the GPU.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
MASTER="$PROJ/logs/pilot_molmoact2.log"
echo "[run_after_pilot] waiting for pilot end at $(date -Is)"
while true; do
  if grep -aq "=== pilot end" "$MASTER" && ! pgrep -f "record_rollouts.p[y]" > /dev/null; then break; fi
  sleep 60
done
echo "[run_after_pilot] pilot finished, starting pilot_base.sh at $(date -Is)"
bash "$SCRIPTS/pilot/pilot_base.sh"
echo "[run_after_pilot] done at $(date -Is)"
