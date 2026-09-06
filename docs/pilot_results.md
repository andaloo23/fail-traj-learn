# Failure-induction pilot, 2026-09-04

Goal: find rollout sources that fail 30 to 70 percent of the time with failures that contain task structure
(a productive prefix and a localizable decisive error), using the LIBERO-fine-tuned MolmoAct2 as the frozen
generator, so the learner (SmolVLA) never sees data from its own family.

All rollouts were recorded with `scripts/record/record_rollouts.py` (one process per task, 10-step chunks, privileged
state and MuJoCo snapshots in sidecars) and analyzed with `scripts/analysis/summarize_datasets.py` and
`scripts/analysis/episode_progress.py`. Datasets live under `data/pilot_*__t<k>` in the project root.

## Results

| Stage | Source | Tasks | Init | Episodes | Success | Failures reaching grasp or later | Verdict |
|---|---|---|---|---|---|---|---|
| A | MolmoAct2-LIBERO | libero_object 0-9 | standard | 50 | 100% | n/a | keep as positive anchor |
| A goal | MolmoAct2-LIBERO | libero_goal 3, 7 | standard | 20 | 90% | 100% (2 of 2) | keep |
| C | MolmoAct2-LIBERO | libero_object 0-9 | shifted 8 cm / 60 deg | 100 | 63% | 76% | **primary failure source** |
| B | MolmoAct2-LIBERO | 14 libero_90 tasks | standard | 140 | 9% | 22% | keep 5 tasks, drop 9 |
| 1-step | MolmoAct2-LIBERO, `num_inference_steps=1` | libero_object 0-9 | standard | 100 | 100% | n/a | drop (no degradation) |
| D | base MolmoAct2 + LIBERO norm stats | libero_object 0-9 | standard | 100 | 0% | 1% | drop (no task grounding) |
| D goal | base MolmoAct2 + LIBERO norm stats | libero_goal 3, 7 | standard | 20 | 0% | 0% | drop |

Total: 550 episodes, 1.1 GB on disk including videos, sidecars, and simulator snapshots.

"Failures reaching grasp or later" is the share of failed episodes whose progress stage (from privileged contact
and pose columns) is grasped, lifted, transported, or placed-but-predicate-false. It is the number that matters:
a source is useful when its failures carry a productive prefix, not when its success rate is high.

## Failure modes observed (all natural, no injected noise)

- **Unstable grasp, re-grasp loop, timeout** (goal task 3; shifted object tasks). OOPSIE cause: grasp, severity low.
- **Wrong object**: policy repeatedly attempts a distractor and never touches the target (shifted object tasks).
  OOPSIE cause: sequencing/semantic.
- **Rim placement**: target set down on the basket rim (z 0.09-0.15, in contact with the basket, not the table);
  LIBERO's `In` predicate requires contact AND center-in-region, so it fails. OOPSIE cause: manipulation.
- **Hold without release**: target carried into the basket and held there until timeout. Stall.
- **Wrong compartment** (libero_90 task 74, 10 of 10): book grasped, transported, inserted into the wrong caddy
  compartment, then 200 frames of aftermath. The cleanest "decisive error then aftermath" trajectories in the pilot.
- **Approach-and-freeze stalls** (most libero_90 kitchen tasks; base checkpoint): reach a fixture or hover, then
  loop with the gripper cycling. Progress about 0.2, no productive segment. Useful only in small quantity as
  examples of the "aftermath" class.

## libero_90 per-task decision

Keep: 74 (book to caddy), 26 (wine bottle to drawer), 38 (moka pot, 2/10 success), 47 (cream cheese to basket,
10/10), 89 (book under shelf, marginal). Drop: 1, 8, 13, 16, 21, 42, 53, 63, 66 (pure stalls or never reaching
the target). Note tasks 47 vs 53: same skill and objects, different living-room layout, 100% vs 0%. The fine-tune
is layout-brittle, which is exactly why unseen scenes must be selected per task.

## Consequences for the full data run

1. Shifted initial states are the volume source. Run at least three shift levels (e.g. 4, 8, 12 cm with matching
   yaw) so competence becomes a dial and the shift level is an ablation axis.
2. Goal tasks 3 and 7 at standard init stay in; consider adding goal tasks 2 (wine bottle on cabinet, collision
   prone) and 6 (cream cheese in bowl).
3. libero_90 contributes only the keep-list tasks, capped.
4. Anchor successes on standard init supply the positive examples for the scarce-successes axis.
5. A second model family (Diffusion Policy or ACT trained on the LIBERO demos, intermediate checkpoints) is still
   needed for the cross-policy experiment; base MolmoAct2 does not fill that role.
