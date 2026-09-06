# fail-traj-learn

Learning from failed robot trajectories: segment failed rollouts, turn the segments into ordinal
advantage constraints for an offline-RL critic, and train a small actor that never generated its own
data. Simulation is LIBERO (MuJoCo / robosuite) through LeRobot; real-data validation is planned on
OOPSIE. Method overview: [docs/proposal_overview.md](docs/proposal_overview.md).
Pilot results and data-collection decisions: [docs/pilot_results.md](docs/pilot_results.md).

## Layout

This repository holds code and docs only. Datasets, checkpoints, logs and the LeRobot environment live
in a separate project root outside the repository.

| Where | What |
|---|---|
| `scripts/record/` | Rollout recorder and its wrapper |
| `scripts/pilot/` | Failure-induction pilot stages |
| `scripts/analysis/` | Dataset checks, progress analysis, failure review |
| `scripts/tools/` | Probes, viewer, task lister, plain eval |
| `docs/` | Proposal and pilot write-up |
| `outputs/` | Generated artifacts (videos, montages, contact sheets, review gallery); not tracked |
| `<project root>/lerobot` | LeRobot source checkout with its `.venv` (Python 3.12, extras `libero`, `molmoact2`, `smolvla`) |
| `<project root>/data/full_<stage>__t<k>` | The schema v3 corpus (full run). `data/archive_pre_v3/` holds pilot and validation sets, not for training. |
| `<project root>/logs` | Recorder and pilot logs |
| Hugging Face cache | MolmoAct2 checkpoints, `lerobot/libero` demo dataset |

## Running things

Every shell wrapper reads two environment variables and falls back to built-in defaults:

| Variable | Meaning |
|---|---|
| `PROJ` | Project root holding `lerobot/`, `data/`, `logs/` |
| `SCRIPTS` | This repository's `scripts/` folder |

Python tools read `FTL_PROJ` (same as `PROJ`) and `FTL_WIN_OUT` (where `outputs/` should be written).
Run any wrapper by absolute path, e.g. `bash $SCRIPTS/analysis/accept_run.sh`; `scripts/analysis/py.sh` runs
any analysis script inside the LeRobot venv. Long recordings are one process per task, so a crash or an
interrupted machine loses at most the task in progress; the run scripts are resumable per stage.

### `scripts/record/` — data collection

| Script | Purpose |
|---|---|
| `record_rollouts.py` | Recorder: runs any LeRobot policy in LIBERO one episode at a time, writes a LeRobotDataset with privileged state (object poses, contacts, grasps, fixture joints), chunk bookkeeping, and per-episode sidecars with MuJoCo state snapshots. Same `--policy.*` / `--env.*` CLI as `lerobot-eval`. Shifted initial states are rejection-sampled so no object overlaps or drifts during settling. |
| `record_config.sh` | Recorder wrapper driven by env vars (`NAME SOURCE CKPT NORM_TAG SUITE TASK_IDS N_EP INIT SXY SYAW NOISE SEED EXTRA NOTES`). One process per task, datasets named `<NAME>__t<k>`. `TASK_IDS=` (empty) means all tasks in the suite. Logs to `logs/record_<NAME>__t<k>.log`. |
| `full_run.sh` | The full schema v3 data run: anchor, shifted init at three levels (`LEVELS="4:30 8:60 12:90"`), goal suite, libero_90 keep-list. Resumable with `SKIP_<stage>=1`. Master log `logs/full_run.log`. |
| `full_run_ext.sh` | Waits for `full_run.sh`, then appends the 16 cm shift stage (`full_shift16`). |
| `full_run_ext2.sh` | Waits for `full_run_ext.sh`, archives the contaminated shift datasets, re-records shift 8/12/4 with clean-init rejection sampling. |
| `full_run_ext3.sh` | Waits for `full_run_ext2.sh`; diversity stages: libero_10 at 8 and 12 cm, all goal tasks at 8 cm. |

### `scripts/pilot/` — the failure-induction pilot

| Script | Purpose |
|---|---|
| `pilot_molmoact2.sh` | Stages with the fine-tuned MolmoAct2: anchor, goal tasks, shifted init, 14 libero_90 tasks, 1-flow-step inference. Resumable with `SKIP_<stage>=1`. Master log `logs/pilot_molmoact2.log`. |
| `pilot_base.sh` | Stage D: base MolmoAct2 weights with LIBERO norm stats. |
| `run_after_pilot.sh` | Waits for the main pilot to finish, then runs `pilot_base.sh` (GPU hand-off). |
| `v2_shift_check.sh`, `v3_test.sh` | Schema v2 validation set (30 shifted episodes, 3 object tasks) and schema v3 smoke recording. |
| `calibrate_shift12.sh` | Shift-level calibration (12 cm / 90 deg on the three hardest object tasks). |

### `scripts/analysis/` — dataset checks and triage

