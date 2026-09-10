"""The learner observation: one low-dimensional vector built the same way offline and online.

`build_dataset.py` calls `ObsBuilder.from_columns` on recorded parquet columns; `eval_env.py` calls
`ObsBuilder.from_priv` on a live `PrivilegedReader.read()` dict. Both go through `_assemble`, so a policy
trained offline sees exactly the features it will see in the simulator.

Layout (v1, `SPEC_VERSION`), all float32, blocks concatenated in this order:

  proprio   27  eef_pos 3 | eef_rot6d 6 | gripper_qpos 2 | gripper_qvel 2 | joint_pos 7 | joint_vel 7
  target    16  pos 3 | rot6d 6 | pos-eef 3 | dist 1 | grasped 1 | gripper_contact 1 | support_contact 1
  goal      14  pos 3 | rot6d 6 | target-goal 3 | dist 1 | valid 1
  distract  20  4 nearest other objects, sorted by distance to the end effector:
                pos-eef 3 | dist 1 | gripper_contact 1 each
  contacts   3  n_contacts | arm_contacts | gripper_static_contacts   (all log1p-compressed)
  fixtures   8  4 one-DoF fixture joints: qpos 4 | valid 4 (zeros for suites without fixtures)
  time       2  t / max_steps | 1 - t / max_steps
  = 90
"""
from __future__ import annotations

import numpy as np

SPEC_VERSION = "obs_v1"
N_DISTRACTORS = 4
N_FIXTURE_JOINTS = 4
OBS_DIM = 27 + 16 + 14 + 5 * N_DISTRACTORS + 3 + 2 * N_FIXTURE_JOINTS + 2


def quat_xyzw_to_rot6d(q: np.ndarray) -> np.ndarray:
    """(..., 4) xyzw unit quaternion -> (..., 6): the first two columns of the rotation matrix.

    The 6D parameterisation is continuous in SO(3); raw quaternions are not (q and -q are the same
    rotation), which makes them a poor network input.
    """
    q = np.asarray(q, np.float32).reshape(-1, 4)
    n = np.linalg.norm(q, axis=1, keepdims=True)
    q = q / np.maximum(n, 1e-8)
    x, y, z, w = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    c0 = np.stack([1 - 2 * (y * y + z * z), 2 * (x * y + z * w), 2 * (x * z - y * w)], axis=1)
    c1 = np.stack([2 * (x * y - z * w), 1 - 2 * (x * x + z * z), 2 * (y * z + x * w)], axis=1)
    return np.concatenate([c0, c1], axis=1).astype(np.float32)


def _col(d, key, n_frames, width):
    """Column `key` as (n_frames, width) float32, whatever the parquet stored it as."""
    v = d[key]
    if isinstance(v, np.ndarray) and v.dtype == object:
        v = np.stack([np.asarray(x, np.float32) for x in v])
    arr = np.asarray(v, np.float32).reshape(n_frames, -1)
    if arr.shape[1] != width:
        raise ValueError(f"{key}: expected width {width}, got {arr.shape[1]}")
    return arr


