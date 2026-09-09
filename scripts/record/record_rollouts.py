#!/usr/bin/env python
"""Record policy rollouts in LIBERO to a LeRobotDataset, with privileged simulator state.

Runs any LeRobot policy (same CLI as lerobot-eval for --policy.* and --env.*) one episode at a time,
and writes:
  * a LeRobotDataset (v3) at <output_root>/<dataset_name> with the standard camera/state/action/reward
    fields plus per-frame privileged columns (object poses, gripper-object contacts, ...) and
    chunk bookkeeping (chunk.index / chunk.step) so 10-step decisions can be rebuilt;
  * per-episode sidecars at <output_root>/<dataset_name>/sidecar/episode_XXXXXX.{json,npz} holding
    episode metadata (source policy, task, init mode, outcome, object slot names), MuJoCo state
    snapshots at every chunk boundary and the gripper controller's hidden command state (together they
    give bit-exact restore + replay, see analysis/check_snapshot_restore.py) for recovery-branching oracles;
  * an append-only <output_root>/<dataset_name>/episodes.jsonl summary.

Example:
  python record_rollouts.py \
    --policy.type=molmoact2 --policy.checkpoint_path=allenai/MolmoAct2-LIBERO --policy.norm_tag=libero \
    --policy.inference_action_mode=continuous --policy.dtype=bfloat16 --policy.device=cuda \
    --env.type=libero --env.task=libero_object --env.task_ids='[0]' \
    --env.observation_height=256 --env.observation_width=256 \
    --env.camera_name_mapping='{"agentview_image":"image","robot0_eye_in_hand_image":"wrist_image"}' \
    --n_episodes=2 --dataset_name=smoke --source=molmoact2_libero --init_mode=standard
"""

import datetime as dt
import json
import logging
import os
import time
import traceback
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

os.environ.setdefault("MUJOCO_GL", "egl")
os.environ.setdefault("PYOPENGL_PLATFORM", "egl")

import numpy as np
import torch

from lerobot import envs, policies  # noqa: F401  (registers subclasses)
from lerobot.configs import parser
from lerobot.configs.policies import PreTrainedConfig
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.envs import make_env, make_env_pre_post_processors, preprocess_observation
from lerobot.envs.libero import get_libero_dummy_action
from lerobot.policies import make_policy, make_pre_post_processors
from lerobot.utils.constants import ACTION, OBS_STATE
from lerobot.utils.device_utils import get_safe_torch_device
from lerobot.utils.random_utils import set_seed
from lerobot.utils.utils import init_logging

logger = logging.getLogger(__name__)


# --------------------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------------------
@dataclass
class RecordConfig:
    env: envs.EnvConfig
    policy: PreTrainedConfig | None = None
    rename_map: dict[str, str] = field(default_factory=dict)
    seed: int = 1000
    n_episodes: int = 10  # per task
    output_root: Path = Path(os.environ.get("FTL_PROJ", "/home/aliu/projects/fail-traj-learn")) / "data"
    dataset_name: str = "pilot"
    # provenance tags (mirror OOPSIE's robot/policy metadata)
    source: str = "unknown_policy"  # policy family, e.g. molmoact2_libero, molmoact2_base, dp_ckpt20k
    checkpoint_tag: str = ""
    notes: str = ""
    # initial-state protocol
    init_mode: str = "standard"  # standard | shifted
    shift_xy: float = 0.0  # meters, uniform +- per object (shifted mode)
    shift_yaw_deg: float = 0.0  # degrees, uniform +- per object (shifted mode)
    shift_max_tries: int = 30  # rejection-sampling attempts for a physically clean shifted layout
    # synthetic perturbation (tagged; off by default)
    action_noise_std: float = 0.0
    # bookkeeping
    save_sim_state: bool = True
    max_obj_slots: int = 12
    max_fixture_joints: int = 16
    max_steps_override: int | None = None
    trust_remote_code: bool = False

    def __post_init__(self) -> None:
        policy_path = parser.get_path_arg("policy")
        if policy_path:
            yaml_overrides = parser.get_yaml_overrides("policy")
            cli_overrides = parser.get_cli_overrides("policy") or []
            self.policy = PreTrainedConfig.from_pretrained(policy_path, cli_overrides=yaml_overrides + cli_overrides)
            self.policy.pretrained_path = Path(policy_path)
        if self.policy is None:
            raise ValueError("A policy is required (--policy.path=... or --policy.type=... with checkpoint args).")
        if self.init_mode not in ("standard", "shifted"):
            raise ValueError(f"init_mode must be standard|shifted, got {self.init_mode}")
        if self.init_mode == "shifted" and self.shift_xy <= 0 and self.shift_yaw_deg <= 0:
            raise ValueError("init_mode=shifted requires shift_xy>0 and/or shift_yaw_deg>0")

    @classmethod
    def __get_path_fields__(cls) -> list[str]:
        return ["policy"]


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def batchify(x: Any) -> Any:
    """Add a leading batch axis to every array leaf of a (possibly nested) observation dict."""
    if isinstance(x, dict):
        return {k: batchify(v) for k, v in x.items()}
    arr = np.asarray(x)
    return arr[None, ...]


