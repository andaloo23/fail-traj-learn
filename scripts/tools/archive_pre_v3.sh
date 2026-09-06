#!/usr/bin/env bash
# Move every dataset that is not part of the schema v3 full run into data/archive_pre_v3/ so downstream code cannot
# load a v1/v2 episode by accident. Idempotent.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
cd "$PROJ/data" || exit 1
mkdir -p archive_pre_v3
n=0
for d in */; do
  d=${d%/}
  case "$d" in full_*|archive_pre_v3) continue ;; esac
  mv "$d" archive_pre_v3/ && n=$((n + 1))
done
echo "moved $n datasets; remaining:"; ls
du -sh archive_pre_v3
