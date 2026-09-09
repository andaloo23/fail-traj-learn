"""Does env.reset() change the MuJoCo MODEL (fixture body positions/orientations, geom sizes)? If yes, a saved
sim state (qpos/qvel) is not enough to reproduce an episode: the model of the recording env must be rebuilt too.

Usage: probe_reset_model.py <suite> <task_id> <seedA> <seedB>
Prints the model bodies whose pos/quat differ between reset(seedA), reset(seedB) and a second reset(seedA).
"""
import os
import sys

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np

from lerobot.envs.libero import LiberoEnv, _get_suite

suite_name, task_id, sa, sb = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
suite = _get_suite(suite_name)
env = LiberoEnv(suite, task_id, suite_name, obs_type="pixels_agent_pos", observation_width=128, observation_height=128, num_steps_wait=10)


def snapshot(seed):
    env.reset(seed=seed)
    sim = env._env.env.sim
    m = sim.model
    names = [m.body_id2name(i) for i in range(m.nbody)]
    return names, np.array(m.body_pos), np.array(m.body_quat), np.array(m.geom_size), np.array(m.geom_pos), np.array(sim.data.qpos)


n1, p1, q1, g1, gp1, qp1 = snapshot(sa)
n2, p2, q2, g2, gp2, qp2 = snapshot(sb)
n3, p3, q3, g3, gp3, qp3 = snapshot(sa)
print(f"{suite_name}[{task_id}] nbody={len(n1)}")
for label, (pa, qa, ga, gpa, qpa), (pb, qb, gb, gpb, qpb) in [
    (f"seed {sa} vs seed {sb}", (p1, q1, g1, gp1, qp1), (p2, q2, g2, gp2, qp2)),
    (f"seed {sa} vs seed {sa} again", (p1, q1, g1, gp1, qp1), (p3, q3, g3, gp3, qp3)),
]:
    dp = np.abs(pa - pb).max(axis=1)
    dq = np.abs(qa - qb).max(axis=1)
    moved = [(n1[i], float(dp[i]), float(dq[i])) for i in range(len(n1)) if dp[i] > 1e-9 or dq[i] > 1e-9]
    print(f"-- {label}: bodies with different model pos/quat: {len(moved)}; geom_size diff {np.abs(ga - gb).max():.1e}; "
          f"geom_pos diff {np.abs(gpa - gpb).max():.1e}; qpos diff {np.abs(qpa - qpb).max():.2e}")
    for nm, a, b in moved[:15]:
        print(f"     {nm:40s} pos {a:.4f} quat {b:.4f}")
env.close()
