#!/usr/bin/env bash
# Download the annotator VLM into the HF cache (resumable). Usage: download_model.sh [repo_id]
PROJ=/home/aliu/projects/fail-traj-learn
MODEL=${1:-Qwen/Qwen3-VL-8B-Instruct}
mkdir -p "$PROJ/logs"
LOG="$PROJ/logs/download_$(echo "$MODEL" | tr '/' '_').log"
echo "$(date -Is) start $MODEL" >> "$LOG"
"$PROJ/lerobot/.venv/bin/python" - "$MODEL" >> "$LOG" 2>&1 <<'EOF'
import sys, time
from huggingface_hub import snapshot_download
t = time.time()
p = snapshot_download(sys.argv[1], max_workers=4)
print(f"DONE {p} in {time.time()-t:.0f}s", flush=True)
EOF
echo "$(date -Is) exit=$? " >> "$LOG"