6. Dropped levers: single-step inference (no effect), base checkpoint (no task grounding).

## Recorder fixes exposed by the pilot (applied 2026-09-04 late evening, schema v2)

- Grasp flag required both finger *pads*; a wide bottle was carried for 180 frames with the flag at zero.
  Now: per-finger contact columns (any finger geom) and `priv.obj_grasped` = both fingers; the pad rule is kept as
  `priv.obj_grasped_pads`. On a drawer episode the finger rule fires on 61 frames vs 37 for pads.
- Articulated fixture joints (drawers, knobs) are logged in `priv.fixture_qpos`, names in the sidecar; verified on
  libero_goal task 3 (top drawer slide 0 -> -0.16 m while the other three joints stay at 0). Gripper contact with a
  named fixture is separated out as `priv.gripper_fixture_contacts`.
- `priv.obj_resting` = support contact OR object-to-object contact (an object inside the basket has support 0
  because the basket is an object slot, not static scenery).
- The parsed BDDL goal state is stored per episode.
- Pilot datasets remain schema v1; the anchor and shifted stages will be re-recorded in the full run.

## Operational lessons

- One recorder process per task. Many offscreen MuJoCo/EGL renderers in one process corrupted the heap after nine
  tasks and the abort skipped dataset finalization (45 episodes lost, re-recorded).
- A system update restarted the machine mid-run (18:04). Stages are resumable with `SKIP_<stage>=1` (scripts/pilot/pilot_molmoact2.sh).
- Recorder jobs are detached from the launching terminal session; log monitors are not and must be re-armed after a restart.

## Validation pass, 2026-09-05 (schema v2 recordings, snapshot restore, predicate audit)

Recorded 30 schema v2 episodes at shifted init (8 cm / 60 deg) on the three libero_object tasks with the most
pilot failures (`v2_C_shift__t{6,4,0}`: butter, ketchup, alphabet soup). Verify tool, progress tool and contact
sheets all behave on failures and on the basket scene (finger-based grasp, `obj_resting`, goal state in sidecar).

**Snapshot restore works, but needed one hidden state.** `scripts/analysis/check_snapshot_restore.py` reloads a
chunk-boundary MuJoCo snapshot, replays the recorded actions and checks that the simulator lands on the next
stored snapshot. From chunk 0 replay is bit-exact; mid-episode it diverged (object error up to 0.25 m, grasp flags
wrong) because robosuite's `PandaGripper.format_action` keeps an accumulated command (`current_action`, moved by
0.01 per substep and clipped to +-1) that is not part of the MuJoCo state. With that value restored, every checked
chunk on pilot and v2 data reaches the next snapshot within 1e-8 (`RESTORE_OK`). The value can be rebuilt from the
action history; schema v3 also stores it per chunk (`gripper_cmd` in the sidecar npz).

**Logged poses lag the simulator by up to one control step.** robosuite observables are sampled at the first
substep of a control step, so `raw_obs` poses are up to 48 ms old while contacts (read from `sim.data`) are fresh.
Harmless for labels but it made snapshot/column comparisons noisy; schema v3 reads poses, joints and gripper state
from `sim.data` directly.

**Part of the shifted-init failures were predicate artifacts.** LIBERO's `SiteObject.in_box` computes the region
half-extents as `abs(R @ size)` with R the container rotation, so a basket yawed near 45 degrees gets a contain
region a few millimetres wide in one axis (and too wide in the other). Our shifted init yawed the basket as well.
`scripts/analysis/predicate_artifacts.py` applies a rotation-correct box test to the last frame of each failure:

| Dataset | Failures with an `in` goal | Object geometrically inside the basket | Basket region collapsed (<3 cm) |
|---|---|---|---|
| pilot_C_object_shift (v1, 10 tasks) | 37 | 10 | 27 |
| v2_C_shift__t6 (butter) | 6 | 4 | 6 |
| v2_C_shift__t4 (ketchup) | 4 | 1 | 4 |
| v2_C_shift__t0 (alphabet soup) | 5 | 4 | 5 |

Across the 30 v2 episodes: 15 successes, 15 failures, 9 of them artifacts, so the real failure rate on the three
hardest object tasks is about 20 percent rather than 50. Roughly a quarter to a half of the "hold without release" and "rim placement" episodes in the pilot were
correct placements that LIBERO refused, followed by 100+ frames of the policy waiting. Decision: shifted init keeps
the yaw of any object that owns a region named in the goal (`yaw_locked` in `shift_applied`), xy shift unchanged.
The shifted-init failure rate will drop accordingly; the pilot's 63 percent success on stage C is an underestimate
of MolmoAct2's competence under shift and the full run should include a 12 cm level to compensate. Existing pilot
and v2 datasets keep their LIBERO labels; the artifact tool identifies the affected episodes if they are ever used.

