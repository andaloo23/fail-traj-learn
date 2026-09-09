"""Shared helpers for the snapshot tools (importable without running the checker's CLI)."""
import numpy as np


def gripper_cmd_history(actions: np.ndarray, n_sub: int, speed: float, n_wait: int) -> np.ndarray:
    """robosuite PandaGripper.format_action keeps `current_action` (not part of the MuJoCo state): every
    simulator substep it moves by [-1, 1] * speed * sign(gripper_action) and is clipped to [-1, 1]. Rebuild it
    for every frame from the LIBERO dummy wait steps (gripper -1) followed by the recorded actions.
    Returns (len(actions) + 1, 2): row f is the value in effect right before the action at frame f."""
    step = np.array([-1.0, 1.0]) * speed
    ca = np.zeros(2)
    for _ in range(n_wait * n_sub):
        ca = np.clip(ca + step * np.sign(-1.0), -1.0, 1.0)
    out = np.zeros((len(actions) + 1, 2))
    out[0] = ca
    for i, a in enumerate(actions[:, -1]):
        s = np.sign(float(a))
        for _ in range(n_sub):
            ca = np.clip(ca + step * s, -1.0, 1.0)
        out[i + 1] = ca
    return out


def apply_fixture_poses(rs_env, fixture_body_pose: dict | None) -> int:
    """Write the recorded fixture body pos/quat (sidecar `fixture_body_pose`, schema v3.2) into the MuJoCo model.
    LIBERO re-samples fixture placement into the model at every reset, so without this a restored episode has its
    cabinets / racks / stoves up to ~1.5 cm from where they were during recording. Returns the number applied."""
    if not fixture_body_pose:
        return 0
    m = rs_env.sim.model
    n = 0
    for entry in fixture_body_pose.values():
        try:
            bid = m.body_name2id(entry["body"])
        except Exception:
            continue
        m.body_pos[bid] = np.asarray(entry["pos"], dtype=np.float64)
        m.body_quat[bid] = np.asarray(entry["quat_wxyz"], dtype=np.float64)
        n += 1
    return n


def restore(ctrl, rs_env, state: np.ndarray, gripper_cmd: np.ndarray | None, fixture_body_pose: dict | None = None):
    """Full episode-state restore: fixture model poses (if recorded), MuJoCo qpos/qvel snapshot, gripper ramp state."""
    apply_fixture_poses(rs_env, fixture_body_pose)
    raw = ctrl.set_init_state(state)
    if gripper_cmd is not None:
        rs_env.robots[0].gripper.current_action = np.array(gripper_cmd, dtype=np.float64)
    return raw
