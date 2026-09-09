"""Build a gallery of what each LIBERO object looks like in our recordings, to write the prompt glossary from evidence.
For each dataset family's task 0..N episode 0, take the frame where the target is first grasped (oracle column) and save
agentview | wrist tiles labelled with the object name. Also saves the first frame of each scene with all object slots.
Usage: object_gallery.py [prefix ...]   -> outputs/annot_preview/_gallery/"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WIN_OUT, Episode, list_datasets, open_dataset, read_episodes_jsonl  # noqa: E402
from render import tile_frame  # noqa: E402

out = WIN_OUT / "annot_preview" / "_gallery"
out.mkdir(parents=True, exist_ok=True)
seen = set()
for name in list_datasets(sys.argv[1:]):
    eps = read_episodes_jsonl(name)
    if not eps:
        continue
    ds = open_dataset(name)
    key = (eps[0]["suite"], eps[0]["task_id"])
    if key in seen:
        continue
    seen.add(key)
    ep = Episode(ds, name, eps[0]["episode_index"])
    slots = ep.meta["object_slots"]
    grasp = ep.col("priv.obj_grasped")
    ag, wr = ep.frame(0)
    Image.fromarray(np.asarray(tile_frame(ag, wr, f"{key[0]}[{key[1]}] start"))).resize((1024, 512)).save(
        out / f"scene_{key[0]}_{key[1]:02d}.png")
    for s, obj in enumerate(slots):
        g = np.flatnonzero(grasp[:, s] > 0)
        if len(g) == 0:
            continue
        i = int(g[min(len(g) - 1, 5)])
        ag, wr = ep.frame(i)
        Image.fromarray(np.asarray(tile_frame(ag, wr, f"{obj} (grasped, step {i})"))).resize((1024, 512)).save(
            out / f"obj_{obj}_{key[0]}_{key[1]:02d}.png")
        print(f"{name}: {obj} grasped at step {i}")
    print(f"{name}: slots={slots} fixtures={ep.meta.get('fixtures')} task='{ep.task}'")
print(f"wrote to {out}")
