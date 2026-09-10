#!/usr/bin/env bash
# Cache visual features for a whole corpus, a few datasets at a time in parallel.
# Each worker opens its own MuJoCo/EGL context and its own copy of the 86M vision tower (~2.5 GB), so
# WORKERS is bounded by GPU memory, not by cores. Re-running is safe: encode_frames.py skips datasets
# that already have a .npy, so a killed run resumes where it stopped.
#
# Usage: encode_all.sh [corpus] ; env: WORKERS, BATCH
set -u
R=${R:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl}
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
CORPUS=${1:-object}
WORKERS=${WORKERS:-5}
BATCH=${BATCH:-32}
export FTL_PROJ="$PROJ"

mapfile -t NAMES < <("$PROJ/lerobot/.venv/bin/python" - "$CORPUS" <<'EOF'
import sys
sys.path.insert(0, "/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/rl")
import common as C
print("\n".join(C.expand([sys.argv[1]])))
EOF
)
echo "== encoding ${#NAMES[@]} datasets from corpus '$CORPUS' with $WORKERS workers"
date -Is

pids=()
for w in $(seq 0 $((WORKERS - 1))); do
  subset=()
  for i in "${!NAMES[@]}"; do
    [ $((i % WORKERS)) -eq "$w" ] && subset+=("${NAMES[$i]}")
  done
  [ ${#subset[@]} -eq 0 ] && continue
  ( bash "$R/py.sh" encode_frames.py --datasets "${subset[@]}" --batch "$BATCH" \
      > "$PROJ/logs/encode_w$w.log" 2>&1 ) &
  pids+=($!)
  echo "  worker $w: ${#subset[@]} datasets -> logs/encode_w$w.log"
done

fail=0
for p in "${pids[@]}"; do wait "$p" || fail=1; done
echo "== done (fail=$fail)"; date -Is
ls "$PROJ/rl/features/smolvlm2_500m_siglip_256" | wc -l
exit "$fail"
