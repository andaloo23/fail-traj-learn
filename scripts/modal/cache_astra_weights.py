"""Cache the pinned Qwen checkpoint on the pilot Volume using a CPU worker."""
from pathlib import Path
import sys

import modal

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "distill"))
from qwen_backbone_timing import MODELS

MODEL, REVISION = MODELS["candidate"]
volume = modal.Volume.from_name("qwen-astra-pilot", create_if_missing=True)
app = modal.App("qwen38-astra-cache")
image = (
    modal.Image.debian_slim(python_version="3.12")
    .pip_install("huggingface-hub")
    .env({"PYTHONPATH": "/root/qwen_astra_imports"})
    .add_local_file(Path(__file__).resolve().parents[1] / "distill" / "qwen_backbone_timing.py",
                    "/root/qwen_astra_imports/qwen_backbone_timing.py")
) if modal.is_local() else None


@app.function(image=image, cpu=2, memory=8192, timeout=2400, volumes={"/astra": volume})
def cache() -> str:
    from huggingface_hub import snapshot_download

    snapshot_download(MODEL, revision=REVISION, cache_dir="/astra/hf",
                      allow_patterns=["*.safetensors", "*.json", "*.jinja", "*.txt"])
    volume.commit()
    return f"/astra/hf/models--{MODEL.replace('/', '--')}/snapshots/{REVISION}"