class ObsBuilder:
    """Turns privileged simulator state into the learner observation for one episode / one env."""

    def __init__(self, target_slot: int, goal_slot: int, max_steps: int, n_slots: int = 12):
        self.target_slot = int(target_slot)
        self.goal_slot = int(goal_slot)
        self.max_steps = int(max_steps)
        self.n_slots = int(n_slots)

    # ---------------------------------------------------------------- offline
    def from_columns(self, cols: dict, n_frames: int, t0: int = 0) -> np.ndarray:
        """(n_frames, OBS_DIM) from recorded parquet columns; `t0` is the frame index of row 0."""
        n, s = n_frames, self.n_slots

        def g(k, w):
            return _col(cols, k, n, w)

        return self._assemble(
            eef_pos=g("priv.eef_pos", 3), eef_quat=g("priv.eef_quat", 4),
            grip_qpos=g("priv.gripper_qpos", 2), grip_qvel=g("priv.gripper_qvel", 2),
            joint_pos=g("priv.joint_pos", 7), joint_vel=g("priv.joint_vel", 7),
            obj_pos=g("priv.obj_pos", 3 * s).reshape(n, s, 3),
            obj_quat=g("priv.obj_quat", 4 * s).reshape(n, s, 4),
            obj_valid=g("priv.obj_valid", s),
            obj_contact=g("priv.obj_gripper_contact", s),
            obj_grasped=g("priv.obj_grasped", s),
            obj_support=g("priv.obj_support_contact", s),
            n_contacts=g("priv.n_contacts", 1)[:, 0],
            arm_contacts=g("priv.arm_contacts", 1)[:, 0],
            grip_static=g("priv.gripper_static_contacts", 1)[:, 0],
            fixture_qpos=g("priv.fixture_qpos", 16)[:, :N_FIXTURE_JOINTS],
            fixture_valid=g("priv.fixture_valid", 16)[:, :N_FIXTURE_JOINTS],
            t=np.arange(t0, t0 + n, dtype=np.float32),
        )

    # ----------------------------------------------------------------- online
    def from_priv(self, priv: dict, t: int) -> np.ndarray:
        """(OBS_DIM,) from one `PrivilegedReader.read()` dict at step `t`."""
        s = self.n_slots

        def one(a):
            return np.asarray(a, np.float32).reshape(1, -1)

        v = self._assemble(
            eef_pos=one(priv["priv.eef_pos"]), eef_quat=one(priv["priv.eef_quat"]),
            grip_qpos=one(priv["priv.gripper_qpos"]), grip_qvel=one(priv["priv.gripper_qvel"]),
            joint_pos=one(priv["priv.joint_pos"]), joint_vel=one(priv["priv.joint_vel"]),
            obj_pos=one(priv["priv.obj_pos"]).reshape(1, s, 3),
            obj_quat=one(priv["priv.obj_quat"]).reshape(1, s, 4),
            obj_valid=one(priv["priv.obj_valid"]),
            obj_contact=one(priv["priv.obj_gripper_contact"]),
            obj_grasped=one(priv["priv.obj_grasped"]),
            obj_support=one(priv["priv.obj_support_contact"]),
            n_contacts=one(priv["priv.n_contacts"])[:, 0],
            arm_contacts=one(priv["priv.arm_contacts"])[:, 0],
            grip_static=one(priv["priv.gripper_static_contacts"])[:, 0],
            fixture_qpos=one(priv["priv.fixture_qpos"])[:, :N_FIXTURE_JOINTS],
            fixture_valid=one(priv["priv.fixture_valid"])[:, :N_FIXTURE_JOINTS],
            t=np.array([t], np.float32),
        )
        return v[0]

    # --------------------------------------------------------------- assembly
    def _assemble(self, *, eef_pos, eef_quat, grip_qpos, grip_qvel, joint_pos, joint_vel,
                  obj_pos, obj_quat, obj_valid, obj_contact, obj_grasped, obj_support,
                  n_contacts, arm_contacts, grip_static, fixture_qpos, fixture_valid, t) -> np.ndarray:
        n = eef_pos.shape[0]
        ti, gi = self.target_slot, self.goal_slot
        eef_rot = quat_xyzw_to_rot6d(eef_quat).reshape(n, 6)

        tp = obj_pos[:, ti, :]
        tq = quat_xyzw_to_rot6d(obj_quat[:, ti, :].reshape(-1, 4)).reshape(n, 6)
        t_rel = tp - eef_pos
        t_dist = np.linalg.norm(t_rel, axis=1, keepdims=True)
        target = np.concatenate(
            [tp, tq, t_rel, t_dist,
             obj_grasped[:, ti:ti + 1], obj_contact[:, ti:ti + 1], obj_support[:, ti:ti + 1]], axis=1)

        if gi >= 0:
            gp = obj_pos[:, gi, :]
            gq = quat_xyzw_to_rot6d(obj_quat[:, gi, :].reshape(-1, 4)).reshape(n, 6)
            g_rel = tp - gp
            goal = np.concatenate([gp, gq, g_rel, np.linalg.norm(g_rel, axis=1, keepdims=True),
                                   np.ones((n, 1), np.float32)], axis=1)
        else:
            goal = np.zeros((n, 14), np.float32)

        # Distractors: every valid slot that is neither the target nor the receptacle, the four nearest
        # to the end effector first. Sorting by distance keeps the block invariant to slot ordering.
        rel = obj_pos - eef_pos[:, None, :]
        dist = np.linalg.norm(rel, axis=2)
        mask = obj_valid > 0.5
        mask[:, ti] = False
        if gi >= 0:
            mask[:, gi] = False
        order = np.argsort(np.where(mask, dist, np.float32(1e3)), axis=1)[:, :N_DISTRACTORS]
        rows = np.arange(n)[:, None]
        sel = mask[rows, order]
        d_rel = rel[rows, order] * sel[..., None]
        d_dist = np.where(sel, dist[rows, order], 0.0).astype(np.float32)
        d_con = (obj_contact[rows, order] * sel).astype(np.float32)
        distract = np.concatenate([d_rel.reshape(n, -1), d_dist, d_con], axis=1)

        contacts = np.log1p(np.stack([n_contacts, arm_contacts, grip_static], axis=1).astype(np.float32))
        fixtures = np.concatenate([fixture_qpos, fixture_valid], axis=1)
        frac = (t / max(self.max_steps, 1)).astype(np.float32).reshape(n, 1)
        time = np.concatenate([frac, 1.0 - frac], axis=1)

        out = np.concatenate(
            [eef_pos, eef_rot, grip_qpos, grip_qvel, joint_pos, joint_vel,
             target, goal, distract, contacts, fixtures, time], axis=1).astype(np.float32)
        if out.shape[1] != OBS_DIM:
            raise AssertionError(f"obs width {out.shape[1]} != OBS_DIM {OBS_DIM}")
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)


