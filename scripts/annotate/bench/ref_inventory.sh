#!/usr/bin/env bash
# Inventory of references on disk: per family count, success count, newest/oldest mtime.
PROJ=/home/aliu/projects/fail-traj-learn
R=$PROJ/bench/references
echo "ref dir: $R"
ls "$R" | sed 's/__t.*//' | sort | uniq -c
echo "total refs: $(find "$R" -name 'episode_*.json' | wc -l)"
echo "success refs: $(grep -l '"success": true' -r "$R" --include='episode_*.json' | wc -l)"
echo "oldest: $(find "$R" -name 'episode_*.json' -printf '%TY-%Tm-%Td %TH:%TM\n' | sort | head -1)"
echo "newest: $(find "$R" -name 'episode_*.json' -printf '%TY-%Tm-%Td %TH:%TM\n' | sort | tail -1)"
echo "versions: $(grep -ho '"reference_version": "[a-z0-9]*"' -r "$R" | sort | uniq -c)"
echo "episodes per family (episodes.jsonl):"
for f in full_anchor full_shift4 full_shift8 full_shift12 full_shift16 full_goal full_goals8 full_l90 full_l10s8 full_l10s12; do
  n=0; s=0
  for d in "$PROJ"/data/${f}__t*; do
    [ -f "$d/episodes.jsonl" ] || continue
    n=$((n + $(wc -l < "$d/episodes.jsonl")))
    s=$((s + $(grep -c '"success": true' "$d/episodes.jsonl")))
  done
  echo "  $f episodes=$n successes=$s"
done
echo "gpu procs: $(pgrep -fc 'run_method.py|annotate.py|segmentation_lab.py')"
tail -3 "$PROJ/logs/bench_oracle_reference.log" 2>/dev/null
