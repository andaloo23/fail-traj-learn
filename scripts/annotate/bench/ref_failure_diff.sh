#!/usr/bin/env bash
# Rebuild a sample of FAILURE references into a scratch bench dir with the current oracle_reference.py and compare
# them byte-for-byte with the references under $PROJ/bench/references (proof that a code change left failures intact).
# Usage: ref_failure_diff.sh [limit_per_dataset] [dataset prefixes...]
PROJ=/home/aliu/projects/fail-traj-learn
SCRIPTS=/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts
LIMIT=${1:-2}; shift || true
DS=${@:-full_shift8 full_shift12 full_shift16 full_goal full_goals8 full_l90 full_l10s8 full_l10s12}
CHECK=$PROJ/bench/.refcheck
rm -rf "$CHECK/references"
mkdir -p "$CHECK" "$PROJ/logs"
cd "$PROJ/lerobot"
export PYTHONUNBUFFERED=1 CUDA_VISIBLE_DEVICES="" FTL_PROJ="$PROJ" FTL_BENCH="$CHECK" HF_DATASETS_CACHE="$PROJ/bench/.hf_cache"
.venv/bin/python "$SCRIPTS/annotate/bench/oracle_reference.py" --datasets $DS --failures-only --limit "$LIMIT" > "$PROJ/logs/ref_failure_diff.log" 2>&1
echo "build exit=$? (log: $PROJ/logs/ref_failure_diff.log)"
same=0; diff=0; missing=0
for f in $(find "$CHECK/references" -name 'episode_*.json' | sort); do
  rel=${f#$CHECK/references/}
  ref=$PROJ/bench/references/$rel
  if [ ! -f "$ref" ]; then missing=$((missing + 1)); echo "MISSING $rel"; continue; fi
  if cmp -s "$f" "$ref"; then same=$((same + 1)); else diff=$((diff + 1)); echo "DIFF $rel"; fi
done
echo "identical=$same different=$diff missing=$missing"
