"""Fetch pinned NVIDIA inference code; optionally cache its model weights.

Code-only download uses the standard library and does not download model tensors.
The data engine's own models.json pins its separate weight revisions; preserve it.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import urllib.request

LOCK = Path(__file__).with_name("models.lock.json")


def fetch(url):
    headers = {"User-Agent": "fail-traj-learn-flora/1"}
    if os.environ.get("HF_TOKEN"):
        headers["Authorization"] = "Bearer " + os.environ["HF_TOKEN"]
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=120) as response:
        return response.read()


def prepare(root, component, weights=False):
    spec = json.loads(LOCK.read_text(encoding="utf-8"))[component]
    target = root / component
    api = json.loads(fetch(f"https://huggingface.co/api/models/{spec['repo']}/revision/{spec['revision']}"))
    if api["sha"] != spec["revision"]:
        raise ValueError("Hub returned a different code revision")
    names = [f["rfilename"] for f in api["siblings"]
             if f["rfilename"].startswith("batch_utils/") or f["rfilename"] in ("infer.py", "README.md")]

    def download(name):
        rel = PurePosixPath(name)
        if rel.is_absolute() or ".." in rel.parts or "\\" in name:
            raise ValueError("Unsafe Hub filename")
        content = fetch(f"https://huggingface.co/{spec['repo']}/resolve/{spec['revision']}/{name}")
        dest = target / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists() and dest.read_bytes() != content:
            raise ValueError(f"Existing code differs: {dest}. Choose a fresh --root.")
        if not dest.exists():
            dest.write_bytes(content)
        return name, hashlib.sha256(content).hexdigest()

    with ThreadPoolExecutor(max_workers=4) as pool:
        hashes = dict(pool.map(download, names))
    receipt = dict(spec, files=hashes)
    (target / "fetch_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"Pinned {component} code ready: {target}", flush=True)
    if weights:
        from huggingface_hub import snapshot_download
        if component == "rewarder":
            path = snapshot_download(spec["repo"], revision=spec["revision"])
            print(f"Rewarder weights cached: {path}")
        else:
            models = json.loads((target / "batch_utils/models.json").read_text(encoding="utf-8"))
            for kind, model in models.items():
                kwargs = {}
                if kind != "tempseg_base":
                    kwargs["local_dir"] = root / "models" / kind
                path = snapshot_download(model["repo"], revision=model["revision"], **kwargs)
                print(f"{kind} weights cached: {path}", flush=True)
    return target


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, required=True)
    p.add_argument("--component", choices=["rewarder", "data-engine"], required=True)
    p.add_argument("--weights", action="store_true")
    a = p.parse_args()
    prepare(a.root.expanduser().resolve(), a.component, a.weights)
