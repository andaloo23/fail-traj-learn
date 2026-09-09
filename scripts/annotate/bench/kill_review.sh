#!/usr/bin/env bash
# Stop the oracle review renderer (and any ffmpeg it spawned).
pgrep -af "review_oracle.py" || echo "no review_oracle.py running"
pkill -f "review_oracle.py" && echo "killed review_oracle.py"
pkill -f "ffmpeg" && echo "killed ffmpeg"
sleep 1
pgrep -af "review_oracle.py|ffmpeg" || echo "nothing left"
