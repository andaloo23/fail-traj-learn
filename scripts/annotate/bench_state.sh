#!/usr/bin/env bash
# Machine state before a benchmark run: GPU, running annotator/lab processes, annot dirs, corpus failure counts.
PROJ=/home/aliu/projects/fail-traj-learn
echo "== gpu"; nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu,temperature.gpu --format=csv,noheader
echo "== python procs"; pgrep -af "annotate.py|segmentation_lab|run_segmentation_loop|local_segmenter|event_experiment|record_rollouts" || echo none
echo "== annot tags"; ls "$PROJ/annot" 2>/dev/null
echo "== failures per dataset family (episodes.jsonl)"
for d in "$PROJ"/data/full_*; do
  n=$(wc -l < "$d/episodes.jsonl"); f=$(grep -c '"success": false' "$d/episodes.jsonl")
  echo "$(basename "$d") total=$n fail=$f"
done | sed 's/__t[0-9]*//' | awk '{split($2,a,"=");split($3,b,"="); t[$1]+=a[2]; f[$1]+=b[2]} END {for (k in t) print k, "episodes", t[k], "failures", f[k]}' | sort
echo "== disk"; df -h /home/aliu | tail -1
