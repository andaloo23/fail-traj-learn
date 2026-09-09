"""Save 2x-enlarged tiles for chosen chunks (every frame of each chunk) plus the last frame, for human inspection of
what the VLM saw. Usage: zoom_episode.py <dataset> <episode> <chunk> [chunk ...]   -> outputs/annot_preview/<dataset>/zoom_*.png"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import WIN_OUT, Episode, open_dataset  # noqa: E402
from render import tile_frame  # noqa: E402

name, ep_i = sys.argv[1], int(sys.argv[2])
chunks = [int(c) for c in sys.argv[3:]]
ds = open_dataset(name)
ep = Episode(ds, name, ep_i)
out = WIN_OUT / "annot_preview" / name
out.mkdir(parents=True, exist_ok=True)
print(f"{name} ep{ep_i} success={ep.success} n={ep.n} chunks={ep.n_chunks} objects={ep.meta['object_slots']} targets={ep.meta['target_objects']}")
for c in chunks:
    a, b = ep.chunks[c]
    tiles = []
    for i in range(a, b, 2):
        ag, wr = ep.frame(i)
        tiles.append(np.asarray(tile_frame(ag, wr, f"chunk {c} step {i}")))
    strip = Image.fromarray(np.concatenate(tiles, axis=0)).resize((1024, 512 * len(tiles)), Image.LANCZOS)
    strip.save(out / f"zoom_ep{ep_i:04d}_chunk{c:02d}.png")
ag, wr = ep.frame(ep.n - 1)
Image.fromarray(np.asarray(tile_frame(ag, wr, f"last step {ep.n - 1}"))).resize((1024, 512), Image.LANCZOS).save(out / f"zoom_ep{ep_i:04d}_last.png")
print(f"wrote to {out}")
