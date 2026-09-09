#!/usr/bin/env bash
# Stop a running review_oracle.py render (launched by review_oracle_bg.sh). Rendered episodes are kept; a later run
# without --overwrite skips them (resumable).
pgrep -af "review_oracle.py" || echo "no review_oracle.py process"
pkill -f "bench.sh review_oracle.py"
pkill -f "review_oracle.py"
sleep 2
pkill -9 -f "review_oracle.py"
pgrep -af "review_oracle.py" || echo "stopped: no review_oracle.py running"
pgrep -af "ffmpeg.*oracle_review" || echo "no ffmpeg writing to oracle_review"
