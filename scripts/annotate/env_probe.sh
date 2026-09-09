#!/usr/bin/env bash
# Probe the WSL side for the annotator environment: GPU, disk, HF cache, venv package versions.
PROJ=/home/aliu/projects/fail-traj-learn
echo "== nvidia-smi"; nvidia-smi --query-gpu=name,memory.total,memory.used,driver_version --format=csv,noheader
echo "== disk"; df -h /home/aliu | tail -1
echo "== hf cache"; ls ~/.cache/huggingface/hub 2>/dev/null | head -30
echo "== data dirs"; ls "$PROJ/data" | wc -l; ls "$PROJ/data" | sed 's/__t.*//' | sort | uniq -c
echo "== venvs"; ls -d "$PROJ"/*/.venv "$PROJ"/.venv* 2>/dev/null
echo "== lerobot venv versions"
"$PROJ/lerobot/.venv/bin/python" - <<'EOF'
import importlib
for m in ["torch","transformers","accelerate","qwen_vl_utils","av","PIL","pydantic","numpy"]:
    try:
        mod = importlib.import_module(m); print(m, getattr(mod, "__version__", "?"))
    except Exception as e:
        print(m, "MISSING", type(e).__name__)
import torch; print("cuda", torch.cuda.is_available(), torch.version.cuda)
EOF
echo "== uv"; /home/aliu/.local/bin/uv --version
echo "== python versions available"; /home/aliu/.local/bin/uv python list 2>/dev/null | head -8
echo "== one sidecar sample"
d=$(ls -d "$PROJ"/data/full_shift8__t0 2>/dev/null | head -1); echo "$d"; ls "$d" | head; head -c 1200 "$d/sidecar/episode_000000.json"; echo; python3 -c "import numpy as np,sys; z=np.load('$d/sidecar/episode_000000.npz'); print({k: z[k].shape for k in z.files})" 2>/dev/null || "$PROJ/lerobot/.venv/bin/python" -c "import numpy as np; z=np.load('$d/sidecar/episode_000000.npz'); print({k: z[k].shape for k in z.files})"
head -2 "$d/episodes.jsonl"
echo "== info.json"; head -c 600 "$d/meta/info.json"
