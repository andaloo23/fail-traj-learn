"""Print the normalization tags (robot setups) available in a MolmoAct2 checkpoint's norm_stats.json.

Usage: inspect_norm_stats.py <hf_repo_id>   e.g. allenai/MolmoAct2
"""
import glob
import json
import sys
from pathlib import Path

repo = sys.argv[1] if len(sys.argv) > 1 else "allenai/MolmoAct2"
d = Path.home() / ".cache/huggingface/hub" / ("models--" + repo.replace("/", "--")) / "snapshots"
paths = glob.glob(str(d / "*" / "norm_stats.json"))
if not paths:
    print(f"no norm_stats.json found under {d}")
    sys.exit(1)
ns = json.load(open(paths[0]))
tags = ns.get("metadata_by_tag", {})
print(f"{repo}: {len(tags)} tags in {paths[0]}")
for k, v in tags.items():
    print(f"  {k:28s} setup={v.get('setup_type')!r:45s} control={v.get('control_mode')!r} horizon={v.get('action_horizon')} cams={v.get('camera_keys')}")
