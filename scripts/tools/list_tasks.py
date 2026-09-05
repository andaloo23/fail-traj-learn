"""List LIBERO tasks for one or more suites: id, scene folder, bddl file, language.

Usage: list_tasks.py [suite ...]   (default: libero_90)
"""
import sys
from collections import Counter

from lerobot.envs.libero import _get_suite

suites = sys.argv[1:] or ["libero_90"]
for s in suites:
    suite = _get_suite(s)
    print(f"=== {s}: {suite.n_tasks} tasks ===")
    scenes = Counter()
    for i in range(suite.n_tasks):
        t = suite.get_task(i)
        scene = t.bddl_file.split("_SCENE")[0] + "_SCENE" + t.bddl_file.split("_SCENE")[1].split("_")[0] if "_SCENE" in t.bddl_file else t.problem_folder
        scenes[scene] += 1
        print(f"{i:3d}  {scene:22s}  {t.language}")
    print("--- scenes ---")
    for k, v in sorted(scenes.items()):
        print(f"  {k}: {v}")
