"""Probe: create one LIBERO env, render a frame, list raw simulator obs keys (privileged state)."""
import os, sys, time
os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
import numpy as np
from lerobot.envs.libero import LiberoEnv, _get_suite, get_libero_dummy_action

suite_name = sys.argv[1] if len(sys.argv) > 1 else "libero_object"
task_id = int(sys.argv[2]) if len(sys.argv) > 2 else 0
suite = _get_suite(suite_name)
task = suite.get_task(task_id)
print(f"suite={suite_name} task_id={task_id} n_tasks={suite.n_tasks}")
print(f"language: {task.language}")
print(f"bddl: {task.bddl_file}")

t0 = time.time()
env = LiberoEnv(suite, task_id, suite_name, obs_type="pixels_agent_pos",
                observation_width=256, observation_height=256, num_steps_wait=10)
obs, info = env.reset(seed=0)
print(f"env created+reset in {time.time()-t0:.1f}s; info={info}")

print("--- policy-facing obs ---")
for cam, img in obs["pixels"].items():
    print(f"  pixels[{cam}] shape={img.shape} dtype={img.dtype} mean={img.mean():.1f} std={img.std():.1f}")
rs = obs["robot_state"]
print(f"  eef pos={np.round(rs['eef']['pos'],3)} gripper qpos={np.round(rs['gripper']['qpos'],3)}")

print("--- raw robosuite obs keys (privileged state candidates) ---")
raw = env._env.env._get_observations()
for k in sorted(raw):
    v = raw[k]
    shp = getattr(v, "shape", None)
    if shp and len(shp) >= 3:
        print(f"  {k:45s} image {shp}")
    else:
        print(f"  {k:45s} {shp} {np.round(np.asarray(v).ravel()[:4],3)}")

inner = env._env.env
print("--- task objects ---")
for attr in ("obj_of_interest", "objects_dict", "fixtures_dict"):
    if hasattr(inner, attr):
        val = getattr(inner, attr)
        print(f"  {attr}: {list(val) if hasattr(val,'__iter__') else val}")
sim = inner.sim
print(f"  n_bodies={sim.model.nbody} n_geoms={sim.model.ngeom}")
print(f"  contacts now: {sim.data.ncon}")
print("--- geom names (non-robot) ---")
names = []
for gid in range(sim.model.ngeom):
    gname = sim.model.geom_id2name(gid) or f"<unnamed:{gid}>"
    bname = sim.model.body_id2name(int(sim.model.geom_bodyid[gid])) or "?"
    if not (bname.startswith("robot0") or bname.startswith("gripper0")):
        names.append(f"{gname} [body={bname}]")
print("  " + "\n  ".join(names[:80]))
print("--- contacts at rest (geom pairs) ---")
for i in range(min(sim.data.ncon, 40)):
    c = sim.data.contact[i]
    g1 = sim.model.geom_id2name(int(c.geom1)) or f"<unnamed:{int(c.geom1)}>"
    g2 = sim.model.geom_id2name(int(c.geom2)) or f"<unnamed:{int(c.geom2)}>"
    b1 = sim.model.body_id2name(int(sim.model.geom_bodyid[int(c.geom1)]))
    b2 = sim.model.body_id2name(int(sim.model.geom_bodyid[int(c.geom2)]))
    print(f"  {g1} [{b1}]  <->  {g2} [{b2}]")
print("--- gripper important_geoms ---")
try:
    print("  ", inner.robots[0].gripper.important_geoms)
except Exception as e:
    print("  unavailable:", e)

print("--- step 5 dummy actions ---")
for i in range(5):
    obs, r, term, trunc, info = env.step(np.array(get_libero_dummy_action(), dtype=np.float32))
print(f"  reward={r} terminated={term} info={info}")
print(f"  check_success={env._env.check_success()}")

out = os.path.expanduser("~/projects/fail-traj-learn/outputs")
os.makedirs(out, exist_ok=True)
from PIL import Image
for cam, img in obs["pixels"].items():
    Image.fromarray(img[::-1]).save(f"{out}/probe_{suite_name}_{task_id}_{cam}.png")
print(f"saved frames to {out}")
env.close()
print("PROBE OK")
