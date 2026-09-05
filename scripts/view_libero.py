"""Open an interactive MuJoCo viewer window (via WSLg) on a LIBERO task and replay a scripted arm motion.

Usage:  view_libero.py [suite] [task_id] [seconds]
Controls in the window: left-drag rotate, right-drag pan, scroll zoom, double-click to select a body.
"""
import os, sys, time
# Offscreen rendering (env cameras) stays on EGL; the on-screen viewer uses GLFW via WSLg.
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
import numpy as np
import mujoco
import mujoco.viewer
from lerobot.envs.libero import LiberoEnv, _get_suite, get_libero_dummy_action

suite_name = sys.argv[1] if len(sys.argv) > 1 else "libero_object"
task_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
seconds = float(sys.argv[3]) if len(sys.argv) > 3 else 60.0

suite = _get_suite(suite_name)
print(f"{suite_name}[{task_id}]: {suite.get_task(task_id).language}")
env = LiberoEnv(suite, task_id, suite_name, obs_type="pixels", observation_width=128, observation_height=128, num_steps_wait=10)
env.reset(seed=0)
sim = env._env.env.sim
model, data = sim.model._model, sim.data._data  # underlying mujoco structs

print("opening viewer window (WSLg)...")
t0 = time.time()
with mujoco.viewer.launch_passive(model, data) as viewer:
    step = 0
    while viewer.is_running() and time.time() - t0 < seconds:
        # small scripted wiggle so the arm visibly moves: oscillate x/y delta, keep gripper open
        a = np.zeros(7, dtype=np.float32)
        a[0] = 0.4 * np.sin(step / 15.0)
        a[1] = 0.4 * np.cos(step / 15.0)
        a[6] = -1.0
        env.step(a)
        viewer.sync()
        step += 1
        time.sleep(0.05)
print(f"viewer closed after {time.time() - t0:.1f}s, {step} steps")
env.close()