def quat_mul_wxyz(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    w1, x1, y1, z1 = q1
    w2, x2, y2, z2 = q2
    return np.array(
        [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ]
    )


# v3 (2026-09-05): priv poses/joints read from sim.data (no observable lag), sidecar npz gains `gripper_cmd`
# (robosuite PandaGripper.current_action per chunk, needed for exact snapshot restore), shifted init keeps the yaw
# of goal-region containers (LIBERO in_box predicate is not rotation-correct).
# v3.2 (2026-09-06): sidecar gains `fixture_body_pose` (model-level pos/quat of every fixture root body): LIBERO
# re-samples fixture placement into the MuJoCo MODEL at each reset, so qpos/qvel snapshots alone cannot rebuild the
# recording env in cabinet / rack / stove scenes. Restore with check_snapshot_restore_lib.restore(..., fixture_body_pose).
SCHEMA_VERSION = 3


def fixture_body_poses(rs_env) -> dict[str, dict]:
    """Body pos/quat (wxyz, MuJoCo model frame) of every fixture root body, as placed by LIBERO at this reset."""
    out: dict[str, dict] = {}
    m = rs_env.sim.model
    for name, obj in (getattr(rs_env, "fixtures_dict", {}) or {}).items():
        try:
            bid = m.body_name2id(obj.root_body)
        except Exception:
            continue
        out[name] = {"body": obj.root_body, "pos": [float(x) for x in m.body_pos[bid]], "quat_wxyz": [float(x) for x in m.body_quat[bid]]}
    return out


def build_features(h: int, w: int, n_slots: int, n_fixture_joints: int) -> dict[str, dict]:
    f32 = lambda n: {"dtype": "float32", "shape": (n,), "names": None}  # noqa: E731
    i64 = lambda n: {"dtype": "int64", "shape": (n,), "names": None}  # noqa: E731
    b = lambda n: {"dtype": "bool", "shape": (n,), "names": None}  # noqa: E731
    feats: dict[str, dict] = {
        "observation.images.image": {"dtype": "video", "shape": (h, w, 3), "names": ["height", "width", "channel"]},
        "observation.images.image2": {"dtype": "video", "shape": (h, w, 3), "names": ["height", "width", "channel"]},
        "observation.state": {"dtype": "float32", "shape": (8,), "names": ["state"]},
        "action": {"dtype": "float32", "shape": (7,), "names": ["actions"]},
        "next.reward": f32(1),
        "next.done": b(1),
        "next.success": b(1),
        # decision structure
        "chunk.index": i64(1),
        "chunk.step": i64(1),
        # privileged (oracle-only) state
        "priv.sim_time": f32(1),
        "priv.eef_pos": f32(3),
        "priv.eef_quat": f32(4),
        "priv.gripper_qpos": f32(2),
        "priv.gripper_qvel": f32(2),
        "priv.joint_pos": f32(7),
        "priv.joint_vel": f32(7),
        "priv.n_contacts": f32(1),
        "priv.obj_valid": f32(n_slots),
        "priv.target_mask": f32(n_slots),
        "priv.obj_pos": f32(n_slots * 3),
        "priv.obj_quat": f32(n_slots * 4),
        "priv.obj_gripper_contact": f32(n_slots),
        "priv.obj_left_finger_contact": f32(n_slots),  # any geom of the left finger touches the object
        "priv.obj_right_finger_contact": f32(n_slots),
        "priv.obj_grasped": f32(n_slots),  # both fingers (any finger geom) in contact  [schema v2 definition]
        "priv.obj_grasped_pads": f32(n_slots),  # both finger PADS in contact (stricter; the schema v1 rule)
        "priv.obj_support_contact": f32(n_slots),  # object touching static scene (floor/table/walls/fixtures)
        "priv.obj_obj_contact": f32(n_slots),  # object touching another movable object
        "priv.obj_resting": f32(n_slots),  # support OR obj-obj contact: not airborne
        "priv.arm_contacts": f32(1),  # robot arm links (not gripper) touching anything: collision signal
        "priv.gripper_static_contacts": f32(1),  # gripper touching any static geom (fixtures included)
        "priv.gripper_fixture_contacts": f32(1),  # subset: gripper touching an articulated/named fixture (handle, knob)
        "priv.fixture_valid": f32(n_fixture_joints),
        "priv.fixture_qpos": f32(n_fixture_joints),  # 1-DoF fixture joints (drawers, knobs, doors); names in sidecar
    }
    return feats


class PrivilegedReader:
    """Extracts object poses and gripper/object contact flags from the robosuite/LIBERO env."""

    def __init__(self, rs_env, n_slots: int, n_fixture_joints: int = 16):
        self.rs_env = rs_env
        self.sim = rs_env.sim
        self.n_slots = n_slots
        self.n_fixture_joints = n_fixture_joints
        objs = getattr(rs_env, "objects_dict", {}) or {}
        fixtures = getattr(rs_env, "fixtures_dict", {}) or {}
        self.fixture_names: list[str] = list(fixtures.keys())
        # 1-DoF joints of fixtures and objects (drawers, knobs, doors); free joints are covered by obj poses.
        self.fixture_joint_names: list[str] = []
        self.fixture_joint_addr: list[int] = []
        for owner in list(fixtures.values()) + list(objs.values()):
            for jn in getattr(owner, "joints", []) or []:
                try:
                    addr = self.sim.model.get_joint_qpos_addr(jn)
                except Exception:
                    continue
                if isinstance(addr, (tuple, list)):
                    continue  # free/ball joint: pose already logged via obj_pos/quat
                if len(self.fixture_joint_names) < n_fixture_joints:
                    self.fixture_joint_names.append(jn)
                    self.fixture_joint_addr.append(int(addr))
        try:
            self.goal_state = [list(map(str, g)) for g in rs_env.parsed_problem["goal_state"]]
        except Exception:
            self.goal_state = []
        self.obj_names: list[str] = list(objs.keys())[:n_slots]
        if len(objs) > n_slots:
            logger.warning(f"{len(objs)} objects but only {n_slots} slots; dropping {list(objs.keys())[n_slots:]}")
        self.objs = [objs[n] for n in self.obj_names]
        self.target_names = list(getattr(rs_env, "obj_of_interest", []) or [])
        m = self.sim.model
        self.eef_body_id = m.body_name2id(rs_env.robots[0].robot_model.eef_name)
        # root body id per object (for pose fallback + contact attribution)
        self.obj_body_ids: list[int] = []
        for o in self.objs:
            rb = getattr(o, "root_body", None)
            try:
                self.obj_body_ids.append(m.body_name2id(rb))
            except Exception:
                self.obj_body_ids.append(-1)
        # geom -> object slot map (via body subtree: any body whose name starts with object name)
        n_geom = m.ngeom
        self.geom_to_slot = np.full(n_geom, -1, dtype=np.int64)
        body_names = [m.body_id2name(i) for i in range(m.nbody)]
        for gid in range(n_geom):
            bid = int(m.geom_bodyid[gid])
            bname = body_names[bid] or ""
            for slot, on in enumerate(self.obj_names):
                if bname == on or bname.startswith(on + "_"):
                    self.geom_to_slot[gid] = slot
                    break
        # gripper geoms
        gripper = rs_env.robots[0].gripper
        self.gripper_geom_ids: set[int] = set()
        self.left_pad: set[int] = set()
        self.right_pad: set[int] = set()
        self.left_finger: set[int] = set()
        self.right_finger: set[int] = set()
        try:
            ig = gripper.important_geoms
            for g in ig.get("left_fingerpad", []):
                self.left_pad.add(m.geom_name2id(g))
            for g in ig.get("right_fingerpad", []):
                self.right_pad.add(m.geom_name2id(g))
            for g in ig.get("left_finger", []) + ig.get("left_fingerpad", []):
                self.left_finger.add(m.geom_name2id(g))
            for g in ig.get("right_finger", []) + ig.get("right_fingerpad", []):
                self.right_finger.add(m.geom_name2id(g))
            self.gripper_geom_ids = set(self.left_finger) | set(self.right_finger)
        except Exception as e:  # pragma: no cover
            logger.warning(f"Could not resolve gripper geoms from important_geoms: {e}")
        if not self.left_finger or not self.right_finger:
            # fallback: classify finger geoms by body name
            for gid in range(n_geom):
                bname = (body_names[int(m.geom_bodyid[gid])] or "").lower()
                if "leftfinger" in bname or "finger1" in bname:
                    self.left_finger.add(gid)
                if "rightfinger" in bname or "finger2" in bname:
                    self.right_finger.add(gid)
        # fixture geoms (articulated / named fixtures such as cabinets, stoves, caddies)
        self.fixture_geom_ids: set[int] = set()
        for gid in range(n_geom):
            bname = body_names[int(m.geom_bodyid[gid])] or ""
            for fn in self.fixture_names:
                if bname == fn or bname.startswith(fn + "_"):
                    self.fixture_geom_ids.add(gid)
                    break
        if not self.gripper_geom_ids:
            for gid in range(n_geom):
                bname = body_names[int(m.geom_bodyid[gid])] or ""
                if bname.startswith("gripper0"):
                    self.gripper_geom_ids.add(gid)
        # robot arm geoms (links, not gripper) and static scene geoms (floor, table, walls, fixtures).
        # In LIBERO the tabletop is often literally the geom named "floor", so classify by body instead of name:
        # anything that is neither an object slot nor part of the robot/gripper counts as static support.
        self.arm_geom_ids: set[int] = set()
        self.static_geom_ids: set[int] = set()
        for gid in range(n_geom):
            bname = body_names[int(m.geom_bodyid[gid])] or ""
            if bname.startswith("gripper0"):
                continue
            if bname.startswith("robot0"):
                self.arm_geom_ids.add(gid)
            elif self.geom_to_slot[gid] < 0:
                self.static_geom_ids.add(gid)
        self.all_gripper_geom_ids: set[int] = {
            gid for gid in range(n_geom) if (body_names[int(m.geom_bodyid[gid])] or "").startswith("gripper0")
        }

    def read(self, raw_obs: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
        n = self.n_slots
        d = self.sim.data
        m = self.sim.model
        # After mj_step the derived quantities (xpos, site_xpos, contacts) belong to the pre-integration qpos.
        # robosuite calls forward() at the start of every substep anyway, so this changes nothing dynamically.
        self.sim.forward()
        obj_pos = np.zeros((n, 3), np.float32)
        obj_quat = np.zeros((n, 4), np.float32)
        valid = np.zeros(n, np.float32)
        target = np.zeros(n, np.float32)
        for slot, name in enumerate(self.obj_names):
            valid[slot] = 1.0
            if name in self.target_names:
                target[slot] = 1.0
            # Poses come from sim.data, not raw_obs: robosuite observables are sampled at the first substep of a
            # control step, so raw_obs lags the true state by up to one control step while the arm moves.
            pk, qk = f"{name}_pos", f"{name}_quat"
            if self.obj_body_ids[slot] < 0 and pk in raw_obs and qk in raw_obs:
                obj_pos[slot] = raw_obs[pk]
                obj_quat[slot] = raw_obs[qk]  # xyzw (robosuite convention)
            elif self.obj_body_ids[slot] >= 0:
                bid = self.obj_body_ids[slot]
                obj_pos[slot] = d.body_xpos[bid]
                q = d.body_xquat[bid]  # wxyz
                obj_quat[slot] = np.array([q[1], q[2], q[3], q[0]], np.float32)
        # contacts
        grip_contact = np.zeros(n, np.float32)
        left = np.zeros(n, bool)  # pads
        right = np.zeros(n, bool)
        lfin = np.zeros(n, bool)  # any finger geom
        rfin = np.zeros(n, bool)
        support_contact = np.zeros(n, np.float32)
        obj_obj_contact = np.zeros(n, np.float32)
        arm_contacts = 0
        gripper_static = 0
        gripper_fixture = 0
        ncon = int(d.ncon)
        for i in range(ncon):
            c = d.contact[i]
            g1, g2 = int(c.geom1), int(c.geom2)
            s1, s2 = int(self.geom_to_slot[g1]), int(self.geom_to_slot[g2])
            if s1 >= 0 and s2 >= 0:
                obj_obj_contact[s1] = 1.0
                obj_obj_contact[s2] = 1.0
            if g1 in self.arm_geom_ids or g2 in self.arm_geom_ids:
                arm_contacts += 1
            if (g1 in self.all_gripper_geom_ids and g2 in self.static_geom_ids) or (
                g2 in self.all_gripper_geom_ids and g1 in self.static_geom_ids
            ):
                gripper_static += 1
                if g1 in self.fixture_geom_ids or g2 in self.fixture_geom_ids:
                    gripper_fixture += 1
            for ga, gb in ((g1, g2), (g2, g1)):
                slot = int(self.geom_to_slot[gb])
                if slot < 0:
                    continue
                if ga in self.all_gripper_geom_ids:
                    grip_contact[slot] = 1.0
                    if ga in self.left_pad:
                        left[slot] = True
                    if ga in self.right_pad:
                        right[slot] = True
                    if ga in self.left_finger:
                        lfin[slot] = True
                    if ga in self.right_finger:
                        rfin[slot] = True
                if ga in self.static_geom_ids:
                    support_contact[slot] = 1.0
        grasped_pads = (left & right).astype(np.float32)
        grasped = (lfin & rfin).astype(np.float32)
        resting = np.maximum(support_contact, obj_obj_contact)
        fq = np.zeros(self.n_fixture_joints, np.float32)
        fv = np.zeros(self.n_fixture_joints, np.float32)
        for i, addr in enumerate(self.fixture_joint_addr):
            fq[i] = float(d.qpos[addr])
            fv[i] = 1.0
        # Robot state straight from sim.data (same quantities as robosuite's robot0_* observables, without the lag).
        robot = self.rs_env.robots[0]
        eef_pos = np.asarray(d.site_xpos[robot.eef_site_id], np.float32)
        eq = d.body_xquat[self.eef_body_id]  # wxyz
        eef_quat = np.array([eq[1], eq[2], eq[3], eq[0]], np.float32)  # xyzw
        return {
            "priv.sim_time": np.array([d.time], np.float32),
            "priv.eef_pos": eef_pos,
            "priv.eef_quat": eef_quat,
            "priv.gripper_qpos": np.asarray(d.qpos[robot._ref_gripper_joint_pos_indexes], np.float32),
            "priv.gripper_qvel": np.asarray(d.qvel[robot._ref_gripper_joint_vel_indexes], np.float32),
            "priv.joint_pos": np.asarray(d.qpos[robot._ref_joint_pos_indexes], np.float32),
            "priv.joint_vel": np.asarray(d.qvel[robot._ref_joint_vel_indexes], np.float32),
            "priv.n_contacts": np.array([ncon], np.float32),
            "priv.obj_valid": valid,
            "priv.target_mask": target,
            "priv.obj_pos": obj_pos.reshape(-1),
            "priv.obj_quat": obj_quat.reshape(-1),
            "priv.obj_gripper_contact": grip_contact,
            "priv.obj_left_finger_contact": lfin.astype(np.float32),
            "priv.obj_right_finger_contact": rfin.astype(np.float32),
            "priv.obj_grasped": grasped,
            "priv.obj_grasped_pads": grasped_pads,
            "priv.obj_support_contact": support_contact,
            "priv.obj_obj_contact": obj_obj_contact,
            "priv.obj_resting": resting,
            "priv.arm_contacts": np.array([arm_contacts], np.float32),
            "priv.gripper_static_contacts": np.array([gripper_static], np.float32),
            "priv.gripper_fixture_contacts": np.array([gripper_fixture], np.float32),
            "priv.fixture_valid": fv,
            "priv.fixture_qpos": fq,
        }


def shift_object_layout(rs_env, rng: np.random.Generator, shift_xy: float, shift_yaw_deg: float) -> tuple[np.ndarray, dict]:
    """Return a flattened MuJoCo state with every movable object's free joint perturbed in xy and yaw."""
    sim = rs_env.sim
    state = sim.get_state()
    qpos = np.array(state.qpos, copy=True)
    applied: dict[str, dict] = {}
    objects = getattr(rs_env, "objects_dict", {}) or {}
    # Objects that own a region named in the goal (basket_1 -> basket_1_contain_region) keep their yaw: LIBERO's
    # SiteObject.in_box uses abs(R @ size) for the region extents, so a container yawed near 45 degrees gets a
    # region that collapses in x or y and correct placements are scored as failures (see predicate_artifacts.py).
    keep_yaw: set[str] = set()
    try:
        for atom in rs_env.parsed_problem["goal_state"]:
            for arg in atom[1:]:
                for on in objects:
                    if str(arg) != on and str(arg).startswith(on + "_"):
                        keep_yaw.add(on)
    except Exception:
        pass
    for name, obj in objects.items():
        for jn in getattr(obj, "joints", []) or []:
            addr = sim.model.get_joint_qpos_addr(jn)
            if not (isinstance(addr, (tuple, list)) and addr[1] - addr[0] == 7):
                continue
            s = int(addr[0])
            dxy = rng.uniform(-shift_xy, shift_xy, size=2) if shift_xy > 0 else np.zeros(2)
            qpos[s : s + 2] += dxy
            yaw = float(np.deg2rad(rng.uniform(-shift_yaw_deg, shift_yaw_deg))) if shift_yaw_deg > 0 else 0.0
            if name in keep_yaw:
                yaw = 0.0
            if yaw != 0.0:
                qz = np.array([np.cos(yaw / 2), 0.0, 0.0, np.sin(yaw / 2)])
                qpos[s + 3 : s + 7] = quat_mul_wxyz(qz, qpos[s + 3 : s + 7])
            applied[name] = {"dxy": dxy.tolist(), "yaw_rad": yaw, "yaw_locked": name in keep_yaw}
    state.qpos[:] = qpos
    state.qvel[:] = 0.0
    return state.flatten(), applied


def object_positions(rs_env) -> dict[str, np.ndarray]:
    sim = rs_env.sim
    out: dict[str, np.ndarray] = {}
    for name, obj in (getattr(rs_env, "objects_dict", {}) or {}).items():
        try:
            out[name] = np.array(sim.data.body_xpos[sim.model.body_name2id(obj.root_body)], copy=True)
        except Exception:
            pass
    return out


def object_contact_pairs(rs_env) -> set[tuple[str, str]]:
    """Unordered pairs of distinct movable objects currently in contact (needs a fresh sim.forward)."""
    sim = rs_env.sim
    m, d = sim.model, sim.data
    objs = list((getattr(rs_env, "objects_dict", {}) or {}).keys())
    body_names = [m.body_id2name(i) for i in range(m.nbody)]

    def owner(gid: int):
        b = body_names[int(m.geom_bodyid[gid])] or ""
        for on in objs:
            if b == on or b.startswith(on + "_"):
                return on
        return None

    pairs: set[tuple[str, str]] = set()
    for i in range(int(d.ncon)):
        c = d.contact[i]
        a, b = owner(int(c.geom1)), owner(int(c.geom2))
        if a and b and a != b:
            pairs.add(tuple(sorted((a, b))))  # type: ignore[arg-type]
    return pairs


def sample_shifted_init(ctrl, rs_env, rng, shift_xy, shift_yaw_deg, n_wait, max_tries=30, max_drift=0.02, max_dz=0.01):
    """Rejection-sample a shifted layout that is physically clean.

    A blind shift can place two objects interpenetrating; MuJoCo then resolves that with a violent push during the
    settle steps and launches objects metres off the table (seen in 2-13 percent of episodes at 4-8 cm). A candidate
    is rejected if placing it creates an object-object contact that the base layout did not have, or if any object
    drifts more than max_drift in xy, or changes height by more than max_dz (tipping), during the settle steps.
    Returns (raw_obs, shift_applied, tries, valid). After max_tries the unshifted layout is used and valid=False.
    """
    base_flat = np.array(ctrl.get_sim_state(), copy=True)
    base_pairs = object_contact_pairs(rs_env)
    for attempt in range(1, max_tries + 1):
        ctrl.set_init_state(base_flat)
        flat, info = shift_object_layout(rs_env, rng, shift_xy, shift_yaw_deg)
        raw = ctrl.set_init_state(flat)  # runs sim.forward, so contacts are current
        placed = object_positions(rs_env)
        if object_contact_pairs(rs_env) - base_pairs:
            continue
        for _ in range(n_wait):
            raw, _, _, _ = ctrl.step(get_libero_dummy_action())
        settled = object_positions(rs_env)
        moved = any(
            np.linalg.norm(settled[n][:2] - p[:2]) > max_drift or abs(settled[n][2] - p[2]) > max_dz
            for n, p in placed.items() if n in settled
        )
        if moved or (object_contact_pairs(rs_env) - base_pairs):
            continue
        return raw, info, attempt, True
    logger.warning(f"shifted init: no clean layout in {max_tries} tries; using the unshifted layout for this episode")
    ctrl.set_init_state(base_flat)
    for _ in range(n_wait):
        raw, _, _, _ = ctrl.step(get_libero_dummy_action())
    return raw, {}, max_tries, False


# --------------------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------------------
@parser.wrap()
def main(cfg: RecordConfig):
    init_logging()
    device = get_safe_torch_device(cfg.policy.device, log=True)
    torch.backends.cudnn.benchmark = True
    torch.backends.cuda.matmul.allow_tf32 = True
    set_seed(cfg.seed)

    root = Path(cfg.output_root) / cfg.dataset_name
    sidecar_dir = root / "sidecar"
    repo_id = f"fail_traj/{cfg.dataset_name}"
    h, w = cfg.env.observation_height, cfg.env.observation_width
    features = build_features(h, w, cfg.max_obj_slots, cfg.max_fixture_joints)

    # ---- dataset (create or resume)
    if (root / "meta" / "info.json").exists():
        ds = LeRobotDataset.resume(repo_id=repo_id, root=root)
        logger.info(f"Resuming dataset at {root} with {ds.num_episodes} episodes")
    else:
        root.parent.mkdir(parents=True, exist_ok=True)  # LeRobotDataset.create requires `root` itself to not exist
        ds = LeRobotDataset.create(repo_id=repo_id, fps=int(cfg.env.fps), features=features, root=root, robot_type="panda", use_videos=True)
        logger.info(f"Created dataset at {root}")
    sidecar_dir.mkdir(parents=True, exist_ok=True)

    # ---- envs + policy
    env_dict = make_env(cfg.env, n_envs=1, use_async_envs=False, trust_remote_code=cfg.trust_remote_code)
    policy = make_policy(cfg=cfg.policy, env_cfg=cfg.env, rename_map=cfg.rename_map)
    policy.eval()
    preprocessor, postprocessor = make_pre_post_processors(
        policy_cfg=cfg.policy,
        pretrained_path=cfg.policy.pretrained_path,
        preprocessor_overrides={
            "device_processor": {"device": str(policy.config.device)},
            "rename_observations_processor": {"rename_map": cfg.rename_map},
        },
    )
    env_pre, env_post = make_env_pre_post_processors(env_cfg=cfg.env, policy_cfg=cfg.policy)
    n_action_steps = int(getattr(policy.config, "n_action_steps", 1) or 1)
    policy_summary = {
        "type": cfg.policy.type,
        "pretrained_path": str(cfg.policy.pretrained_path) if cfg.policy.pretrained_path else None,
        "checkpoint_path": str(getattr(cfg.policy, "checkpoint_path", None)),
        "n_action_steps": n_action_steps,
        "chunk_size": getattr(cfg.policy, "chunk_size", None),
        "inference_action_mode": getattr(cfg.policy, "inference_action_mode", None),
        "num_inference_steps": getattr(cfg.policy, "num_inference_steps", None),
        "dtype": str(getattr(cfg.policy, "dtype", None)),
    }

    run_manifest = {
        "schema_version": SCHEMA_VERSION,
        "created": dt.datetime.now().isoformat(timespec="seconds"),
        "config": json.loads(json.dumps(asdict(cfg), default=str)),
        "policy_summary": policy_summary,
        "features": {k: {kk: (list(vv) if isinstance(vv, tuple) else vv) for kk, vv in v.items()} for k, v in features.items()},
    }
    with open(root / f"run_manifest_{dt.datetime.now():%Y%m%d_%H%M%S}.json", "w") as f:
        json.dump(run_manifest, f, indent=1)

    rng = np.random.default_rng(cfg.seed + 7919)
    ep_counter = 0
    n_success = 0
    t_run = time.time()
    try:
        for suite_name, task_map in env_dict.items():
            for task_id, vec_env in task_map.items():
                # Per-task stream: the wrapper runs one process per task with the same seed, and a shared stream
                # gave every task the identical sequence of shift offsets (found on full_shift16, 2026-09-06).
                rng = np.random.default_rng(cfg.seed + 7919 + 1000 * int(task_id))
                env = vec_env.envs[0]  # LiberoEnv (single, we bypass the vector wrapper)
                max_steps = int(cfg.max_steps_override or env._max_episode_steps)
                # Policy-specific camera mapping may rename cameras (e.g. wrist_image); the dataset always
                # stores agentview as `image` and eye-in-hand as `image2`, matching lerobot/libero.
                cam_main = env.camera_name_mapping.get("agentview_image", "image")
                cam_wrist = env.camera_name_mapping.get("robot0_eye_in_hand_image", "image2")
                for ep_i in range(cfg.n_episodes):
                    ep_seed = cfg.seed + ep_counter
                    t0 = time.time()
                    policy.reset()
                    obs, info = env.reset(seed=ep_seed)
                    ctrl = env._env  # libero ControlEnv (OffScreenRenderEnv)
                    rs_env = ctrl.env  # robosuite / LIBERO problem env
                    init_state_id_used = env.init_state_id - env._reset_stride
                    shift_info: dict = {}
                    shift_tries, shift_valid = 0, True
                    if cfg.init_mode == "shifted":
                        raw, shift_info, shift_tries, shift_valid = sample_shifted_init(
                            ctrl, rs_env, rng, cfg.shift_xy, cfg.shift_yaw_deg, env.num_steps_wait, cfg.shift_max_tries
                        )
                        obs = env._format_raw_obs(raw)
                    priv = PrivilegedReader(rs_env, cfg.max_obj_slots, cfg.max_fixture_joints)
                    init_sim_state = ctrl.get_sim_state()

                    sim_states: list[np.ndarray] = []
                    gripper_cmds: list[np.ndarray] = []  # PandaGripper.current_action: hidden controller state
                    chunk_start_frames: list[int] = []
                    step = 0
                    success = False
                    terminated = False
                    ep_len = 0
                    while step < max_steps:
                        # --- policy forward (mirrors lerobot_eval.rollout)
                        obs_t = preprocess_observation(batchify(obs))
                        obs_t["task"] = [env.task_description]
                        obs_t = env_pre(obs_t)
                        state8 = obs_t[OBS_STATE][0].detach().cpu().numpy().astype(np.float32)
                        obs_t = preprocessor(obs_t)
                        with torch.inference_mode():
                            action_t = policy.select_action(obs_t)
                        action_t = postprocessor(action_t)
                        action_t = env_post({ACTION: action_t})[ACTION]
                        action = action_t[0].detach().cpu().numpy().astype(np.float32)
                        exec_action = action
                        if cfg.action_noise_std > 0:
                            exec_action = np.clip(action + rng.normal(0, cfg.action_noise_std, size=action.shape), -1, 1).astype(np.float32)

                        chunk_step = step % n_action_steps
                        chunk_index = step // n_action_steps
                        if chunk_step == 0 and cfg.save_sim_state:
                            sim_states.append(np.asarray(ctrl.get_sim_state(), dtype=np.float64))
                            gripper_cmds.append(np.array(rs_env.robots[0].gripper.current_action, dtype=np.float64))
                            chunk_start_frames.append(step)

                        # --- privileged read for the pre-step observation
                        raw_now = rs_env._get_observations()
                        priv_frame = priv.read(raw_now)

                        # --- env step
                        obs_next, reward, terminated, truncated, info = env.step(exec_action)
                        success = bool(info.get("is_success", False))
                        step += 1
                        last = terminated or truncated or step >= max_steps

                        frame: dict[str, Any] = {
                            "observation.images.image": np.ascontiguousarray(obs["pixels"][cam_main][::-1, ::-1]),
                            "observation.images.image2": np.ascontiguousarray(obs["pixels"][cam_wrist][::-1, ::-1]),
                            "observation.state": state8,
                            "action": exec_action,
                            "next.reward": np.array([float(reward)], np.float32),
                            "next.done": np.array([bool(last)]),
                            "next.success": np.array([bool(success)]),
                            "chunk.index": np.array([chunk_index], np.int64),
                            "chunk.step": np.array([chunk_step], np.int64),
                            "task": env.task_description,
                        }
                        frame.update(priv_frame)
                        ds.add_frame(frame)
                        ep_len = step
                        obs = obs_next
                        if last:
                            break

                    ep_index = ds.num_episodes
                    ds.save_episode()
                    n_success += int(success)
                    ep_counter += 1
                    meta = {
                        "schema_version": SCHEMA_VERSION,
                        "episode_index": ep_index,
                        "dataset": cfg.dataset_name,
                        "source": cfg.source,
                        "checkpoint_tag": cfg.checkpoint_tag,
                        "policy": policy_summary,
                        "suite": suite_name,
                        "task_id": int(task_id),
                        "task_name": env.task,
                        "task_language": env.task_description,
                        "init_mode": cfg.init_mode,
                        "init_state_id": int(init_state_id_used),
                        "shift_xy": cfg.shift_xy,
                        "shift_yaw_deg": cfg.shift_yaw_deg,
                        "shift_applied": shift_info,
                        "shift_tries": int(shift_tries),  # rejection-sampling attempts (schema v3.1)
                        "shift_valid": bool(shift_valid),  # False = no clean layout found, unshifted layout used
                        "action_noise_std": cfg.action_noise_std,
                        "seed": ep_seed,
                        "success": bool(success),
                        "terminated": bool(terminated),
                        "length": int(ep_len),
                        "max_steps": max_steps,
                        "n_action_steps": n_action_steps,
                        "n_chunks": len(chunk_start_frames),
                        "object_slots": priv.obj_names,
                        "target_objects": priv.target_names,
                        "fixtures": priv.fixture_names,
                        # model-level fixture placement (schema v3.2): LIBERO samples fixture body pos/quat into the MuJoCo
                        # MODEL at every reset (not reproducible from the seed), and qpos/qvel snapshots cannot restore it.
                        "fixture_body_pose": fixture_body_poses(rs_env),
                        "fixture_joint_names": priv.fixture_joint_names,
                        "goal_state": priv.goal_state,
                        "fps": int(cfg.env.fps),
                        "image_hw": [h, w],
                        "wall_time_s": round(time.time() - t0, 2),
                        "recorded_at": dt.datetime.now().isoformat(timespec="seconds"),
                        "notes": cfg.notes,
                    }
                    with open(sidecar_dir / f"episode_{ep_index:06d}.json", "w") as f:
                        json.dump(meta, f, indent=1)
                    if cfg.save_sim_state:
                        np.savez_compressed(
                            sidecar_dir / f"episode_{ep_index:06d}.npz",
                            sim_states=np.stack(sim_states) if sim_states else np.zeros((0,)),
                            gripper_cmd=np.stack(gripper_cmds) if gripper_cmds else np.zeros((0, 2)),
                            chunk_start_frames=np.asarray(chunk_start_frames, np.int64),
                            init_sim_state=np.asarray(init_sim_state, np.float64),
                            object_slots=np.array(priv.obj_names),
                        )
                    with open(root / "episodes.jsonl", "a") as f:
                        f.write(json.dumps({k: meta[k] for k in ("episode_index", "source", "suite", "task_id", "task_language", "init_mode", "success", "length", "seed")}) + "\n")
                    logger.info(
                        f"[ep {ep_index}] {suite_name}[{task_id}] '{env.task_description}' "
                        f"success={success} len={ep_len} chunks={len(chunk_start_frames)} "
                        f"({time.time() - t0:.1f}s) running_success={n_success}/{ep_counter}"
                    )
                # Release this task's MuJoCo/EGL renderer before creating the next one. Keeping many
                # offscreen contexts alive in one process corrupted the heap (glibc abort) after ~9 tasks.
                try:
                    vec_env.close()
                except Exception as e:  # pragma: no cover
                    logger.warning(f"env close failed for {suite_name}[{task_id}]: {e}")
    except Exception:
        logger.error("Recording aborted:\n" + traceback.format_exc())
        raise
    finally:
        ds.finalize()
        for task_map in env_dict.values():
            for vec_env in task_map.values():
                try:
                    vec_env.close()
                except Exception:
                    pass
        logger.info(f"Finalized dataset {root}: {ds.num_episodes} episodes, success {n_success}/{ep_counter}, {time.time() - t_run:.0f}s")


if __name__ == "__main__":
    main()
