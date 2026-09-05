"""Render the first frame (agent view + wrist view) of selected LIBERO tasks into one montage."""
import os
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
import numpy as np
from PIL import Image, ImageDraw
from lerobot.envs.libero import LiberoEnv, _get_suite

OUT = "/home/aliu/projects/fail-traj-learn/outputs"
os.makedirs(OUT, exist_ok=True)

# (suite, task_id) pairs to show
picks = [("libero_object", 0), ("libero_object", 5), ("libero_spatial", 0), ("libero_goal", 0), ("libero_goal", 1), ("libero_10", 0)]

# print all libero_goal task names so we can pick the drawer/stove ones
goal = _get_suite("libero_goal")
print("libero_goal tasks:")
for i in range(goal.n_tasks):
    print(f"  {i}: {goal.get_task(i).language}")

tiles = []
for suite_name, tid in picks:
    suite = _get_suite(suite_name)
    lang = suite.get_task(tid).language
    env = LiberoEnv(suite, tid, suite_name, obs_type="pixels", observation_width=256, observation_height=256, num_steps_wait=10)
    obs, _ = env.reset(seed=0)
    agent = obs["pixels"]["image"][::-1]
    wrist = obs["pixels"]["image2"][::-1]
    env.close()
    pair = np.concatenate([agent, wrist], axis=1)  # 256 x 512
    tile = Image.fromarray(pair)
    canvas = Image.new("RGB", (512, 256 + 28), (20, 20, 20))
    canvas.paste(tile, (0, 28))
    d = ImageDraw.Draw(canvas)
    d.text((6, 6), f"{suite_name}[{tid}]: {lang}"[:80], fill=(255, 255, 255))
    tiles.append(canvas)
    Image.fromarray(agent).save(f"{OUT}/scene_{suite_name}_{tid}.png")
    print(f"rendered {suite_name}[{tid}]: {lang}")

cols = 2
rows = (len(tiles) + cols - 1) // cols
W, H = tiles[0].size
montage = Image.new("RGB", (cols * W, rows * H), (0, 0, 0))
for i, t in enumerate(tiles):
    montage.paste(t, ((i % cols) * W, (i // cols) * H))
montage.save(f"{OUT}/libero_scenes_montage.png")
print("MONTAGE_OK", f"{OUT}/libero_scenes_montage.png")
