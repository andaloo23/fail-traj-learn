#!/usr/bin/env bash
# Stop a running oracle_reference.py rebuild (references already written are kept; the build is resumable).
pgrep -af "oracle_reference.py" || echo "no oracle_reference.py running"
pkill -f "oracle_reference.py" && echo "killed oracle_reference.py"
sleep 1
pgrep -af "oracle_reference.py|oracle_labels.py" || echo "nothing left"
