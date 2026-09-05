"""Probe articulated fixtures in a LIBERO scene: fixtures_dict, non-robot joints, their qpos addresses.

Usage: probe_fixtures.py [suite] [task_id]   (default libero_goal 3: drawer + bowl)
"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")
from lerobot.envs.libero import LiberoEnv, _get_suite

suite_name = sys.argv[1] if len(sys.argv) > 1 else "libero_goal"
tid = int(sys.argv[2]) if len(sys.argv) > 2 else 3
suite = _get_suite(suite_name)
env = LiberoEnv(suite, tid, suite_name, obs_type="pixels", observation_width=128, observation_height=128)
env.reset(seed=0)
rs = env._env.env
sim = rs.sim
print(f"{suite_name}[{tid}] '{suite.get_task(tid).language}'")
print("objects_dict:", list(rs.objects_dict.keys()))
print("fixtures_dict:", list(getattr(rs, 'fixtures_dict', {}).keys()))
free = set()
for name, o in list(rs.objects_dict.items()) + list(getattr(rs, 'fixtures_dict', {}).items()):
    print(f"  {name}: joints={getattr(o, 'joints', None)} root_body={getattr(o, 'root_body', None)}")
    for j in getattr(o, 'joints', []) or []:
        free.add(j)
print("--- non-robot joints (name, qpos addr, type) ---")
import mujoco
for jn in sim.model.joint_names:
    if jn.startswith("robot0") or jn.startswith("gripper0"):
        continue
    addr = sim.model.get_joint_qpos_addr(jn)
    jid = sim.model.joint_name2id(jn)
    jtype = int(sim.model.jnt_type[jid])
    tname = {0: "free", 1: "ball", 2: "slide", 3: "hinge"}.get(jtype, str(jtype))
    q = sim.data.qpos[addr] if isinstance(addr, int) else sim.data.qpos[addr[0]:addr[1]]
    print(f"  {jn:40s} addr={addr} type={tname} free_joint={jn in free} qpos={q if isinstance(addr, int) else '(7)'}")
# what does the success predicate look at?
try:
    print("--- parsed goal state ---")
    print(rs.parsed_problem["goal_state"])
except Exception as e:
    print("goal state unavailable:", e)
env.close()
print("PROBE_FIXTURES_OK")
