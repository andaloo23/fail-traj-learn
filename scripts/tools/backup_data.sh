#!/usr/bin/env bash
# Mirror the recorded corpus (data/) and logs/ from the WSL disk image to a Windows drive, so a hard power-off that
# corrupts the ext4 VHD cannot take the datasets with it. Incremental (rsync); safe to re-run. Args: destination
# directory as seen from WSL (default /mnt/d/fail-traj-learn-backup).
set -uo pipefail
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
DEST=${1:-/mnt/d/fail-traj-learn-backup}
mkdir -p "$DEST"
echo "backup start $(date -Is) -> $DEST"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --no-perms --no-owner --no-group --info=stats1 "$PROJ/data/" "$DEST/data/"
  rsync -a --no-perms --no-owner --no-group "$PROJ/logs/" "$DEST/logs/"
else
  cp -r "$PROJ/data/." "$DEST/data/" && cp -r "$PROJ/logs/." "$DEST/logs/"
fi
echo "backup end $(date -Is) rc=$?"
du -sh "$DEST/data" "$DEST/logs"
echo BACKUP_DONE