Schema v3 (recorder, 2026-09-05): poses from `sim.data`, `gripper_cmd` in the npz, container yaw locked,
`schema_version=3`. Smoke test `v3_test__t6` (4 shifted butter episodes): 4/4 success, `VERIFY_OK`, `RESTORE_OK` with
all pose columns matching the restored simulator exactly and the stored `gripper_cmd` equal to the reconstruction
from the action history, `basket_1` marked `yaw_locked` in `shift_applied`.

## Shift calibration and full run launch, 2026-09-05

`cal_shift12` (12 cm / 90 deg, container yaw locked, tasks 6/4/0, 30 episodes): 16/30 success, 14 failures with
zero predicate artifacts; 64 percent of failures reach grasp or later, 4 never touch the target (policy goes for a
distractor or to the empty basket). Scenes stay physically valid at 12 cm. Full run launched with
`scripts/record/full_run.sh`: anchor (100), shifted 4/8/12 cm (900), goal 2/3/6/7 (120), libero_90 keep-list (100).
Acceptance: `scripts/analysis/accept_run.sh` (artifacts must be 0, restore spot check must pass).

Full run progress (per-stage failures, expected vs actual): anchor 0-2 -> 0/100; shift4 30-60 -> 13/300 (4 cm sits
inside LIBERO's own init-state variation, so the policy is effectively in distribution); shift8 45-75 -> 97/300
(the pilot's corrected 8 cm estimate was too conservative). shift4 is kept as the rare-failure ablation set, not in
the default training mix. A 16 cm stage (`scripts/record/full_run_ext.sh`) is queued after the run as the volume source.

## Shifted initial states were not collision-checked (found 2026-09-05 late, recorder v3.1)

The shift added random offsets without checking overlap. Objects in the object suite sit 10-15 cm apart, so at 4 cm a
close pair can be moved into each other and MuJoCo resolves the interpenetration during the settle steps with a
violent push: objects were found 1.8 m above the table at frame 0 and 6 m away at the end, and in one episode the
target itself was shoved 40 cm. `scripts/analysis/init_state_check.py` audits frame 0 (airborne = no support and no
object contact, far = >45 cm from the table centre, contact = object-object contact):

| Stage | Episodes | Bad initial states | of which failures |
|---|---|---|---|
| full_shift4 | 300 | 7 (2 percent) | 2 |
| full_shift8 | 300 | 68 (23 percent) | 20 |

Fix: `sample_shifted_init` in the recorder rejection-samples the layout: a candidate is rejected if placing it creates
an object-object contact the base layout did not have, or if any object drifts more than 2 cm in xy or 1 cm in z during
the settle steps. At 16 cm it needs 1.8 tries on average (max 4 over 12 base states) and the settled positions equal
the intended offsets exactly. Sidecars record `shift_tries` and `shift_valid`. The contaminated shift4/8/12 datasets
are re-recorded by `scripts/record/full_run_ext2.sh` after the 16 cm stage; the originals move to
`data/archive_pre_v3/contaminated_shift/`. The rejection introduces a bias toward sparser layouts, which is inherent to
any collision-free shift and is documented here.

## Diversity stages (queued 2026-09-05 23:10, `scripts/record/full_run_ext3.sh`)

1,300 of the planned episodes were the ten basket tasks. Added, behind the re-record queue: the long-horizon suite
(libero_10, two-step tasks, the natural source of sequencing failures with a productive first step) at 8 cm on all
ten tasks and at 12 cm on eight (tasks 4 and 6 name plates by "left/right" and "to the right of", which a large shift
can invalidate), and the whole goal suite at 8 cm. 560 episodes, about 5 hours. libero_spatial is skipped on purpose:
its ten tasks identify the target bowl by a spatial relation ("next to the ramekin", "between the plate and the
ramekin"), and independent shifts break that relation while the success test still demands the original bowl.
Predicates checked: `On` for object-on-object is rotation-independent (z order, contact, 3 cm xy); fixture regions
(stove, cabinet drawers, table regions) do not move; movable region owners (basket, caddy, microwave, bowl) keep
their yaw under the existing rule.

Full run continued 2026-09-06: shift16 (clean sampler) 182/300 failures, 0 airborne, 0 contact, mean 2.1 sampling
tries; 41 percent of its failures never touch the target, so 16 cm is the top of the useful range. Two notes from the
audit: the "far" flag needs a 55 cm radius at 16 cm (legitimate placements reach 46 cm), and the recorder used one
random stream per stage so every task saw the same offset sequence; now seeded per task (affects the re-recorded
stages from their later tasks onward, harmless otherwise).