SPEC_VERSION_V2 = "obs_v2"
PROPRIO_DIM = 27   # eef_pos 3 | eef_rot6d 6 | gripper_qpos 2 | gripper_qvel 2 | joint_pos 7 | joint_vel 7
TIME_DIM = 2


def obs_v2_dim(vis_dim: int, n_cameras: int = 2, lang_dim: int = 0) -> int:
    return PROPRIO_DIM + n_cameras * vis_dim + lang_dim + TIME_DIM


class ObsBuilderV2:
    """The strictly observable observation: proprioception, frozen visual features, task language, time.

    Layout (v2), all float32:

      proprio   27  eef_pos 3 | eef_rot6d 6 | gripper_qpos 2 | gripper_qvel 2 | joint_pos 7 | joint_vel 7
      vision  2*D   frozen encoder features, agentview then wrist
      language  L   frozen embedding of the task instruction (0 to disable)
      time      2   t / max_steps | 1 - t / max_steps

    What is deliberately absent, versus `ObsBuilder` (v1): object poses, grasp and contact flags,
    receptacle pose, distractor geometry, contact counts and fixture joint angles. Those are simulator
    state, and a policy that reads them cannot be deployed.

    The proprioceptive block is still read out of the same `priv.*` columns, because that is where the
    recorder put it - but every field in it (end-effector pose by forward kinematics, gripper and joint
    encoders) is measurable on real hardware, which is the test that matters. `observation.state` in the
    LeRobot parquet is the same information in 8 dimensions; we keep the wider version because joint
    positions and velocities are equally observable and the code already builds them.
    """

    def __init__(self, max_steps: int, vis_dim: int, lang_dim: int = 0, n_cameras: int = 2):
        self.max_steps = int(max_steps)
        self.vis_dim, self.lang_dim, self.n_cameras = int(vis_dim), int(lang_dim), int(n_cameras)
        self.dim = obs_v2_dim(self.vis_dim, self.n_cameras, self.lang_dim)

    # ---------------------------------------------------------------- offline
    def from_columns(self, cols: dict, n_frames: int, vis: np.ndarray, lang=None,
                     t0: int = 0) -> np.ndarray:
        """(n_frames, dim). `vis` is (n_frames, n_cameras, vis_dim); `lang` is (lang_dim,) or None."""
        n = n_frames

        def g(k, w):
            return _col(cols, k, n, w)

        return self._assemble(
            eef_pos=g("priv.eef_pos", 3), eef_quat=g("priv.eef_quat", 4),
            grip_qpos=g("priv.gripper_qpos", 2), grip_qvel=g("priv.gripper_qvel", 2),
            joint_pos=g("priv.joint_pos", 7), joint_vel=g("priv.joint_vel", 7),
            vis=np.asarray(vis, np.float32).reshape(n, self.n_cameras, self.vis_dim),
            lang=lang, t=np.arange(t0, t0 + n, dtype=np.float32))

    # ----------------------------------------------------------------- online
    def from_priv(self, priv: dict, t: int, vis: np.ndarray, lang=None) -> np.ndarray:
        """(dim,) for one step. `vis` is (n_cameras, vis_dim) from the live encoder."""
        def one(a):
            return np.asarray(a, np.float32).reshape(1, -1)

        return self._assemble(
            eef_pos=one(priv["priv.eef_pos"]), eef_quat=one(priv["priv.eef_quat"]),
            grip_qpos=one(priv["priv.gripper_qpos"]), grip_qvel=one(priv["priv.gripper_qvel"]),
            joint_pos=one(priv["priv.joint_pos"]), joint_vel=one(priv["priv.joint_vel"]),
            vis=np.asarray(vis, np.float32).reshape(1, self.n_cameras, self.vis_dim),
            lang=lang, t=np.array([t], np.float32))[0]

    # --------------------------------------------------------------- assembly
    def _assemble(self, *, eef_pos, eef_quat, grip_qpos, grip_qvel, joint_pos, joint_vel,
                  vis, lang, t) -> np.ndarray:
        n = eef_pos.shape[0]
        eef_rot = quat_xyzw_to_rot6d(eef_quat).reshape(n, 6)
        frac = (t / max(self.max_steps, 1)).astype(np.float32).reshape(n, 1)
        parts = [eef_pos, eef_rot, grip_qpos, grip_qvel, joint_pos, joint_vel,
                 vis.reshape(n, self.n_cameras * self.vis_dim)]
        if self.lang_dim:
            l = np.asarray(lang, np.float32).reshape(-1)
            if l.size != self.lang_dim:
                raise AssertionError(f"language embedding is {l.size}d, expected {self.lang_dim}")
            parts.append(np.broadcast_to(l, (n, self.lang_dim)))
        parts.append(np.concatenate([frac, 1.0 - frac], axis=1))
        out = np.concatenate(parts, axis=1).astype(np.float32)
        if out.shape[1] != self.dim:
            raise AssertionError(f"obs width {out.shape[1]} != {self.dim}")
        return np.nan_to_num(out, nan=0.0, posinf=0.0, neginf=0.0)

    def blocks(self) -> list[tuple[str, int]]:
        b = [("eef_pos", 3), ("eef_rot6d", 6), ("gripper_qpos", 2), ("gripper_qvel", 2),
             ("joint_pos", 7), ("joint_vel", 7), ("vision", self.n_cameras * self.vis_dim)]
        if self.lang_dim:
            b.append(("language", self.lang_dim))
        return b + [("time", TIME_DIM)]


BLOCKS = [  # (name, width) in concatenation order, for logging and debugging
    ("eef_pos", 3), ("eef_rot6d", 6), ("gripper_qpos", 2), ("gripper_qvel", 2),
    ("joint_pos", 7), ("joint_vel", 7), ("target", 16), ("goal", 14),
    ("distractors", 5 * N_DISTRACTORS), ("contacts", 3), ("fixtures", 2 * N_FIXTURE_JOINTS), ("time", 2),
]
