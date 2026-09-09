#!/usr/bin/env bash
# Stop a running benchmark method: kill_method.sh <method name>. Predictions already written are kept (resumable).
pat="run_method.py --method $1"
pgrep -af "$pat" || echo "no process for $pat"
pkill -f "$pat" && echo "killed $pat"
sleep 2
pgrep -af "run_method.py" || echo "no run_method.py running"
