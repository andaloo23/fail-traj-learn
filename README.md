# fail-traj-learn

Learning from failed robot trajectories: segment failed rollouts, turn the segments into ordinal
advantage constraints for an offline-RL critic, and train a policy (SmolVLA) that never generated
its own data. Simulation is LIBERO (MuJoCo / robosuite) through LeRobot; real-data validation is
planned on OOPSIE. Method overview: [docs/proposal_overview.md](docs/proposal_overview.md).
Pilot results and data-collection decisions: [docs/pilot_results.md](docs/pilot_results.md).

## Layout

This Windows folder is the source of truth for code. Heavy state lives on the WSL side.

| Where | What |
|---|---|
| `scripts/record/` | Rollout recorder and its wrapper |
| `scripts/pilot/` | Failure-induction pilot stages |
| `scripts/analysis/` | Dataset checks, progress analysis, failure review |
| `scripts/tools/` | Probes, viewer, task lister, plain eval |
| `docs/` | Proposal and pilot write-up |
| `outputs/` | Small artifacts copied back from WSL (videos, montages, contact sheets); not tracked |
| WSL `~/projects/fail-traj-learn/lerobot` | LeRobot source checkout + `.venv` (Python 3.12, extras libero, molmoact2, smolvla) |
| WSL `~/projects/fail-traj-learn/data/<dataset_name>` | Recorded LeRobotDatasets + `sidecar/` per-episode metadata and MuJoCo snapshots |
| WSL `~/projects/fail-traj-learn/logs` | Recorder and pilot logs |
| WSL `~/.cache/huggingface` | MolmoAct2 checkpoints, lerobot/libero demo dataset |

## Running things

Always launch WSL from PowerShell (Git Bash rewrites `/home/...` paths), and put logic in script
files rather than inline commands:

```powershell
wsl -d Ubuntu-22.04 -- bash /mnt/c/Users/LocalPC/dev/fail-traj-learn/scripts/<folder>/<script>.sh [args]
```

Shell wrappers read `PROJ` (WSL project root) and `SCRIPTS` (this `scripts/` folder as seen from WSL) from the
environment; Python tools read `FTL_PROJ` and `FTL_WIN_OUT`. Defaults point at this machine.

### `scripts/record/` — data collection

| Script | Purpose |
|---|---|
| `record_rollouts.py` | Recorder: runs any LeRobot policy in LIBERO one episode at a time, writes a LeRobotDataset with privileged state (object poses, contacts, grasps, fixture joints), chunk bookkeeping, and per-episode sidecars with MuJoCo state snapshots. Same `--policy.*` / `--env.*` CLI as `lerobot-eval`. |
| `record_config.sh` | Recorder wrapper driven by env vars (`NAME SOURCE CKPT NORM_TAG SUITE TASK_IDS N_EP INIT SXY SYAW NOISE SEED EXTRA NOTES`). One process per task, datasets named `<NAME>__t<k>`. `TASK_IDS=` (empty) means all tasks in the suite. Logs to WSL `logs/record_<NAME>__t<k>.log`. |

### `scripts/pilot/` — the failure-induction pilot

| Script | Purpose |
|---|---|
| `pilot_molmoact2.sh` | Stages with the fine-tuned MolmoAct2: anchor, goal tasks, shifted init, 14 libero_90 tasks, 1-flow-step inference. Resumable with `SKIP_<stage>=1`. Master log `logs/pilot_molmoact2.log`. |
| `pilot_base.sh` | Stage D: base MolmoAct2 weights with LIBERO norm stats. |
| `run_after_pilot.sh` | Waits for the main pilot to finish, then runs `pilot_base.sh` (GPU hand-off). |

### `scripts/analysis/` — dataset checks and triage

| Script | Purpose |
|---|---|
| `summarize_datasets.py` | Success rate per dataset and per task from `episodes.jsonl`; groups `<prefix>__t<k>` datasets. |
| `episode_progress.py`, `progress.sh` | Per-episode stage reached (none/reached/grasped/lifted/transported/placed), progress p, stall fraction, and a diagnostic usefulness score u in [-1,1] (curation only, not a training reward). |
| `review_failures.py`, `review.sh` | Contact sheets (agent + wrist frames with grasp/support/contact flags and a signal strip) and optional side-by-side mp4 per episode, failures only by default. Output: `outputs/review/<dataset>/`. |
| `verify_dataset.py`, `verify.sh` | Sanity-check one dataset: schema, privileged signals over time, fixture joints, sidecars, recorded frame vs public demo frame. |
| `episode_end_state.py` | End-of-episode object poses and contact flags for one episode (diagnosing placement failures). |

### `scripts/tools/` — probes and utilities

| Script | Purpose |
|---|---|
| `probe_libero.py` | Create one env, render a frame, dump raw simulator observation keys, geoms, contacts. |
| `probe_fixtures.py` | List a scene's objects, fixtures, articulated joints, and parsed goal state. |
| `list_tasks.py` | Tasks of a suite with scene folders. |
| `inspect_norm_stats.py` | Embodiment tags in a MolmoAct2 checkpoint's `norm_stats.json`. |
| `render_suites.py` | First-frame montage of several LIBERO tasks. |
| `view_libero.py`, `run_view.sh` | Interactive MuJoCo viewer window through WSLg. Args: `suite task_id seconds`. |
| `eval_smoke.sh`, `run_smoke.sh` | Plain `lerobot-eval` of MolmoAct2-LIBERO, the independent check on the recorder. |

## Recorded dataset schema (per frame)

Standard: `observation.images.image`, `observation.images.image2` (256x256, 180-degree rotated to
match `lerobot/libero`), `observation.state` (8), `action` (7), `next.reward`, `next.done`,
`next.success`, `task`. Decision structure: `chunk.index`, `chunk.step` (10-step chunks).

Privileged (oracle only, never fed to policies or critics), schema v2:
`priv.obj_pos`, `priv.obj_quat` (12 object slots x 3/4, slot names in the sidecar), `priv.obj_valid`,
`priv.target_mask`, `priv.obj_gripper_contact`, `priv.obj_left_finger_contact`, `priv.obj_right_finger_contact`,
`priv.obj_grasped` (both fingers, any finger geom), `priv.obj_grasped_pads` (both finger pads, the stricter v1 rule),
`priv.obj_support_contact` (touching static scene; in LIBERO the tabletop geom is literally named `floor`),
`priv.obj_obj_contact`, `priv.obj_resting` (support or obj-obj), `priv.arm_contacts`,
`priv.gripper_static_contacts`, `priv.gripper_fixture_contacts` (subset touching a named fixture: handle, knob),
`priv.fixture_qpos` / `priv.fixture_valid` (up to 16 one-DoF fixture joints: drawers, knobs; names in the sidecar),
`priv.n_contacts`, `priv.eef_pos`, `priv.eef_quat`, `priv.gripper_qpos/qvel`, `priv.joint_pos/vel`, `priv.sim_time`.

Sidecar `episode_XXXXXX.json` carries `schema_version`, source policy, task, init protocol, shift parameters,
outcome, object slots, fixtures, fixture joint names, and the parsed BDDL `goal_state`; `episode_XXXXXX.npz`
carries `sim_states` at every chunk boundary. Pilot datasets (`data/pilot_*`) are schema v1: no finger/fixture
columns and `priv.obj_grasped` uses the pad rule.