| Script | Purpose |
|---|---|
| `py.sh` | Run any script in this folder inside the LeRobot venv: `py.sh <script.py> [args]`. |
| `summarize_datasets.py` | Success rate per dataset and per task from `episodes.jsonl`; groups `<prefix>__t<k>` datasets. |
| `episode_progress.py`, `progress.sh` | Per-episode stage reached (none/reached/grasped/lifted/transported/placed), progress p, stall fraction, and a diagnostic usefulness score u in [-1,1] (curation only, not a training reward). |
| `review_failures.py`, `review.sh` | Contact sheets (agent + wrist frames with grasp/support/contact flags and a signal strip, plus which objects were touched or moved and a wrong-object flag), optional side-by-side mp4, and a json summary per episode; failures only by default. Output: `outputs/review/<dataset>/`. |
| `review_batch.sh`, `review_sheets.sh` | Render videos and sheets for a list of datasets (default: one hard task per stage), or regenerate sheets only; both end by rebuilding the gallery. |
| `build_review_index.py` | Builds `outputs/review/index.html`, a local gallery of every rendered episode with task text, per-object shift, touched objects and badges. |
| `episode_objects.py` | Per-object trace of one episode: start and end pose, distance moved, contact, grasp and airborne frames. Answers "did it pick up the wrong thing?". |
| `episode_end_state.py` | End-of-episode object poses and contact flags for one episode (diagnosing placement failures). |
| `verify_dataset.py`, `verify.sh` | Sanity-check one dataset: schema, privileged signals over time, fixture joints, sidecars, recorded frame vs public demo frame. |
| `check_snapshot_restore.py`, `restore.sh` | Restore sidecar MuJoCo snapshots (plus the gripper command state), replay recorded actions, confirm the sim reaches the next stored snapshot. Prints `RESTORE_OK`. |
| `predicate_artifacts.py`, `artifacts.sh` | Count failed episodes whose target ends geometrically inside the goal container (LIBERO `in_box` is not rotation-correct). |
| `init_state_check.py`, `initcheck.sh` | Frame-0 audit of shifted stages: airborne, far, object-object contact (bad initial states). Args: anchor prefix then shifted prefixes. |
| `accept_run.sh` | Acceptance checks for a finished full run: success rates, progress, artifact count (must be 0), restore spot check, init-state audit, contact sheets. Prints `ACCEPT_OK`. |

### `scripts/tools/` — probes and utilities

| Script | Purpose |
|---|---|
| `probe_libero.py` | Create one env, render a frame, dump raw simulator observation keys, geoms, contacts. |
| `probe_fixtures.py` | List a scene's objects, fixtures, articulated joints, and parsed goal state. |
| `list_tasks.py` | Tasks of a suite with scene folders. |
| `inspect_norm_stats.py` | Embodiment tags in a MolmoAct2 checkpoint's `norm_stats.json`. |
| `render_suites.py` | First-frame montage of several LIBERO tasks. |
| `view_libero.py`, `run_view.sh` | Interactive MuJoCo viewer window. Args: `suite task_id seconds`. |
| `eval_smoke.sh`, `run_smoke.sh` | Plain `lerobot-eval` of MolmoAct2-LIBERO, the independent check on the recorder. |
| `archive_pre_v3.sh` | Move every non-`full_*` dataset into `data/archive_pre_v3/` (pilot, v2, v3 smoke, calibration). |

## Recorded dataset schema (per frame)

Standard: `observation.images.image`, `observation.images.image2` (256x256, 180-degree rotated to
match `lerobot/libero`), `observation.state` (8), `action` (7), `next.reward`, `next.done`,
`next.success`, `task`. Decision structure: `chunk.index`, `chunk.step` (10-step chunks).

Privileged (oracle only, never fed to policies or critics), schema v3:
`priv.obj_pos`, `priv.obj_quat` (12 object slots x 3/4, slot names in the sidecar, read from the simulator
state rather than the lagged observables), `priv.obj_valid`, `priv.target_mask`, `priv.obj_gripper_contact`,
`priv.obj_left_finger_contact`, `priv.obj_right_finger_contact`, `priv.obj_grasped` (both fingers, any finger
geom), `priv.obj_grasped_pads` (both finger pads, the stricter v1 rule), `priv.obj_support_contact` (touching
static scene; in LIBERO the tabletop geom is literally named `floor`), `priv.obj_obj_contact`, `priv.obj_resting`
(support or obj-obj), `priv.arm_contacts`, `priv.gripper_static_contacts`, `priv.gripper_fixture_contacts`
(subset touching a named fixture: handle, knob), `priv.fixture_qpos` / `priv.fixture_valid` (up to 16 one-DoF
fixture joints: drawers, knobs; names in the sidecar), `priv.n_contacts`, `priv.eef_pos`, `priv.eef_quat`,
`priv.gripper_qpos/qvel`, `priv.joint_pos/vel`, `priv.sim_time`.

Sidecar `episode_XXXXXX.json` carries `schema_version`, source policy, task, init protocol, per-object shift
applied (with `yaw_locked` for goal containers, `shift_tries`, `shift_valid`), outcome, object slots, fixtures,
fixture joint names, and the parsed BDDL `goal_state`; `episode_XXXXXX.npz` carries `sim_states` and the
gripper command state `gripper_cmd` at every chunk boundary, enough to restore and branch the simulator.
Archived pilot datasets are schema v1 (no finger/fixture columns, pad-rule grasp) or v2.
