#!/usr/bin/env bash
# Rebuild ALL references detached through bench.sh (CPU only); output goes to $PROJ/logs/bench_oracle_reference.log.
#   oracle_reference_bg.sh [--overwrite] [--datasets prefixes...]   (default: --overwrite, all ten families)
# Prints the PID; follow with: tail -f /home/aliu/projects/fail-traj-learn/logs/bench_oracle_reference.log
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export PROJ SCRIPTS
mkdir -p "$PROJ/logs"
if [ $# -eq 0 ]; then
  set -- --overwrite --datasets full_anchor full_shift4 full_shift8 full_shift12 full_shift16 full_goal full_goals8 full_l90 full_l10s8 full_l10s12
fi
if pgrep -f "oracle_reference.py" > /dev/null; then
  echo "oracle_reference.py is already running:"; pgrep -af "oracle_reference.py"; exit 1
fi
# setsid: a plain nohup child dies with the wsl.exe session that launched it (observed 2026-09-08: the log never got its header)
setsid nohup bash "$SCRIPTS/annotate/bench/bench.sh" oracle_reference.py "$@" > /dev/null 2>&1 < /dev/null &
sleep 3
echo "PID=$! log=$PROJ/logs/bench_oracle_reference.log"
pgrep -af "oracle_reference.py" || echo "WARNING: not running after 3 s"
tail -2 "$PROJ/logs/bench_oracle_reference.log"
