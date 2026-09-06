#!/usr/bin/env bash
# Acceptance checks for a finished full run. Args: dataset prefixes (default: the full_run.sh stages).
# Prints per-prefix success/progress, predicate-artifact counts (must be 0), a snapshot-restore spot check on the
# first dataset of each prefix, and contact sheets for a few failures per prefix. Ends with ACCEPT_OK / ACCEPT_FAIL.
PROJ=${PROJ:-/home/aliu/projects/fail-traj-learn}
SCRIPTS=${SCRIPTS:-/mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts}
export PROJ SCRIPTS
PREFIXES=${*:-"full_anchor full_shift4 full_shift8 full_shift12 full_shift16 full_goal full_l90 full_l10s8 full_l10s12 full_goals8"}
cd "$PROJ/lerobot"
ok=1
echo "== success rates"
.venv/bin/python "$SCRIPTS/analysis/summarize_datasets.py" $PREFIXES 2>/dev/null
for p in $PREFIXES; do
  echo; echo "== $p progress"
  .venv/bin/python "$SCRIPTS/analysis/episode_progress.py" "$p" 2>&1 | grep -vE 'FutureWarning|warnings\.warn|^[[:space:]]*$' | head -6
  echo "== $p predicate artifacts"
  out=$(.venv/bin/python "$SCRIPTS/analysis/predicate_artifacts.py" "$p" 2>&1 | grep -vE 'FutureWarning|warnings\.warn' | tail -1)
  echo "$out"
  n=$(echo "$out" | sed -n 's/.*rotation-correct test: \([0-9]*\);.*/\1/p')
  if [ -n "$n" ] && [ "$n" != "0" ]; then echo "!! $p has $n artifact failures"; ok=0; fi
  first=$(ls -d "$PROJ/data/${p}__t"* 2>/dev/null | head -1)
  if [ -n "$first" ]; then
    echo "== $p snapshot restore spot check ($(basename "$first"))"
    r=$(.venv/bin/python "$SCRIPTS/analysis/check_snapshot_restore.py" "$(basename "$first")" --replay 20 2>&1 | grep -E 'RESTORE_|FAIL' | tail -3)
    echo "$r"
    echo "$r" | grep -q RESTORE_OK || ok=0
    .venv/bin/python "$SCRIPTS/analysis/review_failures.py" "$(basename "$first")" --max 3 2>&1 | grep -E 'wrote|reviewing' | tail -2
  fi
done
echo; echo "== initial-state audit (shifted stages; bad inits must be 0)"
shifted=$(for p in $PREFIXES; do case "$p" in *shift*|*s8|*s12) echo "$p";; esac; done)
if [ -n "$shifted" ]; then
  ic=$(.venv/bin/python "$SCRIPTS/analysis/init_state_check.py" full_anchor $shifted 2>&1 | grep -E "BAD INIT")
  echo "$ic"
  echo "$ic" | grep -qE "BAD INIT[^:]*: [1-9]" && ok=0
fi
echo; [ $ok = 1 ] && echo ACCEPT_OK || echo ACCEPT_FAIL
