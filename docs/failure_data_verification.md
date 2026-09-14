# Simulation and oracle-data verification — 2026-09-13

The recorded data passes the structural checks below, and the current r6 exports reproduce exactly.
The semantic labels should still be treated as noisy rule-based supervision, not human-verified
failure explanations or causal action credit. No recording, reference, or label export was changed.

## Scope and current inventory

| Artifact | Episodes | Frames | Status |
|---|---:|---:|---|
| All `data/full_*` recordings (87 datasets) | 2,080 | 458,375 | Structural checks pass |
| Saved references | 2,080 | — | 1,341 r6; 720 r3; 19 r4 |
| `bench/oracle_labels.parquet` | 1,341 | 262,779 | Current r6 export; exact re-export match |
| `bench/oracle_labels_r6_object.parquet` | 1,300 | 251,229 | Current object-subset r6 export; exact match |
| Built `rl/datasets/object_v1` | 1,300 | 251,229 | Fully label-covered; privileged 90d observations |
| Built `rl/datasets/object_v2` | 1,300 | 251,229 | Fully label-covered; observable 2525d observations |

All 2,080 recordings identify the same collecting policy/checkpoint:
`molmoact2_libero / allenai/MolmoAct2-LIBERO`. Setup/task-held-out experiments are possible;
this corpus alone does not support a held-out-collecting-policy or cross-embodiment claim.

The main export contains 898 successes and 443 failures: 1,300 object episodes, 21 `full_goals8`
episodes and 20 `full_l90` episodes. It is not the entire 2,080-episode simulation corpus.

## Checks performed

- All recorded episode/frame keys are unique; frame sequences start at zero without gaps.
- Sidecar lengths, schema v3, FPS and recorded timestamps agree with frame indices.
- All 46,457 chunks follow the regular 10-frame convention, including partial final chunks.
  Recorded chunk indices/steps, snapshot start frames, and snapshot counts agree.
- Recorded actions, observation.state, initial simulator states and chunk snapshots are finite.
- Recorded success flags agree with sidecars. Existing acceptance-audit outcome corrections
  are respected when checking references and built RL episodes.
- Every episode has a saved reference. Reference lengths, FPS, chunk boundaries and success
  agree with recordings; primary roles belong to their allowed sets and event frames are in bounds.
- Both oracle exports have unique keys and agree with the current exporter on every column
  when expanded from the saved references. Companion episode-table key coverage agrees.
- Both built RL datasets have finite observation/action/reward arrays, exact recorded-action
  alignment, complete label coverage, consecutive next-observation alignment, terminal reward
  consistency, and no early episode termination rows.
- All 12 existing `test_oracle_labels.py` tests pass.

Freshly recomputed all 2,080 references from raw parquet telemetry using the current oracle:

| Saved version | Episodes | Different chunk labels under current r6 |
|---|---:|---:|
| r6 | 1,341 | 0; every reference field matches |
| r3 | 720 | 210 |
| r4 | 19 | 8 |

All 739 older references differ at least in their version field. Differences also include attempts,
closures and, for 56 r3 episodes, decisive-chunk assignments. Do not combine versions silently.
Recomputation used a lightweight parquet adapter matching the `Episode` column/chunk interface.
It did not overwrite references or render new annotation videos.

## Simulator replay spot checks

Replayed up to 20 actions from each selected chunk, with the existing snapshot checker:

| Episode | Chunks | Result |
|---|---|---|
| `full_anchor__t0 / 0` (success) | 0, 5 | RESTORE_OK, exact mode |
| `full_shift16__t1 / 18` (recovered success) | 0, 7, 12 | RESTORE_OK, exact mode |
| `full_goals8__t2 / 2` (transport-drop failure) | 0, 5, 6 | RESTORE_OK, approximate fixture mode |

Immediate restored object/end-effector/joint differences were zero in the printed checks, with
no target grasp-flag mismatches during replay. Exact-mode next-snapshot differences were at most
1.8e-10. A 20-step replay from shifted chunk 7 had up to 1.8 mm intermediate object drift even
though its next-chunk snapshot matched; RESTORE_OK is not a guarantee of bitwise trajectory identity.
Rendered-versus-decoded image mean absolute differences were 1.9–2.6 on the 0–255 scale.

The goal-suite scene lacks recorded fixed-fixture poses (pre-v3.2 recording). Its immediate restore
and sampled replay agree closely, but the helper explicitly evaluates it in approximate mode.
This does not establish exact replay for all fixture scenes or long counterfactual continuations.

## Annotation problems relevant to the new model

