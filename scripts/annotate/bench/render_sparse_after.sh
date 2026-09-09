#!/usr/bin/env bash
# Wait for any running oracle_reference.py rebuild to finish, then render the observable-sparse review videos.
while pgrep -f "oracle_reference.py" > /dev/null; do sleep 10; done
exec bash /mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/annotate/bench/bench.sh render_sparse_review.py "$@"
