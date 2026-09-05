# Failure-induction pilot, 2026-09-04

Goal: find rollout sources that fail 30 to 70 percent of the time with failures that contain task structure
(a productive prefix and a localizable decisive error), using the LIBERO-fine-tuned MolmoAct2 as the frozen
generator, so the learner (SmolVLA) never sees data from its own family.

All rollouts were recorded with `scripts/record/record_rollouts.py` (one process per task, 10-step chunks, privileged
state and MuJoCo snapshots in sidecars) and analyzed with `scripts/analysis/summarize_datasets.py` and
`scripts/analysis/episode_progress.py`. Datasets live on the WSL side under `data/pilot_*__t<k>`.

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
- A Microsoft Store auto-update of WSL restarted the VM mid-run (18:04). Stages are resumable with `SKIP_<stage>=1` (scripts/pilot/pilot_molmoact2.sh).
- Jobs launched inside WSL survive a Claude Code session restart; monitors do not and must be re-armed.