1. **Known semantic disagreements remain.** The current oracle SHA-256 is
   `5a5fb5321e5e7bd01831dce1f650e526882ef458577a716326795da7d7dca9ff`.
   It matches the frozen source
   used in the [earlier r6 audit](oracle_r6_audit.md). That purposive 12-episode review found clear
   disagreements in four episodes and semantic concerns in four others. This verification is not
   a new visual review and those counts are not a population accuracy estimate. Reproducing the
   implementation does not resolve its failed-acquisition/recovery or retry/aftermath semantics.
2. **Visible failure is not separately labeled.** `visible_failure_chunk` equals
   `decisive_error_chunk` on every exported row; `recoverable_until_chunk` is entirely null.
   Use physical event records for observed event timing, not the visible-failure placeholder.
3. **Action and observation clocks differ at boundaries.** Across current r6 references, 234
   events have an action-credit chunk different from `event.index // 10`: 161 grasps, 45 releases,
   and 28 drops. This follows the oracle's previous-action/next-observation convention; it is not
   necessarily corruption. Preserve both clocks. The loader's observed-event chunk is derived
   from the observed frame; do not replace it with the oracle's action-credit chunk.
4. **Cause is episode-level.** Every exported episode has one constant cause across all frames.
   That does not establish that each local segment has that cause. The new model's segment
   `failure_types` require a deliberate mapping/review rather than broadcasting cause to all chunks.
5. **No per-class exhaustive-review masks exist.** Neither absence of an event nor successful
   outcome establishes a verified negative for every failure type. Build explicit coverage masks.
   No simultaneous grasp/drop/release events were found at a shared frame in saved references,
   so the exporter's first-event-only frame field loses none in this corpus as currently saved.
6. **Coverage is imbalanced and incomplete.** Among 26,664 exported chunks: progress 16,386;
   aftermath 5,402; neutral 3,397; failure-inducing 1,116; recovery 363. There are 404 q=0 chunks.
   There are 28 failed episodes without a primary failure-inducing chunk, and 179 successful
   episodes with one. The latter are valid candidates for recovered-failure supervision, not
   automatic contradictions. These counts alone do not establish semantic correctness.
7. **The current taxonomy is not fully supported.** Episode causes: unclear 703; grasp 302;
   manipulation 164; sequencing_semantic 163; reaching 9. No exported collision/hardware cause
   supervision exists. Physical target-event counts are 1,417 grasps, 305 drops and 268 releases.
   A generic release is not necessarily a failure.
8. **Missed-release labels use outcome-based inference.** The exporter exempts the last target
   release of a successful episode and treats other target releases as missed. It does not
   independently test placement geometry at each release. Treat this as a proxy target pending
   review. There are 21 such release penalties in successful episodes; some can be legitimate
   intermediate mistakes or placements, so this count alone does not identify an export bug.

## Readiness decision

Use `object_v2` for the initial observable-model experiment: its arrays and label joins are
structurally ready. Treat r6 roles as weak supervision, preserve allowed-label ambiguity and q=0
masking, and review a seed set before treating hard labels as trustworthy. Start event supervision
with audited target drops; do not equate all releases with failures. Derive onset chunks from
observed event frames, explicitly mark verified coverage, and avoid importing the broad episode
cause as a per-chunk fact. The [new manifest format](failure_training.md) supports these distinctions.

There is no clean semantic gold-standard pass here. The remaining work is an audited manifest
with grouped splits and corrected/unknown local targets, not fixing corrupt frame arrays.

## Reproduction and evidence

Run from the repository root:

```bash
PY=/home/aliu/projects/fail-traj-learn/lerobot/.venv/bin/python
$PY scripts/analysis/audit_failure_corpus.py --out outputs/failure_data_audit/verification.json
$PY scripts/analysis/recompute_failure_references.py --out outputs/failure_data_audit/recomputed_references.json
$PY -m unittest discover -s scripts/annotate/bench -p 'test_oracle_labels.py' -v
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl $PY scripts/analysis/check_snapshot_restore.py full_anchor__t0 0 --chunks 0,5 --replay 20
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl $PY scripts/analysis/check_snapshot_restore.py full_shift16__t1 18 --chunks 0,7,12 --replay 20
MUJOCO_GL=egl PYOPENGL_PLATFORM=egl $PY scripts/analysis/check_snapshot_restore.py full_goals8__t2 2 --chunks 0,5,6 --replay 20
```

[Structural report](../outputs/failure_data_audit/verification.json),
[fresh reference comparison](../outputs/failure_data_audit/recomputed_references.json),
[anchor replay](../outputs/failure_data_audit/replay_anchor.log),
[shifted replay](../outputs/failure_data_audit/replay_shift.log),
[failure replay](../outputs/failure_data_audit/replay_failure.log), and
[oracle test log](../outputs/failure_data_audit/oracle_tests.log).

This audit did not exhaustively decode videos, re-encode visual features, independently rejudge
all task success predicates, inspect all initial placements, or conduct new human/visual semantic
annotation. The structural report's absence of errors is limited to its listed checks.
